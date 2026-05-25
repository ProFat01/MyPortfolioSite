"""
portfolio/views.py
One view function per page. Each fetches data from the database
and passes it to the matching HTML template.
"""

from django.shortcuts import render
from .models import Profile, Project


def get_profile():
    """
    Helper: returns the first Profile object, or None if none exists yet.
    Used by every view so we don't repeat the same query everywhere.
    """
    return Profile.objects.first()


# ------------------------------------------------------------------
# Home page  →  /
# ------------------------------------------------------------------
def home(request):
    """
    Displays the hero section with the owner's name, title, and a short
    welcome message pulled from the Profile model.
    """
    profile = get_profile()
    context = {
        'profile': profile,
        'page': 'home',          # used to highlight the active nav link
    }
    return render(request, 'portfolio/home.html', context)


# ------------------------------------------------------------------
# About page  →  /about/
# ------------------------------------------------------------------
def about(request):
    """
    Displays the full bio and social links from the Profile model.
    """
    profile = get_profile()
    context = {
        'profile': profile,
        'page': 'about',
    }
    return render(request, 'portfolio/about.html', context)


# ------------------------------------------------------------------
# Projects page  →  /projects/
# ------------------------------------------------------------------
def projects(request):
    """
    Fetches ALL Project records (newest first, controlled by model Meta ordering)
    and passes them to the template as a list.
    """
    all_projects = Project.objects.all()  # QuerySet of every project
    profile      = get_profile()
    context = {
        'projects': all_projects,
        'profile':  profile,
        'page':     'projects',
    }
    return render(request, 'portfolio/projects.html', context)


# ------------------------------------------------------------------
# Contact page  →  /contact/
# ------------------------------------------------------------------
def contact(request):
    """
    Shows email and social links so visitors can reach out.
    No form processing needed — links handle it.
    """
    profile = get_profile()
    context = {
        'profile': profile,
        'page': 'contact',
    }
    return render(request, 'portfolio/contact.html', context)
