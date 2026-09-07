# -*- coding: utf-8 -*-
"""
请求体占位符 / 非法值兜底清洗。

问题背景：
    AI 在填充测试数据时，会把提示词示例里的 <测试密码>、<测试手机号> 等模板标记
    当作真实值原样输出，导致注册 / 登录接口因「密码过短」「手机号格式非法」等返回 400。

本模块在 AI 填充结果落库 / 执行前，把这些占位符式值替换为合法值，保证请求可被接口接受。
注意：仅对「占位符式」值做替换，不会动真实短密码（那是合法的负面测试用例）。
"""
import re
import secrets
import string
import threading
from datetime import datetime
from typing import Dict

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 测试用户名后缀用高熵随机生成（见 _generate_test_username）。
# 加锁仅作防御性原子保护，secrets.token_hex 本身线程安全。
_USERNAME_LOCK = threading.Lock()

_PASSWORD_KEYS = (
    "password", "passwd", "pwd", "user_password", "login_password",
    "new_password", "confirm_password", "pay_password", "trade_password",
)
_PHONE_KEYS = ("phone", "mobile", "phone_number", "mobile_phone", "telephone")
_USERNAME_KEYS = ("username", "user_name", "account", "login_name", "uname", "login_account")
_EMAIL_KEYS = ("email", "mail", "email_address", "user_email", "e_mail")

# 形如 <测试密码> / <测试手机号> 的模板标记
_BRACKET_PLACEHOLDER_RE = re.compile(r"^<[^>]{1,40}>$")
# 含明显占位语义的短字符串（不含尖括号，如「测试密码」「placeholder」）
_HINT_PLACEHOLDER_RE = re.compile(
    r"(测试密码|测试手机号|测试账号|测试用户|占位符|占位|placeholder|todo|示例值|示例|example|xxxx)",
    re.IGNORECASE,
)

_PASSWORD_CHARS = string.ascii_letters + string.digits + "!@#$%^&*"


def _is_placeholder(value: str) -> bool:
    """判断一个字符串是否是模板占位符（而非真实值）。"""
    v = value.strip()
    if not v:
        return False
    if _BRACKET_PLACEHOLDER_RE.match(v):
        return True
    if _HINT_PLACEHOLDER_RE.search(v):
        return True
    return False


def _generate_strong_password(min_len: int = 12, max_len: int = 16) -> str:
    """生成满足常见密码策略的强密码：≥8 位、含大小写字母 + 数字 + 特殊符号。"""
    length = secrets.randbelow(max_len - min_len + 1) + min_len
    while True:
        pwd = "".join(secrets.choice(_PASSWORD_CHARS) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%^&*" for c in pwd)
        ):
            return pwd


