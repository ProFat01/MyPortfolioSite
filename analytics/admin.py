"""
analytics/admin.py

Read-only admin registration for the raw tables — useful for spot
debugging. The dashboard (Admin top menu → Analytics) is the primary
way to consume this data; these list views are secondary.
"""

from django.contrib import admin

from .models import PageVisit, PortfolioEvent


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('path', 'timestamp', 'device_type', 'browser', 'operating_system', 'is_new_visitor')
    list_filter = ('device_type', 'browser', 'operating_system', 'is_new_visitor')
    search_fields = ('path', 'referrer')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False  # only ever created by VisitorTrackingMiddleware

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PortfolioEvent)
class PortfolioEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'project', 'timestamp', 'path')
    list_filter = ('event_type',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False  # only ever created by the track_event beacon endpoint

    def has_change_permission(self, request, obj=None):
        return False
