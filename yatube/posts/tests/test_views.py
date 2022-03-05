from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django import forms
from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адреса используют соответствующие шаблоны."""
        templates_pages_names = {
            'posts/index.html':
            reverse('posts:index'),
            'posts/profile.html':
            reverse('posts:profile', kwargs={'username': self.user}),
            'posts/post_detail.html':
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/group_list.html':
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/create_post.html':
            reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_page_uses_correct_template(self):
        """URL-адрес использует шаблон posts/create_post.html."""
        self.user = User.objects.get(username='auth')
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, 'Тестовый пост')
        self.assertEqual(first_object.group.title, 'Тестовый заголовок')
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.group.description, 'Описание')
        self.assertEqual(first_object.group.slug, 'test-slug')
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'].title, 'Тестовый заголовок')
        self.assertEqual(response.context['page_obj'][0].image,
                         self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group.title, 'Тестовый заголовок')
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, 'Тестовый пост')
        self.assertEqual(response.context['post_count'], 1)
        self.assertEqual(response.context['post'].image, self.post.image)
        self.assertEqual(response.context['comments'][0].text,
                         'Тестовый комментарий')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        # Проверка на наличие нового поста на страницах
        # index, group_list, profile
        self.post = Post.objects.create(
            author=self.user,
            text='Новый пост',
            group=self.group
        )
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for i in urls:
            with self.subTest(i=i):
                response = self.authorized_client.get(i)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, 'Новый пост')

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_page_index(self):
        """Проверка кеширования страницы index"""
        response_1 = self.guest_client.get(reverse('posts:index'))
        cache_content_1 = response_1.content
        Post.objects.get(id=self.post.id).delete()
        response_2 = self.client.get(reverse('posts:index'))
        cache_content_2 = response_2.content
        # Проверяем соответствие кеша до и после удаления поста
        self.assertEqual(cache_content_1, cache_content_2)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        cache_content_3 = response_3.content
        self.assertNotEqual(cache_content_1, cache_content_3)

    def test_profile_follow_and_profile_unfollow(self):
        """Проверяем возможность подписаться и отписаться для авторизованного
        пользователя."""
        count_follower = Follow.objects.filter(user=self.user).count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author})
        )
        count_follower_add = Follow.objects.filter(user=self.user).count()
        self.assertEqual(count_follower_add, count_follower + 1)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post.author})
        )
        count_follower_add = Follow.objects.filter(user=self.user).count()
        self.assertEqual(count_follower_add, count_follower)

    def test_post_added_to_all_followers(self):
        """Проверка наличия поста в ленте подписки"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context_page = response.context['page_obj'][0].text
        self.assertEqual(context_page, 'Тестовый пост')
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post.author})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn('Тестовый пост', response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Описание',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовая пост {i}',
                group=cls.group
            )

    def test_first_page_index_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records(self):
        """Проверка profile."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_group_list_contains_ten_records(self):
        """Проверка group_list."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_group_list_contains_three_records(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
