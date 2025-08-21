from django.shortcuts import render, get_object_or_404
from .models import Trip

def index(request):
    trips = Trip.objects.filter(is_published=True).select_related("country").order_by("-date_start", "title_full")
    return render(request, "index.html", {"trips": trips})

def trip_detail(request, slug):
    trip = get_object_or_404(Trip, slug=slug, is_published=True)
    return render(request, "trip.html", {"trip": trip})
