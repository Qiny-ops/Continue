# Web 自动化适配器实现方案

> 目标：在现有 AI 驱动接口自动化框架（`api-testing-service` + `TestEngine`）之上，平移出一套 **AI 驱动 Web UI 自动化**能力。
> 核心约束：**不重新生成用例**——直接吃 `TestCase` 里已有的 `precondition` / `steps` / `expected_result`，由 LLM 翻译成浏览器可执行的动作序列。
> 关键难点（也是本方案重点）：LLM 看不到 DOM，编排与操作必须以**页面运行时快照**为输入，以**语义锚点**为输出。

---

## 1. 整体架构

```
TestCase(precondition / steps / expected_result)
        │  直接作为输入（跳过"生成用例"）
        ▼
┌─────────────────────────────────────────────────────┐
│  TestEngine（复用，新增 Web 分支）                      │
│   ├─ ① plan_web_actions   (LLM: 步骤 → action_list)   │
│   ├─ ② fill_web_data      (LLM: 填表单值，保留 {{var}}) │
│   ├─ ③ execute_testcase    ── 分支 ── ▼                │
│   │       接口路径: ApiTestExecutor（已有）            │
│   │       Web  路径: WebTestExecutor（新增，Playwright）│
│   └─ ④ validate_testcase   (LLM: 多模态截图 + DOM 断言) │
│                                                        │
│  复用: {{var}} 占位符解析 / runtime_vars / 账号隔离      │
│        / TestCaseExecution 回写                         │
└─────────────────────────────────────────────────────┘
        │
        ▼
WebTestExecutor(Playwright)
  ├─ 抓取 Accessibility Tree（"看页面"）
  ├─ Locator Resolver（语义锚点 → 真实元素）
  └─ 执行 navigate/fill/click/extract/assert + 截图
        │
        ▼
automation_status = automated
automation_case_id = WebAutomationPlan.plan_uid   ← 见 §6 存储结构
```

**复用 / 新增对照**

| 组件 | 接口自动化 | Web 自动化 | 关系 |
|---|---|---|---|
| 编排 LLM | `get_api_dependency` | `plan_web_actions` | 改写提示词（run_list → action_list） |
| 数据填充 LLM | `fill_test_data` | `fill_web_data` | 同构（填表单值 vs 填 HTTP 参数） |
| 执行器 | `ApiTestExecutor` | `WebTestExecutor` | **重写**（唯一大块新代码） |
| 校验 LLM | `validate_testcase` | `validate_testcase`(多模态) | 升级（截图比对 vs 状态码比对） |
| 占位符 / runtime_vars | `_resolve_placeholders` | 直接复用 | 不改 |
| 账号隔离 | `bind_test_accounts` | 直接复用 | 不改 |
| 执行记录 | `TestCaseExecution` | 直接复用 | 不改 |

---

## 2. 核心概念：语义锚点（Semantic Anchor）

LLM **不输出 CSS 选择器**（重构即崩），而是输出**语义锚点**——描述"想操作哪个元素"的自然语言意图。`WebTestExecutor` 内的 `Locator Resolver` 在真实 DOM 里把锚点解析成元素。

```json
"target": {
  "type": "label",            // label | role | text | css(兜底) | coordinate(兜底视觉)
  "value": "用户名",           // 与页面可见文本匹配
  "role": "textbox",          // type=role 时填，对应 ARIA role
  "confidence": 0.9           // 解析置信度，低则触发自愈/视觉回退
}
```

锚点解析优先级（在 `Locator Resolver` 内按顺序尝试，命中即停）：
1. `label` → `page.getByLabel(value)`
2. `role+name` → `page.getByRole(role, {name})`
3. `text` → `page.getByText(value)`
4. `css` → `page.locator(css)`（兜底，不推荐 LLM 主动使用）
5. `coordinate` → 多模态模型点选 (x,y)（最终兜底，最脆弱）

> **稳定性命门**：只要页面重构后「可见文字 / ARIA role」不变，脚本仍可用。这比 CSS 选择器健壮一个数量级。

---

## 3. 页面快照输入格式（"看页面"的数据契约）

`WebTestExecutor` 在执行每个 `navigate` / 校验 `assert` 前，抓取当前页 **Accessibility Tree**（Playwright `page.accessibility.snapshot()`），裁剪后作为上下文喂给 LLM。

**快照结构（精简版，去掉不可见、限制深度 ≤ 8）**

```json
{
  "url": "https://app.example.com/login",
  "title": "登录",
  "elements": [
    {"ref": "e12", "role": "textbox",  "name": "用户名", "value": "",     "required": true},
    {"ref": "e13", "role": "textbox",  "name": "密码",   "type": "password"},
    {"ref": "e14", "role": "button",   "name": "登录"},
    {"ref": "e15", "role": "link",     "name": "忘记密码？", "href": "/reset"}
  ]
}
```

- `ref`：页面内稳定引用，供 LLM 在 action_list 里直接引用（比重复整段文本省 token）。
- 仅含 `visible` 元素；图片/装饰节点剔除。
- 单页元素上限 200，超出则按视口裁剪并提示 LLM。

