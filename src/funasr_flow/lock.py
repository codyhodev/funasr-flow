"""单实例进程锁 —— 通过 PID 文件确保同一时间只有一个守护进程在运行。"""

import os
from pathlib import Path

LOCK_DIR = Path.home() / ".cache" / "funasr-flow"
LOCK_FILE = LOCK_DIR / "daemon.pid"


def _pid_is_alive(pid: int) -> bool:
    """检查指定 PID 的进程是否仍在运行。"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def acquire() -> bool:
    """尝试获取进程锁。

    返回 True 表示获取成功（当前是唯一实例），
    返回 False 表示已有另一个守护进程在运行。
    """
    LOCK_DIR.mkdir(parents=True, exist_ok=True)

    if LOCK_FILE.exists():
        try:
            content = LOCK_FILE.read_text().strip()
            if content and content.isdigit():
                pid = int(content)
                if _pid_is_alive(pid):
                    return False
        except (ValueError, OSError):
            pass

    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release() -> None:
    """释放进程锁（仅在当前进程持有时删除 PID 文件）。"""
    if LOCK_FILE.exists():
        try:
            content = LOCK_FILE.read_text().strip()
            if content == str(os.getpid()):
                LOCK_FILE.unlink()
        except (ValueError, OSError):
            pass
