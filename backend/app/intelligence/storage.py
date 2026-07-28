"""Filesystem storage helpers for the intelligence publishing layer."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from app.intelligence.errors import (
    IntelligenceStorageError,
    RunAlreadyExistsError,
    RunNotFoundError,
)
from app.intelligence.schemas import is_valid_run_id

# backend/app/intelligence/storage.py → parents[2] == backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OUTPUT_ROOT = _BACKEND_ROOT / "outputs"
ENV_OUTPUT_DIR = "INTELLIGENCE_OUTPUT_DIR"
RUNS_DIRNAME = "runs"
ARTIFACTS_DIRNAME = "artifacts"
SNAPSHOTS_DIRNAME = "snapshots"
MANIFEST_FILENAME = "manifest.json"
LATEST_FILENAME = "latest.json"


def resolve_output_root(env: Optional[dict[str, str]] = None) -> Path:
    """Resolve the intelligence output root without creating directories.

    ``INTELLIGENCE_OUTPUT_DIR`` overrides the default ``backend/outputs``.
    Paths are resolved absolutely; relative env values are taken from CWD.
    """
    source = env if env is not None else os.environ
    raw = (source.get(ENV_OUTPUT_DIR) or "").strip()
    if not raw:
        return _DEFAULT_OUTPUT_ROOT.resolve()
    return Path(raw).expanduser().resolve()


def calculate_sha256(path: Path) -> str:
    """Return the lowercase SHA-256 hex digest of a file's bytes."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise IntelligenceStorageError(f"unable to hash file: {path}") from exc
    return digest.hexdigest()


class IntelligenceStorage:
    """Local filesystem layout: ``<root>/runs/<run_id>/manifest.json``."""

    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        self._root = (root if root is not None else resolve_output_root(env)).resolve()

    @property
    def root(self) -> Path:
        return self._root

    @property
    def runs_dir(self) -> Path:
        return self._root / RUNS_DIRNAME

    @property
    def latest_path(self) -> Path:
        return self._root / LATEST_FILENAME

    def ensure_root(self) -> Path:
        try:
            self.runs_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to create intelligence output root: {self._root}"
            ) from exc
        return self._root

    def validate_run_id(self, run_id: str) -> str:
        if not isinstance(run_id, str) or not is_valid_run_id(run_id):
            raise IntelligenceStorageError(f"invalid run_id: {run_id!r}")
        return run_id

    def run_dir(self, run_id: str) -> Path:
        safe_id = self.validate_run_id(run_id)
        path = (self.runs_dir / safe_id).resolve()
        try:
            path.relative_to(self.runs_dir.resolve())
        except ValueError as exc:
            raise IntelligenceStorageError(
                f"run path escapes runs directory: {run_id!r}"
            ) from exc
        return path

    def artifacts_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / ARTIFACTS_DIRNAME

    def ensure_artifacts_dir(self, run_id: str) -> Path:
        directory = self.artifacts_dir(run_id)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to create artifacts directory for {run_id}"
            ) from exc
        return directory

    def snapshots_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / SNAPSHOTS_DIRNAME

    def ensure_snapshots_dir(self, run_id: str) -> Path:
        directory = self.snapshots_dir(run_id)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to create snapshots directory for {run_id}"
            ) from exc
        return directory

    def manifest_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / MANIFEST_FILENAME

    def run_exists(self, run_id: str) -> bool:
        return self.manifest_path(run_id).is_file()

    def create_run_directory(self, run_id: str) -> Path:
        self.ensure_root()
        directory = self.run_dir(run_id)
        if directory.exists():
            raise RunAlreadyExistsError(f"run directory already exists: {run_id}")
        try:
            directory.mkdir(parents=False, exist_ok=False)
        except FileExistsError as exc:
            raise RunAlreadyExistsError(f"run directory already exists: {run_id}") from exc
        except OSError as exc:
            raise IntelligenceStorageError(
                f"unable to create run directory: {run_id}"
            ) from exc
        return directory

    def relative_manifest_path(self, run_id: str) -> str:
        """Return ``runs/<run_id>/manifest.json`` relative to the output root."""
        self.validate_run_id(run_id)
        return f"{RUNS_DIRNAME}/{run_id}/{MANIFEST_FILENAME}"

    def resolve_run_relative_path(self, run_id: str, relative_path: str) -> Path:
        """Resolve a path relative to the run directory with traversal checks."""
        if not relative_path or relative_path.strip() != relative_path:
            raise IntelligenceStorageError("relative_path must be non-empty and unpadded")
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise IntelligenceStorageError(f"unsafe relative_path: {relative_path!r}")
        run_root = self.run_dir(run_id).resolve()
        target = (run_root / candidate).resolve()
        try:
            target.relative_to(run_root)
        except ValueError as exc:
            raise IntelligenceStorageError(
                f"path escapes run directory: {relative_path!r}"
            ) from exc
        return target

    def write_json_atomic(self, path: Path, payload: Any) -> None:
        """Write UTF-8 indented JSON via temp file + ``os.replace``."""
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        self.write_bytes_atomic(path, text.encode("utf-8"), overwrite=True)

    def write_bytes_atomic(
        self,
        path: Path,
        payload: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        """Write raw bytes via temp file + ``os.replace`` inside the output root."""
        destination = path.resolve()
        parent = destination.parent
        try:
            parent.relative_to(self._root)
        except ValueError as exc:
            raise IntelligenceStorageError(
                f"refusing to write outside output root: {destination}"
            ) from exc
        if destination.exists() and not overwrite:
            raise IntelligenceStorageError(
                f"refusing to overwrite existing file: {destination}"
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
            raise IntelligenceStorageError(
                f"atomic write failed for {destination}"
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

    def read_json(self, path: Path) -> Any:
        target = path.resolve()
        try:
            target.relative_to(self._root)
        except ValueError as exc:
            raise IntelligenceStorageError(
                f"refusing to read outside output root: {target}"
            ) from exc
        if not target.is_file():
            raise RunNotFoundError(f"JSON file not found: {target}")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntelligenceStorageError(f"unable to read JSON: {target}") from exc

    def list_run_ids(self) -> list[str]:
        self.ensure_root()
        if not self.runs_dir.is_dir():
            return []
        ids: list[str] = []
        for child in sorted(self.runs_dir.iterdir()):
            if child.is_dir() and is_valid_run_id(child.name) and (child / MANIFEST_FILENAME).is_file():
                ids.append(child.name)
        return ids
