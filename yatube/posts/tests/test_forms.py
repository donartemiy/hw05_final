import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User
from django.test import Client, TestCase

# Временная папка для файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создание записи в БД. """
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)

        cls.group1 = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test_slug_group_1',
            description='Тестовое описание группы 1'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок группы 2',
            slug='test_slug_group_2',
            description='Тестовое описание группы 2'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста 1',
            author=cls.test_user,
            group=cls.group1
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок и фай
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """ Форма создает запись в Post. """
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст поста 2',
            'group': PostFormTests.group1.id,
            'image': uploaded
        }
        # Отправляем POST-запрос
        response = PostFormTests.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostFormTests.test_user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным текстом
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """ Изменение текста и группы при отправке валидной формы. """
        form_data = {
            'text': 'Текст изменён',
            'group': PostFormTests.group2.id
        }
        # Отправляем POST-запрос
        response = PostFormTests.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(pk=PostFormTests.post.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, что текст с группой изменились
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
