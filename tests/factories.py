"""Shared factories for the tests."""

import factory
from django.contrib.auth import get_user_model

DEFAULT_PASSWORD = 'correct-horse-battery-staple'


class UserFactory(factory.django.DjangoModelFactory):
    """A saved user with a unique email and a usable password."""

    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.django.Password(DEFAULT_PASSWORD)
