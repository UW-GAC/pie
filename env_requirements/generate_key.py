"""Print a new randomly-generated crypto key, to be used as Django's SECRET_KEY setting."""

from django.utils.crypto import get_random_string

chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
print(get_random_string(50, chars))