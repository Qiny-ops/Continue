# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

测试用例管理系统 —— 基于 Vue 3 前端 + Django REST 后端的全栈应用，搭配两个 FastAPI 微服务：AI 测试用例生成（ai-generator）、接口测试执行（api-testing）。通过 WeKnora 代理接入外部知识库。

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
# 使用项目根目录下的 .django-venv
python manage.py runserver 0.0.0.0:8000  # 启动开发服务器
python manage.py migrate                   # 执行数据库迁移
python manage.py makemigrations            # 创建迁移文件
python manage.py createsuperuser           # 创建超级用户
pytest                                      # 运行所有测试（pytest.ini 限定 testpaths=apps）
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

## 架构

### 服务总览

| 服务 | 端口 | 技术栈 | 用途 |
|------|------|--------|------|
| vue3-frontend | 5173 | Vue 3 + Vite + Element Plus | 主 SPA 应用 |
| Testbackend | 8000 | Django 5 + DRF + SQLite | API 后端 |
| ai-generator-service | 8001 | FastAPI + Pydantic v2 | LLM 驱动的测试用例生成 |
| api-testing-service | 8002 | FastAPI + Pydantic v2 | 接口测试执行 + MCP 服务器 |
| web-automation-service | 8003 | FastAPI + Pydantic v2 + Playwright | Web 自动化执行（语义锚点 + 看页面闭环） |

### 数据流
```
浏览器 (Vue3 :5173)
   │  JWT Bearer
   ▼
Django 5 + DRF ( :8000, SQLite )
   │  Repository/Service/View 分层
   ├─► httpx(线程池) ──► ai-generator  :8001   (LLM 生成用例)
   ├─► httpx(SSE 透传) ─► api-testing   :8002   (执行接口测试)
   ├─► httpx(SSE 透传) ─► web-automation :8003  (执行 Web 自动化用例)
   └─► requests(同步)  ─► WeKnora       :3000   (外部知识库代理)
```

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
- Repository/Service/View 分层模式：
  - Repository 基于类方法（无实例状态），负责纯数据访问
  - Service 抛 `apps.core.exceptions.BaseAPIException` 子类（`NotFoundError`/`PermissionDenied`/`ValidationError`/`BusinessError`/`ServiceError`），由 DRF 异常处理器 `custom_exception_handler` 统一转为 `StandardResponse({code, message, data})` 响应体。成功时只返回数据，不再使用 `(data, error)` 元组。
  - View 只负责参数接收 + 调用 Service + 返回响应，不再含错误处理或中文子串判 HTTP 状态码的逻辑。

### Django 应用（`Testbackend/apps/`）
```
users/      → User、Role、Permission、TokenBlacklist | repositories/ services/ views/
projects/   → Project、ProjectMember、ProjectRole | repositories/ services/ views/
testcase/   → TestCaseRepository、TestCaseVersion、TestModule、TestCase | repositories/ services/ views/
knowledge/  → 知识库集成（WeKnora）| clients/ai_client.py views/
apitest/    → 接口测试模型 | models.py serializers/ views/ services/
requirement/ → 需求关联 | services/
core/       → 公共基类、异常体系、中间件、权限装饰器、工具
```

### 后端 API 路由
- `/api/users/` — 认证（登录/注册/登出）、用户 CRUD、角色、权限
- `/api/projects/` — 项目 CRUD、成员、收藏、统计、知识库关联
- `/api/testcase/` — 用例库、版本、模块、用例、评审、执行、AI 生成
- `/api/knowledge/` — 知识库 CRUD、搜索、agent 端点
- `/api/apitest/` — 接口测试管理
- `/api/requirements/` — 需求管理

### 微服务独立原则（2026-09 起）

三个 FastAPI 微服务之间**零共享依赖**（原 `common/` 共享包已于 2026-09 拆分下沉到各服务内部并删除）。每个服务自包含：
- `config.py` — 全量定义自己的配置字段（模型 API、推理参数、重试、CORS 等）
- `utils/logger.py` — 各自独立的日志实现（默认 stderr，MCP 安全）
- `utils/json_parser.py` / `json_extractor.py` — 各自独立的 LLM JSON 解析实现

修改某个服务的配置或工具代码不会影响其他服务；服务目录可整体独立搬移。代价是三份相似代码需要分别维护。

### 前端路由结构
路由按模块组织在 `src/router/modules/`（auth、project、system）。项目路由使用 `/p/:code/...` 模式。路由守卫检查：
1. Token 存在性及会话恢复
2. `meta.requiresAuth`（默认为 true）
3. `meta.permissions` / `meta.roles` — 系统级权限
4. `meta.projectPermissions` / `meta.projectAdmin` — 项目级权限

