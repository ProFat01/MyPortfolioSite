from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    # Public: click-tracking beacon. No visitor data is ever returned.
    path('track/', views.track_event, name='track_event'),

    # Staff-only dashboard (protected by @staff_member_required in views.py).
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),
]
