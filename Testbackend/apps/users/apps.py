import threading
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"

    def ready(self):
        """应用启动时启动后台清理线程"""
        # 仅在主进程中运行（避免在 runserver 的自动重载子进程中重复运行）
        import os
        if os.environ.get('RUN_MAIN') == 'true' or not hasattr(threading, 'main_thread'):
            from apps.users.services.token_cleanup import start_cleanup_scheduler
            start_cleanup_scheduler()
