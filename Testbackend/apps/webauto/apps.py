#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web 自动化应用配置"""

from django.apps import AppConfig


class WebAutoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.webauto'
    verbose_name = 'Web 自动化'
