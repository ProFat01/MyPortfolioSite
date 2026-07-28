"""
portfolio/urls.py
URL patterns for the portfolio app.
Each path() maps a URL to a view function defined in views.py.
"""

from django.urls import path
from . import views   # import views from the same package (the portfolio app)

# app_name lets us use {% url 'portfolio:home' %} in templates
app_name = 'portfolio'

urlpatterns = [
    path('',           views.home,     name='home'),      # /
    path('about/',     views.about,    name='about'),     # /about/
    path('projects/',  views.projects, name='projects'),  # /projects/
    path('contact/',   views.contact,  name='contact'),   # /contact/

    # Used by the contact page's anti-spam JS to timestamp form render time
    path('contact/form-timestamp/', views.contact_form_timestamp, name='contact_form_timestamp'),
]
