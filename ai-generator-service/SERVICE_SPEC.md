# AI Generator Service

基于 AI 模型的推理微服务，支持单次推理、流式推理、批量推理和智能测试用例生成。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 数据验证 | Pydantic v2 |
| 流式响应 | Server-Sent Events (SSE) |
| 模型客户端 | OpenAI SDK (异步) |
| 任务存储 | 内存 / Redis (可选) |
| 容器化 | Docker + Docker Compose |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI 入口层                          │
│  main.py → routers/inference.py (RESTful API + SSE)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     核心引擎层                               │
│  InferenceEngine                                             │
│  - infer_single()    单次推理                                │
│  - infer_stream()     流式推理                               │
│  - infer_batch()      批量推理                                │
│  - generate_testcases() 测试用例生成（并行）                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     服务层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ ModelClient │  │ TaskStore    │  │ JSONExtractor│        │
│  │ (模型调用)   │  │ (任务存储)    │  │ (JSON提取)   │        │
│  │ OpenAI API  │  │ 内存/Redis    │  │ 智能解析      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    提示词层                                   │
│  prompts/                                                    │
│  - testcase_generate.txt   系统提示词                        │
│  - test_directions.txt     测试方向映射                      │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
ai-generator-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # Pydantic 配置管理
│   ├── core/
│   │   ├── __init__.py
│   │   └── engine.py        # 推理引擎（业务逻辑层）
│   ├── prompts/             # 提示词模板
│   │   ├── __init__.py
│   │   ├── testcase_generate.txt
│   │   └── test_directions.txt
│   ├── routers/
│   │   ├── __init__.py
│   │   └── inference.py     # RESTful API 路由
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── inference.py     # Pydantic 数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_client.py  # 模型客户端
│   │   └── task_store.py    # 任务存储
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # 统一日志模块
│       └── json_extractor.py # JSON 提取工具
├── tests/
│   ├── __init__.py
│   └── test_inference.py    # API 测试
├── .env                     # 环境变量配置
├── .env.example             # 环境变量示例
├── Dockerfile               # Docker 构建文件
├── docker-compose.yml       # Docker Compose 配置
├── requirements.txt         # Python 依赖
└── README.md                # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
# 模型 API 配置
MODEL_API_KEY=your_api_key
MODEL_BASE_URL=http://localhost:8000/v1

# 推理参数
MAX_TOKENS=81920
TEMPERATURE=1.0
TOP_P=0.95
PRESENCE_PENALTY=1.5
TOP_K=20

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=2.0

# 服务配置
APP_NAME=AI Generator Service
APP_VERSION=1.0.0
DEBUG=false

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379
USE_REDIS=false
```

### 3. 启动服务

**本地启动：**

```bash
# 直接运行
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Docker 启动：**

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务启动后：
- 服务地址: `http://localhost:8000`
- API 文档: `http://localhost:8000/docs`
- 健康检查: `GET http://localhost:8000/api/v1/health`

## API 接口

### 接口列表

| 方法 | 端点 | 说明 | 响应类型 |
|------|------|------|----------|
| GET | `/api/v1/health` | 健康检查 | JSON |
| POST | `/api/v1/reset` | 重置模型缓存 | JSON |
| POST | `/api/v1/infer` | 单次推理 | JSON |
| POST | `/api/v1/infer/stream` | 流式推理 | SSE |
| POST | `/api/v1/batch` | 同步批量推理 | JSON |
| POST | `/api/v1/batch/async` | 异步批量推理 | JSON |
| GET | `/api/v1/batch/{task_id}` | 查询异步任务状态 | JSON |
| POST | `/api/v1/testcase/generate` | 测试用例生成 | JSON |

### 请求参数示例

#### 单次推理

```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "请解释什么是 REST API"}
    ]
  }'
```

**响应：**

```json
{
  "success": true,
  "result": {"explanation": "REST API 是一种基于 HTTP 协议的 API 设计风格..."},
  "raw_content": null,
  "error": null
}
```

#### 流式推理

```bash
curl -N -X POST http://localhost:8000/api/v1/infer/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "请写一首关于春天的诗"}
    ]
  }'
```

**响应（SSE）：**

```
data: 春风
data: 送暖
data: 入屠苏
data: [DONE]
```

#### 同步批量推理

```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"messages": [{"role": "user", "content": "1+1=?"}]},
      {"messages": [{"role": "user", "content": "2+2=?"}]}
    ]
  }'
```

