"""测试单实例进程锁。"""

import os
from pathlib import Path

import pytest

from funasr_flow.lock import LOCK_DIR, LOCK_FILE, _pid_is_alive, acquire, release


class TestPidIsAlive:
    """测试 _pid_is_alive 函数。"""

    def test_current_pid_is_alive(self):
        """当前进程的 PID 应该被判定为存活。"""
        assert _pid_is_alive(os.getpid()) is True

    def test_very_large_pid_is_dead(self):
        """一个极大的 PID 几乎肯定不存在。"""
        assert _pid_is_alive(99999) is False


class TestAcquireRelease:
    """测试 acquire / release 流程。"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """每个测试前后清理锁文件。"""
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        yield
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()

    def test_acquire_first_time_succeeds(self):
        """首次 acquire 应该返回 True。"""
        assert acquire() is True
        assert LOCK_FILE.exists()
        assert LOCK_FILE.read_text().strip() == str(os.getpid())

    def test_acquire_second_time_fails(self):
        """如果已经有运行中的进程，第二次 acquire 返回 False。"""
        assert acquire() is True  # 第一次成功
        assert acquire() is False  # 第二次失败（PID 还在）

    def test_release_removes_lock_file(self):
        """release 应该删除当前进程的锁文件。"""
        acquire()
        assert LOCK_FILE.exists()
        release()
        assert not LOCK_FILE.exists()

    def test_release_does_not_remove_other_pid(self):
        """release 不应删除其他进程写入的 PID。"""
        # 模拟其他进程写入的锁文件
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text("99999")
        release()  # 不应删除
        assert LOCK_FILE.exists()  # 文件仍然存在

    def test_acquire_recovers_stale_lock(self):
        """如果锁文件中的 PID 已死，acquire 应该覆盖它并返回 True。"""
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text("99999")  # 不存在的 PID
        assert acquire() is True  # 应该成功覆盖死锁

    def test_lock_dir_is_created(self):
        """acquire 应该自动创建锁目录。"""
        acquire()
        assert LOCK_DIR.exists()
        assert LOCK_DIR.is_dir()
