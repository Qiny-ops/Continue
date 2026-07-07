# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

测试用例管理系统 — 基于 Vue 3 前端 + Django REST 后端的全栈应用，搭配三个 FastAPI 微服务：AI 测试用例生成、接口测试、RAG 知识库。

## 开发命令

### 启动/停止所有服务
```bash
python start_all.py                  # 启动所有服务（各服务在独立终端窗口中运行）
python start_all.py --skip-frontend  # 跳过前端
python start_all.py --skip-backend   # 跳过后端
python start_all.py --skip-ai-generator --skip-api-testing  # 跳过指定微服务
python stop_all.py                   # 停止所有服务（按端口杀进程）
```

### 前端 (vue3-frontend/)
```bash
pnpm dev          # 启动开发服务器 (端口 5173)
pnpm build        # 生产构建
pnpm preview      # 预览生产构建
pnpm lint         # 运行 oxlint + ESLint（通过 npm-run-all2 串联）
pnpm format       # Prettier 格式化
```

### 后端 (Testbackend/)
```bash
# Windows 下直接使用 venv 中的 Python
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000  # 启动开发服务器
venv\Scripts\python.exe manage.py migrate                   # 执行数据库迁移
venv\Scripts\python.exe manage.py makemigrations            # 创建迁移文件
venv\Scripts\python.exe manage.py createsuperuser           # 创建超级用户
venv\Scripts\python.exe manage.py test                      # 运行所有测试
venv\Scripts\python.exe manage.py test apps.users           # 运行指定 app 的测试
```

### AI 生成服务 (ai-generator-service/) — 端口 8001
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
pytest tests/                                             # 运行测试
```

### 接口测试服务 (api-testing-service/) — 端口 8002
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
python run_mcp_server.py                                  # 启动 MCP 服务器（stdio 传输）
pytest tests/                                             # 运行测试
```

### RAG 知识库 (RAG_kb/) — 端口通过 .env 配置
```bash
uvicorn app.main:app --reload
cd frontend && pnpm dev          # RAG 前端（如需使用）
pytest                           # 运行测试 (asyncio_mode=auto)
```

## 架构

### 服务总览

| 服务 | 端口 | 技术栈 | 用途 |
|------|------|--------|------|
| vue3-frontend | 5173 | Vue 3 + Vite + Element Plus | 主 SPA 应用 |
| Testbackend | 8000 | Django 5 + DRF + SQLite | API 后端 |
| ai-generator-service | 8001 | FastAPI + Pydantic v2 | LLM 驱动的测试用例生成 |
| api-testing-service | 8002 | FastAPI + Pydantic v2 | 接口测试执行 + MCP 服务器 |
| RAG_kb | 可配置 | FastAPI + SQLAlchemy | RAG 知识库 |

### 前端技术栈
- Vue 3.5+ Composition API（`<script setup>`）
- Pinia 3 状态管理（stores 在 `src/stores/modules/`：user、project、permission、member、nav）
- Vue Router 5 路由守卫（`src/router/guards.js`）
- Element Plus 通过 unplugin 自动导入（无需手动引入组件）
- Axios 统一错误处理（`src/api/axios.js`）— 响应拦截器自动解包 `response.data`，错误标准化为 `{type, message, status, data, originalError}`
- SSE 流式传输支持（`src/utils/sse.js`）

### 后端技术栈
- Django 5.x + Django REST Framework
- JWT 认证：自定义 `JWTAuthentication`（`apps.users.authentication`）
- 自定义用户模型：`apps.users.models.User`，含角色/权限体系
- SQLite（开发）/ PostgreSQL（生产）
- Repository/Service 分层模式：`BaseRepository` 和 `BaseService`（`apps/core/base/`）
  - Repository 基于类方法（无实例状态）
  - Service 返回 `(data, error_message)` 元组

### Django 应用（`Testbackend/apps/`）
```
users/      → User、Role、Permission、TokenBlacklist | repositories/ services/ views/
projects/   → Project、ProjectMember、ProjectRole | models/ repositories/ services/ views/
testcase/   → TestCaseRepository、TestCaseVersion、TestModule、TestCase、TestStep | repositories/ services/ views/
knowledge/  → 知识库集成（WeKnora）| clients/ai_client.py models/ views/
apitest/    → 接口测试模型 | models.py serializers/ views/
core/       → 公共基类（BaseRepository、BaseService）、中间件、工具
```

### 后端 API 路由
- `/api/users/` — 认证（登录/注册/登出）、用户 CRUD、角色、权限
- `/api/projects/` — 项目 CRUD、成员、收藏、统计
- `/api/testcase/` — 用例库、版本、模块、用例、评审、执行、AI 生成
- `/api/knowledge/` — 知识库 CRUD、搜索、agent 端点
- `/api/apitest/` — 接口测试管理

