import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class GalleryConfig(AppConfig):
    name = 'gallery'

    def ready(self):
        self._check_celery()

    @staticmethod
    def _check_celery():
        try:
            from config.celery import app
            conn = app.connection()
            conn.ensure_connection(max_retries=1, timeout=3)
            conn.close()
        except Exception as e:
            logger.warning(
                "Could not connect to Celery broker: %s — "
                "zip downloads will not work until a Celery worker is running.",
                e,
            )