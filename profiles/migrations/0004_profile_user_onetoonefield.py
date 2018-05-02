# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion

def remove_previous_profiles(apps, schema_editor):
    """Delete any profiles that previously existed, because they could violate one-to-one relationship."""
    Profile = apps.get_model('profiles', 'Profile')
    Profile.objects.all().delete()


def create_new_profiles(apps, schema_editor):
    """Create a profile for each user."""
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Profile = apps.get_model('profiles', 'Profile')
    for user in User.objects.all():
        Profile.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_userdata_change_to_profile'),
    ]

    operations = [
        migrations.RunPython(remove_previous_profiles),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.RunPython(create_new_profiles),
    ]
