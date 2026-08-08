"""
analytics/views.py

Two views:

- track_event: a tiny, public POST endpoint hit by a JS beacon when a
  visitor clicks "View Project", "Download Presentation",
  "Book a Meeting", or "Send Email". CSRF-exempt by design — like
  most analytics beacons, it's an anonymous, non-privileged write
  (no session/account state changes) and exempting it avoids needing
  a CSRF cookie warm-up on every public page. It's deliberately
  narrow: it only accepts a known event_type and an optional
  project id, throttles per session, and never returns any stored
  visitor data back to the caller.

- dashboard: the staff-only Visitor Analytics dashboard, integrated
  into the Jazzmin admin chrome via `{% extends "admin/base_site.html" %}`.
"""

import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import EVENT_TYPE_CHOICES, PortfolioEvent
from .utils import get_client_ip, hash_ip

logger = logging.getLogger(__name__)

_VALID_EVENT_TYPES = {choice for choice, _ in EVENT_TYPE_CHOICES}
_THROTTLE_SECONDS = 3
MAX_BODY_BYTES = 2048


@csrf_exempt
@require_POST
def track_event(request):
    """
    Body: {"event_type": "...", "path": "...", "project_id": <int|null>}
    Always responds 204 on anything acceptable-but-uninteresting
    (e.g. throttled) so the beacon never needs branching logic.
    """
    if len(request.body or b'') > MAX_BODY_BYTES:
        return HttpResponseBadRequest("Payload too large")

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    event_type = payload.get('event_type')
    if event_type not in _VALID_EVENT_TYPES:
        return HttpResponseBadRequest("Unknown event_type")

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key or ''

    # Soft throttle: collapse rapid repeat beacons (double-clicks,
    # accidental re-fires) per session+event_type.
    throttle_key = f"analytics:event:{session_key}:{event_type}:{payload.get('project_id') or ''}"
    if session_key and cache.get(throttle_key):
        return JsonResponse({'status': 'ok'}, status=204)
    if session_key:
        cache.set(throttle_key, True, _THROTTLE_SECONDS)

    project = None
    project_id = payload.get('project_id')
    if project_id and event_type in ('project_click', 'presentation_download'):
        from portfolio.models import Project  # local import: keep apps decoupled
        project = Project.objects.filter(pk=project_id).only('id').first()

    try:
        PortfolioEvent.objects.create(
            event_type=event_type,
            path=str(payload.get('path', ''))[:255],
            project=project,
            session_key=session_key,
            ip_hash=hash_ip(get_client_ip(request)),
        )
    except Exception:
        logger.exception("Failed to record PortfolioEvent")
        # Still return success — a dropped analytics event is never
        # worth surfacing an error to a visitor.

    return JsonResponse({'status': 'ok'}, status=204)


@staff_member_required
def dashboard(request):
    """Renders the dashboard shell; all data loads via dashboard_data (AJAX)."""
    from django.shortcuts import render

    from .reporting import RANGE_CHOICES

    return render(request, 'admin/analytics/dashboard.html', {
        'title': 'Visitor Analytics',
        'range_choices': RANGE_CHOICES,
    })


@staff_member_required
def dashboard_data(request):
    """
    JSON data endpoint the dashboard's JS calls to (re)render stats for
    a selected date range, so switching ranges doesn't reload the page.
    """
    from .reporting import build_dashboard_context

    range_key = request.GET.get('range', '7d')
    start = request.GET.get('start') or None
    end = request.GET.get('end') or None

    data = build_dashboard_context(range_key=range_key, start=start, end=end)
    return JsonResponse(data)
