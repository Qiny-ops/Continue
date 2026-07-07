"""
Token 黑名单自动清理服务

在后台线程中定期清理过期的 Token 黑名单记录。
清理间隔通过环境变量 TOKEN_BLACKLIST_CLEANUP_INTERVAL_HOURS 配置，默认 1 小时。
"""

import threading
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 清理间隔（秒），默认 1 小时
CLEANUP_INTERVAL = int(getattr(settings, 'TOKEN_BLACKLIST_CLEANUP_INTERVAL_HOURS', 1)) * 3600

# 线程控制标志
_cleanup_thread = None
_stop_event = threading.Event()


def cleanup_expired_tokens():
    """执行清理过期的 Token 黑名单记录"""
    try:
        from apps.users.models import TokenBlacklist
        deleted_count, _ = TokenBlacklist.cleanup_expired()
        if deleted_count > 0:
            logger.info(f"已清理 {deleted_count} 条过期的 Token 黑名单记录")
    except Exception as e:
        logger.error(f"清理 Token 黑名单失败: {e}")


def _cleanup_loop():
    """后台清理循环"""
    while not _stop_event.is_set():
        cleanup_expired_tokens()
        _stop_event.wait(CLEANUP_INTERVAL)


def start_cleanup_scheduler():
    """启动后台清理调度器"""
    global _cleanup_thread, _stop_event

    if _cleanup_thread is not None and _cleanup_thread.is_alive():
        logger.warning("Token 黑名单清理线程已在运行")
        return

    _stop_event.clear()
    _cleanup_thread = threading.Thread(
        target=_cleanup_loop,
        name="token-blacklist-cleanup",
        daemon=True  # 守护线程，主进程退出时自动结束
    )
    _cleanup_thread.start()
    logger.info(f"Token 黑名单自动清理服务已启动，清理间隔: {CLEANUP_INTERVAL // 3600} 小时")


def stop_cleanup_scheduler():
    """停止后台清理调度器"""
    global _cleanup_thread, _stop_event

    if _cleanup_thread is None:
        return

    _stop_event.set()
    _cleanup_thread.join(timeout=5)
    logger.info("Token 黑名单自动清理服务已停止")
