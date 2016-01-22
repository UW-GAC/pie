from django.shortcuts import render, get_object_or_404
from .models          import HomeContent

def home_page(request):
    home_items = HomeContent.objects.all()
    return render(request, 'home/home_page.html', {'home_items' : home_items})