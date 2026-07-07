"""
分页工具

提供 DRF 分页器的标准实现，可被所有 API 使用。
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    标准分页器

    配置：
    - 默认每页 20 条
    - 支持客户端自定义每页数量 (page_size 参数)
    - 最大每页 100 条
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100