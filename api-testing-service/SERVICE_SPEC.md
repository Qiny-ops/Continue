# API Testing Service

基于 AI 的接口测试微服务，实现测试用例智能生成、依赖分析、数据填充、自动执行与结果校验的全流程自动化。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 数据验证 | Pydantic v2 |
| 流式响应 | Server-Sent Events (SSE) |
| HTTP 客户端 | httpx (异步) |
| LLM 客户端 | OpenAI API 兼容 |
| 知识库 | WeKnora (RAG) |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI 入口层                          │
│  main.py → routers/rpc.py (RESTful API + SSE 流式响应)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     核心引擎层                               │
│  ┌──────────────────┐    ┌───────────────────────────────┐  │
│  │ ApiTestEngine    │    │ TestExecutionEngine           │  │
│  │ (业务逻辑引擎)    │    │ (测试执行引擎)                 │  │
│  │ - get_flow       │    │ - execute_testcase            │  │
│  │ - generate_tc    │    │ - validate_testcase           │  │
│  │ - get_dependency │    │ - 参数填充 & 变量提取          │  │
│  │ - fill_test_data │    │ - 测试账号自动清理             │  │
│  └──────────────────┘    └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     服务层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ KBClient     │  │ LLMService   │  │ DBService    │       │
│  │ (知识库客户端) │  │ (模型调用)    │  │ (数据库存储) │       │
│  │ WeKnora API  │  │ OpenAI兼容    │  │ MySQL/SQLite │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    执行器层                                  │
│  ApiTestExecutor - HTTP请求执行、状态码校验、历史记录管理     │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
api-testing-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # Pydantic 配置管理
│   ├── mcp_server.py        # MCP Server 实现
│   ├── demo.py              # Demo 示例
│   ├── core/
│   │   ├── __init__.py
│   │   └── engine.py        # 业务逻辑引擎（用例生成、依赖分析）
│   ├── execute/
│   │   ├── __init__.py
│   │   ├── engine.py        # 测试执行引擎
│   │   └── executor.py      # HTTP 执行器
│   ├── prompts/             # 提示词模板
│   │   ├── generate_testcase.txt
│   │   ├── get_dependency.txt
│   │   ├── execute_api.txt
│   │   ├── fill_test_data.txt
│   │   └── validate_testcase.txt
│   ├── routers/
│   │   ├── __init__.py
│   │   └── rpc.py           # RESTful API 路由
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── rpc.py           # Pydantic 数据模型
│   ├── services/
│   │   ├── kb_client.py     # 知识库客户端 (WeKnora)
│   │   ├── llm_service.py   # LLM 服务
│   │   └── db_service.py    # 数据库服务
│   └── utils/
│       └── logger.py        # 统一日志模块
├── tests/
│   └── test_rpc.py          # API 测试
├── .env                     # 环境变量配置
├── .env.example             # 环境变量示例
├── requirements.txt         # Python 依赖
├── README.md                # 项目说明
├── run.py                   # FastAPI 服务启动脚本
└── run_mcp_server.py        # MCP Server 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
# 服务配置
APP_NAME=API Testing Service
APP_VERSION=1.0.0
DEBUG=false

# 模型 API 配置
MODEL_API_KEY=your_api_key
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=default

# 知识库服务配置 (WeKnora)
KB_BASE_URL=http://localhost:3000/api/v1
KB_ID=your_kb_id
KB_API_KEY=your_kb_api_key

# Agent 配置
KB_AGENT_ID=builtin-smart-reasoning
KB_TEMPERATURE=0.3
KB_MAX_TOKENS=8192

# 数据库配置（可选）
DB_ENABLED=false
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=test

# API 测试执行配置
API_BASE_URL=http://127.0.0.1:8000
```

### 3. 启动服务

```bash
# 启动 FastAPI 服务
python run.py

# 或启动 MCP Server
python run_mcp_server.py
```

服务启动后：
- 服务地址: `http://localhost:8002`
- API 文档: `http://localhost:8002/docs`
- 健康检查: `GET http://localhost:8002/api/v1/health`

## API 接口

### 接口列表

