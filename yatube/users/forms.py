# Формы принято хранить в отдельном файле.
# К формам обращаемся из views.py

from django.contrib.auth import get_user_model
# UserCreationForm встроенный класс, наследник forms.ModelForm
# UserCreationForm был создан (не мной) на основе модели User
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


# Создаем свой класс для регистрации CreationForm
class CreationForm(UserCreationForm):
    # Наследуется класс Meta, вложенный в класс UserCreationForm
    # что бы унаследовать ключи и переопределить их
    class Meta(UserCreationForm.Meta):
        # На основе модели models.py User создаем класс формы
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
