# API Testing Service

接口测试微服务，支持接口业务流分析、测试用例生成、依赖分析、数据填充、用例执行和结果校验。

## 技术栈

- **Web 框架**: FastAPI
- **数据验证**: Pydantic v2
- **流式响应**: Server-Sent Events (SSE)
- **模型客户端**: OpenAI API 兼容

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `.env` 文件：

```env
# 服务配置
APP_NAME=API Testing Service
APP_VERSION=1.0.0

# 模型 API 配置
MODEL_API_KEY=EMPTY
MODEL_BASE_URL=http://localhost:8000/v1

# 知识库服务配置
KB_BASE_URL=http://localhost:5000
KB_ID=your_kb_id
KB_API_KEY=your_api_key

# 数据库配置（可选）
DB_ENABLED=false
```

### 3. 启动服务

```bash
python run.py
```

服务启动后访问：
- 服务地址: `http://localhost:8002`
- API 文档: `http://localhost:8002/docs`
- 健康检查: `GET http://localhost:8002/api/v1/health`

## API 接口

### 接口列表

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/v1/health | 健康检查 |
| GET | /api/v1/status | 服务状态 |
| POST | /api/v1/flow | 获取接口业务流（流式） |
| POST | /api/v1/testcase/generate | 生成测试用例（流式） |
| POST | /api/v1/dependency | 获取接口依赖（流式） |
| POST | /api/v1/testdata/fill | 填充测试数据（流式） |
| POST | /api/v1/testcase/execute | 执行测试用例（流式） |
| POST | /api/v1/testcase/validate | 校验测试用例（流式） |
| POST | /api/v1/llm/chat | LLM 对话（同步） |
| POST | /api/v1/llm/chat/stream | LLM 对话（流式） |

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
│   │   └── engine.py        # 测试引擎（业务逻辑层）
│   ├── execute/
│   │   ├── __init__.py
│   │   ├── engine.py        # 执行引擎
│   │   └── executor.py      # HTTP 执行器
│   ├── prompts/             # 提示词模板
│   ├── routers/
│   │   ├── __init__.py
│   │   └── rpc.py           # RESTful API 路由
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── rpc.py           # Pydantic 数据模型
│   ├── services/
│   │   ├── kb_client.py     # 知识库客户端
│   │   ├── llm_service.py   # LLM 服务
│   │   └── db_service.py    # 数据库服务
│   └── utils/
│       └── logger.py        # 统一日志模块
├── tests/
├── .env
├── requirements.txt
├── README.md
├── run.py                   # FastAPI 服务启动脚本
└── run_mcp_server.py        # MCP Server 启动脚本
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
| get_api_flow | 获取接口业务流 |
| generate_testcases | 生成测试用例 |
| get_api_dependency | 获取接口依赖关系 |
| fill_testdata | 填充测试数据 |
| execute_testcase | 执行测试用例 |
| validate_testcase | 校验测试结果 |

### 配置 SkillFramework

```yaml
# config/mcp_servers.yaml
apitest:
  transport: stdio
  command: python
  args:
    - "run_mcp_server.py"
```

## 使用示例

### 获取接口业务流

```bash
curl -N -X POST http://localhost:8002/api/v1/flow \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "your_kb_id",
    "query": "分析登录接口的业务流"
  }'
```

### 生成测试用例

```bash
curl -N -X POST http://localhost:8002/api/v1/testcase/generate \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "your_kb_id",
    "query": "对文档中的接口设计接口测试用例"
  }'
```

## 许可证

Copyright © 2026