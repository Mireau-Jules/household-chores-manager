"""T0.4: ruff configuration and the GitHub Actions workflow.

GitHub only runs the workflow on a real pull request, so these tests read the
workflow file and run its commands the way it does: with only its environment
values set, and with no .env file.
"""

import re
import subprocess
import sys
import tomllib
import unittest

from tests.test_settings import REPO_ROOT, ProjectCopyTestCase

WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'ci.yml'
EXPECTED_COMMANDS = [
    'uv sync --locked',
    'uv run ruff check .',
    'uv run python manage.py makemigrations --check',
    'uv run pytest',
]


def workflow_text():
    return WORKFLOW.read_text()


def top_level_block(name):
    """The non-empty lines under a top-level key of the workflow."""
    match = re.search(rf'^{name}:\n((?:[ \t]+.*\n|\n)*)', workflow_text(), re.MULTILINE)
    assert match, f'The workflow has no top-level {name!r} key.'
    return [line for line in match.group(1).splitlines() if line.strip()]


def workflow_env():
    pairs = (line.strip().split(':', 1) for line in top_level_block('env'))
    return {key: value.strip().strip('\'"') for key, value in pairs}


class RuffTests(unittest.TestCase):
    def test_ruff_is_a_configured_dev_dependency(self):
        pyproject = tomllib.loads((REPO_ROOT / 'pyproject.toml').read_text())
        names = [
            re.split(r'[<>=!~\[; ]', dependency)[0]
            for dependency in pyproject['dependency-groups']['dev']
        ]
        self.assertIn('ruff', names)
        self.assertTrue(pyproject['tool']['ruff']['lint']['select'])

    def test_ruff_check_passes(self):
        result = subprocess.run(
            [sys.executable, '-m', 'ruff', 'check', '.'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class WorkflowTests(unittest.TestCase):
    def test_triggers_on_every_pull_request(self):
        self.assertEqual(top_level_block('on'), ['  pull_request:'])

    def test_installs_from_the_lockfile_then_runs_each_check_in_order(self):
        commands = re.findall(r'(?m)^\s*(?:- )?run: (.+)$', workflow_text())
        self.assertEqual(commands, EXPECTED_COMMANDS)

    def test_no_step_may_fail_without_failing_the_run(self):
        self.assertNotIn('continue-on-error', workflow_text())

    def test_uses_no_repository_secrets(self):
        self.assertNotRegex(workflow_text(), r'\bsecrets\b')

    def test_defines_the_required_secret_key_setting(self):
        self.assertTrue(workflow_env()['SECRET_KEY'])


class WorkflowCommandTests(ProjectCopyTestCase):
    """The copy has no .env file, so settings come only from the workflow."""

    def makemigrations_check(self):
        self.assertFalse((self.project / '.env').exists())
        return self.manage('makemigrations', '--check', **workflow_env())

    def test_makemigrations_check_passes_with_only_the_workflow_values(self):
        result = self.makemigrations_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_makemigrations_check_fails_for_a_field_without_a_migration(self):
        models_file = self.project / 'apps' / 'accounts' / 'models.py'
        source = models_file.read_text()
        self.addCleanup(models_file.write_text, source)
        header = 'class User(AbstractUser):\n'
        self.assertIn(header, source)
        models_file.write_text(
            source.replace(
                header, header + '    ci_probe = models.BooleanField(default=False)\n'
            )
        )

        migrations = sorted((models_file.parent / 'migrations').glob('*.py'))
        result = self.makemigrations_check()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('ci_probe', result.stdout)
        self.assertEqual(
            sorted((models_file.parent / 'migrations').glob('*.py')), migrations
        )
