# Импортируем из приложения django.contrib.auth.views
# нужные обработчики/ view-класс
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeView, PasswordResetView)
from django.urls import path

from . import views

app_name = 'users'  # Указываем namespace

urlpatterns = [
    # Представление, основанное на классе. В path()
    # view-классы вызываются через метод :
    # path('any_url/', ClassName.as_view())
    # В as_view() можно прямо дать ссылку на шаблон
    path('logout/', LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    # Полный адрес страницы регистрации - auth/signup/,
    # но префикс auth/ обрабатывется в головном urls.py
    path('signup/', views.SignUp.as_view(), name='var_signup'),
    path('login/', LoginView.as_view(template_name='users/login.html'),
         name='var_login'),
    path('password_reset/', PasswordResetView.as_view(),
         name='var_password_reset_form'),
    path('password_change/', PasswordChangeView.as_view(),
         name='var_password_change'),
]
