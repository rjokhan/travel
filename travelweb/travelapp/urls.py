# travelapp/urls.py
from django.urls import path
from . import views

app_name = 'travelapp'   # <-- важно

urlpatterns = [
    path('', views.index, name='index'),
    path('trip/<slug:slug>/', views.trip_detail, name='trip_detail'),

    # если в проекте раньше использовалось имя "city",
    # оставим совместимость:
    path('city/<slug:slug>/', views.trip_detail, name='city'),
]
