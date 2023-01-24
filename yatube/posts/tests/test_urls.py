from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создание записи в БД. """
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test_slug_group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user,
            group=cls.group
        )

    def setUp(self):
        cache.clear()

    def test_url_200_unknonw_user(self):
        """ Не авторизованный пользователь.
        Странички должны возвращать 200. """
        routes = [
            '/',
            f'/group/{StaticURLTests.post.group.slug}/',
            f'/profile/{StaticURLTests.post.author}/',
            f'/posts/{StaticURLTests.post.pk}/',
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_200_knonw_user(self):
        """ Авторизованный пользователь. Странички должны возвращать 200. """
        self.client.force_login(StaticURLTests.test_user)
        routes = [
            f'/posts/{StaticURLTests.post.pk}/edit/',
            '/create/',
            '/follow/'
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_unknonw_page_return_404(self):
        """ Несуществующая страница отдаёт 404. """
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_302_unknonw_user(self):
        """ Не авторизованный пользователь. Проверка редиректа. """
        url_expected_answer = {
            f'/posts/{StaticURLTests.post.pk}/edit/':
            f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/edit/',
            '/create/': '/auth/login/?next=/create/',
            f'/profile/{StaticURLTests.test_user.username}/follow/':
            (f'/auth/login/?next=/profile/{StaticURLTests.test_user.username}'
             f'/follow/'),
            '/follow/': '/auth/login/?next=/follow/'
        }
        for url, expected_answer in url_expected_answer.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, expected_answer)

    def test_url_302_knonw_user(self):
        """ Авторизованный пользователь. Проверка редиректа. """
        self.test_user2 = User.objects.create_user(username='TestUser2')
        self.client.force_login(self.test_user2)
        response = self.client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )

        self.assertRedirects(response, f'/posts/{StaticURLTests.post.pk}/')

    def test_urls_uses_correct_temp(self):
        """ Проверка шаблона. """
        self.client.force_login(StaticURLTests.test_user)
        urls_templates_names = {
            '/': 'posts/index.html',
            f'/group/{StaticURLTests.post.group.slug}/':
            'posts/group_list.html',

            f'/profile/{StaticURLTests.post.author}/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{StaticURLTests.post.pk}/': 'posts/post_detail.html',
            f'/posts/{StaticURLTests.post.pk}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }
        for url, template in urls_templates_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)
