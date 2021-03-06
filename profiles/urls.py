"""URL configuration for the user_accounts app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /accounts.
"""

from django.conf.urls import url

from . import views


app_name = 'profiles'

urlpatterns = [
    # General views
    url(r'^$', views.Profile.as_view(), name='profile'),
]
