from django.apps import AppConfig


class GwmCrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gwm_crm'

    def ready(self):
        import gwm_crm.signals