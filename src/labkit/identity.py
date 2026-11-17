"""Run identity: the same code, config, data and seed always hash to the same id."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from labkit.config import LabError


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def glob_digests(root: Path, patterns: list[str]) -> dict[str, str]:
    """Hash every file matched by the patterns, keyed by path relative to root."""
    found: dict[str, str] = {}
    for pattern in patterns:
        matches = [p for p in root.glob(pattern) if p.is_file()]
        if not matches:
            raise LabError(f"pattern matches no files: {pattern}")
        for match in matches:
            found[match.relative_to(root).as_posix()] = file_digest(match)
    return dict(sorted(found.items()))


def run_identity(
    root: Path,
    *,
    spec: str,
    command: list[str],
    config: dict,
    seed: int,
    code: list[str],
    inputs: list[str],
    stage: str = "full",
) -> tuple[str, dict]:
    """Return (run id, the payload that was hashed)."""
    payload = {
        "spec": spec,
        "command": command,
        "config": config,
        "seed": seed,
        "stage": stage,
        "code": glob_digests(root, code),
        "inputs": glob_digests(root, inputs),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12], payload
