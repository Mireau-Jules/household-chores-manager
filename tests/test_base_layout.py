"""T0.5: the base layout, Django messages and the custom 403 and 404 pages.

No screens exist yet, so this module is its own URLconf with test-only views.
"""

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import RequestContext, Template
from django.templatetags.static import static
from django.test import TestCase, override_settings
from django.urls import path

SITE_NAME = 'Household Chores Manager'
STYLESHEET = 'css/site.css'
PAGE_CONTENT = 'Test-only page content'
MESSAGE = 'Your test-only change was saved'
UNSAFE_MESSAGE = '<script>alert(1)</script>'
FORBIDDEN_REASON = 'Test-only reason that must stay private'


def page(request):
    template = Template(
        '{% extends "base.html" %}{% block content %}' + PAGE_CONTENT + '{% endblock %}'
    )
    return HttpResponse(template.render(RequestContext(request)))


def set_message(request):
    messages.success(request, MESSAGE)
    return redirect('page')


def set_unsafe_message(request):
    messages.error(request, UNSAFE_MESSAGE)
    return redirect('page')


def forbidden(request):
    raise PermissionDenied(FORBIDDEN_REASON)


urlpatterns = [
    path('page/', page, name='page'),
    path('set-message/', set_message),
    path('set-unsafe-message/', set_unsafe_message),
    path('forbidden/', forbidden),
]


@override_settings(ROOT_URLCONF=__name__)
class BaseLayoutTests(TestCase):
    def test_page_uses_base_layout(self):
        response = self.client.get('/page/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, PAGE_CONTENT)

    def test_navigation_area_shows_the_site_name(self):
        response = self.client.get('/page/')

        self.assertRegex(
            response.content.decode(), rf'(?s)<nav\b[^>]*>.*{SITE_NAME}.*</nav>'
        )

    def test_includes_a_viewport_meta_tag(self):
        response = self.client.get('/page/')

        self.assertContains(
            response,
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            html=True,
        )

    def test_loads_the_project_stylesheet_from_static(self):
        response = self.client.get('/page/')

        self.assertContains(
            response, f'<link rel="stylesheet" href="{static(STYLESHEET)}">', html=True
        )
        found = finders.find(STYLESHEET)
        self.assertIsNotNone(found)
        self.assertEqual(Path(found).parent.parent, Path(settings.BASE_DIR) / 'static')


@override_settings(ROOT_URLCONF=__name__)
class MessagesTests(TestCase):
    def test_message_appears_on_the_next_page_and_not_the_one_after(self):
        next_page = self.client.get('/set-message/', follow=True)

        self.assertEqual(next_page.redirect_chain, [('/page/', 302)])
        self.assertContains(next_page, MESSAGE)
        self.assertTemplateUsed(next_page, 'base.html')

        page_after = self.client.get('/page/')

        self.assertEqual(page_after.status_code, 200)
        self.assertNotContains(page_after, MESSAGE)

    def test_page_without_a_message_has_no_message_list(self):
        response = self.client.get('/page/')

        self.assertNotContains(response, 'class="messages"')

    def test_message_text_is_escaped(self):
        response = self.client.get('/set-unsafe-message/', follow=True)

        self.assertNotContains(response, UNSAFE_MESSAGE)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')


@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
class PermissionDeniedPageTests(TestCase):
    def test_permission_denied_returns_the_custom_403_page(self):
        response = self.client.get('/forbidden/')

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, SITE_NAME, status_code=403)
        self.assertContains(response, 'Permission denied', status_code=403)

    def test_page_does_not_reveal_the_exception_message(self):
        response = self.client.get('/forbidden/')

        self.assertNotContains(response, FORBIDDEN_REASON, status_code=403)


@override_settings(DEBUG=False)
class NotFoundPageTests(TestCase):
    """Uses the project's real URLconf, so these need no test-only views."""

    def test_unknown_url_returns_the_custom_404_page(self):
        response = self.client.get('/no-such-page/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, SITE_NAME, status_code=404)
        self.assertContains(response, 'Page not found', status_code=404)

    def test_page_does_not_repeat_the_requested_path(self):
        response = self.client.get('/no-such-page-marker/')

        self.assertNotContains(response, 'no-such-page-marker', status_code=404)
