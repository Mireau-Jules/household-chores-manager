"""T0.3: the shared factories work against the test database."""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

from tests.factories import DEFAULT_PASSWORD, UserFactory


class UserFactoryTests(TestCase):
    def test_saves_a_user_that_can_be_read_back(self):
        user = UserFactory()

        saved = get_user_model().objects.get(pk=user.pk)

        self.assertEqual(saved.email, user.email)
        self.assertTrue(saved.check_password(DEFAULT_PASSWORD))

    def test_saves_to_the_test_database(self):
        UserFactory()

        database = connection.settings_dict['NAME']

        self.assertTrue(
            connection.creation.is_in_memory_db(database) or 'test' in str(database),
            f'{database} is not a test database',
        )

    def test_two_calls_give_two_users_with_different_emails(self):
        first = UserFactory()
        second = UserFactory()

        self.assertNotEqual(first.pk, second.pk)
        self.assertNotEqual(first.email, second.email)
        self.assertEqual(get_user_model().objects.count(), 2)
