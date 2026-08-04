"""Filesystem helpers for the Portfolio registry (Phase 5.1B)."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Type

from app.portfolio.errors import PortfolioLockError, PortfolioStorageError
from app.portfolio.schemas import is_valid_portfolio_id

# backend/app/portfolio/storage.py → parents[2] == backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_REGISTRY_ROOT = _BACKEND_ROOT / "outputs" / "portfolios"
ENV_PORTFOLIO_OUTPUT_DIR = "PORTFOLIO_OUTPUT_DIR"
DEFAULT_LOCK_TIMEOUT_SECONDS = 30.0
DEFAULT_LOCK_POLL_INTERVAL_SECONDS = 0.05

PORTFOLIOS_DIRNAME = "portfolios"  # unused when root IS portfolios/
DRAFT_DIRNAME = "draft"
PUBLISHED_DIRNAME = "published"
MANIFEST_FILENAME = "manifest.json"
INTEGRITY_FILENAME = "integrity.json"
LATEST_FILENAME = "latest.json"
LOCK_FILENAME = "portfolio.lock"

INTEGRITY_SCHEMA_VERSION = "portfolio-integrity/v1"
LATEST_SCHEMA_VERSION = "portfolio-latest/v1"
CHECKSUM_ALGORITHM = "sha256"


def resolve_portfolio_registry_root(env: Optional[dict[str, str]] = None) -> Path:
    source = env if env is not None else os.environ
    raw = (source.get(ENV_PORTFOLIO_OUTPUT_DIR) or "").strip()
    if not raw:
        return _DEFAULT_REGISTRY_ROOT.resolve()
    return Path(raw).expanduser().resolve()


def version_dirname(version: int) -> str:
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise PortfolioStorageError(f"invalid portfolio version for path: {version!r}")
    if version > 9999:
        raise PortfolioStorageError(
            f"portfolio version {version} exceeds supported vNNNN directory range"
        )
    return f"v{version:04d}"


def parse_version_dirname(name: str) -> Optional[int]:
    if not name.startswith("v") or len(name) != 5:
        return None
    digits = name[1:]
    if not digits.isdigit():
        return None
    value = int(digits)
    if value < 1:
        return None
    return value


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise PortfolioStorageError(
            "unable to hash portfolio file",
            path_category="integrity",
        ) from exc
    return digest.hexdigest()


class PortfolioWriteLock:
    """Exclusive advisory lock for one portfolio identity (POSIX flock).

    Uses non-blocking ``LOCK_EX | LOCK_NB`` with an explicit timeout so lock
    acquisition failure surfaces as ``PortfolioLockError`` rather than hanging
    indefinitely. Stale locks are released when the holding process exits
    (advisory ``flock`` semantics).
    """

    def __init__(
        self,
        lock_path: Path,
        *,
        timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
        poll_interval_seconds: float = DEFAULT_LOCK_POLL_INTERVAL_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise PortfolioLockError(
                "portfolio lock timeout must be positive",
                operation="lock",
                path_category="lock",
            )
        self._lock_path = lock_path
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._fd: Optional[int] = None

    def __enter__(self) -> "PortfolioWriteLock":
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._fd = os.open(
                self._lock_path,
                os.O_RDWR | os.O_CREAT,
                0o644,
            )
        except OSError as exc:
            self._close_fd()
            raise PortfolioLockError(
                "unable to open portfolio write lock",
                operation="lock",
                path_category="lock",
            ) from exc

        deadline = time.monotonic() + self._timeout_seconds
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    self._close_fd()
                    raise PortfolioLockError(
                        "timed out acquiring portfolio write lock",
                        operation="lock",
                        path_category="lock",
                    )
                time.sleep(self._poll_interval_seconds)
            except OSError as exc:
                self._close_fd()
                raise PortfolioLockError(
                    "unable to acquire portfolio write lock",
                    operation="lock",
                    path_category="lock",
                ) from exc

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


class PortfolioStorage:
    """Local layout: ``<root>/<portfolio_id>/{draft,published,latest.json}``."""

    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        self._root = (
            root if root is not None else resolve_portfolio_registry_root(env)
        ).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def ensure_root(self) -> Path:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PortfolioStorageError(
                "unable to create portfolio registry root",
                path_category="root",
            ) from exc
        return self._root

    def validate_portfolio_id(self, portfolio_id: str) -> str:
        if not isinstance(portfolio_id, str) or not is_valid_portfolio_id(portfolio_id):
            raise PortfolioStorageError(
                f"invalid portfolio_id: {portfolio_id!r}",
                portfolio_id=portfolio_id if isinstance(portfolio_id, str) else None,
                path_category="identity",
            )
        return portfolio_id

    def portfolio_dir(self, portfolio_id: str) -> Path:
        safe_id = self.validate_portfolio_id(portfolio_id)
        path = (self._root / safe_id).resolve()
        try:
            path.relative_to(self._root)
        except ValueError as exc:
            raise PortfolioStorageError(
                "portfolio path escapes registry root",
                portfolio_id=safe_id,
                path_category="identity",
            ) from exc
        return path

    def lock_path(self, portfolio_id: str) -> Path:
        return self.portfolio_dir(portfolio_id) / LOCK_FILENAME

    def acquire_write_lock(
        self,
        portfolio_id: str,
        *,
        timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    ) -> PortfolioWriteLock:
        return PortfolioWriteLock(
            self.lock_path(portfolio_id),
            timeout_seconds=timeout_seconds,
        )

    def draft_dir(self, portfolio_id: str) -> Path:
        return self.portfolio_dir(portfolio_id) / DRAFT_DIRNAME

    def draft_manifest_path(self, portfolio_id: str) -> Path:
        return self.draft_dir(portfolio_id) / MANIFEST_FILENAME

    def draft_integrity_path(self, portfolio_id: str) -> Path:
        return self.draft_dir(portfolio_id) / INTEGRITY_FILENAME

    def published_dir(self, portfolio_id: str) -> Path:
        return self.portfolio_dir(portfolio_id) / PUBLISHED_DIRNAME

    def published_version_dir(self, portfolio_id: str, version: int) -> Path:
        return self.published_dir(portfolio_id) / version_dirname(version)

    def published_manifest_path(self, portfolio_id: str, version: int) -> Path:
        return self.published_version_dir(portfolio_id, version) / MANIFEST_FILENAME

    def published_integrity_path(self, portfolio_id: str, version: int) -> Path:
        return self.published_version_dir(portfolio_id, version) / INTEGRITY_FILENAME

    def latest_path(self, portfolio_id: str) -> Path:
        return self.portfolio_dir(portfolio_id) / LATEST_FILENAME

    def _assert_under_root(self, path: Path) -> Path:
        destination = path.resolve()
        try:
            destination.relative_to(self._root)
        except ValueError as exc:
            raise PortfolioStorageError(
                "refusing path outside portfolio registry root",
                path_category="containment",
            ) from exc
        return destination

    def write_bytes_atomic(
        self,
        path: Path,
        payload: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        destination = self._assert_under_root(path)
        parent = destination.parent
        if destination.exists() and not overwrite:
            raise PortfolioStorageError(
                "refusing to overwrite existing portfolio file",
                path_category="write",
            )
        parent.mkdir(parents=True, exist_ok=True)
        fd: Optional[int] = None
        tmp_name: Optional[str] = None
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=str(parent),
            )
            with os.fdopen(fd, "wb") as handle:
                fd = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, destination)
            tmp_name = None
        except OSError as exc:
            raise PortfolioStorageError(
                "atomic write failed for portfolio file",
                path_category="write",
            ) from exc
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if tmp_name is not None and os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    def write_json_atomic(
        self,
        path: Path,
        payload: Any,
        *,
        overwrite: bool = False,
    ) -> None:
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        self.write_bytes_atomic(path, text.encode("utf-8"), overwrite=overwrite)

    def read_bytes(self, path: Path) -> bytes:
        target = self._assert_under_root(path)
        if not target.is_file():
            raise PortfolioStorageError(
                "portfolio file not found",
                path_category="read",
            )
        try:
            return target.read_bytes()
        except OSError as exc:
            raise PortfolioStorageError(
                "unable to read portfolio file",
                path_category="read",
            ) from exc

    def read_json(self, path: Path) -> Any:
        try:
            return json.loads(self.read_bytes(path).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PortfolioStorageError(
                "unable to parse portfolio JSON",
                path_category="read",
            ) from exc

    def list_portfolio_ids(self) -> list[str]:
        self.ensure_root()
        if not self._root.is_dir():
            return []
        ids: list[str] = []
        for child in sorted(self._root.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("."):
                continue
            if not is_valid_portfolio_id(child.name):
                continue
            ids.append(child.name)
        return ids

    def list_published_versions(self, portfolio_id: str) -> list[int]:
        published = self.published_dir(portfolio_id)
        if not published.is_dir():
            return []
        versions: list[int] = []
        for child in published.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            parsed = parse_version_dirname(child.name)
            if parsed is None:
                continue
            if (child / MANIFEST_FILENAME).is_file():
                versions.append(parsed)
        return sorted(versions)
