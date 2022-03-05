from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus


User = get_user_model()


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        response = [
            self.guest_client.get('/about/author/'),
            self.guest_client.get('/about/tech/')
        ]
        for i in response:
            self.assertEqual(i.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        responses = {
            self.guest_client.get('/about/author/'): 'about/author.html',
            self.guest_client.get('/about/tech/'): 'about/tech.html'
        }
        for response, template in responses.items():
            self.assertTemplateUsed(response, template)

    def test_about_pages_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
