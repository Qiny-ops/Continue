# -*- coding: utf-8 -*-
"""
最小集成测试（不依赖外部 LLM/网络）

- 启动 FastAPI 测试客户端
- 验证：健康检查、参数校验、任务触发后立即返回 202
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_trigger_missing_fields(client):
    r = client.post("/api/v1/check/trigger", json={})
    assert r.status_code == 422 or r.status_code == 400


def test_trigger_inline_success(client):
    r = client.post(
        "/api/v1/check/trigger",
        json={
            "project_name": "demo",
            "repository_url": "https://example.com/repo.git",
            "case_source": "inline",
            "test_cases": [
                {"case_no": "TC001", "testpoint": "demo", "steps": "step", "expectation": "ok"}
            ],
        },
    )
    assert r.status_code == 202
    body = r.json()
    assert "task_id" in body
    assert body["status"] == "pending"


def test_get_nonexistent_task(client):
    r = client.get("/api/v1/check/nonexistent")
    assert r.status_code == 404


def test_webhook_github_bad_signature(client):
    r = client.post(
        "/api/v1/webhook/github",
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=bad"},
        content=b"{}",
    )
    assert r.status_code == 401