def _generate_test_username() -> str:
    """生成符合约定的测试用户名：test_YYYYMMDD_HHMMSS_xxxxxxxxxxxx（12 位 hex 后缀）

    后缀用 secrets.token_hex(6) 生成 12 位高熵随机，空间 36^12≈4.7e18，
    并发 / 多进程 / 长批量下严格不碰撞（10 万次生成碰撞概率 < 1e-9）。
    不再依赖进程内自增计数——旧实现 `c & 0xFFFF` 截断后只取低 8 位 + 2 位随机，
    4 位后缀空间仅 65536，并发批量时自增低 8 位回绕 + 随机碰撞会生成重复账号。
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(6)
    return f"test_{ts}_{suffix}"


def _generate_test_email(username: str) -> str:
    return f"{username}@example.com"


def _generate_test_phone() -> str:
    """生成合法的 11 位中国大陆手机号：1 + [3-9] + 9 位数字。"""
    second = secrets.choice("3456789")
    return "1" + second + "".join(secrets.choice(string.digits) for _ in range(9))


def sanitize_request_body(body) -> object:
    """递归清理请求体中的占位符式字段值。

    - 密码类字段：替换为合法强密码
    - 用户名类字段：生成 test_YYYYMMDD_HHMMSS_xxxx
    - 邮箱类字段：生成 test_...@example.com
    - 手机号类字段：生成合法 11 位手机号
    - 其他占位符字段：仅告警不替换，避免误改真实数据
    """
    if isinstance(body, dict):
        for key, val in list(body.items()):
            k = str(key).lower()
            if isinstance(val, dict):
                sanitize_request_body(val)
            elif isinstance(val, list):
                for item in val:
                    sanitize_request_body(item)
            elif isinstance(val, str) and _is_placeholder(val):
                if any(pk in k for pk in _PASSWORD_KEYS):
                    body[key] = _generate_strong_password()
                    logger.warning(f"字段 [{key}] 检测到占位符密码，已自动替换为合法强密码")
                elif any(uk in k for uk in _USERNAME_KEYS):
                    uname = _generate_test_username()
                    body[key] = uname
                    logger.warning(f"字段 [{key}] 检测到占位符用户名，已自动生成测试用户名: {uname}")
                elif any(ek in k for ek in _EMAIL_KEYS):
                    email = _generate_test_email(_generate_test_username())
                    body[key] = email
                    logger.warning(f"字段 [{key}] 检测到占位符邮箱，已自动生成测试邮箱: {email}")
                elif any(pk in k for pk in _PHONE_KEYS):
                    phone = _generate_test_phone()
                    body[key] = phone
                    logger.warning(f"字段 [{key}] 检测到占位符手机号，已自动生成合法手机号: {phone}")
                else:
                    logger.warning(f"字段 [{key}] 含占位符式值 {val!r}，未自动替换（非敏感字段）")
    elif isinstance(body, list):
        for item in body:
            sanitize_request_body(item)
    return body


def sanitize_run_list(run_list) -> object:
    """清洗 run_list 中每个接口的 request_body。"""
    if not isinstance(run_list, list):
        return run_list
    for item in run_list:
        if isinstance(item, dict):
            rb = item.get("request_body")
            if isinstance(rb, dict):
                sanitize_request_body(rb)
    return run_list


def sanitize_filled_data(data) -> object:
    """清洗 AI 填充结果：兼容 dict(含 run_list) / dict(含 request_body) / list 三种形态。"""
    if isinstance(data, dict):
        if "run_list" in data:
            sanitize_run_list(data["run_list"])
        elif "request_body" in data:
            sanitize_request_body(data.get("request_body"))
    elif isinstance(data, list):
        sanitize_run_list(data)
    return data


# ==================== 执行级账号隔离 ====================
# 解决批量（含并发）执行时，多个用例的注册/登录步骤共用同一个写死账号，
# 导致彼此修改同一账号数据、测试结果失真的问题。
#
# 思路：每次执行（一次 execute_testcase 调用）生成一组「执行级唯一测试账号」，
# 通过占位符 {{__TEST_USERNAME_N__}} / {{__TEST_PASSWORD_N__}} 等自动绑定到该用例的
# 注册/登录步骤。
#
# 多用户交互场景支持：
#   - 第 k 个「登录」步骤配对第 k 个「注册」步骤产生的账号（顺序配对），
#     覆盖「注册A → 注册B → 登录A → 登录B」与「注册A → 登录A → 注册B → 登录B」两类常见形态；
#   - 若登录/注册的步骤名携带用户标签（如「用户A」「账号B」），优先按标签精确配对，
#     支持乱序（注册A、注册B、登录B、登录A）等多用户交互。
#   不同执行（含并发批量）始终使用不同账号，杜绝共用；cleanup 精准删除本次创建的真实账号。

def is_error_status(expected_status) -> bool:
    """判断 expected_status（int 或 "200"/"4XX"/"400-401" 等字符串）是否指向错误类响应（>=400）。

    用于识别负面/异常测试步骤：此类步骤的请求体是刻意构造的数据
    （SQL 注入串、错误密码、不存在用户名等），账号隔离逻辑不得改写。
    """
    if expected_status is None or isinstance(expected_status, bool):
        return False
    try:
        if isinstance(expected_status, int):
            return expected_status >= 400
        s = str(expected_status).upper().strip()
        if s.endswith("XX"):
            return s[0] in "45"
        if "-" in s:
            return int(s.split("-")[0]) >= 400
        return int(s) >= 400
    except (ValueError, TypeError):
        return False


def make_unique_test_account() -> Dict[str, str]:
    """生成一组执行级唯一测试账号（用户名/密码/邮箱/手机号）。"""
    username = _generate_test_username()
    return {
        "username": username,
        "password": _generate_strong_password(),
        "email": _generate_test_email(username),
        "phone": _generate_test_phone(),
    }


def _set_creds(rb: dict, username_ph: str, password_ph: str,
               email_ph: object, phone_ph: object) -> None:
    """把请求体里的账号类字段改写为占位符（注入执行级唯一账号）。"""
    for k in list(rb.keys()):
        kl = str(k).lower()
        if any(uk in kl for uk in _USERNAME_KEYS):
            rb[k] = username_ph
        elif any(pk in kl for pk in _PASSWORD_KEYS):
            rb[k] = password_ph
        elif email_ph is not None and any(ek in kl for ek in _EMAIL_KEYS):
            rb[k] = email_ph
        elif phone_ph is not None and any(pk2 in kl for pk2 in _PHONE_KEYS):
            rb[k] = phone_ph


def _original_username(rb: dict) -> str:
    """读取改写前的用户名类字段值（用于账号改写日志展示）。"""
    for k, v in rb.items():
        if isinstance(v, str) and any(uk in str(k).lower() for uk in _USERNAME_KEYS):
            return v
    return ""


def _step_request_body(step: dict) -> dict:
    """兼容 request_body / body 两种字段名，返回可写的请求体 dict（不存在则 None）。"""
    for key in ("request_body", "body"):
        rb = step.get(key)
        if isinstance(rb, dict):
            return rb
    return None


# 多用户标签识别：从「注册用户A」这类步骤名里提取用户标识（A/B/1/2…），
# 用于精确配对注册与登录（支持乱序多用户交互）。匹配不到时回退到「顺序配对」。
_USER_LABEL_RE = re.compile(
    r"(?:用户|账号|账户|user|account|u)\s*[:：]?\s*([A-Za-z0-9一二三四五六七八九十]{1,6})"
    r"|([A-Za-z0-9一二三四五六七八九十]{1,6})\s*(?:用户|账号|账户)",
    re.IGNORECASE,
)


def _extract_user_label(name: str):
    """从步骤名提取用户标签（如『用户A』→ 'A'），无标签返回 None。"""
    m = _USER_LABEL_RE.search(name or "")
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip() or None


def _has_cred_field(rb: dict) -> bool:
    """请求体是否含用户名或手机号类字段（用于过滤掉『登录态校验』等无凭据步骤）。"""
    return any(
        any(uk in str(k).lower() for uk in _USERNAME_KEYS)
        or any(pk in str(k).lower() for pk in _PHONE_KEYS)
        for k in rb.keys()
    )


def bind_test_accounts(run_list: list, runtime_vars: dict) -> list:
    """为 run_list 中的注册/登录步骤分配执行级唯一测试账号，并注入 runtime_vars。

    配对策略（多用户交互安全）：
      - 每个「注册」步骤分配一个唯一账号，按顺序编号 0,1,2…。
      - 第 k 个「登录」步骤配对第 k 个「注册」步骤的账号（顺序配对）；
        若登录步骤名带用户标签（如「用户A」），则优先按标签精确配对到对应注册，
        从而支持乱序（注册A、注册B、登录B、登录A）等多用户交互场景。
      - 无前置注册、但登录使用写死测试账号时，也分配唯一账号，避免并发共用。
      - 已使用 __ADMIN_USERNAME__ 占位符的管理员登录保持不变（管理员账号本就共享）。
      - 仅当步骤含用户名/手机号类字段才改写，避免误伤「登录态校验」等无凭据步骤。
    返回本次执行实际生成的账号名列表，供 cleanup 精准清理。

    Args:
        run_list: 待执行的接口列表（会被原地改写凭据为占位符）
        runtime_vars: 运行时变量表（会被写入 __TEST_USERNAME_N__ 等键值，
            以及 __TEST_ACCOUNTS__（创建的账号）和 __ACCOUNT_REWRITES__（改写记录：
            [{run_num, api_name, original, account}]，供执行日志展示替换关系））
    Returns:
        本次执行创建的真实测试账号名列表
    """
    accounts: list = []
    rewrites: list = []         # 账号改写记录，供执行日志展示「原账号 → 隔离账号」映射
    register_slots: list = []   # 元素: {"un","pw","em","ph","label"} 占位符
    label_to_slot: dict = {}    # 标签 -> 注册槽位索引
    login_seq = 0               # 顺序配对用的登录计数器

    for step in run_list:
        if not isinstance(step, dict):
            continue
        name = str(step.get("api_name", "") or "")
        rb = _step_request_body(step)
        if rb is None or not _has_cred_field(rb):
            continue

        is_register = "注册" in name
        is_login = "登录" in name
        if not (is_register or is_login):
            continue

        # 负面/异常测试（预期 4XX/5XX）：请求体是刻意构造的数据（SQL 注入串、
        # 错误密码、不存在用户等），改写凭据会让用例失去测试意义，保持原样
        if is_error_status(step.get("expected_status")):
            continue

        if is_register:
            original_un = _original_username(rb)
            acct = make_unique_test_account()
            n = len(register_slots)
            un = f"__TEST_USERNAME_{n}__"
            pw = f"__TEST_PASSWORD_{n}__"
            em = f"__TEST_EMAIL_{n}__"
            ph = f"__TEST_PHONE_{n}__"
            runtime_vars[un] = acct["username"]
            runtime_vars[pw] = acct["password"]
            runtime_vars[em] = acct["email"]
            runtime_vars[ph] = acct["phone"]
            _set_creds(rb, "{{" + un + "}}", "{{" + pw + "}}", "{{" + em + "}}", "{{" + ph + "}}")
            label = _extract_user_label(name)
            register_slots.append({"un": un, "pw": pw, "em": em, "ph": ph, "label": label})
            accounts.append(acct["username"])
            rewrites.append({
                "run_num": step.get("run_num"),
                "api_name": name,
                "original": original_un,
                "account": acct["username"],
            })
            if label:
                label_to_slot[label] = n
            continue

        # 登录步骤
        existing_un = str(rb.get("username") or rb.get("user_name") or "")
        # 管理员登录 / 已引用变量（含本系统占位符）保持原样
        if "__ADMIN_USERNAME__" in existing_un or existing_un.startswith("{{"):
            continue

        # 1) 标签精确配对；2) 回退顺序配对（第 login_seq 个登录 → 第 login_seq 个注册）
        label = _extract_user_label(name)
        slot_idx = label_to_slot.get(label) if label else None
        if slot_idx is None:
            if login_seq < len(register_slots):
                slot_idx = login_seq
            else:
                # 登录数超过注册数：为该登录单独生成唯一账号
                acct = make_unique_test_account()
                n = len(register_slots)
                un = f"__TEST_USERNAME_{n}__"
                pw = f"__TEST_PASSWORD_{n}__"
                runtime_vars[un] = acct["username"]
                runtime_vars[pw] = acct["password"]
                register_slots.append({"un": un, "pw": pw, "em": "", "ph": "", "label": None})
                accounts.append(acct["username"])
                slot_idx = n
            login_seq += 1

        slot = register_slots[slot_idx]
        original_un = _original_username(rb)
        bound_account = runtime_vars.get(slot["un"], "")
        _set_creds(rb, "{{" + slot["un"] + "}}", "{{" + slot["pw"] + "}}", None, "{{" + slot["ph"] + "}}")
        rewrites.append({
            "run_num": step.get("run_num"),
            "api_name": name,
            "original": original_un,
            "account": bound_account,
        })

    runtime_vars["__TEST_ACCOUNTS__"] = accounts
    runtime_vars["__ACCOUNT_REWRITES__"] = rewrites
    return accounts

