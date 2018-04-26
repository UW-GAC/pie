"""phenotype_inventory URL Configuration.

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

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView  # For static pages.


urlpatterns = [
    # Non-app custom pages.
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),
    url(r'^about/$', TemplateView.as_view(template_name="about.html"), name='about'),
    url(r'^contact/$', TemplateView.as_view(template_name="contact.html"), name='contact'),
    # Django-provided apps.
    url(r'^pages/', include('django.contrib.flatpages.urls')),  # Flat pages.
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),  # Documentation in the admin.
    url(r'^admin/', admin.site.urls),  # Admin interface.
    url(r'^', include('django.contrib.auth.urls')),  # Authentication views.
    # 3rd-party apps.
    url(r'^auth/', include('authtools.urls')),
    # Custom apps.
    url(r'^phenotypes/', include('trait_browser.urls')),
    url(r'^profiles/', include('profiles.urls')),
    url(r'^recipes/', include('recipes.urls')),
    url(r'^tags/', include('tags.urls')),
]

# Include URLs for django-debug-toolbar if DEBUG=True
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
