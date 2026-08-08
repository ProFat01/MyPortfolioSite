"""
analytics/tests.py

Covers:
- Automatic page-visit tracking via the middleware (and what it
  correctly skips: admin, static/media, non-GET, staff browsing).
- Dashboard/data endpoints requiring staff auth.
- Unique-visitor / new-vs-returning calculation.
- Date-range filtering.
- Most-visited-pages aggregation.
- Project click + presentation-download tracking via the beacon endpoint.
"""

import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from portfolio.models import Project

from .models import PageVisit, PortfolioEvent
from .reporting import build_dashboard_context
from .utils import hash_ip, should_track_path

User = get_user_model()


class ShouldTrackPathTests(TestCase):
    def test_excludes_admin_static_media_analytics(self):
        self.assertFalse(should_track_path('/admin/'))
        self.assertFalse(should_track_path('/admin/portfolio/project/'))
        self.assertFalse(should_track_path('/static/portfolio/css/style.css'))
        self.assertFalse(should_track_path('/media/project_images/x.png'))
        self.assertFalse(should_track_path('/analytics/dashboard/'))

    def test_excludes_seo_and_file_like_paths(self):
        self.assertFalse(should_track_path('/robots.txt'))
        self.assertFalse(should_track_path('/sitemap.xml'))
        self.assertFalse(should_track_path('/favicon.ico'))
        self.assertFalse(should_track_path('/contact/form-timestamp/'))

    def test_allows_ordinary_pages(self):
        self.assertTrue(should_track_path('/'))
        self.assertTrue(should_track_path('/projects/'))
        self.assertTrue(should_track_path('/contact/'))


class HashIpTests(TestCase):
    def test_same_ip_hashes_consistently(self):
        self.assertEqual(hash_ip('203.0.113.5'), hash_ip('203.0.113.5'))

    def test_different_ips_hash_differently(self):
        self.assertNotEqual(hash_ip('203.0.113.5'), hash_ip('203.0.113.6'))

    def test_never_contains_the_raw_ip(self):
        self.assertNotIn('203.0.113.5', hash_ip('203.0.113.5'))

    def test_empty_ip_returns_empty_string(self):
        self.assertEqual(hash_ip(''), '')


class VisitorTrackingMiddlewareTests(TestCase):
    """Exercises the middleware through the real request/response cycle."""

    def test_ordinary_page_view_is_recorded(self):
        self.assertEqual(PageVisit.objects.count(), 0)
        response = self.client.get('/', HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageVisit.objects.count(), 1)

        visit = PageVisit.objects.first()
        self.assertEqual(visit.path, '/')
        self.assertEqual(visit.device_type, 'desktop')
        self.assertEqual(visit.browser, 'Chrome')
        self.assertEqual(visit.operating_system, 'Windows')
        self.assertTrue(visit.is_new_visitor)
        self.assertNotEqual(visit.ip_hash, '')

    def test_admin_requests_are_not_tracked(self):
        self.client.get('/admin/login/')
        self.assertEqual(PageVisit.objects.count(), 0)

    def test_static_and_media_requests_are_not_tracked(self):
        # These 404 in tests (no filesystem asset), but the middleware
        # should skip them by path regardless of status code.
        self.client.get('/static/portfolio/css/style.css')
        self.client.get('/media/project_images/does-not-exist.png')
        self.assertEqual(PageVisit.objects.count(), 0)

    def test_repeat_request_within_dedupe_window_is_not_double_counted(self):
        self.client.get('/')
        self.client.get('/')
        self.assertEqual(PageVisit.objects.count(), 1)

    def test_staff_browsing_their_own_site_is_not_tracked(self):
        User.objects.create_user('owner', 'owner@example.com', 'pw12345', is_staff=True)
        self.client.login(username='owner', password='pw12345')
        self.client.get('/')
        self.assertEqual(PageVisit.objects.count(), 0)

    def test_second_visit_from_same_ip_is_marked_returning(self):
        self.client.get('/', REMOTE_ADDR='203.0.113.9')
        self.client.get('/projects/', REMOTE_ADDR='203.0.113.9')
        visits = list(PageVisit.objects.order_by('timestamp'))
        self.assertEqual(len(visits), 2)
        self.assertTrue(visits[0].is_new_visitor)
        self.assertFalse(visits[1].is_new_visitor)


class DashboardAccessTests(TestCase):
    def setUp(self):
        cache.clear()  # the dashboard's short-lived cache must not leak between tests
        self.staff = User.objects.create_user('staffuser', 'staff@example.com', 'pw12345', is_staff=True)
        self.regular = User.objects.create_user('regular', 'regular@example.com', 'pw12345', is_staff=False)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertNotEqual(response.status_code, 200)  # redirected to admin login

    def test_dashboard_denies_non_staff(self):
        self.client.login(username='regular', password='pw12345')
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_dashboard_allows_staff(self):
        self.client.login(username='staffuser', password='pw12345')
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_data_requires_staff(self):
        response = self.client.get(reverse('analytics:dashboard_data'))
        self.assertNotEqual(response.status_code, 200)

        self.client.login(username='staffuser', password='pw12345')
        response = self.client.get(reverse('analytics:dashboard_data'))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertIn('summary', payload)


class TrackEventEndpointTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(title="Test Project", description="desc")

    def _post(self, body):
        return self.client.post(
            reverse('analytics:track_event'),
            data=json.dumps(body),
            content_type='application/json',
        )

    def test_project_click_is_recorded(self):
        response = self._post({'event_type': 'project_click', 'project_id': self.project.id, 'path': '/projects/'})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(PortfolioEvent.objects.filter(event_type='project_click', project=self.project).count(), 1)

    def test_presentation_download_is_recorded(self):
        self._post({'event_type': 'presentation_download', 'project_id': self.project.id, 'path': '/projects/'})
        self.assertEqual(
            PortfolioEvent.objects.filter(event_type='presentation_download', project=self.project).count(), 1
        )

    def test_book_meeting_and_send_email_clicks_recorded(self):
        self._post({'event_type': 'book_meeting_click', 'path': '/contact/'})
        self._post({'event_type': 'send_email_click', 'path': '/contact/'})
        self.assertEqual(PortfolioEvent.objects.filter(event_type='book_meeting_click').count(), 1)
        self.assertEqual(PortfolioEvent.objects.filter(event_type='send_email_click').count(), 1)

    def test_unknown_event_type_is_rejected(self):
        response = self._post({'event_type': 'not_a_real_event'})
        self.assertEqual(response.status_code, 400)

    def test_endpoint_does_not_require_csrf_token(self):
        # Public beacon — must work without a CSRF token from an anonymous
        # visitor. Use a client with CSRF checks actively enforced (the
        # default test client disables them, which wouldn't prove anything).
        from django.test import Client

        strict_client = Client(enforce_csrf_checks=True)
        response = strict_client.post(
            reverse('analytics:track_event'),
            data=json.dumps({'event_type': 'send_email_click'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)

    def test_get_is_not_allowed(self):
        response = self.client.get(reverse('analytics:track_event'))
        self.assertEqual(response.status_code, 405)


class ReportingAggregationTests(TestCase):
    """Tests reporting.py directly, independent of HTTP/middleware."""

    def setUp(self):
        cache.clear()  # each test's date-range cache key must start cold

    def _make_visit(self, path='/', ip='203.0.113.1', is_new=True, days_ago=0):
        visit = PageVisit.objects.create(
            path=path,
            session_key='sess-1',
            ip_hash=hash_ip(ip),
            is_new_visitor=is_new,
            device_type='desktop',
            browser='Chrome',
            operating_system='Windows',
        )
        if days_ago:
            visit.timestamp = timezone.now() - timezone.timedelta(days=days_ago)
            visit.save(update_fields=['timestamp'])
        return visit

    def test_unique_visitor_counts_distinct_ip_hashes(self):
        self._make_visit(ip='203.0.113.1')
        self._make_visit(ip='203.0.113.1')  # same visitor, second page
        self._make_visit(ip='203.0.113.2')  # different visitor

        data = build_dashboard_context(range_key='all')
        self.assertEqual(data['summary']['total_visits'], 3)
        self.assertEqual(data['summary']['unique_visitors'], 2)

    def test_most_visited_pages_orders_by_count(self):
        self._make_visit(path='/projects/')
        self._make_visit(path='/projects/', ip='203.0.113.2')
        self._make_visit(path='/contact/', ip='203.0.113.3')

        data = build_dashboard_context(range_key='all')
        top = data['most_visited_pages'][0]
        self.assertEqual(top['path'], '/projects/')
        self.assertEqual(top['count'], 2)

    def test_date_range_filtering_excludes_older_visits(self):
        self._make_visit(days_ago=0)
        self._make_visit(days_ago=40, ip='203.0.113.2')  # outside a 7-day window

        data_7d = build_dashboard_context(range_key='7d')
        data_all = build_dashboard_context(range_key='all')

        self.assertEqual(data_7d['period']['visits'], 1)
        self.assertEqual(data_all['summary']['total_visits'], 2)

    def test_project_click_analytics_reflected_in_context(self):
        project = Project.objects.create(title="Demo", description="d")
        PortfolioEvent.objects.create(event_type='project_click', project=project, path='/projects/')
        PortfolioEvent.objects.create(event_type='project_click', project=project, path='/projects/')

        data = build_dashboard_context(range_key='all')
        self.assertEqual(len(data['projects']['most_viewed']), 1)
        self.assertEqual(data['projects']['most_viewed'][0]['count'], 2)

    def test_empty_database_does_not_error(self):
        data = build_dashboard_context(range_key='30d')
        self.assertEqual(data['summary']['total_visits'], 0)
        self.assertEqual(data['summary']['unique_visitors'], 0)
        self.assertEqual(data['most_visited_pages'], [])
        self.assertIsNone(data['contact']['conversion_rate'])
