"""Process-safe run-level write locks for intelligence publishing.

Uses POSIX ``fcntl.flock`` exclusive locks on ``runs/<run_id>/.write.lock``.

Limitations
-----------
* POSIX-oriented (macOS / Linux). Not supported on native Windows without
  an alternate backend.
* Serializes writers **within and across processes** on the same host and
  filesystem that honors ``flock``.
* Does not provide distributed locking across hosts or shared network
  filesystems that ignore advisory locks.
* Lock files are never registered as artifacts or snapshots.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

from app.intelligence.errors import IntelligenceStorageError

LOCK_FILENAME = ".write.lock"


class RunWriteLock:
    """Exclusive advisory lock for one research run directory."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._fd: Optional[int] = None

    def __enter__(self) -> "RunWriteLock":
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            # Open without truncating; create if missing.
            self._fd = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT,
                0o644,
            )
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        except OSError as exc:
            self._close_fd()
            raise IntelligenceStorageError(
                f"unable to acquire run write lock: {self._lock_path}"
            ) from exc
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        try:
            if self._fd is not None:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self._close_fd()

    def _close_fd(self) -> None:
        if self._fd is None:
            return
        try:
            os.close(self._fd)
        except OSError:
            pass
        self._fd = None
