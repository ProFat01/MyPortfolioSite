"""
portfolio/admin.py
Registers our models with Django's built-in admin panel so you can
add, edit, and delete Profile and Project records at /admin/.
"""

from django.contrib import admin
from .models import Profile, Project


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
    list_display  = ('title', 'created_at', 'link')   # table columns
    search_fields = ('title', 'description')           # search box
    ordering      = ('-created_at',)                   # newest first
