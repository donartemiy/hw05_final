from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Введите текст посттав',
            'group': 'Выберите значение из выпадающего списка',
            'image': 'Загрузите нужную картинку'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Комментарий'
        }
        help_texts = {
            'text': 'Введите текст комментария'
        }
