"""
analytics/middleware.py

VisitorTrackingMiddleware — records one PageVisit per qualifying GET
request. Deliberately conservative about what it tracks and how much
work it does per-request, since this runs on every page load:

- Only GET requests, only 2xx HTML responses.
- Skips admin/static/media/analytics/API-ish paths (see analytics.utils).
- Skips staff users (so the site owner's own browsing doesn't pollute
  their own analytics).
- De-dupes rapid repeat hits (e.g. a double navigation, a resource
  that also triggers a full request) via a short-lived cache key
  rather than a database query, so the guard itself is cheap.
- Never raises: any failure in tracking is logged and swallowed so a
  bug here can never break the actual page response.
"""

import logging

from django.core.cache import cache

from .models import PageVisit
from .user_agent import parse_user_agent
from .utils import get_client_ip, hash_ip, should_track_path

logger = logging.getLogger(__name__)

# How long a (session, path) pair is "cooled down" after being recorded,
# to collapse near-duplicate requests (e.g. a page's own sub-requests,
# rapid double-clicks on nav links) into a single PageVisit.
DEDUPE_WINDOW_SECONDS = 5


class VisitorTrackingMiddleware:
    """
    Django middleware, added near the end of MIDDLEWARE (after
    SessionMiddleware and AuthenticationMiddleware, so request.session
    and request.user are available).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            self._maybe_track(request, response)
        except Exception:
            # Tracking must never break the actual response.
            logger.exception("VisitorTrackingMiddleware failed to record a page visit")

        return response

    def _maybe_track(self, request, response):
        if request.method != 'GET':
            return
        if not (200 <= response.status_code < 300):
            return
        if not should_track_path(request.path):
            return

        content_type = response.get('Content-Type', '')
        if content_type and 'text/html' not in content_type:
            return

        # The site owner's own visits (while logged in as staff) skew
        # analytics of their own site — exclude them.
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False) and getattr(user, 'is_staff', False):
            return

        # Ensure a session key exists so visits can be grouped per browsing
        # session without ever touching cookies/identity beyond what
        # Django's session framework already provides.
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or ''

        ip_hash = hash_ip(get_client_ip(request))

        dedupe_key = f"analytics:seen:{session_key}:{request.path}"
        if session_key and cache.get(dedupe_key):
            return
        if session_key:
            cache.set(dedupe_key, True, DEDUPE_WINDOW_SECONDS)

        ua_info = parse_user_agent(request.META.get('HTTP_USER_AGENT', ''))
        is_new_visitor = True
        if ip_hash:
            is_new_visitor = not PageVisit.objects.filter(ip_hash=ip_hash).exists()

        PageVisit.objects.create(
            path=request.path[:255],
            referrer=(request.META.get('HTTP_REFERER', '') or '')[:500],
            user_agent=(request.META.get('HTTP_USER_AGENT', '') or '')[:500],
            device_type=ua_info['device_type'],
            browser=ua_info['browser'],
            operating_system=ua_info['os'],
            session_key=session_key,
            ip_hash=ip_hash,
            is_new_visitor=is_new_visitor,
        )
