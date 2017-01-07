'''phenotype_inventory URL Configuration

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
'''

from django.conf.urls import include, url
from django.views.generic import TemplateView # for static pages


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),    # static home page
    url(r'^about/$', TemplateView.as_view(template_name="about.html"), name='about'),    # static home page
    url(r'^contact/$', TemplateView.as_view(template_name="contact.html"), name='contact'),    # static home page
    url(r'^pages/', include('django.contrib.flatpages.urls')),    # Flat pages 
    url(r'^admin/', include(admin.site.urls)),    # Admin interface
    url(r'^phenotypes/', include('trait_browser.urls', namespace='trait_browser')),    # Trait browser app
    url('^', include('django.contrib.auth.urls')), # authentication views
    url(r'^profile/', include('profiles.urls', namespace='profiles')),    # relating to user accounts
    url(r'^recipe/', include('recipes.urls', namespace='recipes')),    # Recipes app
    url(r'^auth/', include('authtools.urls')),
]

