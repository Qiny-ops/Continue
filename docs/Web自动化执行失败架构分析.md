# Web 自动化执行失败 · 架构级分析报告

> 日期：2026-08-16　范围：web-automation-service(:8003) / Django 转发层 / 前端入口 / 推理后端
> 依据：2026-08-12 ~ 2026-08-15 连续四轮「执行失败」的实证排查记录（BUGS.md 共 23 条）

---

## 1. 运行环境

| 项 | 值 |
|---|---|
| OS | Windows（win32），Git Bash 启动服务 |
| Python | 托管 venv `C:/Users/Qiny/.workbuddy/binaries/python/envs/default`（playwright 1.62.0 ↔ chromium-1234 匹配） |
| 服务拓扑 | Vue3 前端(:5173) → Django Testbackend(:8000) → web-automation-service(:8003, FastAPI) + Ollama(:11434, qwen2.5:3b) |
| 推理后端 | Ollama（本机正常，qwen2.5:3b 运行中） / WeKnora(:3000，**本机未启动**，`.env` 里 API Key 是非空占位符） |
| 被测站点 | B 站等真实站点（agentic 无头浏览器） |

## 2. 所用框架

- **8003 微服务**：FastAPI + `playwright.async_api`；pydantic-settings 读 `.env`；`httpx.AsyncClient` 流式调推理后端。
- **转发层**：Django `StreamingHttpResponse`（同步生成器逐行转发）+ 同步 `httpx.Client`（`apps/webauto/clients/`）。
- **前端**：Vue3 + 原生 fetch SSE 解析（`utils/sse.js`）；两个入口（`TestPage.vue` 独立列表页、`WebExecuteDialog.vue` 项目用例对话框）。
- **编排引擎**：`WebTestEngine`（lifespan 单例，持单个浏览器实例）→ `WebPlanner`（LLM 看页面快照规划）→ `WebTestExecutor`（语义锚点执行 + 自愈）。Reasoner 抽象：`OllamaReasoner` / `WeKnoraReasoner`。

## 3. 失败的具体报错信息或现象（近四轮实证清单）

| # | 现象 / 报错 | 定位根因 | 性质 |
|---|---|---|---|
| ① | `unsupported operand type(s) for +: 'coroutine' and 'str'` | `engine._expected_text_hit` 同步函数调 async Playwright `page.content()/title()`，漏 `await`，协程被拼接 | 脚本逻辑（async 契约违反）—— 已修 |
| ② | `plan_chunk` 第一轮就 `actions: []`，随后 `report(passed=false)`，前端「执行失败」 | planner 提示词缺动作规则 + `extract_json`/`_coerce_action_list` 容错不足，弱模型抖动输出被丢弃 | 脚本逻辑 —— 已修 |
| ③ | 同 ②（再次出现） | **推理后端选路黑洞**：`select_reasoner()` 只读 `os.getenv`，`.env` 不注入 `os.environ` → 进程在残留 `WEKNORA` 变量的 shell 里启动 → 误选未启动的 WeKnora → `reasoner.reason` 抛异常被吞 → 空 plan_chunk | 配置来源分裂 —— 已修 |
| ④ | `404 Not Found`，前端写死 `ElMessage.error('执行失败: ' + ...)` | `TestPage.vue` 把 Web 自动化用例打到 api-testing-service(:8002) 不存在的 `/api/v1/execute` | 前端对接错误 —— 已修 |
| ⑤ | 前端兜底「执行失败」（无任何细节） | SSE 链路任一层异常都被归一化成该文案，真实错误逐层丢失 | **架构问题（现存）** |

**共同特征**：用户看到的一切失败都收敛为同一个黑盒文案「执行失败」—— 这是本次分析的核心线索。

## 4. 执行流程

```
[触发] WebExecuteDialog.vue（项目用例）或 TestPage.vue（列表页）
   │  POST /webauto/execute/  {case_id | testcase, start_url, environment_id?, kb_id?, site_hint?}
   ▼
[Django :8000] WebAutomationViewSet.execute
   │  _resolve_testcase（case_id → TestCase.steps/expected_result）
   │  _resolve_start_url（start_url 或 environment.base_url）
   │  建 WebAutomationRun 记录 → StreamingHttpResponse 逐行转发
   ▼
[clients] WebAutomationClient.execute_stream（同步 httpx，180s 超时）
   ▼
[8003 :8003] /api/v1/webtest/execute
   │  engine._execute_web_testcase_impl（async generator，SSE）
   │    ├─ _build_reasoner(kb_id)  → kb_id 非空则强制 WeKnoraReasoner，否则 select_reasoner()
   │    ├─ planner = WebPlanner(reasoner)
   │    ├─ _session()：每次请求 new_context + page（浏览器实例进程级共享）
   │    ├─ 模式A 给定 action_list 确定性执行
   │    └─ 模式B agentic：capture_snapshot → planner.plan_chunk → executor.execute_actions
   │                          → repair 自愈 → 收敛判定 → planner.judge 语义裁判
   ▼
[推理后端] Ollama(:11434, qwen2.5:3b) 或 WeKnora(:3000, 未启动)
   ▼
[回传] 8003 SSE → Django 逐行透传（step/report/error 事件）→ 前端 sse.js 解析
   └─ 任一层异常 → 各自 try/except 兜底 → 前端 onError →「执行失败」
```

**执行节点与生命周期**：
- `WebTestEngine` 在 **lifespan 启动时创建一次**（`app.state.engine`），进程级单例，持有**单个 Playwright browser**；
- 每次 execute 由 `_session()` 新建独立 context/page（用例间隔离，✓）；
- reasoner 每次请求由 `_build_reasoner()` 新建，但**选路依据在进程启动时固化**（os.environ 启动后不可变 / .env 只读一次）；
- 无并发控制：多个 execute 可同时跑（各自 context，但共享浏览器内核 + 共享 Ollama）。

## 5. 判定：架构设计缺陷 vs 配置 / 脚本逻辑 / 环境不稳定

### 5.1 属于架构设计缺陷（需要结构性修复）

**F1｜错误信息逐层丢失（通信机制缺陷）—— 最致命**
4 层 SSE 透传（8003 → httpx → Django StreamingHttpResponse → 前端 fetch），每层都有 try/except 兜底并降级成泛化文案：8003 吞 reasoner 异常返回空 plan_chunk → Django 聚合为 `report(fail)` → 前端 `onError(err.error || '执行失败')` → 用户只见「执行失败」。真实根因（reasoner 连不上、planner 零产出、断言失败）全部不可见。**这是所有失败"看起来一样"的根本原因，也让每次排查都必须重跑链路取证。**

**F2｜推理后端选路双路径 + 参数优先 + 无探活（组件耦合缺陷）**
`engine._build_reasoner()`：
```python
kb_id = kb_id or settings.web_kb_id
if kb_id:
    return WeKnoraReasoner(kb_id=kb_id, kb_api_key=kb_api_key)   # ← 请求带 kb_id 即强制 WeKnora
return select_reasoner()
```
- 用户在 WebExecuteDialog 填了「站点知识库 ID」（`kb_id`）→ **无条件强制 WeKnoraReasoner**，即使 `.env` 配置是 `ollama`；本机 WeKnora(:3000) 未启动 → 必失败。**这是当前仍存在的触发点**（已修的三轮都不含 kb_id 场景）。
- `select_reasoner()`（修复前）只读 `os.environ`，与 `.env`（pydantic-settings）脱节 → 选路由「启动 shell 环境」决定，进程生命周期内固化。
- 无可用性探测/自动降级/告警：选错后端 = 确定性持续失败，而非偶发；因与启动环境相关，表面看像偶发。

**F3｜配置来源分裂（配置机制缺陷）**
`run.py` 不调用 `load_dotenv()`；pydantic-settings 只把 `.env` 读进 Settings 字段、不回写 `os.environ`。于是「读 `os.getenv` 的代码」（修复前的 select_reasoner）与「读 `settings` 的代码」对同一配置得到不同值 → `.env` 改了「看似生效」实际部分生效。这是 ③ 的直接土壤。

**F4｜资源调度缺失**
- 单浏览器实例 + 无并发队列/信号量：并发 execute 共享浏览器内核与 Ollama，无上限约束；
- 无**全局执行超时**：agentic 最多 8 轮 ×（LLM 单次 120s + 执行）可拖到十几分钟；仅有 `nav_timeout=20s` 与 httpx 180s 局部超时；
- `screenshots/` 无清理策略，长期运行累积磁盘。

**F5｜前端入口职责重复**
两个「Web 自动化」入口（TestPage / WebExecuteDialog）各自实现环境/知识库/执行逻辑，曾出现对接错服务(④)。同类能力重复实现 → 维护与排查成本翻倍。

### 5.2 属于脚本逻辑问题（已修复，防回归即可）

| 根因 | 修复 | 状态 |
|---|---|---|
| async 契约违反（协程拼接） | `_expected_text_hit` 改 async + await；全服务正则扫漏 | 已修 |
| planner 解析容错不足 / 提示词缺规则 | `extract_json` 重写 + `_coerce_action_list` + `ACTION_RULES` 注入 | 已修 |
| agentic 空转不收敛 | chunk 指纹重复检测 + 提前收敛 + `judge` 语义裁判 | 已修 |
| reasoner 选路黑洞 | `select_reasoner` 改读 `get_settings()`；`.env=ollama`；启动 export 双保险；首轮空 chunk 显式报错 | 已修 |

### 5.3 属于配置 / 环境不稳定（偶发或一次性）

- **启动 shell 环境残留**（曾 export `WEKNORA_*`）：进程继承后误选 WeKnora（③ 的诱因）—— 一次性，重启即恢复；
- **Ollama 可用性抖动**：模型未加载/服务重启的冷窗口；
- **目标站点与用例质量**：自然语言 steps 与真实页面元素不匹配（如 bilibili 首页无名为「登录」的 link）、站点反爬/验证码、网络波动 → agentic 判 `fail`，**非系统故障**。

### 5.4 关键结论

1. **已定位的四轮失败几乎全部是"条件触发即必现"的确定性缺陷**（coroutine、404、选路、解析），真正的偶发性只来自 LLM 输出抖动与环境（启动 shell）差异。不能归因为「环境不稳定」就收手。
2. **当前架构最大的问题不是某个 bug，而是 F1（错误黑盒）+ F2/F3（选路可信性）**——它们把"可诊断的失败"变成"不可诊断的失败"，导致每轮都需从链路取证才能定位。
3. **现存风险点**：用户在前端填写 `kb_id`（站点知识库）→ `_build_reasoner` 强制 WeKnora → 本机必失败。若用户再报「执行失败」，**首先确认 WebExecuteDialog 里是否填了知识库 ID**。
4. 浏览器/会话隔离（每请求独立 context）与 SSE 契约设计本身是合理的，不是缺陷。

## 6. 排查模块范围（明确清单）

| 优先级 | 模块 | 动作 |
|---|---|---|
| **P0** | `web-automation-service/app/engine.py::_build_reasoner` | kb_id 分支改为「仅当配置 weknora 才启用，否则忽略并提示」；reasoner 创建时探活，不可用自动降级 Ollama + 告警 |
| **P0** | `web-automation-service/app/services/reasoner.py` | `select_reasoner` 输出选中 reasoner（name/base_url/kb_id）到启动日志；`WeKnoraReasoner.reason` 失败记 `service_logger.error` 而非静默 |
| **P0** | `Testbackend/apps/webauto/clients/__init__.py` + `views/web_automation.py` | error 事件**透传原始 message**（含 stage/reasoner 信息），禁止降级成「服务异常/连接失败」 |
| **P0** | `vue3-frontend/src/api/modules/webauto.js` + `utils/sse.js` | onError 展示真实 `err.error`，禁止写死「执行失败」兜底 |
| **P1** | `run.py` + 全项目配置 | 显式 `load_dotenv()`；删除对 `os.getenv` 的配置读取，统一 `get_settings()` |
| **P1** | 8003 `/api/v1/health` | 加入 reasoner 探活（Ollama ping / WeKnora health）与浏览器状态 |
| **P1** | `WebTestEngine` | 并发信号量（如 max_concurrency=2）+ 全局执行超时（如 300s） |
| **P2** | 截图存储 | 定期清理 / 按 run 归档 |
| **P2** | 前端两入口 | 合并或菜单明确区分；kbId 输入加「未配置 WeKnora 时不生效」提示 |
| **P2** | 用例质量 | 补充站点知识库（`kb_seed`）、用例 steps 与真实站点对齐 |

## 7. 期望修复方向

1. **错误可观测性优先**：定义统一 SSE 错误协议 —— `{type:"error", data:{message, stage, detail}}`，所有兜底不得写死文案；Django 与前端透传原始错误。一次失败必须能一眼看到「卡在哪个 stage、哪个后端、什么异常」。
2. **选路可信性**：reasoner 选路单一来源（`get_settings()`）+ 启动日志打印实际选中项 + 创建前探活、失败降级 Ollama。
3. **配置单一来源**：`run.py` 显式加载 `.env`，代码统一从 `get_settings()` 读，消除「`.env` 改了不生效」类黑盒。
4. **资源治理**：并发信号量 + 全局执行超时 + 截图清理，杜绝资源型偶发。
5. **防回归**：把「reasoner 不可用」「plan_chunk 空」「kb_id 误触发 WeKnora」等场景纳入离线自检（扩展 `check_judge.py` 模式），每次改配置/选路逻辑后一键验证。