**响应：**

```json
{
  "total": 2,
  "completed": 2,
  "results": [
    {"index": 0, "success": true, "result": {"answer": 2}, "error": null},
    {"index": 1, "success": true, "result": {"answer": 4}, "error": null}
  ]
}
```

#### 异步批量推理

```bash
# 创建任务
curl -X POST http://localhost:8000/api/v1/batch/async \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"messages": [{"role": "user", "content": "任务1"}]},
      {"messages": [{"role": "user", "content": "任务2"}]}
    ]
  }'

# 响应
{"task_id": "550e8400-e29b-41d4-a716-446655440000", "message": "任务已创建，请通过 task_id 查询结果"}

# 查询任务状态
curl http://localhost:8000/api/v1/batch/550e8400-e29b-41d4-a716-446655440000
```

#### 测试用例生成

```bash
curl -X POST http://localhost:8000/api/v1/testcase/generate \
  -H "Content-Type: application/json" \
  -d '{
    "module": "用户管理",
    "func_point": "用户登录",
    "related_detail": "支持用户名密码登录、手机验证码登录",
    "test_directions": ["功能点测试", "业务逻辑测试", "其他测试"],
    "temperature": 0.8
  }'
```

**响应：**

```json
{
  "success": true,
  "cases": [
    {
      "title": "用户名密码登录-正常登录",
      "steps": "1. 打开登录页面\n2. 输入正确的用户名和密码\n3. 点击登录按钮",
      "expected_result": "登录成功，跳转到首页",
      "priority": "高",
      "test_type": "功能点测试"
    },
    {
      "title": "用户名密码登录-密码错误",
      "steps": "1. 打开登录页面\n2. 输入正确的用户名和错误密码\n3. 点击登录按钮",
      "expected_result": "提示密码错误，登录失败",
      "priority": "中",
      "test_type": "业务逻辑测试"
    }
  ],
  "error": null
}
```

## 核心功能详解

### 1. 推理模式

服务支持三种推理模式：

| 模式 | 接口 | 特点 | 适用场景 |
|------|------|------|----------|
| 单次推理 | `/infer` | 同步返回，自动提取 JSON | 单个问题查询 |
| 流式推理 | `/infer/stream` | SSE 流式返回，实时输出 | 长文本生成、实时交互 |
| 批量推理 | `/batch` | 同步处理多个请求 | 批量数据处理 |
| 异步批量 | `/batch/async` | 后台处理，轮询查询 | 大批量耗时任务 |

### 2. JSON 自动提取

AI 模型返回的内容可能包含：
- 思考过程标签：`<thought>...</thought>`、`<thinking>...</thinking>`、`...`
- Markdown 代码块：` ```json ... ``` `
- 混合文本

`json_extractor.py` 模块会智能提取：
```python
# 处理流程
原始内容 → 去除思考标签 → 提取 JSON 代码块/数组/对象 → 解析 JSON → 返回结果
```

### 3. 测试用例生成

**并行生成机制：**

```python
# 输入
module: "用户管理"
func_point: "用户登录"
test_directions: ["功能点测试", "业务逻辑测试", "其他测试"]

# 内部处理
并行调用模型 → generate_for_direction("功能点测试")
              → generate_for_direction("业务逻辑测试")
              → generate_for_direction("其他测试")

# 合并结果
所有测试方向的用例合并为一个列表返回
```

**测试方向提示词：**

| 测试方向 | 说明 |
|----------|------|
| 功能点测试 | 验证功能是否按预期工作 |
| 业务逻辑测试 | 验证业务规则和流程 |
| 其他测试 | 边界值、异常、安全等场景 |

### 4. 模型客户端

```python
class ModelClient:
    # 单例模式，避免重复创建连接
    _instance: AsyncOpenAI | None = None
    _model_id: str | None = None

    @classmethod
    async def infer(cls, messages, extract_json=True, temperature=None):
        """推理（非流式）"""

    @classmethod
    async def infer_stream(cls, messages):
        """推理（流式）"""

    @classmethod
    def reset(cls):
        """重置客户端"""
```

**特性：**
- 自动获取可用模型 ID
- 内置重试机制（可配置重试次数和间隔）
- 支持自定义 temperature
- 支持强制提取 JSON

### 5. 任务存储

```python
class TaskStatus(Enum):
    PENDING = "pending"       # 等待处理
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败

class TaskStore:
    # 内存存储（默认）
    _instance: dict[str, Task] = {}

    # 支持 Redis（分布式部署）
```

