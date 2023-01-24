from django.conf import settings
from django.conf.urls.static import static
# По умолчанию в проект Django подключена система администрирования
from django.contrib import admin
# Функция include позволит использовать path() из других файлов.
from django.urls import include, path

# Каким view обрабатывать ошибки
handler404 = 'core.views.page_not_found'
handler403 = 'core.views.permission_denied'
handler500 = 'core.views.server_error'

urlpatterns = [
    # Если на сервер пришел запрос '', только для namespace 'posts'
    # перейди в urls приложения posts и проверь там все path()
    # на совпадения с запрошенный url
    path('', include('posts.urls', namespace='posts')),
    path('admin/', admin.site.urls),

    # Все адреса с префиксом auth/ будут перенаправлены
    # в приложение users файл users/urls,
    # и там уже указывать auth/ в ссылке не нужно
    path('auth/', include('users.urls')),

    # Все что не проматчилось выше в  'users/urls'
    # попадет в django.contrib.auth
    path('auth/', include('django.contrib.auth.urls')),

    path('about/', include('about.urls', namespace='about_namespace')),
]

# В режиме отлажки позволяет обращаться к файлам в директории,
# указанной в MEDIA_ROOT по имени, через префикс MEDIA_URL.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
