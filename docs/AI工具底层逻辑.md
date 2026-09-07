# AI 工具底层逻辑 — 融会贯通

从本项目中提炼出的 AI 应用底层架构，适用于任何 AI 工具的构建。

---

## 一、全局架构：AI 应用的五层模型

```
┌─────────────────────────────────────────────────┐
│  Layer 5: 业务流程编排（Agent / Pipeline）        │  ← 多步推理、工具链、状态机
├─────────────────────────────────────────────────┤
│  Layer 4: Prompt 工程（模板 + 变量 + 输出约束）    │  ← 提示词即代码
├─────────────────────────────────────────────────┤
│  Layer 3: 输出解析（JSON 提取 + 结构化校验）       │  ← 从非确定性中提取确定性
├─────────────────────────────────────────────────┤
│  Layer 2: LLM 调用层（同步/流式/批量 + 重试）      │  ← 屏蔽模型差异的统一接口
├─────────────────────────────────────────────────┤
│  Layer 1: 基础设施（配置 + 日志 + 会话管理）       │  ← 一切的地基
└─────────────────────────────────────────────────┘
```

每一层只依赖下一层，不跨层调用。理解这五层，就理解了所有 AI 工具的骨架。

---

## 二、Layer 1：基础设施

### 2.1 配置管理 — 单例模式 + 环境变量

所有 AI 服务共享同一个配置模式：

```python
# 模式：Pydantic BaseSettings + lru_cache 单例
class Settings(BaseSettings):
    model_api_key: str = "EMPTY"          # API 密钥
    model_base_url: str = "http://..."    # API 地址（兼容 OpenAI 格式）
    max_tokens: int = 81920               # 最大输出长度
    temperature: float = 1.0              # 生成温度
    top_p: float = 0.95                   # 采样范围
    max_retries: int = 3                  # 重试次数
    retry_delay: float = 2.0              # 重试间隔

    class Config:
        env_file = ".env"                 # 从 .env 读取，覆盖默认值

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**核心洞察**：
- `model_base_url` 使用 OpenAI 兼容格式（`/v1`），这意味着任何兼容 OpenAI API 的模型（国产模型、本地部署、Azure）都可以无缝替换
- `lru_cache` 保证全局只有一个配置实例，避免重复读取环境变量
- 推理参数（temperature、top_p）放在配置层而非硬编码，因为不同任务需要不同参数

### 2.2 会话管理 — 创建-使用-销毁模式

RAG 场景下的会话生命周期：

```
创建会话 → 多轮对话 → 销毁会话
   ↑                        ↑
  必须配对                  finally 保证
```

```python
session_id = None
try:
    session_result = await kb_client.create_session(kb_id)
    session_id = session_result.get("id")
    # ... 使用会话 ...
finally:
    if session_id:
        await kb_client.destroy_session(session_id)
```

**核心洞察**：会话是有状态资源，必须用 try/finally 保证销毁，否则会泄漏。这个模式和数据库连接、文件句柄完全一致。

---

## 三、Layer 2：LLM 调用层

### 3.1 统一调用接口 — 屏蔽模型差异

项目中有两种 LLM 调用方式，但本质相同：

| 方式 | 实现 | 适用场景 |
|------|------|----------|
| SDK 调用 | `AsyncOpenAI().chat.completions.create()` | 直接调模型 |
| HTTP 调用 | `httpx.post("/chat/completions")` | 通过中间服务（RAG）调模型 |

**它们的共同协议** — OpenAI Chat Completions 格式：

```python
# 请求
{
    "model": "model-id",
    "messages": [
        {"role": "system", "content": "系统提示词"},
        {"role": "user", "content": "用户输入"}
    ],
    "max_tokens": 81920,
    "temperature": 1.0,
    "stream": false
}

# 响应
{
    "choices": [{
        "message": {"content": "AI 回复"},
        "finish_reason": "stop"
    }]
}
```

**核心洞察**：OpenAI 的 Chat Completions API 已经成为事实标准。所有国产模型（通义千问、智谱、讯飞、DeepSeek）都兼容这个格式。掌握这一个协议，就能调用市面上 90% 的模型。

### 3.2 三种调用模式

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  同步调用  │    │  流式调用  │    │  批量调用  │
│  infer()  │    │  stream() │    │  batch()  │
└──────────┘    └──────────┘    └──────────┘
     ↓               ↓               ↓
 等待完整结果    逐 chunk 返回    并行多个请求
 适合后台任务    适合实时展示     适合批量生成
```

