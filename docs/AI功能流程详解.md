# AI功能流程详解

本文档详细描述测试用例管理系统中两个核心AI功能的完整流程和技术实现。

---

## 目录

1. [AI生成测试用例](#1-ai生成测试用例)
   - [架构设计](#架构设计)
   - [执行流程](#执行流程)
   - [关键技术](#关键技术)
   - [文件索引](#文件索引)
2. [AI驱动接口自动化](#2-ai驱动接口自动化)
   - [架构设计](#架构设计-1)
   - [执行流程](#执行流程-1)
   - [关键技术](#关键技术-1)
   - [文件索引](#文件索引-1)
3. [两流程对比](#3-两流程对比)

---

## 1. AI生成测试用例

### 功能概述

从需求文档中自动提取功能点，并生成符合规范的测试用例，支持流式输出、质量验证和自动去重。

### 架构设计

```
┌─────────────────┐     SSE      ┌──────────────────┐     HTTP     ┌─────────────────────┐
│  Vue前端        │ ─────────→  │  Django后端      │ ─────────→  │  ai-generator-service│
│ AIGenerateDialog│             │  ai_views.py     │             │  (FastAPI微服务)     │
└─────────────────┘             └──────────────────┘             └─────────────────────┘
       │                                │                                  │
       │                                │                                  ↓
       │                                │                         ┌──────────────────┐
       │                                └───────────────────────→│  LLM API         │
       │                                                         │  (DeepSeek等)    │
       ↓                                                         └──────────────────┘
┌─────────────────┐
│  WeKnora        │  ← RAG知识库服务（向量检索+智能推理）
│  知识库服务     │
└─────────────────┘
```

### 执行流程

#### 阶段1：前端准备（Step 1）

用户在弹窗中完成以下选择：

| 选择项 | 说明 | 数据来源 |
|-------|------|---------|
| 项目知识库 | 当前项目关联的知识库 | `getProjectKnowledgeBase(projectId)` |
| 需求文档 | 从知识库中选择要分析的文档 | `listKnowledge(kbId)` |
| 目标版本 | 生成的用例归属版本 | 项目版本列表 |

同时调用 `GET /api/testcase/ai/status` 检查AI服务健康状态。

#### 阶段2：发起生成请求（Step 2）

点击"开始生成"，前端发起SSE流式请求：

```javascript
// 前端调用
aiApi.generateTestCasesStream({
  knowledge_base_ids: [projectKnowledgeBase.id],
  knowledge_ids: selectedFiles.value,
  version_id: targetVersion.value
})

// SSE事件类型
- started: {task_id}         // 用于取消操作
- progress: {step, status, message, data}  // 步骤进度
- request: {index, status, cases, error}   // 单个请求结果
- complete: {created_count, error_count}   // 最终统计
```

#### 阶段3：后端处理核心流程

**步骤A：需求提取（extract）**

```
目标：从需求文档中提取功能点列表

流程：
1. 创建WeKnora会话
   POST /api/session/create → {id: session_id}

2. 调用智能推理Agent
   使用提示词：
   "请分析文档内容，提取所有功能模块和功能点..."
   
3. Agent执行RAG检索
   - 向量检索相关文档片段
   - 推理生成结构化功能点

4. 解析JSON响应
   返回格式：
   [{"模块": "用户管理", "功能点": "用户注册"}, ...]

5. 销毁会话（避免堆积）
   DELETE /api/session/{session_id}
```

**步骤B：关联内容检索（retrieve）**

```
目标：为每个功能点找到原文中的详细描述

优化策略：
- 分批处理：每批10个功能点
- 并行执行：最多3个并发线程
- 独立会话：每批创建独立会话，避免干扰

流程：
for batch in batches:
    1. 创建会话
    2. 构建批量查询：
       "请根据需求文档原文，找出以下功能点对应的相关内容。
        功能点列表：
        1. 用户注册
        2. 用户登录
        ..."
    3. Agent返回：
       [{"index": 1, "content": "原文引用..."}, ...]
    4. 组装结果：
       {module, func_point, related_detail, related_chunks}
    5. 销毁会话
```

**步骤C：模块预创建（module）**

```
目标：提前创建测试模块，减少后续数据库查询

实现：
module_names = set(item['module'] for item in requirements_with_details)
module_map = {}
for name in module_names:
    module_map[name] = TestModule.objects.get_or_create(
        version_id=version_id,
        name=name,
        defaults={'sort_order': 0}
    )[0]
```

**步骤D：AI生成测试用例（generate）**

```
目标：为每个功能点生成具体测试用例

并行策略：
- ThreadPoolExecutor，默认5线程
- 每个功能点独立处理

单功能点处理流程：

for attempt in [1, 2, 3]:  # 重试机制
    1. 调用AI微服务
       POST /api/v1/testcase/generate
       {
         module: "用户管理",
         func_point: "用户注册",
         related_detail: "用户可以通过手机号...",
         test_directions: ["功能点测试", "业务逻辑测试"],
         temperature: 1.0 - attempt * 0.1  # 重试时降低温度
       }

    2. AI返回测试用例
       [{
         title: "正常注册-手机号",
         steps: "1. 输入手机号\n2. 输入密码...",
         expected_result: "注册成功，跳转首页",
         priority: "高",
         precondition: "手机号未被注册"
       }, ...]

    3. 字段完整性验证
       必需字段：title, steps, expected_result
       - 缺失字段 → 记录负样本 → 重试

    4. 验证成功 → 记录正样本 → 退出重试

5. 向量去重（threshold=0.85）
   - 计算每个用例的embedding向量
   - 余弦相似度 > 0.85 视为重复
   - 过滤重复项

6. 保存到数据库
   TestCase.objects.create(
     title=title,
     steps=steps_text,
     expected_result=expected_result_text,
     priority=priority,
     module=module_obj,
     version_id=version_id,
     generation_source="ai_generated",
     review_status="pending"
   )
```

**步骤E：返回结果**

```json
{
  "success": true,
  "created_count": 45,
  "error_count": 3,
  "total_requests": 48,
  "total_elapsed": 125.6,
  "cases": [
    {"id": 1, "title": "正常注册-手机号", "module": "用户管理", "priority": "高"},
    ...
  ]
}
```

### 关键技术

#### 1. KTO数据集收集

用于收集AI生成样本，支持后续模型微调：

```python
class KTODatasetWriter:
    SYSTEM_PROMPT = "你的任务是帮我生成功能测试用例"
    
    def _build_kto_record(self, user_content, assistant_content, label):
        return {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content}
            ],
            "label": label  # True=正样本，False=负样本
        }

# 正样本：有效用例 → label=True
# 负样本：格式错误/字段缺失 → label=False
```

存储位置：`kto_dataset/kto_YYYYMMDD.jsonl`

#### 2. 重试策略

```python
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# 温度递减策略
temperature = 1.0  # 第一次
temperature = 0.9  # 第二次
temperature = 0.7  # 第三次

# 降低温度 → 输出更稳定/确定性更高
```

#### 3. 向量去重

```python
class OpenAIEmbeddingClient:
    def find_duplicates(self, cases, threshold=0.85):
        texts = [f"{case['title']} {case['steps'][:200]}" for case in cases]
        embeddings = await self.get_embeddings(texts)
        
        duplicates = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                if similarity >= threshold:
                    duplicates.append(j)
        return duplicates
```

#### 4. 流式进度推送

```python
# SSE事件格式
def send_event(event_type, data):
    return f": keepalive\n\nevent: {event_type}\ndata: {json.dumps(data)}\n\n"

# 事件类型
- started: 任务开始，返回task_id
- progress: 步骤进度（extract/retrieve/generate/save）
- request: 单个AI请求结果
- complete: 最终统计
- error: 错误信息
```

### 文件索引

| 文件 | 路径 | 说明 |
|-----|------|------|
| 前端弹窗 | `vue3-frontend/src/views/testcase/components/AIGenerateDialog.vue` | UI界面、SSE处理 |
| 后端视图 | `Testbackend/apps/testcase/views/ai_views.py` | SSE流式接口、流程编排 |
| 生成服务 | `Testbackend/apps/testcase/services/ai_generation_service.py` | KTO写入、验证器 |
| AI客户端 | `Testbackend/apps/testcase/clients/ai_client.py` | HTTP通信、向量去重 |
| AI微服务 | `ai-generator-service/app/main.py` | FastAPI推理服务 |
| 推理接口 | `ai-generator-service/app/routers/inference.py` | 单次/批量/流式推理 |
| 提示词 | `ai-generator-service/app/prompts/testcase_generate.txt` | 生成用例的提示词模板 |

---

## 2. AI驱动接口自动化

### 功能概述

从接口文档中生成测试用例，自动分析接口依赖关系，动态填充参数，执行真实的HTTP请求，并自动校验结果。

### 架构设计

```
┌─────────────────┐     SSE      ┌──────────────────────┐
│  Vue前端        │ ─────────→  │  api-testing-service │
│  接口测试页面   │             │  (FastAPI独立服务)   │
└─────────────────┘             └──────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ↓                    ↓                    ↓
           ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
           │ WeKnora      │    │ LLM服务      │    │ 目标API      │
           │ (接口文档)   │    │ (参数分析)   │    │ (实际执行)   │
           └──────────────┘    └──────────────┘    └──────────────┘
```

### 执行流程

#### 阶段1：生成接口测试用例

```
POST /api/v1/testcase/generate

提示词（generate_testcase.txt）：
你是接口测试用例生成专家。根据提供的API接口文档，设计完整的接口测试用例。

输出格式：
[
  {
    "id": "1",
    "apiname": "用户注册接口",
    "precondition": "无",
    "testpoint": "正常注册-手机号格式正确",
    "expectation": "返回201，用户创建成功，data包含id和username"
  },
  {
    "id": "2",
    "apiname": "用户登录接口",
    "precondition": "已注册用户",
    "testpoint": "正常登录",
    "expectation": "返回200，data包含token"
  }
]
```

#### 阶段2：分析接口依赖

```
POST /api/v1/dependency

提示词（get_dependency.txt）：
请根据测试用例的需求帮我梳理接口文档，并且判断执行这个接口测试用例，
需要依赖的接口和执行顺序。

输入：
- case_id: 1
- api_name: "用户登录接口"
- precondition: "已注册用户"
- testpoint: "正常登录"

输出：
{
  "case_id": 1,
  "run_list": [
    {
      "run_num": 1,
      "api_name": "用户注册接口",
      "api_url": "/api/users/register/",
      "method": "POST",
      "request_body": {
        "username": "test_20260529_123456_a1b2",
        "password": "Test@123456",
        "email": "test@example.com"
      },
      "expected_status": 201,
      "description": "注册用户A"
    },
    {
      "run_num": 2,
      "api_name": "用户登录接口",
      "api_url": "/api/users/login/",
      "method": "POST",
      "request_body": {
        "username": "test_20260529_123456_a1b2",
        "password": "Test@123456"
      },
      "expected_status": 200,
      "description": "主接口测试"
    }
  ]
}
```

**账号标准化规则**

```
用户名格式：test_YYYYMMDD_HHMMSS_xxxx（如 test_20260529_123456_a1b2）

规则：
1. 注册接口必须使用时间戳格式的唯一用户名
2. 同一用户角色的注册和登录使用相同用户名
3. 不同用户角色使用不同用户名
4. 禁止使用固定账号名（如testuser、admin）
```

#### 阶段3：填充测试数据（可选）

```
POST /api/v1/testdata/fill

提示词（fill_test_data.txt）：
你是一位 API 测试参数分析助手。根据测试用例信息、历史执行记录和当前接口信息，
分析并填充当前接口执行所需的参数。

输入：
- dependency: 上一步的依赖关系
- test_data: 真实测试数据（配置、特定账号等）
- base_url: 目标API地址

输出：填充后的完整测试配置
```

#### 阶段4：执行测试用例

```
POST /api/v1/testcase/execute

核心执行循环：

initialize():
  - 重置用户名映射 _username_mapping = {}
  - 创建 ApiTestExecutor(base_url)

for api_info in run_list:
  
  if first_api:
    # 第一个接口直接执行
    api_info["request_body"] = replace_username(api_info["request_body"], is_register=True)
    execute_api(api_info)
    
  else:
    # 后续接口需要参数填充
    
    # A. AI参数填充
    filled_info = await _fill_params_with_ai(
      execution_history=executor.get_history(),
      current_api_info=api_info
    )
    api_info.update(filled_info)
    
    # B. 后处理占位符替换
    # 1. 从 extract_vars 提取变量
    for var_name, var_path in api_info.get("extract_vars", {}).items():
      value = extract_value_by_path(history, var_path)
      extracted_values[var_name] = value
    
    # 2. 智能推断未填充的占位符
    for placeholder in unresolved_placeholders:
      inferred_path = infer_extract_path(placeholder, history)
      value = extract_value_by_path(history, inferred_path)
      extracted_values[placeholder] = value
    
    # 3. 替换URL和Body中的占位符
    api_url = api_url.replace("{{user_id}}", value)
    request_body["field"] = request_body["field"].replace("{{token}}", value)
    
    # C. 自动添加认证头
    if "token" in extracted_values:
      headers["Authorization"] = f"Bearer {token_value}"
    
    # D. 动态用户名替换
    is_register = "注册" in api_name
    api_info["request_body"] = replace_username(api_info["request_body"], is_register)
    
    # E. 执行HTTP请求
    execute_api(api_info)
    
    # F. 判断结果
    if success:
      continue
    elif is_skippable_error(error):  # 如"用户已存在"
      continue
    else:
      break  # 停止后续执行

# 清理测试账号
cleanup_test_users(all_generated_usernames)
```

**智能参数推断**

```python
def infer_extract_path(placeholder_name, history):
    """
    根据占位符名称推断提取路径
    
    规则：
    - user_a_id → 第一个注册接口的 response.body.data.id
    - user_b_id → 第二个注册接口的 response.body.data.id  
    - token → 登录接口的 response.body.data.token
    - user_id → 最后一个注册接口的 response.body.data.id
    """
    
    if "token" in placeholder_name.lower():
        # 从登录接口提取
        for record in history:
            if "登录" in record["api_name"]:
                return f"$.run_list[{record['run_num']-1}].response.body.data.token"
    
    elif "id" in placeholder_name.lower():
        # 从注册接口提取
        if "user_a" in placeholder_name.lower():
            return "$.run_list[0].response.body.data.id"
        elif "user_b" in placeholder_name.lower():
            return "$.run_list[1].response.body.data.id"
```

**执行历史数据结构**

```json
[
  {
    "run_num": 1,
    "api_name": "用户注册接口",
    "request": {
      "method": "POST",
      "url": "http://localhost:8000/api/users/register/",
      "body": {"username": "test_xxx", "password": "Test@123"}
    },
    "response": {
      "status_code": 201,
      "body": {
        "code": 201,
        "data": {"id": 6, "username": "test_xxx"}
      }
    },
    "success": true
  },
  {
    "run_num": 2,
    "api_name": "用户登录接口",
    "response": {
      "status_code": 200,
      "body": {
        "data": {"token": "eyJhbGci..."}
      }
    },
    "success": true
  }
]
```

#### 阶段5：校验测试结果

```
POST /api/v1/testcase/validate

提示词（validate_testcase.txt）：
根据执行结果，判断测试是否通过，分析问题原因。

输出：
{
  "pass": true/false,
  "issues": [
    {
      "api": "用户登录接口",
      "issue": "返回401，密码格式不符合要求",
      "suggestion": "密码需要包含大小写字母和数字"
    }
  ],
  "summary": "测试通过/未通过，存在X个问题"
}
```

### 关键技术

#### 1. 动态账号管理

```python
class TestExecutionEngine:
    _username_mapping: Dict[str, str] = {}
    _all_generated_usernames: List[str] = []
    
    def generate_unique_username(original_username: str) -> str:
        """
        规则：
        1. 已有映射 → 返回映射值（保持一致性）
        2. 时间戳格式 → 生成新账号（区分不同用户）
        3. 普通名称 → 生成时间戳格式账号
        """
        if original_username in self._username_mapping:
            return self._username_mapping[original_username]
        
        new_username = f"test_{timestamp}_{random_suffix}"
        self._username_mapping[original_username] = new_username
        self._all_generated_usernames.append(new_username)
        return new_username
    
    def replace_username_in_data(data, is_register_api: bool):
        """
        注册接口：生成新用户名
        其他接口：使用已有映射
        """
```

#### 2. 状态码模糊匹配

```python
def check_success(expected_status, actual_status):
    """
    支持多种格式：
    - 单个状态码：200, 404
    - 通配符：4XX（匹配400-499）
    - 范围：400-499
    
    异常场景模糊匹配：
    expected=401, actual=403 → success（都是4xx）
    expected=200, actual=403 → fail
    """
    
    if isinstance(expected_status, int):
        if 400 <= expected_status < 600:
            # 异常场景：同类型都算成功
            base = (expected_status // 100) * 100
            return base <= actual_status < base + 100
        else:
            return actual_status == expected_status
    
    elif expected_status.upper().endswith("XX"):
        prefix = int(expected_status[0])
        base = prefix * 100
        return base <= actual_status < base + 100
```

#### 3. JSONPath提取

```python
def extract_value_by_path(history, path):
    """
    支持的路径格式：
    - $.run_list[0].response.body.data.id
    - $.run_list[1].response.body.results[0].id
    - $.run_list[*].response.body.data.token（搜索所有）
    """
    
    # 移除 $. 前缀
    path = path[2:] if path.startswith("$.") else path
    
    # 解析路径部分
    parts = path.split(".")  # ["run_list[0]", "response", "body", "data", "id"]
    
    # 导航数据结构
    current = history
    for part in parts:
        if "[" in part:
            key, idx = parse_array_index(part)
            current = current[key][idx]
        else:
            current = current[part]
    
    return current
```

#### 4. 测试账号清理

```python
async def cleanup_test_user(base_url, username):
    """
    只清理时间戳格式的测试账号
    
    正则验证：test_\d{8}_\d{6}_[a-z0-9]{4}
    
    调用清理接口：
    DELETE /api/users/cleanup-test-user/?username={username}
    """
    
    pattern = r'test_\d{8}_\d{6}_[a-z0-9]{4}$'
    if not re.match(pattern, username):
        return False
    
    response = await client.delete(f"{base_url}/api/users/cleanup-test-user/?username={username}")
    return response.json().get("success")
```

### 文件索引

| 文件 | 路径 | 说明 |
|-----|------|------|
| 业务流引擎 | `api-testing-service/app/core/engine.py` | 生成用例、依赖分析、数据填充 |
| 执行引擎 | `api-testing-service/app/execute/engine.py` | 执行测试、参数填充、账号管理 |
| 执行器 | `api-testing-service/app/execute/executor.py` | HTTP请求发送、结果解析 |
| API路由 | `api-testing-service/app/routers/rpc.py` | RESTful接口定义 |
| 提示词-生成 | `api-testing-service/app/prompts/generate_testcase.txt` | 生成接口测试用例 |
| 提示词-依赖 | `api-testing-service/app/prompts/get_dependency.txt` | 分析接口依赖关系 |
| 提示词-执行 | `api-testing-service/app/prompts/execute_api.txt` | 填充执行参数 |
| 提示词-校验 | `api-testing-service/app/prompts/validate_testcase.txt` | 校验测试结果 |

---

## 3. 两流程对比

### 功能对比

| 维度 | AI生成测试用例 | AI驱动接口自动化 |
|-----|--------------|----------------|
| **核心目标** | 生成测试用例文档 | 自动执行接口测试 |
| **输入源** | 需求文档（业务需求） | 接口文档（技术文档） |
| **输出物** | TestCase数据库记录 | HTTP请求/响应结果 |
| **AI角色** | 内容生成者 | 参数分析者+执行决策者 |
| **知识库作用** | RAG检索需求内容 | RAG检索接口定义 |
| **执行方式** | 无实际执行 | 真实HTTP调用 |
| **数据依赖** | 无状态 | 有状态（执行历史） |
| **重试机制** | 生成质量重试（3次） | 执行失败可跳过/停止 |
| **环境管理** | 不涉及 | 自动创建/清理测试账号 |
| **验证方式** | JSON格式+字段完整性 | HTTP状态码+响应内容 |

### 技术对比

| 技术 | AI生成测试用例 | AI驱动接口自动化 |
|-----|--------------|----------------|
| **并发策略** | ThreadPoolExecutor（5线程） | 顺序执行（依赖链） |
| **数据收集** | KTO数据集（正/负样本） | 无 |
| **去重机制** | Embedding向量去重 | 无（顺序执行） |
| **流式输出** | SSE（实时进度） | SSE（实时执行状态） |
| **错误处理** | 重试+记录负样本 | 跳过/停止+清理账号 |
| **温度控制** | 递减（1.0→0.7） | 固定（由知识库控制） |

### 流程图对比

**AI生成测试用例流程**

```
需求文档
    │
    ↓ 需求提取（RAG+Agent）
功能点列表
    │
    ↓ 关联内容检索（并行）
功能点+原文引用
    │
    ↓ AI生成测试用例（并行+重试）
测试用例JSON
    │
    ↓ 字段验证+向量去重
有效用例列表
    │
    ↓ 保存数据库
TestCase记录
```

**AI驱动接口自动化流程**

```
接口测试用例
    │
    ↓ 依赖分析（AI）
执行顺序run_list
    │
    ↓ 执行第一个接口
执行结果1 → history
    │
    ↓ AI分析+参数填充
    ↓ 智能推断+占位符替换
执行结果2 → history
    │
    ↓ ... 循环执行 ...
    │
    ↓ 结果校验（AI）
测试报告
    │
    ↓ 清理测试账号
环境恢复
```

---

## 附录：常见问题

### Q1: AI生成用例为什么需要KTO数据集？

KTO（Kahneman-Tversky Optimization）是一种偏好学习方法。通过收集正样本（有效用例）和负样本（无效用例），可以：

1. 分析AI生成的常见错误模式
2. 用于后续模型微调，提高生成质量
3. 构建自动化评估基准

### Q2: 接口自动化如何保证测试账号不冲突？

采用时间戳格式的唯一用户名：

```
test_YYYYMMDD_HHMMSS_xxxx

示例：test_20260529_143052_a1b2

特点：
- 每次执行生成新账号
- 不同用户角色使用不同账号
- 执行后自动清理
```

### Q3: 接口执行失败时如何处理？

```python
# 可跳过的错误配置
SKIPPABLE_ERRORS = {
    "注册": ["已存在", "已注册", "duplicate"],
    "登录": []  # 登录失败不跳过
}

# 处理逻辑
if not result.success:
    if is_skippable_error(result):
        continue  # 继续执行后续接口
    else:
        break  # 停止执行
```

### Q4: 如何处理动态参数（如user_id、token）？

1. **extract_vars字段**：在依赖分析时定义提取路径
   ```json
   {"extract_vars": {"user_id": "$.run_list[0].response.body.data.id"}}
   ```

2. **智能推断**：根据占位符名称自动推断
   ```
   user_a_id → 第一个注册接口的id
   token → 登录接口的token
   ```

3. **后处理替换**：执行前自动替换URL和Body中的占位符

---

文档版本：v1.0
最后更新：2025-05-29