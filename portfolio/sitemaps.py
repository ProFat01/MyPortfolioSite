"""
portfolio/sitemaps.py
Feeds /sitemap.xml — helps search engines discover every page.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return ['portfolio:home', 'portfolio:about', 'portfolio:projects', 'portfolio:contact']

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    priority = 0.6
    changefreq = 'yearly'

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        # Projects don't have individual detail pages (yet) — point back
        # at the Projects listing so they're still indexable.
        return reverse('portfolio:projects')
