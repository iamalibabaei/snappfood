from django.urls import path

from store import views

urlpatterns = [
    path('delay/announce/<uuid:order_uuid>', views.announce_delay, name='announce'),
    path('delay/assign/', views.assign_delayed_order, name='assign'),
    path('delay/report/', views.delay_report, name='report'),
]
