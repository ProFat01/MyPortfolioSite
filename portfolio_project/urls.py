"""
portfolio_project/urls.py
Root URL configuration — wires the admin and the portfolio app.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # needed to serve media in dev
from django.contrib.sitemaps.views import sitemap

from portfolio.sitemaps import StaticViewSitemap, ProjectSitemap
from portfolio.views import robots_txt

sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
}

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # Visitor analytics: public click-tracking beacon + staff-only dashboard
    path('analytics/', include('analytics.urls')),

    # SEO helpers
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),

    # All portfolio-app URLs (defined in portfolio/urls.py)
    path('', include('portfolio.urls')),
]

# Serve uploaded media files during development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
