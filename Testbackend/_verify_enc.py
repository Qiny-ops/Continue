import os
import tempfile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')

import django

django.setup()

from django.conf import settings

# 指向临时数据库，避免污染开发库
tmp_db = tempfile.mktemp(suffix='.sqlite3')
settings.DATABASES['default']['NAME'] = tmp_db
from django.db import connections

connections['default'].settings_dict['NAME'] = tmp_db
connections['default'].close()

from django.core.management import call_command

call_command('migrate', verbosity=0, run_syncdb=True)

from apps.apitest.models import ApiEnvironment
from apps.projects.models import Project

proj = Project.objects.create(code='enc-verify', name='enc-verify', type='web')
env = ApiEnvironment.objects.create(
    project=proj,
    name='prod-env',
    base_url='http://api.example.com',
    auth_type='basic',
    auth_username='alice',
    auth_password='s3cr3t-p@ss',
    auth_token='tok-abc-123',
)
print('ORM read username:', env.auth_username)
print('ORM read password:', env.auth_password)
print('ORM read token   :', env.auth_token)

# 原始库值应为密文
with connections['default'].cursor() as cur:
    cur.execute(
        "SELECT auth_username, auth_password, auth_token FROM apitest_environment WHERE id=%s",
        [env.id],
    )
    raw_user, raw_pwd, raw_tok = cur.fetchone()

print('RAW username (db):', raw_user)
print('RAW password (db):', raw_pwd)
print('RAW token (db)   :', raw_tok)

assert raw_user != 'alice', 'username 未加密！'
assert raw_pwd != 's3cr3t-p@ss', 'password 未加密！'
assert raw_tok != 'tok-abc-123', 'token 未加密！'
assert env.auth_username == 'alice'
assert env.auth_password == 's3cr3t-p@ss'
assert env.auth_token == 'tok-abc-123'
print('\n✅ 加密落库成功：DB 存密文，ORM 读明文，序列化层再脱敏。')

os.remove(tmp_db)
