"""Run directory path helpers."""

# Modified from Strix original. See NOTICE and LICENSE for details.

from __future__ import annotations

from pathlib import Path
from typing import Any


RUNS_DIR_NAME = "strix_runs"
RUNTIME_STATE_DIR_NAME = ".state"
RUN_RECORD_FILENAME = "run.json"
WORK_SOC_DIR_NAME = ".work.soc"

_output_dir_override: list[Path | None] = [None]


def set_output_dir(path: Path | None) -> None:
    """Override the base directory for all run directories.

    When set, ``run_dir_for()`` uses this instead of ``Path.cwd()``.
    Pass ``None`` to clear the override.
    """
    _output_dir_override[0] = path.resolve() if path is not None else None


def get_output_dir(*, cwd: Path | None = None) -> Path:
    """Return the active scan output base (parent of ``strix_runs/``)."""
    base = _output_dir_override[0] or cwd or Path.cwd()
    return base.resolve()


def run_dir_for(run_name: str, *, cwd: Path | None = None) -> Path:
    base = cwd or _output_dir_override[0] or Path.cwd()
    return base / RUNS_DIR_NAME / run_name


def runtime_state_dir(run_dir: Path) -> Path:
    return run_dir / RUNTIME_STATE_DIR_NAME


def run_record_path(run_dir: Path) -> Path:
    return run_dir / RUN_RECORD_FILENAME


def output_base_for_run_dir(run_dir: Path) -> Path:
    """Return the output base directory that contains ``run_dir``."""
    if run_dir.name == RUNS_DIR_NAME:
        return run_dir.parent.resolve()
    if run_dir.parent.name == RUNS_DIR_NAME:
        return run_dir.parent.parent.resolve()
    return run_dir.parent.resolve()


def resolve_default_output_dir(targets_info: list[dict[str, Any]] | None) -> Path | None:
    """Infer ``<local-target>/.work.soc`` when ``--output-dir`` is omitted."""
    for target in targets_info or []:
        if target.get("type") != "local_code":
            continue
        details = target.get("details") or {}
        path_str = details.get("target_path")
        if not path_str:
            continue
        base = Path(path_str).expanduser().resolve()
        if base.is_file():
            base = base.parent
        return base / WORK_SOC_DIR_NAME
    return None


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    return ordered


def output_dir_candidates(
    *,
    targets_info: list[dict[str, Any]] | None = None,
    explicit_output_dir: Path | str | None = None,
) -> list[Path]:
    """Ordered bases to search when locating a prior run directory."""
    candidates: list[Path] = []
    if explicit_output_dir is not None:
        candidates.append(Path(explicit_output_dir))
    default = resolve_default_output_dir(targets_info)
    if default is not None:
        candidates.append(default)
    candidates.append(Path.cwd())
    return _dedupe_paths(candidates)


def find_run_dir(
    run_name: str,
    *,
    targets_info: list[dict[str, Any]] | None = None,
    explicit_output_dir: Path | str | None = None,
) -> Path | None:
    """Locate an existing run directory across known output bases."""
    for base in output_dir_candidates(
        targets_info=targets_info,
        explicit_output_dir=explicit_output_dir,
    ):
        run_dir = base / RUNS_DIR_NAME / run_name
        if run_record_path(run_dir).exists() or run_dir.exists():
            return run_dir.resolve()
    return None


def configure_scan_output_dir(
    *,
    output_dir: Path | str | None = None,
    run_name: str | None = None,
    targets_info: list[dict[str, Any]] | None = None,
) -> Path:
    """Resolve and activate where ``strix_runs/<run-name>/`` (and ``strix.log``) live."""
    if output_dir is not None:
        base = Path(output_dir).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)
        set_output_dir(base)
        return base

    if run_name:
        found = find_run_dir(run_name, targets_info=targets_info)
        if found is not None:
            base = output_base_for_run_dir(found)
            set_output_dir(base)
            return base

    default = resolve_default_output_dir(targets_info)
    if default is not None:
        default.mkdir(parents=True, exist_ok=True)
        set_output_dir(default)
        return default

    base = Path.cwd().resolve()
    set_output_dir(base)
    return base
