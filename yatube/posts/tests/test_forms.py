import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User
from django.test import Client, TestCase

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создание записи в БД. """
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='TestUser')
        cls.group_dogs = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test_slug_group_dogs',
            description='Тестовое описание группы 1'
        )
        cls.group_cats = Group.objects.create(
            title='Тестовый заголовок группы 2',
            slug='test_slug_group_cats',
            description='Тестовое описание группы 2'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста 1',
            author=cls.test_user,
            group=cls.group_dogs
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.test_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """ Форма создает запись в Post. """
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст поста 2',
            'group': PostFormTests.group_dogs.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostFormTests.test_user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
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
            'group': PostFormTests.group_cats.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(pk=PostFormTests.post.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создание записи в БД. """
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='TestUser')
        cls.group_dogs = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test_slug_group_dogs',
            description='Тестовое описание группы 1'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста 1',
            author=cls.test_user,
            group=cls.group_dogs
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTest.test_user)
        self.guest_client = Client()

    def test_add_comment_to_post_detail_authorized(self):
        """ После успешной отправки комментарий
        появляется на странице поста. """
        form_data = {
            'text': 'Тестовый комментарий',
            'user': CommentFormTest.test_user,
            'author': CommentFormTest.post.author
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTest.post.pk}
            ),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTest.post.pk})
        )
        self.assertEqual(
            response.context.get('comments').last().text,
            form_data['text']
        )

        comment = Comment.objects.get(
            post=CommentFormTest.post.id,
            text=form_data['text'],
            author=form_data['author']
        )
        self.assertTrue(comment)

    def test_add_comment_to_post_detail_anonymus(self):
        """ Неавторизованный пользователь. После отправки,
        комментарий не добавляется в БД. """
        form_data = {
            'text': 'Тестовый комментарий',
            'user': CommentFormTest.test_user,
            'author': CommentFormTest.post.author
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentFormTest.post.pk}
            ),
            data=form_data,
            follow=True
        )
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTest.post.pk})
        )
        self.assertNotEqual(
            response.context.get('comments').last(),
            form_data['text']
        )
        comment = Comment.objects.filter(
            post=CommentFormTest.post.id,
            text=form_data['text'],
            author=form_data['author']
        ).exists()
        self.assertFalse(comment)
