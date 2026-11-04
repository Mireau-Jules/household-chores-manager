"""T0.1: project configuration read from the environment and a local .env file.

Each test runs Django in a subprocess against a throwaway copy of the project,
because settings are read once per process and because the copy's BASE_DIR is
isolated from any real .env or db.sqlite3 in the working tree.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parent.parent
MANAGED_VARS = ('SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'DATABASE_URL')
# Split so this file doesn't itself contain the text it searches for.
INSECURE_MARKER = 'django-' + 'insecure'

READ_SETTINGS = """
import json
from django.conf import settings
database = settings.DATABASES['default']
print(json.dumps({
    'SECRET_KEY': settings.SECRET_KEY,
    'DEBUG': settings.DEBUG,
    'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
    'DB_ENGINE': database['ENGINE'],
    'DB_NAME': str(database['NAME']),
    'TEMPLATES_DIRS': [str(path) for path in settings.TEMPLATES[0]['DIRS']],
    'STATICFILES_DIRS': [str(path) for path in settings.STATICFILES_DIRS],
    'STATIC_ROOT': str(settings.STATIC_ROOT),
    'USE_TZ': settings.USE_TZ,
    'TIME_ZONE': settings.TIME_ZONE,
}))
"""

OPEN_DATABASE = """
import django
django.setup()
from django.db import connection
connection.ensure_connection()
"""


def clean_env(**variables):
    """The current environment, without anything that could configure the copy."""
    removed = {*MANAGED_VARS, 'DJANGO_SETTINGS_MODULE', 'PYTHONPATH'}
    env = {key: value for key, value in os.environ.items() if key not in removed}
    env.update(variables)
    return env


class ProjectCopyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.project = Path(tmp.name).resolve() / 'project'
        ignore = shutil.ignore_patterns('__pycache__')
        cls.project.mkdir()
        for name in ('apps', 'config', 'static', 'templates'):
            shutil.copytree(REPO_ROOT / name, cls.project / name, ignore=ignore)
        for name in ('manage.py', '.gitignore', '.env.example'):
            if (REPO_ROOT / name).exists():
                shutil.copy(REPO_ROOT / name, cls.project / name)

    def write_env_file(self, content):
        path = self.project / '.env'
        path.write_text(content)
        self.addCleanup(path.unlink, missing_ok=True)

    def manage(self, *args, **variables):
        return subprocess.run(
            [sys.executable, 'manage.py', *args],
            cwd=self.project,
            env=clean_env(**variables),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_python(self, script, **variables):
        env = clean_env(DJANGO_SETTINGS_MODULE='config.settings', **variables)
        return subprocess.run(
            [sys.executable, '-c', script],
            cwd=self.project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def read_settings(self, **variables):
        variables.setdefault('SECRET_KEY', 'test-key')
        result = self.run_python(READ_SETTINGS, **variables)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)


class SecretKeyTests(ProjectCopyTestCase):
    def test_settings_source_has_no_secret_key_value(self):
        source = (REPO_ROOT / 'config' / 'settings.py').read_text()
        self.assertIsNone(re.search(r"""SECRET_KEY\s*=\s*['"]""", source))
        self.assertIsNone(re.search(r"""['"]SECRET_KEY['"]\s*,""", source))

    def test_no_committable_file_contains_the_insecure_key_marker(self):
        listed = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout.decode()
        offenders = [
            name
            for name in filter(None, listed.split('\0'))
            if name != 'backlog.md'
            and (REPO_ROOT / name).is_file()
            and INSECURE_MARKER.encode() in (REPO_ROOT / name).read_bytes()
        ]
        self.assertEqual(offenders, [])

    def test_check_fails_with_no_secret_key_and_no_env_file(self):
        self.assertFalse((self.project / '.env').exists())
        result = self.manage('check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SECRET_KEY', result.stderr)

    def test_check_fails_with_an_empty_secret_key(self):
        result = self.manage('check', SECRET_KEY='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SECRET_KEY', result.stderr)


class EnvFileTests(ProjectCopyTestCase):
    def test_example_lists_every_variable(self):
        values = dotenv_values(REPO_ROOT / '.env.example')
        self.assertEqual(set(values), set(MANAGED_VARS))

    def test_example_values_are_placeholders(self):
        values = dotenv_values(REPO_ROOT / '.env.example')
        self.assertIn('change-me', values['SECRET_KEY'])
        self.assertNotIn(INSECURE_MARKER, values['SECRET_KEY'])
        self.assertEqual(values['DATABASE_URL'], '')

    def test_git_ignores_env_but_not_the_example(self):
        repo = self.project
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        self.addCleanup(shutil.rmtree, repo / '.git')

        def check_ignore(name):
            return subprocess.run(
                ['git', 'check-ignore', '-q', name], cwd=repo, check=False
            ).returncode

        self.assertEqual(check_ignore('.env'), 0)
        self.assertEqual(check_ignore('.env.example'), 1)

    def test_check_passes_with_env_copied_from_example(self):
        self.write_env_file((REPO_ROOT / '.env.example').read_text())
        result = self.manage('check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shell_takes_priority_over_env_file(self):
        self.write_env_file(
            'SECRET_KEY=from-file\n'
            'DEBUG=True\n'
            'ALLOWED_HOSTS=file.example\n'
            'DATABASE_URL=sqlite:////tmp/from-file.sqlite3\n'
        )
        values = self.read_settings(
            SECRET_KEY='from-shell',
            DEBUG='False',
            ALLOWED_HOSTS='shell.example',
            DATABASE_URL='sqlite:////tmp/from-shell.sqlite3',
        )
        self.assertEqual(values['SECRET_KEY'], 'from-shell')
        self.assertIs(values['DEBUG'], False)
        self.assertEqual(values['ALLOWED_HOSTS'], ['shell.example'])
        self.assertEqual(values['DB_NAME'], '/tmp/from-shell.sqlite3')

    def test_env_file_supplies_values_when_shell_has_none(self):
        self.write_env_file('SECRET_KEY=from-file\nDEBUG=True\n')
        result = self.run_python(READ_SETTINGS)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual(values['SECRET_KEY'], 'from-file')
        self.assertIs(values['DEBUG'], True)


class ParsingTests(ProjectCopyTestCase):
    def test_debug_true(self):
        self.assertIs(self.read_settings(DEBUG='True')['DEBUG'], True)

    def test_debug_false(self):
        self.assertIs(self.read_settings(DEBUG='False')['DEBUG'], False)

    def test_debug_defaults_to_false(self):
        self.assertIs(self.read_settings()['DEBUG'], False)

    def test_two_allowed_hosts_in_the_example_format(self):
        example = dotenv_values(REPO_ROOT / '.env.example')['ALLOWED_HOSTS']
        hosts = example.split(',')
        self.assertEqual(len(hosts), 2)
        self.assertEqual(
            self.read_settings(ALLOWED_HOSTS=example)['ALLOWED_HOSTS'], hosts
        )

    def test_allowed_hosts_defaults_to_empty(self):
        self.assertEqual(self.read_settings()['ALLOWED_HOSTS'], [])


class DatabaseTests(ProjectCopyTestCase):
    def assert_default_sqlite(self, values):
        self.assertEqual(values['DB_ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(values['DB_NAME'], str(self.project / 'db.sqlite3'))

    def test_unset_database_url_uses_project_sqlite(self):
        self.assert_default_sqlite(self.read_settings())

    def test_empty_database_url_uses_project_sqlite(self):
        self.assert_default_sqlite(self.read_settings(DATABASE_URL=''))

    def test_empty_database_url_in_env_file_uses_project_sqlite(self):
        self.write_env_file('SECRET_KEY=from-file\nDATABASE_URL=\n')
        self.assert_default_sqlite(self.read_settings())

    def test_another_sqlite_url_uses_that_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'other.sqlite3'
            url = f'sqlite:///{path}'
            values = self.read_settings(DATABASE_URL=url)
            self.assertEqual(values['DB_ENGINE'], 'django.db.backends.sqlite3')
            self.assertEqual(values['DB_NAME'], str(path))

            result = self.run_python(OPEN_DATABASE, SECRET_KEY='k', DATABASE_URL=url)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.exists())


class DependencyTests(unittest.TestCase):
    def test_dj_database_url_is_a_dependency(self):
        pyproject = tomllib.loads((REPO_ROOT / 'pyproject.toml').read_text())
        names = [
            re.split(r'[<>=!~\[; ]', dependency)[0]
            for dependency in pyproject['project']['dependencies']
        ]
        self.assertIn('dj-database-url', names)

    def test_lockfile_matches_pyproject(self):
        result = subprocess.run(
            ['uv', 'lock', '--check'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class PathsAndTimeTests(ProjectCopyTestCase):
    def test_templates_dirs_includes_templates(self):
        self.assertIn(
            str(self.project / 'templates'), self.read_settings()['TEMPLATES_DIRS']
        )

    def test_staticfiles_dirs_includes_static(self):
        self.assertIn(
            str(self.project / 'static'), self.read_settings()['STATICFILES_DIRS']
        )

    def test_collectstatic_writes_to_static_root_and_leaves_git_status_unchanged(self):
        repo = self.project
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        self.addCleanup(shutil.rmtree, repo / '.git')

        def status():
            return subprocess.run(
                ['git', 'status', '--short'],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

        before = status()

        result = self.manage('collectstatic', '--noinput', SECRET_KEY='k')
        self.assertEqual(result.returncode, 0, result.stderr)

        static_root = Path(self.read_settings()['STATIC_ROOT'])
        self.addCleanup(shutil.rmtree, static_root, ignore_errors=True)
        self.assertTrue((static_root / 'admin').is_dir())
        self.assertEqual(status(), before)

    def test_time_zone_support_is_still_utc(self):
        values = self.read_settings()
        self.assertIs(values['USE_TZ'], True)
        self.assertEqual(values['TIME_ZONE'], 'UTC')
