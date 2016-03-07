"""phenotype_inventory URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.views.generic import TemplateView # for static pages
from django.contrib import admin


urlpatterns = [
    url(r'^home/', TemplateView.as_view(template_name="home.html"), name='home'), # static home page
    url(r'^about/', TemplateView.as_view(template_name="about.html"), name='about'), # static home page
    url(r'^contact/', TemplateView.as_view(template_name="contact.html"), name='contact'), # static home page
    url(r'^pages/', include('django.contrib.flatpages.urls')),   # Flat pages 
    url(r'^admin/', include(admin.site.urls)),                   # Admin interface
    url(r'^trait_browser/', include('trait_browser.urls')),      # Trait browser app
]

# Set the name for the admin site
admin.site.site_header = 'NHLBI TOPMed Phenotype Inventory Administration'