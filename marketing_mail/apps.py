# marketing_mail/apps.py

from django.apps import AppConfig


class MarketingMailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'marketing_mail'
    verbose_name       = 'Marketing Mail'