### 微服务公共模式
所有 FastAPI 微服务共享：
- Pydantic v2 `BaseSettings`，通过 `app.config.get_settings()` 获取（RAG_kb 使用 `app.config.settings`）
- CORS 中间件允许所有来源
- 请求日志中间件
- 全面使用 async/await
- API 文档：`/docs`（Swagger）、`/redoc`
- 健康检查：`/api/v1/health`（RAG_kb 为 `/health`）

**ai-generator-service**：路由在 `/api/v1/inference`，核心为 `InferenceEngine`，支持同步/流式/批量推理，`TaskStore` 管理异步任务状态

**api-testing-service**：路由在 `/api/v1`（`routers/rpc.py`），`execute/` 包含引擎和执行器，MCP 服务器通过 stdio 传输暴露工具

**RAG_kb**：SQLAlchemy 异步引擎，启动时自动建表，路由包括 knowledge-bases、documents、search、chat、agent、import/export、team、tasks；启动时创建默认管理员用户

### 前端路由结构
路由按模块组织在 `src/router/modules/`（auth、project、system）。项目路由使用 `/p/:code/...` 模式。路由守卫检查：
1. Token 存在性及会话恢复
2. `meta.requiresAuth`（默认为 true）
3. `meta.permissions` / `meta.roles` — 系统级权限
4. `meta.projectPermissions` / `meta.projectAdmin` — 项目级权限

### 前端 API 层
API 模块在 `src/api/modules/`（auth、project、testcase、knowledge、apitest、member、permission、projectKnowledgeBase），均使用共享 axios 实例。SSE 端点使用 `src/utils/sse.js` 的 `createSSEStream()`。

### 前端 Composables
按领域组织在 `src/composables/`：auth/、common/、permission/、project/、testcase/

## 关键模式

### 后端 Repository/Service 分层
```python
# repositories/ — 数据访问层（类方法，无实例）
class TestCaseRepository(BaseRepository):
    model = TestCase
    def get_by_module(cls, module_id): ...

# services/ — 业务逻辑层（返回 (data, error) 元组）
class TestCaseService(BaseService):
    repository = TestCaseRepository
    def create_case(cls, data):
        case = cls.repository.create(**data)
        return cls.success(case)

# views/ — 薄 HTTP 处理层，委托给 service
```

### 认证流程
1. 登录返回 JWT token
2. Token 通过 Pinia 持久化存储在 localStorage，Axios 请求拦截器自动附加
3. 后端通过 `JWTAuthentication` 类验证
4. 401 响应由 Axios 响应拦截器处理，自动跳转 `/login`
5. 登出时将 token 加入 `TokenBlacklist`

### 前端 Element Plus 使用
组件自动导入 — 无需手动 import Element Plus 组件或注册。`el-*` 组件和 `El*` 组合式 API 均全局可用。

## 环境变量

### 后端 (Testbackend/.env)
- `DJANGO_SECRET_KEY` — 生产环境必须设置
- `DJANGO_DEBUG` — 生产环境设为 'false'
- `DJANGO_ALLOWED_HOSTS` — 逗号分隔的允许主机
- `JWT_SECRET` — JWT 签名密钥
- `JWT_EXPIRATION_HOURS` — Token 过期时间（默认 24）
- `WEKNORA_API_KEY` — 知识库 API 密钥
- `AI_SERVICE_URL` — AI 生成服务地址（默认 http://localhost:8001）
- `API_TESTING_SERVICE_URL` — 接口测试服务地址（默认 http://localhost:8002）

### AI 生成服务 (ai-generator-service/.env)
- `OPENAI_API_KEY` — LLM API 密钥
- `OPENAI_BASE_URL` — API 基础地址（支持 OpenAI 兼容端点）
- `REDIS_URL` — Redis 连接，用于任务存储（可选）

### 接口测试服务 (api-testing-service/.env)
- `DATABASE_URL` — 数据库连接字符串
- `LLM_API_KEY` / `LLM_BASE_URL` — LLM 配置

### 前端
- `VITE_API_BASE_URL` — 后端地址（默认 http://localhost:8000/api）

## 代码风格

- 前端：ESLint 9 flat config + Prettier（semi: false, singleQuote: true, printWidth: 100）
- 前端 lint 执行顺序：先 oxlint，后 ESLint（通过 `run-s lint:*` 串联）
- 前端要求 Node ^20.19.0 || >=22.12.0
- 后端：Python，遵循 Django 规范
- RAG_kb：Ruff（line-length: 100, target: py310）
- Vue 组件：PascalCase 文件名，`<script setup>` 语法，`vue/multi-word-component-names` 已关闭
- 提交信息：Conventional Commits 格式

## 注意事项

- 前端颜色必须使用纯色，禁止渐变（来自用户反馈）
- `AIGeneratorTest/` 和 `ApiTesting/` 是 `ai-generator-service/` 和 `api-testing-service/` 的早期版本，开发请使用后者
- `vue3-frontend-backup-20260609/` 是备份目录，非活跃代码
