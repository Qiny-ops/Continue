from django.apps import AppConfig


class TestcaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.testcase'
    verbose_name = '测试用例管理'
