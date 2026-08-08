"""
portfolio/admin.py
Registers our models with Django's built-in admin panel so you can
add, edit, and delete Profile and Project records at /admin/.
"""

from django.contrib import admin
from .models import Profile, Project, ContactMessage

admin.site.site_header = "Saidu Portfolio Admin"
admin.site.site_title = "Saidu Dashboard"
admin.site.index_title = "Welcome to Control Center"


# ------------------------------------------------------------------
# Profile admin
# ------------------------------------------------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Columns shown in the admin list view
    list_display = ('name', 'title', 'email')


# ------------------------------------------------------------------
# Project admin
# ------------------------------------------------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ('title', 'created_at', 'link', 'has_presentation')  # table columns
    search_fields = ('title', 'description')           # search box
    ordering      = ('-created_at',)                   # newest first

    @admin.display(boolean=True, description="Presentation")
    def has_presentation(self, obj):
        return bool(obj.presentation)


# ------------------------------------------------------------------
# Contact message admin
# ------------------------------------------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display   = ('name', 'email', 'subject', 'created_at', 'notified')
    list_filter    = ('notified', 'created_at')
    search_fields  = ('name', 'email', 'subject', 'message')
    ordering       = ('-created_at',)
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at', 'notified')

    def has_add_permission(self, request):
        # These only ever come from the public contact form.
        return False
