#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推理 API 测试
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert "version" in response.json()


def test_health(client):
    """测试健康检查"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_infer_endpoint_exists(client):
    """测试推理端点存在"""
    # 仅验证端点可访问，不验证推理结果（需要真实模型）
    response = client.post(
        "/api/v1/infer",
        json={"messages": [{"role": "user", "content": "test"}]},
    )
    # 端点应该响应（可能是成功或失败，取决于模型是否可用）
    assert response.status_code in [200, 500]


def test_batch_endpoint_exists(client):
    """测试批量推理端点存在"""
    response = client.post(
        "/api/v1/batch",
        json={
            "items": [
                {"messages": [{"role": "user", "content": "test1"}]},
                {"messages": [{"role": "user", "content": "test2"}]},
            ]
        },
    )
    assert response.status_code in [200, 500]


def test_async_batch_endpoint(client):
    """测试异步批量推理端点"""
    response = client.post(
        "/api/v1/batch/async",
        json={
            "items": [
                {"messages": [{"role": "user", "content": "test"}]},
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data


def test_get_task_not_found(client):
    """测试查询不存在的任务"""
    response = client.get("/api/v1/batch/non-existent-task-id")
    assert response.status_code == 404