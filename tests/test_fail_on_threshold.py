"""Tests for SOC-008-F: the ``--fail-on`` severity-threshold exit code."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from strix.interface.main import parse_arguments, should_fail_on_severity


if TYPE_CHECKING:
    from pathlib import Path


# --- should_fail_on_severity: pure comparison logic -------------------------


def test_none_threshold_never_fails() -> None:
    assert should_fail_on_severity(["critical", "high", "low"], "none") is False


def test_none_threshold_never_fails_even_with_no_findings() -> None:
    assert should_fail_on_severity([], "none") is False


def test_any_threshold_fails_on_any_finding_regardless_of_severity() -> None:
    assert should_fail_on_severity(["info"], "any") is True
    assert should_fail_on_severity(["low"], "any") is True
    assert should_fail_on_severity(["critical"], "any") is True


def test_any_threshold_matches_pre_soc_008_f_behavior_with_no_findings() -> None:
    # This is the exact condition the old code checked directly:
    # `if report_state.vulnerability_reports: sys.exit(2)`.
    assert should_fail_on_severity([], "any") is False


@pytest.mark.parametrize(
    ("severities", "threshold", "expected"),
    [
        (["high", "medium"], "critical", False),
        (["critical"], "critical", True),
        (["medium", "low"], "high", False),
        (["high"], "high", True),
        (["critical", "low"], "high", True),  # one finding meets the bar
        (["low"], "medium", False),
        (["medium"], "medium", True),
        (["info"], "low", False),
        (["low"], "low", True),
    ],
)
def test_threshold_comparison_matrix(severities: list[str], threshold: str, expected: bool) -> None:
    assert should_fail_on_severity(severities, threshold) is expected


def test_unrecognized_severity_never_causes_a_false_failure() -> None:
    assert should_fail_on_severity(["not-a-real-severity"], "critical") is False


def test_severity_comparison_is_case_insensitive() -> None:
    assert should_fail_on_severity(["CRITICAL"], "critical") is True


def test_empty_severities_never_fails_at_any_threshold() -> None:
    for threshold in ("critical", "high", "medium", "low", "any", "none"):
        assert should_fail_on_severity([], threshold) is False


# --- --fail-on CLI wiring ----------------------------------------------------


def test_fail_on_defaults_to_any_preserving_prior_behavior(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "argv", ["soc", "--target", str(tmp_path), "-n"])
    args = parse_arguments()
    assert args.fail_on == "any"


def test_fail_on_accepts_a_valid_choice(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys, "argv", ["soc", "--target", str(tmp_path), "-n", "--fail-on", "critical"]
    )
    args = parse_arguments()
    assert args.fail_on == "critical"


def test_fail_on_rejects_an_invalid_choice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["soc", "--target", str(tmp_path), "-n", "--fail-on", "extreme"]
    )
    with pytest.raises(SystemExit) as exc_info:
        parse_arguments()
    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
