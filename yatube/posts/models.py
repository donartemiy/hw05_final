from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
NUMB_SIBM = 15


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='Ссылка')
    description = models.TextField(verbose_name='Описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',  # Иная форма записи verbose_name
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )
    comments = models.ForeignKey(
        'Comment',
        null=True,
        on_delete=models.CASCADE,
        verbose_name='Комментарий'
    )

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'posts_rname'

    def __str__(self):
        return self.text[:NUMB_SIBM]


class Comment(models.Model):
    # post = models.SlugField(unique=True, verbose_name='Ссылка')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='comments',
        # verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комменатрия'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        default_related_name = 'comment_rname'
        # default_related_name = 'comments'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='following'
    )
