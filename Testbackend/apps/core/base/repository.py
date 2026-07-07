"""
Repository 基类

提供数据访问层的抽象基类，封装常见的数据库操作。
所有具体的 Repository 类应继承此基类。
"""

from django.db import models


class BaseRepository:
    """
    Repository 基类

    数据访问层，负责与数据库的直接交互。
    不包含业务逻辑，只提供数据的 CRUD 操作。

    使用示例:
        class UserRepository(BaseRepository):
            model = User

            def get_by_username(self, username):
                return self.model.objects.filter(username=username).first()
    """

    model = None  # 子类必须指定关联的 Model

    @classmethod
    def get_by_id(cls, id):
        """根据 ID 获取单个对象"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.filter(id=id).first()

    @classmethod
    def get_all(cls):
        """获取所有对象"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.all()

    @classmethod
    def get_by_ids(cls, ids):
        """根据 ID 列表获取多个对象"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.filter(id__in=ids)

    @classmethod
    def create(cls, **kwargs):
        """创建对象"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.create(**kwargs)

    @classmethod
    def update(cls, instance, **kwargs):
        """更新对象"""
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @classmethod
    def delete(cls, instance):
        """删除对象"""
        instance.delete()

    @classmethod
    def delete_by_id(cls, id):
        """根据 ID 删除对象"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.filter(id=id).delete()

    @classmethod
    def count(cls, filters=None):
        """计数"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        queryset = cls.model.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.count()

    @classmethod
    def exists(cls, filters):
        """检查是否存在"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.filter(**filters).exists()

    @classmethod
    def bulk_create(cls, objects_list):
        """批量创建"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.bulk_create(objects_list)

    @classmethod
    def bulk_update(cls, objects_list, fields):
        """批量更新"""
        if cls.model is None:
            raise NotImplementedError("必须指定 model 属性")
        return cls.model.objects.bulk_update(objects_list, fields)