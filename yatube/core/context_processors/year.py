import datetime


def get_year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'key_year': datetime.date.today().year
    }