| 方法 | 端点 | 说明 | 响应类型 |
|------|------|------|----------|
| GET | `/api/v1/health` | 健康检查 | JSON |
| GET | `/api/v1/status` | 服务状态 | JSON |
| POST | `/api/v1/flow` | 获取接口业务流 | SSE |
| POST | `/api/v1/testcase/generate` | 生成测试用例 | SSE |
| POST | `/api/v1/dependency` | 获取接口依赖 | SSE |
| POST | `/api/v1/testdata/fill` | 填充测试数据 | SSE |
| POST | `/api/v1/testcase/execute` | 执行测试用例 | SSE |
| POST | `/api/v1/testcase/validate` | 校验测试用例 | SSE |
| POST | `/api/v1/llm/chat` | LLM 对话 | JSON |
| POST | `/api/v1/llm/chat/stream` | LLM 对话 | SSE |

### SSE 事件类型

所有流式接口返回统一格式的事件：

```json
{"type": "session", "data": {"action": "created", "session_id": "xxx"}}
{"type": "chunk", "data": {"content": "AI 输出内容片段..."}}
{"type": "result", "data": {"dependency": {...}}}
{"type": "step", "data": {"message": "正在执行..."}}
{"type": "error", "data": {"message": "错误信息"}}
{"type": "complete", "data": {"message": "完成"}}
```

### 请求参数示例

#### 获取接口业务流

```bash
curl -N -X POST http://localhost:8002/api/v1/flow \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "your_kb_id",
    "query": "分析登录接口的业务流"
  }'
```

#### 生成测试用例

```bash
curl -N -X POST http://localhost:8002/api/v1/testcase/generate \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "your_kb_id",
    "query": "对文档中的接口设计接口测试用例",
    "save_to_db": false,
    "knowledge_id": "optional_doc_id"
  }'
```

#### 获取接口依赖

```bash
curl -N -X POST http://localhost:8002/api/v1/dependency \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "1",
    "api_name": "修改用户角色接口",
    "precondition": "已登录管理员账号",
    "testpoint": "管理员修改普通用户角色",
    "expectation": "修改成功，返回200",
    "kb_id": "your_kb_id"
  }'
```

#### 执行测试用例

```bash
curl -N -X POST http://localhost:8002/api/v1/testcase/execute \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "1",
    "api_name": "修改用户角色接口",
    "precondition": "已登录管理员账号",
    "testpoint": "管理员修改普通用户角色",
    "expectation": "修改成功，返回200",
    "run_list": [
      {
        "run_num": 1,
        "api_name": "用户注册接口",
        "api_url": "/api/users/register/",
        "method": "POST",
        "request_body": {"username": "test_xxx", "password": "Test@123", "email": "test@test.com"},
        "expected_status": 201
      },
      {
        "run_num": 2,
        "api_name": "用户登录接口",
        "api_url": "/api/users/login/",
        "method": "POST",
        "request_body": {"username": "test_xxx", "password": "Test@123"},
        "expected_status": 200,
        "extract_vars": {"token": "$.run_list[1].response.body.data.token"}
      }
    ],
    "test_data": {},
    "kb_id": "your_kb_id"
  }'
```

## 核心业务流程

### 测试用例生命周期

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. 业务流分析 │ → │ 2. 用例生成   │ → │ 3. 依赖分析   │
│   /flow      │    │ /testcase/   │    │ /dependency  │
│              │    │   generate   │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
                                              ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 6. 结果校验   │ ← │ 5. 用例执行   │ ← │ 4. 数据填充   │
│ /testcase/   │    │ /testcase/   │    │ /testdata/   │
│   validate   │    │   execute    │    │   fill       │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 依赖分析流程

```
输入: 测试用例信息
  ↓
AI 分析需要的前置接口
  ↓
输出: run_list (按执行顺序排列的接口列表)
  [
    {注册接口, username: "test_20260525_143000_a1b2"},
    {登录接口, 获取 token},
    {目标接口, URL 含 {{user_id}}, Header 含 token}
  ]
```

### 测试执行流程

```
遍历 run_list
  ↓
第一个接口 → 直接执行
  ↓
后续接口 → 调用 AI 填充参数 (基于历史执行记录)
  ↓
自动替换占位符 {{user_id}}, {{token}} 等
  ↓
执行接口 → 记录结果到历史
  ↓
失败检测 → 某些错误可跳过 (如"账号已存在")
  ↓
执行完成 → 清理测试账号
```

## 核心特性

### 1. 智能参数提取

支持 JSONPath 风格路径从历史执行记录中提取值：

```json
{
  "extract_vars": {
    "user_id": "$.run_list[0].response.body.data.id",
    "token": "$.run_list[1].response.body.data.token"
  }
}
```