**同步调用**：
```python
response = await client.chat.completions.create(
    model=model_id, messages=messages, stream=False
)
content = response.choices[0].message.content
```

**流式调用**（SSE — Server-Sent Events）：
```python
stream = await client.chat.completions.create(
    model=model_id, messages=messages, stream=True
)
async for chunk in stream:
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

**批量调用**（并行 + asyncio.gather）：
```python
tasks = [generate_for_direction(d) for d in directions]
results = await asyncio.gather(*tasks)
```

**核心洞察**：
- 流式调用的本质是 SSE 协议：服务端持续发送 `data: xxx\n\n`，客户端逐行读取
- 批量调用不是 API 特性，而是应用层的并行编排 — 用 `asyncio.gather` 同时发起多个独立请求
- 三种模式的选择标准：用户是否需要实时看到中间结果

### 3.3 重试机制 — 指数退避

```python
for attempt in range(max_retries):
    try:
        response = await client.chat.completions.create(...)
        return response
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
        else:
            return None, error_msg
```

**核心洞察**：LLM API 是不可靠的 — 会超时、限流、返回空内容。重试不是可选的，是必须的。但重试要有上限，否则会无限阻塞。

### 3.4 客户端单例 — 避免重复初始化

```python
class ModelClient:
    _instance: AsyncOpenAI | None = None
    _model_id: str | None = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        if cls._instance is None:
            cls._instance = AsyncOpenAI(api_key=..., base_url=...)
        return cls._instance
```

**核心洞察**：每次创建 OpenAI 客户端都会建立连接池，重复创建浪费资源。单例模式确保全局共享一个连接池。

---

## 四、Layer 3：输出解析 — 从非确定性中提取确定性

这是 AI 工程中最容易被忽视、但最关键的层。LLM 的输出是不可控的，你必须从混乱中提取你需要的数据。

### 4.1 问题：LLM 输出的不确定性

你要求 LLM 输出 JSON，但它可能返回：

```
✅ 理想情况：[{"title": "测试登录", "steps": "..."}]

