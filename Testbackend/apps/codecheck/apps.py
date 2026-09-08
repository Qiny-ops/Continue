# -*- coding: utf-8 -*-
"""代码变更检查 应用配置"""

from django.apps import AppConfig


class CodeCheckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.codecheck"
    verbose_name = "代码变更检查"
