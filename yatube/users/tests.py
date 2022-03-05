from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_guest_client_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_pages_names = {
            'users/login.html':
            reverse('users:login'),
            'users/signup.html':
            reverse('users:signup'),
            'users/password_reset_form.html':
            reverse('users:password_reset'),
            'users/password_reset_done.html':
            reverse('users:password_reset_done'),
            'users/password_reset_complete.html':
            reverse('users:password_reset_complete')
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_authorized_client_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_pages_names = {
            'users/password_change_form.html':
            reverse('users:password_change'),
            'users/password_change_done.html':
            reverse('users:password_change_done'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class UserCreateTests(TestCase):
    """Проверка создания нового пользователя."""
    def setUp(self):
        self.registration_data = {
            'username': 'testuser',
            'password': 'secret',
        }
        self.user = User.objects.create_user(**self.registration_data)

    def test_login(self):
        """Проверка контекста при создании пользователя."""
        response = self.client.post(
            '/auth/login/',
            self.registration_data, follow=True
        )
        self.assertTrue(response.context['user'].is_active)