❌ 带 实际可能：
- 包含思考过程：<thinking>让我分析...</thinking>[{"title":...}]
- 包含 markdown：```json\n[{"title":...}]\n```
- 包含解释文字：以下是测试用例：[{"title":...}] 以上是全部用例
- 包含嵌套：[[{"title":...}]]
- JSON 格式错误：缺少逗号、多余逗号、引号不匹配
```

### 4.2 解决方案：多层提取策略

```
原始输出
  │
  ├─ Step 1: 去除思考标签（<thinking>、<thought>、<tool_call>）
  │
  ├─ Step 2: 提取 markdown 代码块（```json ... ```）
  │
  ├─ Step 3: 定位 JSON 起始位置（第一个 [ 或 {）
  │
  ├─ Step 4: 尝试 json.loads()
  │     │
  │     ├─ 成功 → 返回
  │     └─ 失败 → Step 5: 清理后重试
  │
  └─ Step 5: 截取 { ... } 或 [ ... ] 范围，再次解析
```

```python
def extract_json_from_content(content: str) -> str | None:
    # Step 1: 去除思考标签
    for tag in ["</thought>", "</thinking>", ""]:
        match = re.search(rf'{tag}\s*(.*?)$', content, re.DOTALL)
        if match:
            content = match.group(1)

    # Step 2: 提取 markdown 代码块
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return match.group(1)

    # Step 3: 定位 JSON 起始
    json_start = re.search(r'[\[{]', content)
    if json_start:
        content = content[json_start.start():]

    return content.strip()
```

**核心洞察**：
- 永远不要假设 LLM 会严格按格式输出 — 它不会
- 解析层是 AI 工程的"脏活"，但没它系统就不可靠
- 好的解析器是防御性的：先尝试最严格的方式，逐步降级到最宽松的方式

### 4.3 流式输出中的标签检测

流式场景下，`<thinking>` 标签可能跨 chunk 分割：

```
chunk 1: "让我分析这<thi"
chunk 2: "nking>个接口..."
```

解决方案 — 缓冲区 + 状态机：

```python
in_thinking = False
thinking_buffer = ""  # 缓存可能跨 chunk 的标签

while process_text:
    if not in_thinking:
        idx = process_text.find("<thinking>")
        if idx >= 0:
            in_thinking = True
            process_text = process_text[idx + len("<thinking>"):]
        else:
            # 检查末尾是否有不完整标签
            partial = check_partial_tag(process_text, "<thinking>")
            if partial:
                safe_part = process_text[:-len(partial)]
                thinking_buffer = partial
                break
    else:
        idx = process_text.find("</thinking>")
        if idx >= 0:
            in_thinking = False
            process_text = process_text[idx + len("</thinking>"):]
```

**核心洞察**：流式处理不是简单的"收到就输出"，而是需要状态机来跟踪上下文。标签可能被分割到多个 chunk 中，必须用缓冲区拼接后再判断。

---

## 五、Layer 4：Prompt 工程 — 提示词即代码

### 5.1 Prompt 模板管理

```
prompts/
├── testcase_generate.txt      # 系统提示词
├── test_directions.txt        # 测试方向映射
├── generate_testcase.txt      # 用例生成
├── get_dependency.txt         # 依赖分析
├── fill_test_data.txt         # 数据填充
├── execute_api.txt            # 接口执行
└── validate_testcase.txt      # 结果校验
```

```python
# 模式：文件存储 + lru_cache + 函数封装
@lru_cache
def load_prompt(filename: str) -> str:
    filepath = os.path.join(PROMPTS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

def get_system_prompt() -> str:
    return load_prompt("testcase_generate.txt")
```

**核心洞察**：
- Prompt 不是字符串常量，是独立的文本文件 — 需要独立版本管理、独立迭代
- `lru_cache` 避免每次请求都读文件
- 函数封装（`get_system_prompt()`）让调用方不需要知道文件名

### 5.2 变量替换 — 模板引擎

Prompt 中的 `{{变量名}}` 在运行时替换为实际值：

```python
prompt = system_prompt.replace("{{case_id}}", str(case_id))
prompt = prompt.replace("{{api_name}}", api_name)
prompt = prompt.replace("{{precondition}}", precondition)
prompt = prompt.replace("{{execution_results}}", json.dumps(results))
```

**核心洞察**：这本质上是一个极简模板引擎。复杂场景可以用 Jinja2，但简单的 `str.replace` 链足够应对大多数情况。关键原则：**Prompt 是模板，不是硬编码的字符串**。

### 5.3 Prompt 设计的四个关键要素

从项目的 prompt 文件中提炼出的通用结构：

```
1. 角色定义    → "你是一位专业的软件测试工程师"
2. 输出约束    → "只输出JSON数组，不要输出任何其他内容"
3. 规则详述    → 具体的生成规则、边界条件、禁止事项
4. 格式示例    → Few-shot 示例，明确输出格式
```

**最重要的约束 — 输出格式控制**：

```text
## 输出要求
1. 只输出JSON数组，不要输出任何其他内容
2. 禁止重复输出，每个用例只出现一次
3. 禁止嵌套JSON，数组内不能包含另一个数组
4. 禁止在JSON前后添加任何文字
5. 输出完 `]` 后立即停止
```

**核心洞察**：LLM 天然倾向于"多说"（加解释、加总结、加 markdown 包裹）。Prompt 中必须用强烈的否定约束来对抗这种倾向。这是 Prompt 工程的核心技巧之一。

### 5.4 多步 Prompt 链 — 任务分解

接口测试的完整流程被分解为 5 个独立的 Prompt：

```
generate_testcase  →  get_dependency  →  fill_test_data  →  execute_api  →  validate_testcase
   生成用例            分析依赖          填充数据          执行接口         校验结果
```

每一步的输出是下一步的输入：

```
用例文本 → 依赖 JSON → 填充后的 run_list → 执行结果 → 校验结论
```

**核心洞察**：
- 不要试图用一个 Prompt 完成复杂任务 — LLM 的单次推理能力有限
- 任务分解的原则：每一步都有明确的输入格式和输出格式
- 链式调用的风险：错误会累积传播。每一步都需要输出解析和错误处理

---

## 六、Layer 5：业务流程编排

### 6.1 引擎模式 — 业务逻辑的核心抽象

```
┌─────────────────────────────────────────────┐
│                  Engine                      Engine                  │
│                                              │
│  输入 → [Prompt构建] → [LLM调用] → [解析] → 输出  │
│                                              │
│  依赖：ModelClient / KBClient / DBService    │
└─────────────────────────────────────────────┘
```

引擎的职责：
1. 组装 Prompt（从模板 + 变量）
2. 调用 LLM（同步/流式）
3. 解析输出（JSON 提取）
4. 返回结构化结果

```python
class InferenceEngine:
    async def infer_single(self, messages, extract_json=True):
        full_messages = [{"role": "system", "content": get_system_prompt()}]
        full_messages.extend(messages)
        result, error = await ModelClient.infer(full_messages, extract_json)
        return result, error
```

**核心洞察**：Engine 是业务逻辑的唯一入口。它把"调 LLM"这个底层操作封装成"推理"这个业务操作。调用方不需要知道用的是哪个模型、怎么调的、怎么解析的。

### 6.2 事件流模式 — 流式进度反馈

复杂任务需要实时反馈进度，项目使用统一的事件格式：

```python
# 统一事件格式
{"type": "step",    "data": {"message": "正在分析依赖..."}}
{"type": "chunk",   "data": {"content": "AI输出的文本片段"}}
{"type": "result",  "data": {"dependency": {...}}}
{"type": "error",   "data": {"message": "解析失败"}}
{"type": "complete","data": {"message": "生成完成"}}
```

```python
async def get_api_dependency(self, ...) -> AsyncGenerator:
    yield self._create_event("step", {"message": "正在加载..."})

    async for event in kb_client.chat_stream(...):
        if event.get("type") == "chunk":
            yield self._create_event("chunk", {"content": content})

    yield self._create_event("result", {"dependency": dependency_info})
```

**核心洞察**：
- 事件流 = AsyncGenerator + 统一事件格式
- 调用方可以按 type 过滤事件：只显示 step 给用户，只收集 chunk 做解析
- 这个模式和前端的状态管理（Redux/Vuex 的 action → mutation）异曲同工

### 6.3 Agent 模式 — LLM 驱动的自主决策

项目中的 `demo.py` 展示了 Claude Agent SDK 的模式：

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import ToolUseBlock

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep"],  # 声明可用工具
)

async for message in query(prompt=prompt, options=options):
    for block in message.content:
        if isinstance(block, ToolUseBlock):
            # LLM 自主决定调用哪个工具、传什么参数
            print(f"[调用工具: {block.name}]")
```

**Agent vs Pipeline 的区别**：

```
Pipeline（本项目主流模式）：
  人工定义步骤顺序 → 每步调 LLM → 解析输出 → 下一步
  优点：可控、可预测
  缺点：无法处理意外情况

Agent（demo.py 展示的模式）：
  LLM 自主决定 → 调工具 → 观察结果 → 再决策 → 循环
  优点：灵活、能处理意外
  缺点：不可预测、成本高
```

**核心洞察**：当前项目 95% 用 Pipeline，5% 用 Agent。选择标准是：步骤是否可预定义。如果可以，用 Pipeline；如果需要根据中间结果动态决策，用 Agent。

### 6.4 MCP 工具注册 — 标准化的工具暴露

MCP（Model Context Protocol）是让 AI 调用工具的标准协议：

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("api-testing")

@server.tool()
async def generate_testcases(kb_id: str, query: str = "...") -> str:
    """生成接口测试用例。参数：kb_id（必填）、query（可选）"""
    # ... 业务逻辑 ...
    return json.dumps(response)

@server.tool()
async def execute_testcase(case_id: str, run_list: list, ...) -> str:
    """执行测试用例。参数：case_id（必填）、run_list（必填）"""
    # ... 业务逻辑 ...
    return json.dumps(response)
```

**MCP 的三层含义**：

```
1. 工具定义层：@server.tool() + 类型注解 + docstring
   → 自动生成 JSON Schema，AI 知道有哪些工具、参数是什么

2. 通信层：stdio 传输
   → AI 通过标准输入/输出与工具服务通信

3. 调用层：AI 自主选择调用哪个工具
   → Function Calling 的标准化版本
```

**核心洞察**：MCP 是 Function Calling 的"接口规范"。Function Calling 是每个模型厂商自己定义的工具调用格式，MCP 统一了它们。写一个 MCP Server，任何支持 MCP 的 AI 客户端都能调用你的工具。

---

## 七、跨层模式

### 7.1 分层调用链 — 从 HTTP 请求到 LLM 调用

```
HTTP 请求
  │
  ├─ Router（路由层）：参数校验、格式转换
  │    ↓
  ├─ Engine（引擎层）：Prompt 组装、流程编排
  │    ↓
  ├─ ModelClient / KBClient（调用层）：LLM 调用、流式处理
  │    ↓
  └─ OpenAI API / WeKnora API（外部服务）
```

每一层只做一件事：
- Router 不调 LLM，只做参数校验和格式转换
- Engine 不直接调 HTTP，只调 ModelClient
- ModelClient 不做业务逻辑，只做 API 调用

### 7.2 Django 后端调用微服务 — 跨进程的 LLM 调用

```
Django View
  │
  ├─ AITestCaseClient（HTTP 客户端）
  │    ↓ HTTP POST
  ├─ ai-generator-service（FastAPI 微服务）
  │    ↓
  ├─ InferenceEngine
  │    ↓
  └─ ModelClient → OpenAI API
```

**同步 Django 调异步微服务的桥接模式**：

```python
class AITestCaseClientSync:
    """同步包装器 — 让 Django 同步视图能调异步微服务"""

    def generate_cases(self, *args, **kwargs):
        return self._loop_manager.run_async(
            self._async_client.generate_cases(*args, **kwargs)
        )

class AsyncEventLoopManager:
    """在新线程中创建新事件循环，运行异步协程"""
    def run_async(self, coro, timeout=None):
        def run_in_new_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

        future = self._executor.submit(run_in_new_loop)
        return future.result(timeout=timeout)
```

**核心洞察**：Django 是同步框架，FastAPI 是异步框架。桥接的关键是"新线程 + 新事件循环" — 不能在已有事件循环中嵌套另一个事件循环。

### 7.3 错误处理 — 每一层都有防御

```
LLM API 调用失败 → 重试 3 次 → 返回 (None, error_msg)
     ↓
Engine 解析失败 → 返回 (None, "解析失败")
     ↓
Router 收到 error → 返回 HTTP 200 + {success: false, error: "..."}
     ↓
前端收到 → 显示错误提示
```

**核心洞察**：AI 应用的错误不是异常，是常态。LLM 会失败、会返回格式错误、会超时。每一层都要处理错误，而不是抛异常让上层处理。返回 `(data, error)` 元组比抛异常更适合 AI 场景。

---

## 八、核心数据流图

### 8.1 AI 测试用例生成（ai-generator-service）

```
用户输入（模块 + 功能点）
  │
  ├─ 构建基础文本："模块：XX，功能点：YY"
  │
  ├─ 按测试方向并行（asyncio.gather）
  │   ├─ 方向1：功能点测试 → Prompt → LLM → JSON → 用例列表
  │   ├─ 方向2：业务逻辑测试 → Prompt → LLM → JSON → 用例列表
  │   └─ 方向3：其他测试 → Prompt → LLM → JSON → 用例列表
  │
  └─ 合并所有用例 → 标准化格式 → 返回
```

### 8.2 接口测试执行（api-testing-service）

```
测试用例
  │
  ├─ Step 1: 生成测试用例（generate_testcase）
  │   RAG 检索接口文档 → LLM 生成用例 JSON
  │
  ├─ Step 2: 分析依赖关系（get_dependency）
  │   用例信息 → LLM → run_list（执行顺序 + extract_vars）
  │
  ├─ Step 3: 填充测试数据（fill_test_data）
  │   run_list + 测试数据 → LLM → 填充后的 run_list
  │
  ├─ Step 4: 执行接口（execute_testcase）
  │   按 run_list 顺序执行 → 提取变量 → 替换占位符 → 下一个接口
  │
  └─ Step 5: 校验结果（validate_testcase）
      执行结果 → LLM → passed/fail + 原因分析
```

### 8.3 MCP 工具调用链

```
AI 客户端（如 Claude Desktop）
  │ stdio
  ├─ MCP Server（api-testing-service）
  │   ├─ Tool: get_api_flow → ApiTestEngine.get_flow()
  │   ├─ Tool: generate_testcases → ApiTestEngine.generate_testcase()
  │   ├─ Tool: get_api_dependency → ApiTestEngine.get_api_dependency()
  │   ├─ Tool: fill_testdata → ApiTestEngine.fill_test_data()
  │   ├─ Tool: execute_testcase → TestExecutionEngine.execute_testcase()
  │   └─ Tool: validate_testcase → TestExecutionEngine.validate_testcase()
  │       │
  │       └─ 内部调用链：
  │           KBClient（RAG检索）→ LLMService（推理）→ Executor（HTTP执行）
```

---

## 九、设计原则总结

### 9.1 七条核心原则

1. **Prompt 是模板，不是字符串** — 独立文件管理，变量替换，版本控制
2. **输出解析是必须的，不是可选的** — LLM 永远不会严格按格式输出
3. **流式 = AsyncGenerator + 统一事件格式** — 不是简单的 yield 字符串
4. **错误是常态，不是异常** — 每层返回 (data, error)，不抛异常
5. **配置外置，不硬编码** — 模型地址、参数、密钥全部从环境变量读取
6. **单例共享，不重复创建** — 客户端、配置、模型 ID 全局共享
7. **分层隔离，不跨层调用** — Router → Engine → Client，每层只依赖下一层

### 9.2 选择决策树

```
需要调 LLM？
  ├─ 直接调模型 → ModelClient（OpenAI SDK）
  └─ 通过 RAG → KBClient（HTTP + SSE）

需要实时反馈？
  ├─ 是 → 流式调用（SSE / AsyncGenerator）
  └─ 否 → 同步调用

任务步骤可预定义？
  ├─ 是 → Pipeline 模式（多步 Prompt 链）
  └─ 否 → Agent 模式（Function Calling / MCP）

需要暴露给外部 AI 调用？
  ├─ 是 → MCP Server（@server.tool()）
  └─ 否 → 普通 API（FastAPI router）

输出需要结构化？
  ├─ 是 → Prompt 约束 + JSON 解析（当前项目方式）
  └─ 更好 → Function Calling / Structured Output（模型原生支持）
```

### 9.3 当前项目 vs 更优方案

| 维度 | 当前项目做法 | 更优方案 |
|------|-------------|---------|
| 结构化输出 | Prompt 约束 + JSON 解析 | Function Calling / Structured Output |
| 工具调用 | MCP Server（仅暴露） | MCP Server + Agent 循环调用 |
| Prompt 管理 | 文件 + str.replace | Jinja2 模板引擎 |
| 错误重试 | 固定间隔重试 | 指数退避 + jitter |
| 会话状态 | 内存 TaskStore | Redis / 数据库 |
| 多模型适配 | 仅 OpenAI 兼容格式 | LiteLLM / 多 Provider 抽象 |

**核心洞察**：当前项目用"Prompt 约束 + JSON 解析"代替 Function Calling，是因为兼容性考虑（国产模型不一定支持 Function Calling）。但随着模型能力提升，Function Calling / Structured Output 是更可靠的方向。理解当前做法的原理，才能理解为什么要升级、怎么升级。

---

## 十、一张图总结

```
                        ┌─────────────────┐
                        │   AI 客户端      │
                        │ (Claude / GPT)   │
                        └────────┬────────────────┬┘
                         │ stdio          │ HTTP
                         ↓                ↓
                    ┌─────────┐    ┌──────────────┐
                    │ MCP     │    │ FastAPI       │
                    │ Server  │    │ Router        │
                    └────┬────┘    └──────┬───────┘
                         │                │
                         └───────┬────────┘
                                 ↓
                          ┌─────────────┐
                          │   Engine     │  ← 流程编排
                          │  (业务逻辑)  │
                          └──┬──────┬───┘
                             │      │
                    ┌────────↓┐  ┌──↓──────────┐
                    │ KBClient │  │ ModelClient  │  ← LLM 调用
                    │ (RAG)    │  │ (Direct)     │
                    └────┬────┘  └──┬───────────┘
                         │          │
                    ┌────↓────┐  ┌──↓───────────┐
                    │ WeKnora │  │ OpenAI API    │  ← 外部服务
                    │ (RAG服务)│  │ (兼容端点)    │
                    └─────────┘  └──────────────┘

    横切关注点：
    ┌──────────────────────────────────────────┐
    │  Prompt 模板 │ JSON 解析 │ 配置 │ 日志    │
    └──────────────────────────────────────────┘
```

理解了这五层、七条原则、一个决策树，你就掌握了构建任何 AI 工具的底层逻辑。