**任务生命周期：**

```
创建任务(PENDING) → 开始处理(PROCESSING) → 完成或失败(COMPLETED/FAILED)
                                                              ↓
                                                    自动清理（默认1小时后）
```

## 提示词管理

### 系统提示词 (`testcase_generate.txt`)

```
你是一位专业的软件测试工程师，你的任务是根据功能点帮我生成功能测试用例。

## 输出要求
1. 数组中的每个用例都必须是 JSON 格式
2. 每个测试用例必须包含以下字段：
   - testpoint: 测试点/用例标题
   - priority: 优先级（高/中/低）
   - steps: 测试步骤
   - expectation: 预期结果
```

### 测试方向映射 (`test_directions.txt`)

```
功能点测试:测试方向：功能点测试用例场景。请依据这些信息帮我生成功能测试用例。
业务逻辑测试:测试方向：业务逻辑测试用例场景。请依据这些信息帮我生成功能测试用例。
其他测试:测试方向：其他测试场景。请依据这些信息帮我生成功能测试用例。
```

**扩展测试方向：**
在 `test_directions.txt` 中添加新行即可扩展：

```
性能测试:测试方向：性能测试用例场景。请依据这些信息帮我生成性能测试用例。
安全测试:测试方向：安全测试用例场景。请依据这些信息帮我生成安全测试用例。
```

## 配置说明

### 模型配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `MODEL_API_KEY` | 模型 API 密钥 | EMPTY |
| `MODEL_BASE_URL` | 模型 API 地址 | http://120.209.70.202:31389/v1 |
| `MAX_TOKENS` | 最大输出 token | 81920 |
| `TEMPERATURE` | 温度参数 | 1.0 |
| `TOP_P` | Top-p 采样 | 0.95 |
| `PRESENCE_PENALTY` | 存在惩罚 | 1.5 |
| `TOP_K` | Top-k 采样 | 20 |

### 重试配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `MAX_RETRIES` | 最大重试次数 | 3 |
| `RETRY_DELAY` | 重试间隔（秒） | 2.0 |

### Redis 配置（可选）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `REDIS_URL` | Redis 连接 URL | redis://localhost:6379 |
| `USE_REDIS` | 是否使用 Redis | false |

## Docker 部署

### 单机部署

```bash
docker-compose up -d
```

### 分布式部署

```bash
# 启用 Redis
docker-compose --profile distributed up -d
```

### 健康检查

Docker Compose 配置了健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 日志

服务使用统一的日志模块 `app/utils/logger.py`，支持：
- 服务日志 (`service_logger`)
- 业务日志 (`get_logger(__name__)`)

### 添加新的提示词

1. 在 `app/prompts/` 目录下创建 `.txt` 文件
2. 在 `app/prompts/__init__.py` 中添加加载函数
3. 在引擎中调用提示词函数

### 扩展推理引擎

```python
class InferenceEngine:
    async def custom_infer(self, ...):
        """自定义推理方法"""
        full_messages = [{"role": "system", "content": custom_prompt}]
        full_messages.extend(messages)
        return await ModelClient.infer(full_messages)
```

### 切换模型

```bash
# 方法1：修改环境变量
MODEL_BASE_URL=http://new-model-url/v1

# 方法2：调用重置接口
curl -X POST http://localhost:8000/api/v1/reset
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `未获取到可用模型` | 模型 API 不可达 | 检查 `MODEL_BASE_URL` |
| `JSON 解析错误` | AI 返回格式异常 | 检查提示词，或降低 temperature |
| `达到最大重试次数` | 网络/模型问题 | 增加 `MAX_RETRIES` |

### 错误响应格式

```json
{
  "success": false,
  "result": null,
  "error": "错误描述信息"
}
```

## 性能优化

### 批量推理

使用批量接口减少网络开销：

```python
# 不推荐：循环调用单次推理
for item in items:
    result = await infer_single(item)

# 推荐：使用批量推理
results = await infer_batch(items)
```

### 并行生成

测试用例生成内部已实现并行：

```python
# 多个测试方向并行处理
tasks = [generate_for_direction(d) for d in test_directions]
results = await asyncio.gather(*tasks)
```

### 连接复用

`ModelClient` 使用单例模式，自动复用连接：

```python
# 全局单例，避免重复创建
_instance: AsyncOpenAI | None = None
```

## 许可证

Copyright © 2026
