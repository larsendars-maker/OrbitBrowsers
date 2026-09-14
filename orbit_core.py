from __future__ import annotations

import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional


class OrbitCore:
    """Small process-wide coordination layer: background tasks, debouncing, and recent commands."""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max(2, min(max_workers, 6)), thread_name_prefix="orbit-core")
        self.recent_commands = deque(maxlen=20)
        self._last_tasks = {}

    def submit(self, key: str, fn: Callable, callback: Optional[Callable] = None):
        future = self.executor.submit(fn)
        self._last_tasks[key] = future
        if callback:
            def done(f):
                try:
                    result = f.result()
                except Exception as exc:
                    result = exc
                callback(result)
            future.add_done_callback(done)
        return future

    def remember_command(self, command: str):
        command = str(command or "").strip()
        if command:
            try:
                self.recent_commands.remove(command)
            except ValueError:
                pass
            self.recent_commands.appendleft(command)

    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)


class PerformancePolicy:
    WEBENGINE_CACHE_MB = 256
    MAX_RESTORED_TABS = 12
    MAX_HISTORY = 2000
    MAX_DOWNLOADS = 500
    BACKGROUND_POLL_MS = 60_000
    UPDATE_POLL_MS = 30 * 60 * 1000

    @classmethod
    def webengine_flags(cls) -> str:
        return "--disable-background-networking --disable-component-update --disable-domain-reliability --disable-features=TranslateUI,MediaRouter --disk-cache-size=268435456"

    @classmethod
    def now_ms(cls) -> int:
        return int(time.time() * 1000)
