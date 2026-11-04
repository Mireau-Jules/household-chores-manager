"""T0.2: the custom user model, which logs in with a unique email (D8)."""

import io
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from django.db.migrations.loader import MigrationLoader
from django.test import SimpleTestCase, TestCase

REPO_ROOT = Path(__file__).resolve().parent.parent
PASSWORD = 'correct-horse-battery-staple'
PROJECT_APPS = ('accounts', 'households', 'chores', 'assignments', 'notifications')
NON_ASCII_EMAILS = (
    'sam@éxample.com',  # domain
    'sam@ÉXAMPLE.com',  # domain, uppercase
    'sám@example.com',  # local part
    'sam@example.com\u00a0',  # non-ASCII whitespace, which str.strip() would remove
    '\uff53am@example.com',  # full-width s, which NFKC would turn into ASCII
)
PUNYCODE_EMAIL = 'sam@xn--xample-9ua.com'


def manage_on_new_database(database, *args):
    """Run manage.py against a throwaway SQLite file, not the local database."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ('DJANGO_SETTINGS_MODULE', 'PYTHONPATH')
    }
    env.update(SECRET_KEY='test-key', DATABASE_URL=f'sqlite:///{database}')
    return subprocess.run(
        [sys.executable, 'manage.py', *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class NewDatabaseTestCase(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name).resolve() / 'empty.sqlite3'


class SettingsAndMigrateTests(NewDatabaseTestCase):
    def test_auth_user_model_is_the_accounts_user(self):
        self.assertEqual(settings.AUTH_USER_MODEL, 'accounts.User')
        self.assertEqual(get_user_model()._meta.label, 'accounts.User')

    def test_migrate_succeeds_on_an_empty_database(self):
        self.assertFalse(self.database.exists())

        result = manage_on_new_database(self.database, 'migrate')

        self.assertEqual(result.returncode, 0, result.stderr)
        with sqlite3.connect(self.database) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        self.assertIn('accounts_user', tables)
        self.assertNotIn('auth_user', tables)


class MigrationOrderTests(NewDatabaseTestCase):
    def plan(self):
        result = manage_on_new_database(self.database, 'showmigrations', '--plan')
        self.assertEqual(result.returncode, 0, result.stderr)
        return [line.split()[-1] for line in result.stdout.splitlines() if line.strip()]

    def test_accounts_initial_comes_before_admin_initial(self):
        plan = self.plan()
        self.assertLess(
            plan.index('accounts.0001_initial'), plan.index('admin.0001_initial')
        )

    def test_accounts_initial_comes_before_every_other_project_migration(self):
        # This stays true as later tasks add migrations to the other apps, so it
        # checks the lasting part of the rule. That no other app has a migration
        # yet is only true for now, so it is checked by hand at handover.
        plan = self.plan()
        first = plan.index('accounts.0001_initial')
        others = [
            position
            for position, name in enumerate(plan)
            if name.split('.')[0] in PROJECT_APPS and name != 'accounts.0001_initial'
        ]
        self.assertTrue(all(first < position for position in others))

    def test_accounts_initial_depends_on_no_other_project_app(self):
        migration = MigrationLoader(None).disk_migrations[('accounts', '0001_initial')]
        apps = {app for app, _ in migration.dependencies}
        self.assertEqual(apps & set(PROJECT_APPS), set())


class AuthenticationTests(TestCase):
    def test_user_is_created_with_no_username(self):
        user = get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertEqual(user.get_username(), 'sam@example.com')
        with self.assertRaises(FieldDoesNotExist):
            get_user_model()._meta.get_field('username')

    def test_authenticates_with_email_and_password(self):
        user = get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertEqual(authenticate(email='sam@example.com', password=PASSWORD), user)

    def test_authenticates_through_the_username_argument_login_forms_use(self):
        user = get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertEqual(
            authenticate(username='sam@example.com', password=PASSWORD), user
        )

    def test_authenticates_with_a_mixed_case_email_exactly_as_it_was_created(self):
        user = get_user_model().objects.create_user('Sam@EXAMPLE.com', PASSWORD)

        self.assertEqual(authenticate(email='Sam@EXAMPLE.com', password=PASSWORD), user)

    def test_password_is_stored_hashed(self):
        user = get_user_model().objects.create_user('sam@example.com', PASSWORD)

        user.refresh_from_db()
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_wrong_password_does_not_authenticate(self):
        get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertIsNone(authenticate(email='sam@example.com', password='wrong'))

    def test_unknown_email_does_not_authenticate(self):
        get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertIsNone(authenticate(email='alex@example.com', password=PASSWORD))

    def test_create_user_gives_no_staff_or_superuser_rights(self):
        user = get_user_model().objects.create_user('sam@example.com', PASSWORD)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class Terminal(io.StringIO):
    """A stdin that createsuperuser accepts as interactive."""

    def isatty(self):
        return True


class CreateSuperuserTests(TestCase):
    def run_interactively(self, *answers):
        prompts = []
        answers = iter(answers)

        def answer(prompt=''):
            prompts.append(prompt)
            return next(answers)

        self.stderr = io.StringIO()
        with (
            mock.patch('builtins.input', answer),
            mock.patch('getpass.getpass', return_value=PASSWORD),
        ):
            call_command(
                'createsuperuser',
                interactive=True,
                stdin=Terminal(),
                stdout=io.StringIO(),
                stderr=self.stderr,
            )
        return prompts

    def run_without_input(self, email):
        call_command(
            'createsuperuser',
            interactive=False,
            email=email,
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )

    def test_asks_for_an_email_and_not_a_username(self):
        prompts = self.run_interactively('root@example.com')

        self.assertEqual(len(prompts), 1)
        self.assertIn('email', prompts[0].lower())
        self.assertNotIn('username', prompts[0].lower())

    def test_creates_a_superuser_who_can_authenticate(self):
        self.run_interactively('root@example.com')

        user = authenticate(email='root@example.com', password=PASSWORD)
        self.assertIsNotNone(user)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_asks_again_after_a_blank_email(self):
        prompts = self.run_interactively('', 'root@example.com')

        self.assertEqual(len(prompts), 2)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_asks_again_after_a_whitespace_only_email(self):
        prompts = self.run_interactively('   ', 'root@example.com')

        self.assertEqual(len(prompts), 2)
        self.assertEqual(
            list(get_user_model().objects.values_list('email', flat=True)),
            ['root@example.com'],
        )

    def test_without_input_rejects_an_empty_or_whitespace_only_email(self):
        for email in ('', '   '):
            with self.subTest(email=email), self.assertRaises(CommandError):
                self.run_without_input(email)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_asks_again_after_a_non_ascii_email(self):
        for email in NON_ASCII_EMAILS:
            with self.subTest(email=email):
                prompts = self.run_interactively(email, 'root@example.com')

                self.assertEqual(len(prompts), 2)
                self.assertEqual(
                    list(get_user_model().objects.values_list('email', flat=True)),
                    ['root@example.com'],
                )
                get_user_model().objects.all().delete()

    def test_without_input_rejects_a_non_ascii_email(self):
        for email in NON_ASCII_EMAILS:
            with self.subTest(email=email), self.assertRaises(CommandError):
                self.run_without_input(email)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_accepts_an_all_ascii_punycode_domain(self):
        self.run_interactively(PUNYCODE_EMAIL)

        self.assertTrue(get_user_model().objects.filter(email=PUNYCODE_EMAIL).exists())

    def test_reports_a_case_variant_as_taken_and_asks_again(self):
        for existing, variant in (
            ('sam@example.com', 'SAM@example.com'),
            ('sam@example.com', 'sam@EXAMPLE.COM'),
            ('Sam@Example.com', 'sam@example.com'),
        ):
            with self.subTest(existing=existing, variant=variant):
                User = get_user_model()
                User.objects.create_user(existing, PASSWORD)

                prompts = self.run_interactively(variant, 'root@example.com')

                self.assertEqual(len(prompts), 2)
                self.assertIn('already taken', self.stderr.getvalue())
                self.assertCountEqual(
                    User.objects.values_list('email', flat=True),
                    [existing, 'root@example.com'],
                )
                User.objects.all().delete()

    def test_reports_a_case_variant_the_same_way_as_an_exact_duplicate(self):
        get_user_model().objects.create_user('sam@example.com', PASSWORD)
        self.run_interactively('sam@example.com', 'first@example.com')
        duplicate_message = self.stderr.getvalue()

        self.run_interactively('SAM@example.com', 'second@example.com')

        self.assertEqual(self.stderr.getvalue(), duplicate_message)

    def test_case_variant_is_rejected_before_the_password_is_asked_for(self):
        get_user_model().objects.create_user('sam@example.com', PASSWORD)
        with (
            mock.patch(
                'builtins.input', side_effect=['SAM@example.com', 'r@example.com']
            ),
            mock.patch('getpass.getpass', return_value=PASSWORD) as getpass,
        ):
            call_command(
                'createsuperuser',
                interactive=True,
                stdin=Terminal(),
                stdout=io.StringIO(),
                stderr=io.StringIO(),
            )
        # One pair of password prompts, for the second email only.
        self.assertEqual(getpass.call_count, 2)

    def test_without_input_reports_a_case_variant_as_taken(self):
        get_user_model().objects.create_user('sam@example.com', PASSWORD)

        with self.assertRaisesMessage(CommandError, 'already taken'):
            self.run_without_input('SAM@example.com')
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_different_emails_are_not_reported_as_taken(self):
        get_user_model().objects.create_user('sam_x@example.com', PASSWORD)

        prompts = self.run_interactively('samyx@example.com')

        self.assertEqual(len(prompts), 1)
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_create_superuser_refuses_to_drop_the_superuser_flags(self):
        manager = get_user_model().objects
        with self.assertRaises(ValueError):
            manager.create_superuser('root@example.com', PASSWORD, is_staff=False)
        with self.assertRaises(ValueError):
            manager.create_superuser('root@example.com', PASSWORD, is_superuser=False)
        self.assertEqual(manager.count(), 0)


class CaseInsensitiveEmailTests(TestCase):
    def assert_rejected_by_the_database(self, email):
        User = get_user_model()
        # Model.objects.create() skips validation and the create_user manager
        # method, so only the database can reject this.
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(email=email)
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_an_email_differing_only_by_letter_case(self):
        get_user_model().objects.create(email='sam@example.com')

        self.assert_rejected_by_the_database('SAM@example.com')
        self.assert_rejected_by_the_database('sam@EXAMPLE.COM')
        self.assert_rejected_by_the_database('Sam@Example.com')

    def test_rejects_a_lowercase_email_when_the_existing_one_is_mixed_case(self):
        get_user_model().objects.create(email='Sam@Example.com')

        self.assert_rejected_by_the_database('sam@example.com')

    def test_rejects_an_identical_email(self):
        get_user_model().objects.create(email='sam@example.com')

        self.assert_rejected_by_the_database('sam@example.com')

    def test_rejects_a_case_variant_through_create_user(self):
        User = get_user_model()
        User.objects.create_user('sam@example.com', PASSWORD)

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user('SAM@EXAMPLE.COM', PASSWORD)
        self.assertEqual(User.objects.count(), 1)

    def test_rejects_changing_an_email_to_a_case_variant_of_another(self):
        User = get_user_model()
        User.objects.create(email='sam@example.com')
        other = User.objects.create(email='alex@example.com')

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=other.pk).update(email='SAM@example.com')
        other.refresh_from_db()
        self.assertEqual(other.email, 'alex@example.com')

    def test_model_validation_reports_a_case_variant(self):
        User = get_user_model()
        User.objects.create(email='sam@example.com')

        with self.assertRaises(ValidationError):
            User(email='SAM@example.com', password='x').full_clean()

    def test_accepts_different_emails(self):
        User = get_user_model()
        User.objects.create(email='sam@example.com')
        User.objects.create(email='alex@example.com')

        self.assertEqual(User.objects.count(), 2)


class EmptyEmailTests(TestCase):
    def test_create_user_rejects_an_empty_email(self):
        for email in ('', '   ', None):
            with self.subTest(email=email), self.assertRaises(ValueError):
                get_user_model().objects.create_user(email, PASSWORD)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_create_superuser_rejects_an_empty_email(self):
        for email in ('', '   ', None):
            with self.subTest(email=email), self.assertRaises(ValueError):
                get_user_model().objects.create_superuser(email, PASSWORD)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_database_rejects_an_empty_email(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            get_user_model().objects.create(email='')
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_database_rejects_clearing_an_email(self):
        User = get_user_model()
        user = User.objects.create(email='sam@example.com')

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=user.pk).update(email='')
        user.refresh_from_db()
        self.assertEqual(user.email, 'sam@example.com')

    def test_model_validation_rejects_an_empty_email(self):
        with self.assertRaises(ValidationError) as caught:
            get_user_model()(email='', password='x').full_clean()
        self.assertIn('email', caught.exception.message_dict)

    def test_model_validation_rejects_a_whitespace_only_email(self):
        with self.assertRaises(ValidationError) as caught:
            get_user_model()(email='   ', password='x').full_clean()
        self.assertIn('email', caught.exception.message_dict)


class NonAsciiEmailTests(TestCase):
    def test_create_user_rejects_a_non_ascii_email(self):
        for email in NON_ASCII_EMAILS:
            with self.subTest(email=email), self.assertRaises(ValidationError):
                get_user_model().objects.create_user(email, PASSWORD)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_create_superuser_rejects_a_non_ascii_email(self):
        for email in NON_ASCII_EMAILS:
            with self.subTest(email=email), self.assertRaises(ValidationError):
                get_user_model().objects.create_superuser(email, PASSWORD)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_model_validation_rejects_a_non_ascii_email(self):
        for email in NON_ASCII_EMAILS:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError) as caught:
                    get_user_model()(email=email, password='x').full_clean()
                self.assertIn('email', caught.exception.message_dict)

    def test_an_all_ascii_punycode_domain_is_accepted(self):
        User = get_user_model()
        User(email=PUNYCODE_EMAIL, password='x').full_clean()
        user = User.objects.create_user(PUNYCODE_EMAIL, PASSWORD)
        self.assertEqual(authenticate(email=PUNYCODE_EMAIL, password=PASSWORD), user)
        user.delete()

        User.objects.create_superuser(PUNYCODE_EMAIL, PASSWORD)
        self.assertEqual(User.objects.count(), 1)
