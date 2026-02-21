from django.apps import AppConfig


class NutriappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'NutriApp'

    def ready(self):
        import NutriApp.signals