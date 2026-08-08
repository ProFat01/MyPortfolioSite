"""
analytics/reporting.py

All dashboard aggregation logic lives here, separate from the view,
so it's easy to unit-test without going through HTTP.

Performance notes:
- Every query is a single aggregate/annotate call — no per-row Python
  loops over the visit table.
- `TruncDate` + `django.utils.timezone` are used throughout instead of
  naive datetime math, so day boundaries follow settings.TIME_ZONE
  (currently UTC — see README note in the chat response; switching
  TIME_ZONE to "Africa/Lagos" later needs no code change here).
- The whole computed context is cached for CACHE_TTL_SECONDS per
  (range, start, end) combination using Django's default local-memory
  cache, so rapidly reloading/switching the dashboard doesn't re-run
  every query each time.
"""

from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import PageVisit, PortfolioEvent

RANGE_CHOICES = [
    ('today', 'Today'),
    ('7d', 'Last 7 days'),
    ('30d', 'Last 30 days'),
    ('90d', 'Last 90 days'),
    ('all', 'All time'),
    ('custom', 'Custom range'),
]

CACHE_TTL_SECONDS = 60


def _resolve_range(range_key, start=None, end=None):
    """Returns (range_start, range_end) as timezone-aware datetimes; range_start=None means 'all time'."""
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if range_key == 'today':
        return today_start, now
    if range_key == '7d':
        return today_start - timedelta(days=6), now
    if range_key == '30d':
        return today_start - timedelta(days=29), now
    if range_key == '90d':
        return today_start - timedelta(days=89), now
    if range_key == 'all':
        return None, now
    if range_key == 'custom' and start and end:
        try:
            start_dt = timezone.make_aware(datetime.strptime(start, '%Y-%m-%d'))
            end_dt = timezone.make_aware(datetime.strptime(end, '%Y-%m-%d')) + timedelta(days=1)
            if start_dt <= end_dt:
                return start_dt, end_dt
        except ValueError:
            pass

    # Unknown/malformed range_key — safe default.
    return today_start - timedelta(days=6), now


def build_dashboard_context(range_key='7d', start=None, end=None):
    cache_key = f"analytics:dashboard:{range_key}:{start}:{end}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    range_start, range_end = _resolve_range(range_key, start, end)

    visits_qs = PageVisit.objects.filter(timestamp__lte=range_end)
    if range_start:
        visits_qs = visits_qs.filter(timestamp__gte=range_start)

    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # --- All-time summary cards (independent of the selected range) ---
    total_visits = PageVisit.objects.count()
    unique_visitors_total = PageVisit.objects.exclude(ip_hash='').values('ip_hash').distinct().count()
    visits_today = PageVisit.objects.filter(timestamp__gte=today_start).count()
    visits_this_week = PageVisit.objects.filter(timestamp__gte=week_start).count()
    visits_this_month = PageVisit.objects.filter(timestamp__gte=month_start).count()

    # --- Period-scoped stats (respect the selected date range) ---
    period_visits = visits_qs.count()
    period_unique_visitors = visits_qs.exclude(ip_hash='').values('ip_hash').distinct().count()
    new_visitors = visits_qs.filter(is_new_visitor=True).count()
    returning_visitors = max(period_visits - new_visitors, 0)

    daily = (
        visits_qs
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(visits=Count('id'), visitors=Count('ip_hash', distinct=True))
        .order_by('day')
    )
    visits_over_time = [{'date': row['day'].isoformat(), 'visits': row['visits']} for row in daily if row['day']]
    visitors_over_time = [{'date': row['day'].isoformat(), 'visitors': row['visitors']} for row in daily if row['day']]

    most_visited_pages = list(visits_qs.values('path').annotate(count=Count('id')).order_by('-count')[:10])
    top_referrers = list(
        visits_qs.exclude(referrer='').values('referrer').annotate(count=Count('id')).order_by('-count')[:10]
    )
    device_breakdown = list(visits_qs.values('device_type').annotate(count=Count('id')).order_by('-count'))
    browser_breakdown = list(
        visits_qs.exclude(browser='').values('browser').annotate(count=Count('id')).order_by('-count')[:8]
    )
    os_breakdown = list(
        visits_qs.exclude(operating_system='')
        .values('operating_system').annotate(count=Count('id')).order_by('-count')[:8]
    )

    # --- Project analytics ---
    # Projects don't have individual detail pages on this site (they're
    # all listed on one /projects/ page), so "project views" are tracked
    # as clicks on a project's "View Project" link — a stronger signal
    # of interest than a page render anyway.
    events_qs = PortfolioEvent.objects.filter(timestamp__lte=range_end)
    if range_start:
        events_qs = events_qs.filter(timestamp__gte=range_start)

    most_viewed_projects = list(
        events_qs.filter(event_type='project_click', project__isnull=False)
        .values('project__id', 'project__title')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    project_views_daily = (
        events_qs.filter(event_type='project_click')
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    project_views_over_time = [
        {'date': row['day'].isoformat(), 'count': row['count']} for row in project_views_daily if row['day']
    ]
    presentation_downloads = list(
        events_qs.filter(event_type='presentation_download', project__isnull=False)
        .values('project__id', 'project__title')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    book_meeting_clicks = events_qs.filter(event_type='book_meeting_click').count()
    send_email_clicks = events_qs.filter(event_type='send_email_click').count()

    # --- Contact / conversion analytics ---
    # Reuses the EXISTING portfolio.ContactMessage model (the source of
    # truth for real submissions) rather than duplicating it here.
    from portfolio.models import ContactMessage

    contact_qs = ContactMessage.objects.filter(created_at__lte=range_end)
    if range_start:
        contact_qs = contact_qs.filter(created_at__gte=range_start)

    contact_submissions_period = contact_qs.count()
    contact_submissions_today = ContactMessage.objects.filter(created_at__gte=today_start).count()
    contact_submissions_month = ContactMessage.objects.filter(created_at__gte=month_start).count()

    conversion_rate = None
    if period_unique_visitors:
        conversion_rate = round((contact_submissions_period / period_unique_visitors) * 100, 1)

    context = {
        'range_key': range_key,
        'range_start': range_start.isoformat() if range_start else None,
        'range_end': range_end.isoformat(),

        'summary': {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors_total,
            'visits_today': visits_today,
            'visits_this_week': visits_this_week,
            'visits_this_month': visits_this_month,
        },

        'period': {
            'visits': period_visits,
            'unique_visitors': period_unique_visitors,
            'new_visitors': new_visitors,
            'returning_visitors': returning_visitors,
        },

        'charts': {
            'visits_over_time': visits_over_time,
            'visitors_over_time': visitors_over_time,
            'device_breakdown': device_breakdown,
            'most_visited_pages': most_visited_pages[:8],
        },

        'top_referrers': top_referrers,
        'browser_breakdown': browser_breakdown,
        'os_breakdown': os_breakdown,
        'most_visited_pages': most_visited_pages,

        'projects': {
            'most_viewed': most_viewed_projects,
            'views_over_time': project_views_over_time,
            'presentation_downloads': presentation_downloads,
        },

        'engagement': {
            'book_meeting_clicks': book_meeting_clicks,
            'send_email_clicks': send_email_clicks,
        },

        'contact': {
            'submissions_period': contact_submissions_period,
            'submissions_today': contact_submissions_today,
            'submissions_month': contact_submissions_month,
            'conversion_rate': conversion_rate,
        },
    }

    cache.set(cache_key, context, CACHE_TTL_SECONDS)
    return context