**两种编排范式（见 §5 提示词）**
- **Agent 式（边走边编）**：每个动作前实时抓快照 → LLM 决定下一动作。
- **编译缓存式（先看后编）**：首跑探针采集各步快照+元素指纹 → LLM 一次编译 `action_list` → 存盘 → 后续回放。

---

## 4. action_list 完整 Schema

```json
{
  "case_id": 1,
  "base_url": "https://app.example.com",
  "browser": "chromium",
  "action_list": [
    {
      "step": 1,
      "action": "navigate",
      "url": "{{base_url}}/login",
      "description": "打开登录页"
    },
    {
      "step": 2,
      "action": "fill",
      "target": {"type": "label", "value": "用户名"},
      "value": "{{user}}"
    },
    {
      "step": 3,
      "action": "fill",
      "target": {"type": "label", "value": "密码"},
      "value": "__ADMIN_PASSWORD__"
    },
    {
      "step": 4,
      "action": "click",
      "target": {"type": "role", "role": "button", "name": "登录"}
    },
    {
      "step": 5,
      "action": "wait",
      "target": {"type": "url", "match": "**/home"},
      "timeout_ms": 5000
    },
    {
      "step": 6,
      "action": "extract",
      "name": "order_id",
      "from": {"type": "text", "target": {"type": "text", "value": "订单号：.*"}, "attribute": "innerText"}
    },
    {
      "step": 7,
      "action": "assert",
      "expect": "首页欢迎语可见",
      "check": {"type": "visible", "target": {"type": "text", "value": "欢迎"}}
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `action` | `navigate` / `fill` / `click` / `wait` / `extract` / `assert` |
| `target` | §2 语义锚点；`navigate`/`wait` 用 `url` |
| `value` | 表单值；支持 `{{var}}` 与 `__ADMIN_PASSWORD__` 等预设 |
| `extract.name` + `from` | 从页面提取值存为 `runtime_vars[name]`（替代接口版的 JSONPath extract_vars） |
| `assert.check` | `visible` / `text_equals` / `contains` / `url_match` / `attribute`（DOM 断言）；复杂视觉断言交给 §4 校验 LLM |

---

## 5. 与 `TestEngine` 的对接 diff

### 5.1 `execute_testcase`（engine.py:206）—— 新增 Web 分支

```python
# 现有（接口路径）：遍历 run_list → ApiTestExecutor.execute_api
# 新增：若传入 action_list 而非 run_list，走 Web 路径

async def execute_testcase(self, case_id, ..., run_list=None, action_list=None, ...):
    if action_list:                                   # ← Web 分支
        executor = WebTestExecutor(base_url=base_url)
        results = await executor.execute_actions(action_list, runtime_vars)
    else:                                             # ← 现有接口分支（不变）
        executor = ApiTestExecutor(base_url=base_url)
        for api_info in run_list:
            api_info = self._resolve_placeholders(api_info, runtime_vars)  # 复用
            result = await executor.execute_api(api_info)
            self._collect_extract(result, runtime_vars)                      # 复用
    ...
```

**占位符系统 `_resolve_placeholders`（engine.py:581）直接复用**——`{{var}}` 的替换逻辑与 HTTP 完全解耦，Web 版只是把 `runtime_vars` 的来源从「response body」改成「页面提取值」。

### 5.2 提取逻辑：新增 `_extract_value_from_page` 替换 `_extract_value_from_response`（engine.py:666）

```python
def _extract_value_from_page(self, page_state: dict, spec: dict) -> Optional[Any]:
    """spec 来自 action_list 的 extract.from，如 {type:'text', attribute:'innerText'}"""
    locator = self._resolve_locator(spec["target"])   # 复用 §2 Resolver
    if spec["attribute"] == "innerText":   return locator.inner_text()
    if spec["attribute"] == "value":       return locator.input_value()
    if spec["attribute"] == "href":        return locator.get_attribute("href")
    if spec["attribute"] == "visible":     return locator.is_visible()
```

### 5.3 新增 `WebTestExecutor`（对齐 `ExecutionResult`）

`api-testing-service/app/execute/web_executor.py`：

```python
@dataclass
class WebExecutionResult:
    step: int
    action: str
    target: Optional[dict] = None
    success: bool = False
    url: Optional[str] = None
    screenshot_path: Optional[str] = None     # 每步留证，供多模态校验
    extracted: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0

class WebTestExecutor:
    async def execute_actions(self, action_list, runtime_vars) -> List[WebExecutionResult]:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()      # 长生命周期，维持 session
            page = await context.new_page()
            for act in action_list:
                snap = await page.accessibility.snapshot()   # §3 看页面
                # 解析语义锚点 → 真实元素 → 执行 → 截图 → 自愈
                ...
