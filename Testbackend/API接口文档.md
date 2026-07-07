# 测试用例管理系统 API 接口文档

## 概述

- **基础URL**: `http://localhost:8000`
- **认证方式**: JWT Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON

## 通用响应格式

```json
{
    "code": 200,
    "message": "操作成功",
    "data": { ... }
}
```

## 认证说明

除了登录、注册、重置密码等接口外，其他接口都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <token>
```

---

# 一、用户管理模块 `/api/users/`

## 1.1 认证相关

### 用户登录

- **URL**: `POST /api/users/login/`
- **认证**: 无需认证

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

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
        "avatar": "/media/avatars/default.png",
        "title": "系统管理员",
        "system_role": "admin",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

### 用户注册

- **URL**: `POST /api/users/register/`
- **认证**: 无需认证

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |
| name | string | 是 | 真实姓名 |
| phone | string | 否 | 手机号码 |

**响应示例**:
```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "id": 2,
        "username": "newuser",
        "name": "新用户",
        "email": "newuser@example.com"
    }
}
```

### 用户登出

- **URL**: `POST /api/users/logout/`
- **认证**: 需要认证

将当前 Token 加入黑名单，使其立即失效。

### 刷新 Token

- **URL**: `POST /api/users/refresh-token/`
- **认证**: 需要认证

**响应示例**:
```json
{
    "code": 200,
    "message": "Token刷新成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

### 忘记密码

- **URL**: `POST /api/users/forgot-password/`
- **认证**: 无需认证

发送密码重置邮件到用户邮箱。

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 注册时使用的邮箱地址 |

### 重置密码

- **URL**: `POST /api/users/reset-password/<token>/`
- **认证**: 无需认证

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| new_password | string | 是 | 新密码 |

---

## 1.2 用户管理

### 获取用户列表

- **URL**: `GET /api/users/`
- **认证**: 需要认证

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页数量，默认 20 |
| keyword | string | 否 | 搜索关键词 |
| status | string | 否 | 用户状态筛选 |
| role | string | 否 | 角色筛选 |

**响应示例**:
```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "users": [
            {
                "id": 1,
                "username": "admin",
                "name": "管理员",
                "avatar": "/media/avatars/default.png",
                "status": "active",
                "system_role": "admin",
                "system_role_name": "系统管理员"
            }
        ],
        "total": 10
    }
}
```

### 搜索用户

- **URL**: `GET /api/users/search/`
- **认证**: 需要认证

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 否 | 搜索关键词 |
| limit | int | 否 | 返回数量，默认 20 |

### 获取单个用户详情

- **URL**: `GET /api/users/<user_id>/`
- **认证**: 需要认证

### 更新用户信息

- **URL**: `PUT /api/users/<user_id>/update/`
- **认证**: 需要认证（管理员或本人）

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 否 | 真实姓名 |
| phone | string | 否 | 手机号码 |

### 删除用户

- **URL**: `DELETE /api/users/<user_id>/delete/`
- **认证**: 需要认证（仅管理员）

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| transfer_to | int | 否 | 数据转移目标用户ID |

### 更新用户角色

- **URL**: `PUT /api/users/<user_id>/role/`
- **认证**: 需要认证（仅管理员）

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| role | string | 是 | 角色代码 |

### 更新用户状态

- **URL**: `PUT /api/users/<user_id>/status/`
- **认证**: 需要认证（仅管理员）

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | string | 是 | 用户状态：active/disabled/suspended/pending |

---

# 二、错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 失效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

# 三、数据模型

## 用户 (User)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户ID |
| username | string | 用户名 |
| name | string | 真实姓名 |
| email | string | 邮箱 |
| phone | string | 手机号码 |
| avatar | string | 头像URL |
| title | string | 职位/头衔 |
| system_role | string | 系统角色代码 |
| status | string | 用户状态：active/disabled/suspended/pending |
| created_at | datetime | 创建时间 |
| last_login_time | datetime | 最后登录时间 |

---

**文档版本**: v1.0
**最后更新**: 2024年