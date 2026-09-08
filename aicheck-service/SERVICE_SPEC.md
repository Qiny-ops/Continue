# AI Code Check Service

基于 Claude Agent SDK 的代码变更 AI 检查微服务，对齐 Continue 平台 FastAPI 微服务规范。

## 概述

接收 Git 仓库地址与测试用例，拉取代码、获取 diff、先做风险评估，再按测试用例逐条 AI 校验是否实现。可作为 CI/CD 提测门禁（Webhook 触发 + Commit Status 上报），也可由 Continue 平台手动触发（平台用例作为内联参数传入）。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.100+ |
| 数据验证 | Pydantic v2 / pydantic-settings |
| 模型客户端 | claude_agent_sdk（保留模型主动 Read/Grep 仓库文件能力） |
| 任务存储 | SQLite（实时写库，防进程重启丢失） |
| HTTP 客户端 | httpx（异步） |
| 重试 | tenacity（指数退避） |
| 并发 | asyncio.Semaphore + 用例间 1s 限流 |

## 架构

```
Webhook / Django 触发
        │
        ▼
  routers/{health,tasks,webhook}  (FastAPI, /api/v1 前缀)
        │
        ▼
  services/task_manager.py       编排：拉代码→diff→风险→用例→并发校验→门禁
        │
   ┌────┴────────────┬────────────┐
   ▼                 ▼            ▼
git_handler      risk_analyzer  executor
   │                 │            │
   ▼                 ▼            ▼
  git CLI      verifier      verifier (claude_agent_sdk)
                  │
                  ▼
            case_provider (inline | file | platform)
```

## API

| Method | Path | 鉴权 | 说明 |
|--------|------|------|------|
| GET | /api/v1/health | API Key | 健康检查 |
| POST | /api/v1/check/trigger | API Key | 触发检查任务 |
| GET | /api/v1/check/{task_id} | API Key | 查询任务报告 |
| GET | /api/v1/checks | API Key | 任务列表 |
| POST | /api/v1/webhook/github | 签名验签 | GitHub push 事件 |
| POST | /api/v1/webhook/gitlab | Token 验签 | GitLab push 事件 |

### 触发请求

```json
POST /api/v1/check/trigger
{
  "project_name": "demo",
  "repository_url": "https://github.com/owner/repo.git",
  "branch": "develop",
  "commit_sha": "abc123",
  "case_source": "platform",   // inline | file | platform
  "project_code": "demo-app",  // platform 模式必填
  "gate": {
    "provider": "github",
    "repo_ref": "owner/repo",
    "commit_sha": "abc123",
    "token": ""                 // 覆盖全局
  },
  "trigger_source": "manual"
}
```

### 任务报告

```json
{
  "task_id": "uuid",
  "status": "completed",
  "conclusion": "passed",      // passed | blocked | failed
  "risk": {"level": "中", "score": 50, "high_risk_files": [], "reason": ""},
  "summary": {"total": 5, "pass": 5, "fail": 0, "error": 0, "pass_rate": "100.0%"},
  "results": [{"case_no": "TC001", "testpoint": "...", "result": "通过", "reason": "...", "success": true}],
  "gate": {"provider": "github", "commit_sha": "abc", "state": "success"}
}
```

## 门禁流程

1. 任务开始 → `pending`（若配 gate）
2. 风险评估 → 高风险直接 `failure` 阻断，跳过用例
3. 中/低风险 → 执行用例；全部通过 → `success`；任一失败/异常 → `failure`

## 启动

```bash
cd aicheck-service
pip install -r requirements.txt
cp .env.example .env  # 修改后启动
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## 启动选项

- 加入 `start_all.py --skip-ai-check`：跳过本服务
- `stop_all.py` 按端口 8004 杀进程
