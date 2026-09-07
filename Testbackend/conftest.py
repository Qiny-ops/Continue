"""
pytest 全局 conftest

确保本地直接 `pytest` 也能运行：默认以开发模式加载 settings，
避免 settings 在缺少 DJANGO_SECRET_KEY / WEKNORA_API_KEY 等生产环境变量时抛 ValueError。
CI 可通过显式设置 DJANGO_DEBUG=false + 各 SECRET 覆盖此默认行为。
"""
import os

os.environ.setdefault('DJANGO_DEBUG', 'true')
