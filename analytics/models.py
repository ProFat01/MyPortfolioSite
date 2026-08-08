"""
analytics/models.py

Two models, kept intentionally simple and append-only:

- PageVisit: one row per tracked page request, written automatically
  by analytics.middleware.VisitorTrackingMiddleware.
- PortfolioEvent: one row per tracked *interaction* (a click on
  "View Project", "Download Presentation", "Book a Meeting", or
  "Send Email") reported by a tiny JS beacon. Page requests and
  clicks are different things — a project's "views" on this site
  are clicks on its link/card, since projects don't have individual
  detail pages to track visits to (see docs).

PRIVACY: raw IP addresses are never stored. `ip_hash` is a salted,
truncated SHA-256 digest of the client IP, used only to approximate
unique visitors and new-vs-returning status. It cannot be reversed
to recover the original IP.
"""

from django.db import models


DEVICE_CHOICES = [
    ('desktop', 'Desktop'),
    ('mobile', 'Mobile'),
    ('tablet', 'Tablet'),
    ('other', 'Other'),
]

EVENT_TYPE_CHOICES = [
    ('project_click', 'Project link click ("View Project")'),
    ('presentation_download', 'Presentation download'),
    ('book_meeting_click', 'Book a Meeting click'),
    ('send_email_click', 'Send Email click'),
]


class PageVisit(models.Model):
    """One recorded page view. Written by VisitorTrackingMiddleware."""

    # Indexed via Meta.indexes below rather than db_index=True here, so
    # each column gets exactly one index instead of a duplicate pair.
    path = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    referrer = models.CharField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    device_type = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='other')
    browser = models.CharField(max_length=40, blank=True)
    operating_system = models.CharField(max_length=40, blank=True)

    # Django session key (created via request.session) — identifies a
    # single browsing session, NOT a person.
    session_key = models.CharField(max_length=40)

    # Salted hash of the client IP — see module docstring. Never the raw IP.
    ip_hash = models.CharField(max_length=64, blank=True)

    # True if this ip_hash had no earlier PageVisit at write time.
    is_new_visitor = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            # Powers "visits over time" / date-range filtering — the
            # single most common dashboard query.
            models.Index(fields=['timestamp'], name='analytics_pv_timestamp_idx'),
            # Powers "most visited pages" grouped counts.
            models.Index(fields=['path'], name='analytics_pv_path_idx'),
            # Powers unique-visitor / new-vs-returning aggregation.
            models.Index(fields=['ip_hash'], name='analytics_pv_ip_hash_idx'),
            # Powers per-session lookups (e.g. approximate session duration).
            models.Index(fields=['session_key'], name='analytics_pv_session_idx'),
        ]

    def __str__(self):
        return f"{self.path} @ {self.timestamp:%Y-%m-%d %H:%M}"


class PortfolioEvent(models.Model):
    """
    One recorded interaction: a click that signals real interest,
    reported by a small JS beacon (see analytics/static/analytics/js/track.js).
    """

    # event_type and timestamp are indexed via the compound Meta.indexes
    # below (a composite index also serves single-column lookups on its
    # leading field, so no separate db_index=True is needed here).
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=255, blank=True, help_text="Page the click happened on")

    # Only meaningful for project_click / presentation_download.
    # Kept as a lazy FK reference (string) so this app has no hard
    # import-time dependency on the portfolio app's model layout.
    project = models.ForeignKey(
        'portfolio.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
    )

    session_key = models.CharField(max_length=40, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp'], name='analytics_pe_timestamp_idx'),
            models.Index(fields=['event_type', 'timestamp'], name='analytics_pe_type_ts_idx'),
            models.Index(fields=['project', 'event_type'], name='analytics_pe_proj_type_idx'),
        ]

    def __str__(self):
        label = self.get_event_type_display()
        return f"{label} — {self.project or self.path}"
