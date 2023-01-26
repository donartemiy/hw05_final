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

NUMB_POSTS = 6
NUMB_POSTS_PAGINATOR = 12
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
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
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post_text = 'Текст поста'
        cls.post = Post.objects.create(
            text=cls.post_text,
            author=cls.test_user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
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

    def test_context_to_index_group_list_profile(self):
        """  Соответствует ли ожиданиям словарь 'context',
        передаваемый в шаблон при вызове. Context должен
        - содержать список постов;
        - список постов отфильтрованных по группе;
        - список постов отфильтрованных по пользователю."""
        pages = [
            (reverse('posts:index')),
            (reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.group.slug})),
            (reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.test_user.username}))
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    response.context['page_obj'][0],
                    PostsViewsTests.post)

    def test_context_post_detail(self):
        """  Соответствует ли ожиданиям словарь 'context',
        передаваемый в шаблон при вызове. Context должен содержать
        один пост, отфильтрованный по id. """
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object, PostsViewsTests.post)
        self.assertEqual(
            response.context.get('post').text,
            PostsViewsTests.post_text
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
        """  Соответствует ли ожиданиям словарь 'context',
        передаваемый в шаблон при вызове. Context должен содержать
        форму редактирования поста, отфильтрованного по id. """
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
        """  Соответствует ли ожиданиям словарь 'context',
        передаваемый в шаблон при вызове. Context должен содержать
        форму создания поста. """
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

    def test_authorized_has_form_to_comment(self):
        """ Авторизованный пользователь может комментировать посты. """
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk})
        )
        self.assertTrue(response.context.get('form'))

    def test_cache(self):
        """ Проверка работы кеша на главной странице. """
        post = Post.objects.create(
            author=self.test_user,
            text='Тестовый пост_Кэш',
            group=self.group,
            image=None
        )
        response_first = (self.authorized_client.get(reverse('posts:index')))
        post.delete()
        response_second = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = (self.authorized_client.get(reverse('posts:index')))
        self.assertNotEqual(response_first.content, response_third.content)

    def test_img_on_pages(self):
        """ Проверяем, что на страницах есть картинка. """
        pages = [
            (reverse('posts:index')),
            (reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.test_user})),
            (reverse(
                'posts:group_list',
                kwargs={'slug': PostsViewsTests.post.group.slug})),
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTests.post.pk}))
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                if response.context.get('page_obj'):
                    self.assertTrue(response.context['page_obj'][0].image)
                elif response.context.get('post'):
                    self.assertTrue(response.context['post'].image)
                    self.assertEqual(
                        response.context['post'].image,
                        PostsViewsTests.post.image
                    )

    def test_profile_follow(self):
        """ Авторизованный пользователь. Переход по ссылке
        'profile/<str:username>/follow/' должен создать запись в БД. """
        username = 'mr_blue'
        test_user_red = User.objects.create_user(username=username)

        count_follow_obj = Follow.objects.count()

        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': test_user_red})
        )
        follow_obj = (Follow.objects.get(
            user=PostsViewsTests.test_user,
            author=test_user_red))

        self.assertEqual(count_follow_obj + 1, Follow.objects.count())
        self.assertEqual(follow_obj.user, PostsViewsTests.test_user)
        self.assertEqual(follow_obj.author, test_user_red)

    def test_profile_unfollow(self):
        """ Авторизованный пользователь. Переход по ссылке
        'profile/<str:username>/unfollow/' должен удалить запись из БД. """
        username = 'mr_blue'
        test_user_red = User.objects.create_user(username=username)

        Follow.objects.create(
            user=PostsViewsTests.test_user,
            author=test_user_red
        )
        count_follow_obj = Follow.objects.count()

        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': test_user_red})
        )
        self.assertEqual(Follow.objects.count() + 1, count_follow_obj)
        self.assertFalse(Follow.objects.filter(
            user=PostsViewsTests.test_user,
            author=test_user_red).exists()
        )

    def test_entity_appeared_after_follow(self):
        """ Новая запись пользователя появляется в ленте тех,
        кто на него подписан. """
        username_blue = 'mr_blue'
        test_user_blue = User.objects.create_user(username=username_blue)
        post_blue = Post.objects.create(text='', author=test_user_blue)

        Follow.objects.create(
            user=PostsViewsTests.test_user,
            author=test_user_blue
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.context['page_obj'][0], post_blue)

    def test_no_follow_no_entity(self):
        """ Пост не появляется, если не подписан. """
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertFalse(response.context['page_obj'])


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

        posts = []
        for index in range(NUMB_POSTS_PAGINATOR):
            posts.append(Post(
                author=cls.user,
                text=f'Тестовый пост {index}',
                group=cls.group)
            )
        cls.posts = Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """ Количество постов на 1ых страницах page_name.keys()
        не должно превышать COUNT_POSTS. """
        self.page_name = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): 'page_obj'
        }
        for value, expected in self.page_name.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(
                    len(response.context[expected]),
                    COUNT_POSTS)

    def test_second_page_contains_three_records(self):
        """ Количество постов на 2ых страницах page_name.keys()
        не должно превышать NUMB_POSTS_PAGINATOR - COUNT_POSTS. """
        self.page_name = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): 'page_obj'
        }
        for value, expected in self.page_name.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(
                    len(response.context[expected]),
                    NUMB_POSTS_PAGINATOR - COUNT_POSTS)
