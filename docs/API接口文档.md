# 测试用例管理系统 - API 接口文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | 测试用例管理系统 |
| 文档版本 | V1.0 |
| 基础路径 | http://localhost:8000/api |
| 认证方式 | JWT Bearer Token |

---

## 一、接口概述

### 1.1 请求格式

- Content-Type: `application/json`
- 认证头: `Authorization: Bearer <token>`

### 1.2 响应格式

#### 成功响应

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... }
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "错误信息"
}
```

### 1.3 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器内部错误 |

---

## 二、用户认证接口

### 2.1 用户登录

**接口地址**: `POST /api/users/login/`

**是否认证**: 否

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例**:

```json
{
  "username": "admin",
  "password": "password123"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "system_role": "超级管理员",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### 2.2 用户注册

**接口地址**: `POST /api/users/register/`

**是否认证**: 否

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名（唯一） |
| password | string | 是 | 密码 |
| email | string | 是 | 邮箱（唯一） |
| name | string | 是 | 姓名 |
| phone | string | 否 | 手机号 |

**请求示例**:

```json
{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com",
  "name": "测试用户",
  "phone": "13900139000"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 2,
    "username": "testuser",
    "name": "测试用户",
    "email": "test@example.com"
  }
}
```

---

### 2.3 忘记密码

**接口地址**: `POST /api/users/forgot-password/`

**是否认证**: 否

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 注册邮箱 |

**请求示例**:

```json
{
  "email": "test@example.com"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "重置密码链接已发送到您的邮箱",
  "data": {
    "reset_url": "http://localhost:8000/api/users/reset-password/abc123..."
  }
}
```

---

### 2.4 重置密码

**接口地址**: `POST /api/users/reset-password/<token>/`

**是否认证**: 否

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| token | string | 重置密码令牌 |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| new_password | string | 是 | 新密码 |

**请求示例**:

```json
{
  "new_password": "newpassword123"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "密码重置成功"
}
```

---

### 2.5 用户登出

**接口地址**: `POST /api/users/logout/`

**是否认证**: 是

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "登出成功"
}
```

---

### 2.6 获取用户信息

**接口地址**: `GET /api/users/profile/`

**是否认证**: 是

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "avatar": null,
    "title": "高级工程师",
    "system_role": "超级管理员",
    "status": "active",
    "last_login_time": "2024-01-01T10:00:00Z",
    "last_login_ip": "127.0.0.1",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 2.7 获取用户列表

**接口地址**: `GET /api/users/`

**是否认证**: 是

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "users": [
      {
        "id": 1,
        "name": "管理员",
        "email": "admin@example.com",
        "avatar": ""
      },
      {
        "id": 2,
        "name": "测试用户",
        "email": "test@example.com",
        "avatar": ""
      }
    ]
  }
}
```

---

## 三、项目管理接口

### 3.1 获取项目列表

**接口地址**: `GET /api/projects/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页数量，默认 10 |
| status | string | 否 | 项目状态筛选 |
| type | string | 否 | 项目类型筛选 |
| keyword | string | 否 | 搜索关键词 |

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "projects": [
      {
        "id": 1,
        "name": "电商平台测试",
        "code": "ECOMMERCE",
        "description": "电商平台功能测试项目",
        "type": "web",
        "status": "active",
        "owner": "admin",
        "isFavorite": true,
        "testCases": 150,
        "testPlans": 10,
        "bugs": 25
      }
    ],
    "total": 1
  }
}
```

---

### 3.2 获取项目详情

**接口地址**: `GET /api/projects/<id>/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | int | 项目 ID |

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "name": "电商平台测试",
    "code": "ECOMMERCE",
    "description": "电商平台功能测试项目",
    "type": "web",
    "status": "active",
    "owner": "admin",
    "isFavorite": true,
    "testCases": 150,
    "testPlans": 10,
    "bugs": 25,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### 3.3 创建项目

**接口地址**: `POST /api/projects/create/`

**是否认证**: 是

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 项目名称 |
| code | string | 是 | 项目标识（唯一） |
| description | string | 否 | 项目描述 |
| type | string | 否 | 项目类型，默认 web |
| status | string | 否 | 项目状态，默认 active |

**请求示例**:

```json
{
  "name": "新项目",
  "code": "NEW_PROJECT",
  "description": "项目描述",
  "type": "web",
  "status": "active"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 2,
    "name": "新项目",
    "code": "NEW_PROJECT",
    "description": "项目描述",
    "type": "web",
    "status": "active",
    "owner": "admin",
    "isFavorite": false,
    "testCases": 0,
    "testPlans": 0,
    "bugs": 0
  }
}
```

---

### 3.4 更新项目

**接口地址**: `PUT /api/projects/<id>/update/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | int | 项目 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 否 | 项目名称 |
| code | string | 否 | 项目标识 |
| description | string | 否 | 项目描述 |
| type | string | 否 | 项目类型 |
| status | string | 否 | 项目状态 |
| isFavorite | boolean | 否 | 是否收藏 |