### 前端 API 层
API 模块在 `src/api/modules/`（auth、project、testcase、knowledge、apitest、member、permission、projectKnowledgeBase），均使用共享 axios 实例。SSE 端点使用 `src/utils/sse.js` 的 `createSSEStream()`。401 通过回调实现路由跳转（而非整页刷新 `window.location.href`），见 `src/api/axios.js::setOnAuthRedirect`。

### 前端 Composables
按领域组织在 `src/composables/`：auth/、common/、permission/、project/、testcase/

## 错误处理契约（2026-08 统一）

所有 Service 方法：
- **成功**：直接返回数据（非元组）
- **失败**：抛出 `BaseAPIException` 子类，由 `apps.core.utils.exception_handler.custom_exception_handler` 自动转换为 `StandardResponse({code, message, data})`

异常类型 → HTTP 状态码映射：
| 异常类 | HTTP | 语义 |
|--------|------|------|
| `NotFoundError` | 404 | 资源不存在 |
| `PermissionDenied` | 403 | 无权限 |
| `ValidationError` | 400 | 参数/数据校验失败 |
| `BusinessError` | 400 | 业务规则冲突（重复/已存在等） |
| `AuthenticationError` | 401 | 身份认证失败 |
| `ServiceError` | 400 | 服务/配置错误 |
| `RateLimitError` | 429 | 频率限制 |

## 认证流程
1. 登录返回 JWT token
2. Token 通过 Pinia 持久化存储在 localStorage，Axios 请求拦截器自动附加
3. 后端通过 `JWTAuthentication` 类验证
4. 401 响应由 Axios 响应拦截器处理，通过 `setOnAuthRedirect(router.push)` 回调使用 Vue Router 跳转 `/login`（不刷新整页）
5. 登出时将 token 加入 `TokenBlacklist`

## 前端 Element Plus 使用
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
- `WEB_AUTOMATION_SERVICE_URL` — Web 自动化服务地址（默认 http://localhost:8003）
- `WEB_AUTOMATION_API_KEY` — 调用 Web 自动化服务时携带的 API Key（空=开发模式不强制）

### AI 生成服务 (ai-generator-service/.env)
- `MODEL_API_KEY` — LLM API 密钥
- `MODEL_BASE_URL` — API 基础地址（支持 OpenAI 兼容端点）
- `REDIS_URL` — Redis 连接，用于任务存储（可选）

### 接口测试服务 (api-testing-service/.env)
- `MODEL_API_KEY` / `MODEL_BASE_URL` — LLM 配置
- `KB_BASE_URL` / `KB_ID` / `KB_API_KEY` — 知识库配置（WeKnora）

### Web 自动化服务 (web-automation-service/.env)
- `WEB_REASONER` — 推理后端选路：`auto`（默认，配了 WeKnora 才用，否则 Ollama 兜底）/ `ollama` / `weknora`
- `WEKNORA_BASE_URL` / `WEKNORA_API_KEY` / `WEB_KB_ID` — 知识库配置（WeKnora 智能推理，站点知识）
- `WEB_MODEL_BASE_URL` / `WEB_MODEL_NAME` — Ollama 兜底（本地优先、离线可用，默认 `qwen2.5:3b`）
- `HEADLESS` / `BROWSER_TIMEOUT` / `SCREENSHOT_DIR` — 浏览器与执行配置
- `API_KEY` / `INTERNAL_API_KEY` — 安全配置（与 Django 侧 `WEB_AUTOMATION_API_KEY` / `INTERNAL_API_KEY` 对应）

### 前端
- `VITE_API_BASE_URL` — 后端地址（默认 http://localhost:8000/api）

## 代码风格

- 前端：ESLint 9 flat config + Prettier（semi: false, singleQuote: true, printWidth: 100）
- 前端 lint 执行顺序：先 oxlint，后 ESLint（通过 `run-s lint:*` 串联）
- 前端要求 Node ^20.19.0 || >=22.12.0
- 后端：Python，遵循 Django 规范
- Vue 组件：PascalCase 文件名，`<script setup>` 语法，`vue/multi-word-component-names` 已关闭
- 提交信息：Conventional Commits 格式

## 注意事项

- 前端颜色必须使用纯色，禁止渐变（来自用户反馈）
- `docs/项目重构分析报告与计划.md` 包含各阶段的详细重构计划与已知技术债清单
