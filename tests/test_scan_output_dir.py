"""Tests for scan output directory resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from strix.core.paths import (
    configure_scan_output_dir,
    find_run_dir,
    resolve_default_output_dir,
    run_dir_for,
    set_output_dir,
)


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _clear_output_dir_override() -> None:
    set_output_dir(None)
    yield
    set_output_dir(None)


def test_resolve_default_output_dir_for_local_target(tmp_path: Path) -> None:
    repo = tmp_path / "system-erp"
    repo.mkdir()
    targets = [
        {
            "type": "local_code",
            "details": {"target_path": str(repo)},
            "original": str(repo),
        }
    ]
    assert resolve_default_output_dir(targets) == (repo / ".work.soc").resolve()


def test_configure_scan_output_dir_uses_target_work_soc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "system-erp"
    repo.mkdir()
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "local_code",
            "details": {"target_path": str(repo)},
            "original": str(repo),
        }
    ]

    base = configure_scan_output_dir(targets_info=targets)

    assert base == (repo / ".work.soc").resolve()
    assert run_dir_for("demo-run") == repo / ".work.soc" / "strix_runs" / "demo-run"


def test_find_run_dir_prefers_target_work_soc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "system-erp"
    repo.mkdir()
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "local_code",
            "details": {"target_path": str(repo)},
            "original": str(repo),
        }
    ]
    run_dir = repo / ".work.soc" / "strix_runs" / "demo-run"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text("{}", encoding="utf-8")

    found = find_run_dir("demo-run", targets_info=targets)

    assert found == run_dir.resolve()


def test_configure_scan_output_dir_resume_discovers_prior_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "system-erp"
    repo.mkdir()
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "local_code",
            "details": {"target_path": str(repo)},
            "original": str(repo),
        }
    ]
    run_dir = repo / ".work.soc" / "strix_runs" / "demo-run"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text("{}", encoding="utf-8")

    base = configure_scan_output_dir(run_name="demo-run", targets_info=targets)

    assert base == (repo / ".work.soc").resolve()
    assert run_dir_for("demo-run") == run_dir.resolve()