**请求示例**:

```json
{
  "name": "更新后的项目名",
  "description": "更新后的描述",
  "status": "completed"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "name": "更新后的项目名",
    "code": "ECOMMERCE",
    "description": "更新后的描述",
    "type": "web",
    "status": "completed",
    "owner": "admin",
    "isFavorite": false,
    "testCases": 150,
    "testPlans": 10,
    "bugs": 25
  }
}
```

---

### 3.5 删除项目

**接口地址**: `DELETE /api/projects/<id>/delete/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | int | 项目 ID |

**响应示例**:

```json
{
  "code": 200,
  "message": "删除成功"
}
```

---

### 3.6 搜索项目

**接口地址**: `GET /api/projects/search/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| q | string | 是 | 搜索关键词 |

**响应示例**:

```json
{
  "code": 200,
  "message": "搜索成功",
  "data": {
    "results": [
      {
        "id": 1,
        "name": "电商平台测试",
        "code": "ECOMMERCE",
        "description": "电商平台功能测试项目",
        "type": "web",
        "status": "active",
        "owner": "admin",
        "isFavorite": true
      }
    ]
  }
}
```

---

### 3.7 获取项目统计

**接口地址**: `GET /api/projects/stats/`

**是否认证**: 是

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 10,
    "active": 5,
    "completed": 3,
    "pending": 1,
    "archived": 1,
    "byType": {
      "web": 4,
      "mobile": 2,
      "api": 2,
      "performance": 1,
      "security": 0,
      "other": 1
    }
  }
}
```

---

## 四、项目成员接口

### 4.1 获取项目成员列表

**接口地址**: `GET /api/projects/<project_id>/members/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| project_id | int | 项目 ID |

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "members": [
      {
        "id": 1,
        "userId": 1,
        "name": "管理员",
        "email": "admin@example.com",
        "avatar": "",
        "role": "admin",
        "status": "active",
        "joinedAt": "2024-01-01T00:00:00Z",
        "isOwner": true
      }
    ]
  }
}
```

---

### 4.2 添加项目成员

**接口地址**: `POST /api/projects/<project_id>/members/add/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| project_id | int | 项目 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| userId | int | 是 | 用户 ID |
| role | string | 否 | 成员角色，默认 viewer |
| status | string | 否 | 成员状态，默认 active |

**请求示例**:

```json
{
  "userId": 2,
  "role": "tester",
  "status": "active"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "添加成功",
  "data": {
    "id": 2,
    "userId": 2,
    "name": "测试用户",
    "email": "test@example.com",
    "avatar": "",
    "role": "tester",
    "status": "active",
    "joinedAt": "2024-01-15T10:00:00Z"
  }
}
```

---

### 4.3 更新项目成员

**接口地址**: `PUT /api/projects/<project_id>/members/<member_id>/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| project_id | int | 项目 ID |
| member_id | int | 成员 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| role | string | 否 | 成员角色 |
| status | string | 否 | 成员状态 |

**请求示例**:

```json
{
  "role": "developer",
  "status": "active"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 2,
    "userId": 2,
    "name": "测试用户",
    "email": "test@example.com",
    "avatar": "",
    "role": "developer",
    "status": "active",
    "joinedAt": "2024-01-15T10:00:00Z"
  }
}
```

---

### 4.4 移除项目成员

**接口地址**: `DELETE /api/projects/<project_id>/members/<member_id>/delete/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| project_id | int | 项目 ID |
| member_id | int | 成员 ID |

**响应示例**:

```json
{
  "code": 200,
  "message": "移除成功"
}
```

---

### 4.5 批量更新成员

**接口地址**: `PUT /api/projects/<project_id>/members/batch/`

**是否认证**: 是

**路径参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| project_id | int | 项目 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| memberIds | array | 是 | 成员 ID 列表 |
| role | string | 否 | 要更新的角色 |
| status | string | 否 | 要更新的状态 |

**请求示例**:

```json
{
  "memberIds": [2, 3, 4],
  "role": "tester"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "成功更新 3 个成员",
  "data": {
    "updatedCount": 3
  }
}
```

---

### 4.6 获取项目角色

**接口地址**: `GET /api/projects/<project_id>/roles/`

**是否认证**: 是

**响应示例**:

```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "key": "admin",
      "name": "管理员",
      "color": "#ef4444",
      "memberCount": 1,
      "permissions": ["project_manage", "member_manage", "testcase_manage"]
    },
    {
      "key": "developer",
      "name": "开发人员",
      "color": "#3b82f6",
      "memberCount": 2,
      "permissions": ["testcase_view", "api_view", "bug_manage"]
    },
    {
      "key": "tester",
      "name": "测试人员",
      "color": "#22c55e",
      "memberCount": 3,
      "permissions": ["testcase_manage", "testcase_view", "test_execute"]
    },
    {
      "key": "viewer",
      "name": "观察者",
      "color": "#6b7280",
      "memberCount": 0,
      "permissions": ["testcase_view", "report_view"]
    }
  ]
}
```

---

## 五、测试用例接口

### 5.1 用例库接口

#### 获取用例库列表

**接口地址**: `GET /api/testcase/repositories/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project | int | 否 | 项目 ID |
| is_default | boolean | 否 | 是否默认 |

**响应示例**:

```json
{
  "id": 1,
  "name": "主用例库",
  "project": 1,
  "description": "项目主用例库",
  "is_default": true,
  "created_by": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 创建用例库

**接口地址**: `POST /api/testcase/repositories/`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 用例库名称 |
| project | int | 否 | 所属项目 ID |
| description | string | 否 | 描述 |
| is_default | boolean | 否 | 是否默认 |

---

### 5.2 版本接口

#### 获取版本列表

**接口地址**: `GET /api/testcase/versions/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| repository | int | 否 | 用例库 ID |
| status | string | 否 | 版本状态 |
| is_default | boolean | 否 | 是否默认版本 |

#### 设置默认版本

**接口地址**: `POST /api/testcase/versions/<id>/set_default/`

**是否认证**: 是

---

### 5.3 模块接口

#### 获取模块列表

**接口地址**: `GET /api/testcase/modules/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| version | int | 否 | 版本 ID |
| parent | int | 否 | 父模块 ID |

#### 获取模块树

**接口地址**: `GET /api/testcase/modules/tree/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| version | int | 是 | 版本 ID |

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "用户模块",
    "version": 1,
    "parent": null,
    "sort_order": 1,
    "children": [
      {
        "id": 2,
        "name": "登录功能",
        "version": 1,
        "parent": 1,
        "sort_order": 1,
        "children": []
      }
    ]
  }
]
```

#### 创建模块

**接口地址**: `POST /api/testcase/modules/`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 模块名称 |
| version | int | 是 | 版本 ID |
| parent | int | 否 | 父模块 ID |
| sort_order | int | 否 | 排序序号 |

---

### 5.4 测试用例接口

#### 获取测试用例列表

**接口地址**: `GET /api/testcase/testcases/`

**是否认证**: 是

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| version | int | 否 | 版本 ID |
| module | int | 否 | 模块 ID |
| priority | string | 否 | 优先级 (p0/p1/p2/p3) |
| automation_status | string | 否 | 自动化状态 |
| search | string | 否 | 搜索关键词 |

**响应示例**:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/testcase/testcases/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "用户登录-正常登录",
      "module": 2,
      "module_name": "登录功能",
      "version": 1,
      "priority": "p0",
      "tags": ["登录", "冒烟"],
      "automation_status": "automated",
      "created_by": 1,
      "created_by_name": "管理员",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 按版本获取用例

**接口地址**: `GET /api/testcase/testcases/by_version/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| version | int | 是 | 版本 ID |

#### 按模块获取用例

**接口地址**: `GET /api/testcase/testcases/by_module/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| module | int | 是 | 模块 ID |

#### 按模块树获取用例（包含子模块）

**接口地址**: `GET /api/testcase/testcases/by_module_tree/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| module | int | 是 | 模块 ID |

#### 获取用例详情

**接口地址**: `GET /api/testcase/testcases/<id>/`

**响应示例**:

```json
{
  "id": 1,
  "title": "用户登录-正常登录",
  "module": 2,
  "module_name": "登录功能",
  "version": 1,
  "priority": "p0",
  "estimated_hours": "0.50",
  "tags": ["登录", "冒烟"],
  "automation_status": "automated",
  "automation_case_id": "TC_LOGIN_001",
  "requirement": "REQ-001",
  "precondition": "用户已注册",
  "steps": [
    {
      "id": 1,
      "step_number": 1,
      "description": "打开登录页面",
      "expected_result": "登录页面正常显示"
    },
    {
      "id": 2,
      "step_number": 2,
      "description": "输入正确的用户名和密码",
      "expected_result": "输入框显示正确"
    },
    {
      "id": 3,
      "step_number": 3,
      "description": "点击登录按钮",
      "expected_result": "登录成功，跳转到首页"
    }
  ],
  "created_by": 1,
  "created_by_name": "管理员",
  "updated_by": 1,
  "updated_by_name": "管理员",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 创建测试用例

**接口地址**: `POST /api/testcase/testcases/`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 用例标题 |
| module | int | 否 | 所属模块 |
| version | int | 是 | 所属版本 |
| priority | string | 否 | 优先级，默认 p2 |
| estimated_hours | decimal | 否 | 评估工时 |
| tags | array | 否 | 标签列表 |
| automation_status | string | 否 | 自动化状态 |
| automation_case_id | string | 否 | 自动化用例 ID |
| requirement | string | 否 | 关联需求 |
| precondition | string | 否 | 前置条件 |
| steps | array | 否 | 测试步骤 |

**请求示例**:

```json
{
  "title": "用户登录-密码错误",
  "module": 2,
  "version": 1,
  "priority": "p1",
  "tags": ["登录", "异常"],
  "precondition": "用户已注册",
  "steps": [
    {
      "step_number": 1,
      "description": "打开登录页面",
      "expected_result": "登录页面正常显示"
    },
    {
      "step_number": 2,
      "description": "输入错误的密码",
      "expected_result": "显示密码错误提示"
    }
  ]
}
```

#### 更新测试用例

**接口地址**: `PUT /api/testcase/testcases/<id>/`

#### 删除测试用例

**接口地址**: `DELETE /api/testcase/testcases/<id>/`

#### 复制测试用例

**接口地址**: `POST /api/testcase/testcases/<id>/copy/`

**响应示例**:

```json
{
  "id": 2,
  "title": "用户登录-正常登录 (复制)",
  "module": 2,
  "version": 1,
  "priority": "p0",
  "steps": [
    {
      "id": 4,
      "step_number": 1,
      "description": "打开登录页面",
      "expected_result": "登录页面正常显示"
    }
  ]
}
```

---

### 5.5 评审接口

#### 获取评审列表

**接口地址**: `GET /api/testcase/reviews/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| test_case | int | 否 | 测试用例 ID |
| reviewer | int | 否 | 评审人 ID |
| status | string | 否 | 评审状态 |

#### 创建评审

**接口地址**: `POST /api/testcase/reviews/`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| test_case | int | 是 | 测试用例 ID |
| status | string | 是 | 评审状态 |
| comment | string | 否 | 评审意见 |

**请求示例**:

```json
{
  "test_case": 1,
  "status": "approved",
  "comment": "用例编写规范，覆盖全面"
}
```

---

### 5.6 执行记录接口

#### 获取执行记录列表

**接口地址**: `GET /api/testcase/executions/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| test_case | int | 否 | 测试用例 ID |
| executed_by | int | 否 | 执行人 ID |
| result | string | 否 | 执行结果 |

#### 获取用例执行历史

**接口地址**: `GET /api/testcase/executions/by_test_case/`

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| test_case | int | 是 | 测试用例 ID |

#### 创建执行记录

**接口地址**: `POST /api/testcase/executions/`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| test_case | int | 是 | 测试用例 ID |
| result | string | 是 | 执行结果 (pass/fail/block/skip) |
| actual_result | string | 否 | 实际结果 |
| remark | string | 否 | 备注 |

**请求示例**:

```json
{
  "test_case": 1,
  "result": "pass",
  "actual_result": "登录成功",
  "remark": "测试通过"
}
```

---

## 六、枚举值说明

### 6.1 项目类型

| 值 | 说明 |
|------|------|
| web | Web项目 |
| mobile | 移动应用 |
| api | API项目 |
| performance | 性能测试 |
| security | 安全测试 |
| other | 其他 |

### 6.2 项目状态

| 值 | 说明 |
|------|------|
| active | 进行中 |
| completed | 已完成 |
| pending | 待开始 |
| archived | 已归档 |

### 6.3 成员角色

| 值 | 说明 |
|------|------|
| admin | 管理员 |
| developer | 开发人员 |
| tester | 测试人员 |
| viewer | 观察者 |

### 6.4 用例优先级

| 值 | 说明 |
|------|------|
| p0 | P0 - 最高优先级 |
| p1 | P1 - 高优先级 |
| p2 | P2 - 中优先级 |
| p3 | P3 - 低优先级 |

### 6.5 自动化状态

| 值 | 说明 |
|------|------|
| not_analyzed | 未分析 |
| not_automated | 未自动化 |
| automated | 已自动化 |

### 6.6 评审状态

| 值 | 说明 |
|------|------|
| pending | 待评审 |
| approved | 已通过 |
| rejected | 已拒绝 |

### 6.7 执行结果

| 值 | 说明 |
|------|------|
| pass | 通过 |
| fail | 失败 |
| block | 阻塞 |
| skip | 跳过 |

---

## 七、错误码说明

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权，Token 无效或已过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 409 | 资源冲突（如用户名已存在） |
| 500 | 服务器内部错误 |

---

## 八、修订历史

| 版本 | 日期 | 修订人 | 修订内容 |
|------|------|--------|----------|
| V1.0 | 2024 | 开发团队 | 初始版本 |