```

### 5.4 `validate_testcase`（engine.py:409）—— 多模态升级

- 接口版：比对 `expected_status` + JSON body。
- Web 版：把每步 `screenshot_path` + DOM 断言结果 + `expected_result` 喂给**多模态 LLM**，输出 `pass/fail` + 原因。
- 降级策略：DOM 断言（§4 `assert.check`）直接判定，仅关键节点用截图抽验，控制成本。

---

## 6. `automation_case_id` 存储结构（关键约束）

**现状问题**：`TestCase.automation_case_id` 是 `CharField(max_length=255)`（test_case.py:210），**存不下完整 action_list JSON**（一个用例动作序列常超 255 字符）。

**解决方案：新增独立表 `WebAutomationPlan`**（与现有 `AIGenerationRecord` 解耦风格一致，不破坏接口自动化逻辑）

```python
class WebAutomationPlan(models.Model):
    plan_uid = models.CharField(max_length=64, unique=True)   # 如 "WAP-20260811-0a1b"
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="web_plans")
    action_plan = models.JSONField()        # §4 完整 action_list（任意长度）
    snapshot_meta = models.JSONField(default=dict)  # 页面指纹 / 版本戳，用于自愈判定
    browser = models.CharField(max_length=20, default="chromium")
    base_url = models.URLField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**映射关系**
- `TestCase.automation_case_id` ← 存 `WebAutomationPlan.plan_uid`（仍是短字符串，符合 255 限制）。
- `TestCase.automation_status` ← 编译成功后置 `automated`。
- 执行时：`plan = WebAutomationPlan.objects.get(plan_uid=test_case.automation_case_id)` → 取 `action_plan` 回放。

**备选方案 B**（不推荐）：给 `TestCase` 直接加 `web_action_plan = JSONField()`——需 migration 且与 `automation_case_id` 语义重叠。

---

## 7. 提示词草案

### 7.1 `web_dependency.txt`（编排：步骤 → action_list）

```
你是 Web 测试动作编排助手。根据功能测试用例的步骤和当前页面快照，输出浏览器动作序列。

测试用例步骤：
{{steps}}
前置条件：{{precondition}}
预期结果：{{expected_result}}

当前页面快照（Accessibility Tree）：
{{page_snapshot}}

要求：
1. 直接返回 JSON（不要 markdown），格式见 action_list Schema。
2. 元素的 target 必须用「语义锚点」（label / role+name / text），禁止输出 CSS 选择器。
3. 需要从上一步结果取值时，用 extract + {{变量名}} 占位符；路径用 DOM 提取描述（innerText/value/href/visible）。
4. 动态账号用时间戳格式；管理员用 __ADMIN_USERNAME__ / __ADMIN_PASSWORD__。
5. 每步保留 description，便于回放与排错。
```

### 7.2 `web_execute.txt`（数据填充，改写自 execute_api.txt）

```
你是 Web 测试数据填充助手。为 action_list 的 fill 动作填充静态值。
关键规则：不要替换 {{变量名}} 占位符！这些会在运行时从页面提取值注入。
只填充静态表单值（用户名/密码/手机号/邮箱），保留所有 extract 与 {{var}} 原样。
...（同 execute_api.txt 的强密码/合法手机号约束）
```

### 7.3 校验（多模态，升级自 validate_testcase）

```
你是 Web 测试校验助手。对比「预期结果」与「执行截图 + DOM 断言」：
- 优先采信 DOM 断言（可见性/文本/URL）；
- 视觉类诉求（布局/文案语气）用截图判定；
输出 {pass: bool, reason: str}。
```

---

## 8. 复用清单（无需新建）

| 能力 | 来源 | 说明 |
|---|---|---|
| `{{var}}` 占位符解析 | `_resolve_placeholders` (engine.py:581) | 直接复用，仅变量来源变 |
| `runtime_vars` 按步骤索引 | execute_testcase:261 | 防多用户串号，直接复用 |
| 账号隔离 / 清理 | `bind_test_accounts` / `_cleanup_test_user` | 直接复用 |
| 执行记录回写 | `TestCaseExecution` (result / actual_result) | 直接复用，连 UI 都不用新建 |
| MCP 接入 | `app/mcp_server.py` (FastMCP) | 新增 Web 工具组挂同一 MCP |
| 截图留证 | `WebExecutionResult.screenshot_path` | 新字段，供多模态校验 |

---

## 9. 风险与下一步

| 风险 | 缓解 |
|---|---|
| 元素定位随重构失效 | 语义锚点 + 每步回抓自愈 + 视觉兜底 |
| UI 比 API 更易 flaky | 智能等待 / 重试；`wait` 动作显式等待条件 |
| 多模态校验成本高 | DOM 断言优先，仅关键节点截图抽验 |
| 首编依赖"看页面" | 编译缓存式：首次探针采集，后续回放 |

**建议落地顺序**
1. 新增 `WebAutomationPlan` 模型 + migration（§6）。
2. 实现 `WebTestExecutor` + `Locator Resolver` + 快照抓取（§3/§5.3），先跑通"登录→首页"单链路。
3. 写 `web_dependency.txt` / `web_execute.txt`，接 `plan_web_actions` / `fill_web_data`（§5.1/§7）。
4. 多模态 `validate_testcase` 升级（§5.4）。
5. 在 `mcp_server.py` 注册 Web 工具组，对齐现有 MCP。
