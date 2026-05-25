"""
portfolio_project/urls.py
Root URL configuration — wires the admin and the portfolio app.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # needed to serve media in dev

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # All portfolio-app URLs (defined in portfolio/urls.py)
    path('', include('portfolio.urls')),
]

# Serve uploaded media files during development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
