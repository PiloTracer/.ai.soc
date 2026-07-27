"""Tests for scan output directory resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from strix.core.paths import (
    WORK_SOC_DIR_NAME,
    configure_scan_output_dir,
    find_run_dir,
    output_dir_candidates,
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


# --- SOC-010: URL/IP/repo scans default to <cwd>/.work.soc -----------


def test_configure_scan_output_dir_url_target_defaults_to_cwd_work_soc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """URL-only targets should land under ``<cwd>/.work.soc/strix_runs/...``,
    matching the operator's documented default — not ``<cwd>/strix_runs/...``
    (the pre-SOC-010 behavior)."""
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "web_application",
            "details": {"target_url": "http://localhost:13000"},
            "original": "http://localhost:13000",
        }
    ]

    base = configure_scan_output_dir(targets_info=targets)

    assert base == (tmp_path / WORK_SOC_DIR_NAME).resolve()
    assert run_dir_for("20260721-localhost-13000_27b7") == (
        tmp_path / WORK_SOC_DIR_NAME / "strix_runs" / "20260721-localhost-13000_27b7"
    )


def test_configure_scan_output_dir_explicit_output_dir_overrides_url_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Operator-supplied ``--output-dir`` remains authoritative even for URL
    targets — the SOC-010 default only kicks in when nothing was supplied."""
    monkeypatch.chdir(tmp_path)
    explicit = tmp_path / "custom-reports"
    targets = [
        {
            "type": "web_application",
            "details": {"target_url": "http://localhost:13000"},
            "original": "http://localhost:13000",
        }
    ]

    base = configure_scan_output_dir(
        output_dir=explicit,
        targets_info=targets,
    )

    assert base == explicit.resolve()
    assert run_dir_for("demo-run") == explicit / "strix_runs" / "demo-run"


def test_output_dir_candidates_includes_cwd_work_soc_and_legacy_for_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resume discovery should find runs created under the SOC-010 default
    (``<cwd>/.work.soc/strix_runs/``) AS WELL AS pre-SOC-10 legacy runs
    (``<cwd>/strix_runs/``) so prior URL scans stay resolvable across the
    improvement boundary."""
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "web_application",
            "details": {"target_url": "http://localhost:13000"},
            "original": "http://localhost:13000",
        }
    ]

    candidates = output_dir_candidates(targets_info=targets)

    assert (tmp_path / WORK_SOC_DIR_NAME).resolve() in candidates
    assert tmp_path.resolve() in candidates


def test_find_run_dir_discovers_legacy_cwd_run_for_url_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A URL scan created pre-SOC-10 (at ``<cwd>/strix_runs/<run>``) is still
    resumable after SOC-10 because ``<cwd>`` remains in the candidate list."""
    monkeypatch.chdir(tmp_path)
    targets = [
        {
            "type": "web_application",
            "details": {"target_url": "http://localhost:13000"},
            "original": "http://localhost:13000",
        }
    ]
    legacy_run_dir = tmp_path / "strix_runs" / "20260101-localhost-13000_aaaa"
    legacy_run_dir.mkdir(parents=True)
    (legacy_run_dir / "run.json").write_text("{}", encoding="utf-8")

    found = find_run_dir("20260101-localhost-13000_aaaa", targets_info=targets)

    assert found == legacy_run_dir.resolve()
