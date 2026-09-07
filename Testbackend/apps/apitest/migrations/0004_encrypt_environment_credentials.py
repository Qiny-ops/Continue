# 历史明文凭据重加密为密文
# 依赖 0003（字段类型切换为加密字段）后执行；通过原始游标读写，绕过 ORM 加解密。
from django.db import migrations

from apps.apitest.fields import decrypt_value, encrypt_value, is_ciphertext

TABLE = 'apitest_environment'
COLS = ['auth_token', 'auth_password', 'auth_username']


def encrypt_existing_credentials(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute(f"SELECT id, {', '.join(COLS)} FROM {TABLE}")
        rows = cur.fetchall()
    for row in rows:
        pk = row[0]
        updates = {}
        for idx, col in enumerate(COLS, start=1):
            val = row[idx]
            # 仅加密仍为明文的字段（已是密文则跳过，幂等）
            if val and not is_ciphertext(val):
                updates[col] = encrypt_value(val)
        if updates:
            set_clause = ", ".join(f"{c}=%s" for c in updates)
            params = list(updates.values()) + [pk]
            with connection.cursor() as cur:
                cur.execute(
                    f"UPDATE {TABLE} SET {set_clause} WHERE id=%s", params
                )


def decrypt_existing_credentials(apps, schema_editor):
    """回滚：将密文还原为明文（配合 0003 字段类型回退）。"""
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute(f"SELECT id, {', '.join(COLS)} FROM {TABLE}")
        rows = cur.fetchall()
    for row in rows:
        pk = row[0]
        updates = {}
        for idx, col in enumerate(COLS, start=1):
            val = row[idx]
            if val and is_ciphertext(val):
                updates[col] = decrypt_value(val)
        if updates:
            set_clause = ", ".join(f"{c}=%s" for c in updates)
            params = list(updates.values()) + [pk]
            with connection.cursor() as cur:
                cur.execute(
                    f"UPDATE {TABLE} SET {set_clause} WHERE id=%s", params
                )


class Migration(migrations.Migration):

    dependencies = [
        ('apitest', '0003_alter_apienvironment_auth_password_and_more'),
    ]

    operations = [
        migrations.RunPython(
            encrypt_existing_credentials,
            decrypt_existing_credentials,
        ),
    ]
