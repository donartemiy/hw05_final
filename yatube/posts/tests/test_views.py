import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from posts.views import COUNT_POSTS

EXPECT_NUMB_POSTS_PAGE_1 = COUNT_POSTS
EXPECT_NUMB_POSTS_PAGE_2 = 2
NUMB_POSTS_PAGINATOR = 12
NUMB_POSTS = 25
NUMB_POSTS_G1_U1 = 5
# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    def add_entities_to_db(self):
        """ Добавляем записи в БД. """
        self.test_user1 = User.objects.create_user(username='TestUser1')
        self.test_user2 = User.objects.create_user(username='TestUser2')

        self.group1 = Group.objects.create(
            title='Тестовый заголовок группы1',
            slug='test_slug_group1',
            description='Тестовое описание группы1'
        )
        self.group2 = Group.objects.create(
            title='Тестовый заголовок группы2',
            slug='test_slug_group2',
            description='Тестовое описание группы2'
        )
        self.expect_set = set()

        for i in range(NUMB_POSTS):
            if i < NUMB_POSTS_G1_U1:
                Post.objects.create(
                    text=f'Тестовый текст{i}',
                    author=self.test_user1,
                    group=self.group1
                )
                self.expect_set.add(f'Тестовый текст{i}')
            else:
                Post.objects.create(
                    text=f'Тестовый текст{i}',
                    author=self.test_user2,
                    group=self.group2
                )

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
            text='Тестовый текст поста',
            author=cls.test_user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        # Неавторизованный клиент
        self.guest_client = Client()
        # Авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.test_user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_context_pages_uses_correct_template(self):
        """ URL-адрес использует соответствующий шаблон. """
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.post.group.slug}
            ): 'posts/group_list.html',

            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.test_user}
            ): 'posts/profile.html',

            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ): 'posts/post_detail.html',

            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ): 'posts/create_post.html',

            reverse('posts:follow_index'): 'posts/follow.html',

            '/unexisting_page/': 'core/404.html',
        }
        for namspace_name, template in templates_page_names.items():
            with self.subTest(namspace_name=namspace_name):
                response = self.authorized_client.get(namspace_name)
                self.assertTemplateUsed(response, template)

    def test_context_index_count_posts_on_page(self):
        """ Считаем количество постов на странице. """
        self.add_entities_to_db()
        response = self.authorized_client.get(reverse('posts:index'))
        page_object = response.context['page_obj']
        self.assertEqual(len(page_object), EXPECT_NUMB_POSTS_PAGE_1)

    def test_context_group_list(self):
        """ Сравниваем текст постов для определенной группы. """
        self.add_entities_to_db()
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group1.slug})
        )
        result_set = set()
        for i in response.context['page_obj']:
            result_set.add(i.text)
        self.assertEqual(result_set, self.expect_set)

    def test_context_profile(self):
        self.add_entities_to_db()
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.test_user1})
        )
        result_set = set()
        for i in response.context['page_obj']:
            result_set.add(i.text)
        self.assertEqual(result_set, self.expect_set)

    def test_context_post_detail(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object, PostsViewsTests.post)
        self.assertEqual(
            response.context.get('post').text,
            'Тестовый текст поста'
        )
        self.assertEqual(
            response.context['post'].group.title,
            'Тестовый заголовок группы'
        )
        self.assertEqual(
            response.context['post'].author.username,
            PostsViewsTests.test_user.username
        )

    def test_context_post_create(self):
        """Страница с шаблоном сформирована с правильным контекстом. """
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertIn('form', response.context)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post_id'], PostsViewsTests.post.pk)
        # Важный момент, получаем значения формы через instance
        self.assertEqual(
            response.context.get('form').instance,
            PostsViewsTests.post)

    def test_context_additional_check(self):
        reverse_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.post.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.test_user})
        ]
        post = PostsViewsTests.post
        for rev in reverse_list:
            with self.subTest(rev=rev):
                response = self.authorized_client.get(rev)
                page_object = response.context['page_obj']
                self.assertEqual(page_object[0], post)

    def test_authorized_create_comment(self):
        """ Авторизованный пользователь может комментировать посты. """
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertTrue(response.context.get('form'))

    def test_guest_no_create_comment(self):
        """ Неавторизованный пользователь не может комментировать посты. """
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertFalse(response.context.get('form'))

    def test_addition_comment_to_post_detail(self):
        """ После успешной отправки комментарий
        появляется на странице поста. """
        form_data = {
            'text': 'Тестовый комментарий',
            'user': PostsViewsTests.test_user,
            'author': PostsViewsTests.post.author
        }
        # Добавляем комментарий
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        # Получаем страницу после добавления комм-я
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertEqual(
            response.context.get('comments').last().text,
            form_data['text']
        )

    def test_cache(self):
        """ Проверка работы кеша на главной странице. """
        post = Post.objects.create(
            author=self.test_user,
            text='Тестовый пост_Кэш',
            group=self.group,
            image=None
        )
        response1 = (self.authorized_client.get(reverse('posts:index')))
        post.delete()
        cache.clear()
        response2 = (self.authorized_client.get(reverse('posts:index')))
        self.assertNotEqual(response1.content, response2.content)

    def test_img_in_context_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertTrue(response.context['page_obj'][0].image)

    def test_img_in_context_profile(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': PostsViewsTests.test_user})
        )
        self.assertTrue(response.context['page_obj'][0].image)

    def test_img_in_context_grouplist(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PostsViewsTests.post.group.slug})
        )
        self.assertTrue(response.context['page_obj'][0].image)

    def test_img_in_context_detail(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertTrue(response.context['post'].image)

    def test_profile_follow(self):
        """ Авторизованный пользователь. Переход по ссылке
        'profile/<str:username>/follow/' должен создать запись в БД"""
        user_egor_petrovich = User.objects.create_user(
            username='EgorPetrovich'
        )
        # Проверим, что запись отсутсвует в таблице
        self.assertFalse(Follow.objects.filter(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user)
        )
        authorized_client_egor_petrovich = Client()
        authorized_client_egor_petrovich.force_login(user_egor_petrovich)
        authorized_client_egor_petrovich.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'TestUser'})
        )
        # Проверим, что запись появилась
        self.assertTrue(Follow.objects.get(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user)
        )

    def test_profile_unfollow(self):
        user_egor_petrovich = User.objects.create_user(
            username='EgorPetrovich'
        )
        # Создаем запись в таблице
        Follow.objects.create(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user
        )
        self.assertTrue(Follow.objects.get(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user)
        )
        authorized_client_egor_petrovich = Client()
        authorized_client_egor_petrovich.force_login(user_egor_petrovich)
        authorized_client_egor_petrovich.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'TestUser'})
        )
        self.assertFalse(Follow.objects.filter(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user)
        )

    def test_entity_appeared_after_follow(self):
        """ Новая запись пользователя появляется в ленте тех,
        кто на него подписан. """
        # Добавляем пачку постов от имени пользователей TestUser1 и TestUser2
        self.add_entities_to_db()

        user_egor_petrovich = User.objects.create_user(
            username='EgorPetrovich'
        )
        authorized_client_egor_petrovich = Client()
        authorized_client_egor_petrovich.force_login(user_egor_petrovich)

        # Создаем подписку на test_user
        Follow.objects.create(
            user=user_egor_petrovich,
            author=PostsViewsTests.test_user
        )
        response = authorized_client_egor_petrovich.get(
            reverse('posts:follow_index')
        )

        # Для каждого поста на странице сверяем имя автора
        for post in response.context['page_obj']:
            with self.subTest(post=post):
                self.assertEqual(post.author.username, 'TestUser')
                self.assertNotEqual(post.author.username, 'TestUser1')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testovyj_slug',
            description='Тестовое описание',
        )

        posts_list = []
        for i in range(NUMB_POSTS_PAGINATOR):
            posts_list.append(Post(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group)
            )
        # хак для быстрого создания записей
        cls.posts = Post.objects.bulk_create(posts_list)

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.page_name = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}): 'page_obj'
        }

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        for value, expected in self.page_name.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(
                    len(response.context[expected]),
                    EXPECT_NUMB_POSTS_PAGE_1)

    def test_second_page_contains_three_records(self):
        for value, expected in self.page_name.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(
                    len(response.context[expected]),
                    EXPECT_NUMB_POSTS_PAGE_2)
