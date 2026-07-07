#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 接口测试
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


def test_status(client):
    """测试服务状态"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data