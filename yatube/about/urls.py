# about/urls.py
from django.urls import path

from . import views

app_name = 'about_namespace'

urlpatterns = [
    # Если из views подтягиваем класс,
    # то нужно использовать метод as_view()
    path('author/', views.AboutAuthorView.as_view(), name='author'),
    path('tech/', views.AboutTechView.as_view(), name='tech')
]
