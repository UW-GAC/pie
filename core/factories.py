"""Factory classes for generating test data for the whole project."""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

import factory
import factory.fuzzy

User = get_user_model()
USER_FACTORY_PASSWORD = 'qwerty'


class UserFactory(factory.DjangoModelFactory):
    """Uses Faker fake data to make a fake User object."""

    name = factory.Faker('name')
    email = factory.Faker('email')
    password = make_password(USER_FACTORY_PASSWORD)

    class Meta:
        model = User
        django_get_or_create = ('email',)


class SuperUserFactory(UserFactory):
    """Just like a UserFactory, but super."""

    is_superuser = True
    is_staff = True
