from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("trip/<slug:slug>/", views.trip_detail, name="trip_detail"),
]