常用提取路径：
- 用户 ID: `$.run_list[0].response.body.data.id`
- Token: `$.run_list[x].response.body.data.token`
- 列表首个元素: `$.run_list[x].response.body.results[0].id`

### 2. 占位符自动替换

URL 和 request_body 中的 `{{xxx}}` 会自动从历史记录提取并替换：

```
原始 URL: /api/users/{{user_id}}/role/
替换后:   /api/users/6/role/
```

### 3. Token 自动注入

提取到的 token 会自动添加到 Authorization header：

```
extract_vars: {"token": "$.run_list[1].response.body.data.token"}
→ 自动添加 Header: Authorization: Bearer xxx
```

### 4. 测试账号自动化管理

- **自动生成唯一账号**：时间戳格式 `test_YYYYMMDD_HHMMSS_xxxx`
- **多用户场景支持**：不同用户使用不同账号
- **自动清理**：执行完成后自动删除测试账号

### 5. 模糊状态码匹配

支持通配符匹配异常场景：

```json
{"expected_status": "4XX"}  // 匹配 400-499
{"expected_status": "5XX"}  // 匹配 500-599
```

### 6. 可跳过错误配置

某些错误不影响后续执行，可配置跳过：

```python
SKIPPABLE_ERRORS = {
    "注册": ["已存在", "已注册", "duplicate", "already exists"],
    "登录": []
}
```

## MCP Server

将 API Testing 功能暴露为 MCP Tools，供 SkillFramework 调用。

### 启动方式

```bash
python run_mcp_server.py
```

### MCP Tools

| Tool | 说明 |
|------|------|
| `get_api_flow` | 获取接口业务流 |
| `generate_testcases` | 生成测试用例 |
| `get_api_dependency` | 获取接口依赖关系 |
| `fill_testdata` | 填充测试数据 |
| `execute_testcase` | 执行测试用例 |
| `validate_testcase` | 校验测试结果 |

### 配置 SkillFramework

```yaml
# config/mcp_servers.yaml
apitest:
  transport: stdio
  command: python
  args:
    - "run_mcp_server.py"
```

## 提示词模板说明

### generate_testcase.txt

测试用例生成提示词，要求：
- 只输出 JSON 数组，禁止额外说明
- 覆盖边界值、等价类、安全测试、异常测试
- 每个 id 唯一且递增

### get_dependency.txt

依赖分析提示词，要求：
- 返回 run_list 结构
- 定义动态参数提取规则 (extract_vars)
- 强制使用时间戳格式账号名
- 标注 expected_status

### execute_api.txt

参数填充提示词，要求：
- 分析历史执行记录
- 替换 URL 路径参数
- 填充 request_body 占位符

### validate_testcase.txt

结果校验提示词，校验规则：
- HTTP 状态码
- 业务 code
- 关键字段存在性
- 数据一致性

## 配置说明

### 模型配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `MODEL_API_KEY` | 模型 API 密钥 | EMPTY |
| `MODEL_BASE_URL` | 模型 API 地址 | http://localhost:8000/v1 |
| `MODEL_NAME` | 模型名称 | default |
| `MAX_TOKENS` | 最大输出 token | 81920 |
| `TEMPERATURE` | 温度参数 | 1.0 |
| `TOP_P` | Top-p 采样 | 0.95 |

### 知识库配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `KB_BASE_URL` | WeKnora 服务地址 | http://localhost:3000/api/v1 |
| `KB_ID` | 知识库 ID | - |
| `KB_API_KEY` | 知识库 API 密钥 | - |
| `KB_AGENT_ID` | Agent ID | builtin-smart-reasoning |

### 执行配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `API_BASE_URL` | 被测 API 基座 URL | http://127.0.0.1:8000 |
| `MAX_RETRIES` | 最大重试次数 | 3 |
| `RETRY_DELAY` | 重试间隔 (秒) | 2.0 |

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 日志

服务使用统一的日志模块 `app/utils/logger.py`，日志级别可通过环境变量控制。

### 添加新的提示词

1. 在 `app/prompts/` 目录下创建 `.txt` 文件
2. 在 `app/prompts/__init__.py` 中添加加载函数
3. 在引擎中调用提示词函数

### 扩展执行器

`ApiTestExecutor` 支持扩展：
- 添加新的 HTTP 方法支持
- 自定义状态码校验逻辑
- 添加响应解析器

## 许可证

Copyright © 2026
