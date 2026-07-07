# -*- coding: utf-8 -*-
from django.apps import AppConfig


class ApiTestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.apitest'
    verbose_name = '接口测试管理'
