"""Что тут происходит?
В шаблон users/signup.html будет отправлена форма с полями,
описанными в классе CreationForm. После заполнения этой формы
пользователь будет переадресован на страницу, для которой в urls.py
указано имя name='posts:index'. Данные, отправленные через форму,
будут переданы в модель User и сохранены в БД.
"""

# Функция reverse_lazy позволяет получить URL по параметрам функции path()
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Импортируем класс формы, что бы сослаться на неё во view-классе
from .forms import CreationForm


class SignUp(CreateView):
    # Создаем объект формы
    form_class = CreationForm
    # success_url - URL-адрес для перенаправления
    # после успешной обработки формы.
    # Так и не понял зачем нужен reverse_lazy
    success_url = reverse_lazy('posts:index')

    # template_name — имя шаблона, куда будет передана переменная form
    template_name = 'users/signup.html'

# Отсальные пути обрабатываются стандартным обработчиком,
# см. users/urls.py
