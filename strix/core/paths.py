"""Run directory path helpers."""

# Modified from Strix original. See NOTICE and LICENSE for details.

from __future__ import annotations

from pathlib import Path


RUNS_DIR_NAME = "strix_runs"
RUNTIME_STATE_DIR_NAME = ".state"
RUN_RECORD_FILENAME = "run.json"

_output_dir_override: list[Path | None] = [None]


def set_output_dir(path: Path | None) -> None:
    """Override the base directory for all run directories.

    When set, ``run_dir_for()`` uses this instead of ``Path.cwd()``.
    Pass ``None`` to clear the override.
    """
    _output_dir_override[0] = path


def run_dir_for(run_name: str, *, cwd: Path | None = None) -> Path:
    base = cwd or _output_dir_override[0] or Path.cwd()
    return base / RUNS_DIR_NAME / run_name


def runtime_state_dir(run_dir: Path) -> Path:
    return run_dir / RUNTIME_STATE_DIR_NAME


def run_record_path(run_dir: Path) -> Path:
    return run_dir / RUN_RECORD_FILENAME
