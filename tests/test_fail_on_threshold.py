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


# --- SOC-011 #3c: ``--exclude-unverified`` --------------------------------


def test_exclude_unverified_defaults_off_preserving_prior_behavior(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "argv", ["soc", "--target", str(tmp_path), "-n"])
    args = parse_arguments()
    assert args.exclude_unverified is False


def test_exclude_unverified_cli_flag_parses_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["soc", "--target", str(tmp_path), "-n", "--exclude-unverified"]
    )
    args = parse_arguments()
    assert args.exclude_unverified is True


def test_exclude_unverified_off_counts_every_filing_default_severity_any() -> None:
    """Default behavior: every filed finding (verified or not) counts.
    Preserves pre-SOC-011 / pre-#3c behavior — no flag means no filter."""
    assert (
        should_fail_on_severity(
            ["critical", "low"], "any", exclude_unverified=False, verified_flags=[True, False]
        )
        is True
    )


def test_exclude_unverified_on_with_all_verified_keeps_counting() -> None:
    """If every finding is verified=True, the filter is a no-op: count
    every filing exactly as before."""
    assert (
        should_fail_on_severity(["critical"], "any", exclude_unverified=True, verified_flags=[True])
        is True
    )


def test_exclude_unverified_on_filters_out_unverified_findings() -> None:
    """2 findings: one verified critical, one unverified critical. With
    filter ON and threshold 'critical', should still fail because the
    verified critical meets the bar."""
    assert (
        should_fail_on_severity(
            ["critical", "critical"],
            "critical",
            exclude_unverified=True,
            verified_flags=[True, False],
        )
        is True
    )


def test_exclude_unverified_on_returns_false_when_all_findings_are_unverified() -> None:
    """Operator opted into the filter; every finding is verified=false.
    Don't fail the build — the operator explicitly asked for verified
    findings only, and there are none."""
    assert (
        should_fail_on_severity(
            ["critical", "high"],
            "any",
            exclude_unverified=True,
            verified_flags=[False, False],
        )
        is False
    )


def test_exclude_unverified_on_treats_missing_verified_as_unverified() -> None:
    """Pre-SOC-011 findings re-loaded from disk on resume lack the
    ``verified`` field — they must be treated as unverified when the
    operator opts into the filter, never silently counted."""
    assert (
        should_fail_on_severity(
            ["critical"],
            "critical",
            exclude_unverified=True,
            verified_flags=[None],
        )
        is False
    )


def test_exclude_unverified_on_with_threshold_high_filters_unverified_critical() -> None:
    """A single finding: critical, unverified. Threshold=high. Without
    filter: fails (critical ≤ high). With filter+unverified: does not fail."""
    assert (
        should_fail_on_severity(
            ["critical"], "high", exclude_unverified=False, verified_flags=[False]
        )
        is True
    )
    assert (
        should_fail_on_severity(
            ["critical"], "high", exclude_unverified=True, verified_flags=[False]
        )
        is False
    )


def test_exclude_unverified_with_none_threshold_never_fails_regardless_of_state() -> None:
    """--fail-on none means no findings count, period — exclude_unverified
    is irrelevant. The two flags are independent."""
    assert (
        should_fail_on_severity(
            ["critical"], "none", exclude_unverified=True, verified_flags=[False]
        )
        is False
    )
    assert (
        should_fail_on_severity(
            ["critical"], "none", exclude_unverified=False, verified_flags=[True]
        )
        is False
    )


def test_exclude_unverified_on_but_verified_flags_missing_returns_false_safe() -> None:
    """If the caller forgets to pass ``verified_flags`` with the filter
    ON, we must NOT fabricate verification — fail closed (return False).
    This is the safe direction: never fail the build on unverified
    findings when the operator asked to filter."""
    assert should_fail_on_severity(["critical"], "critical", exclude_unverified=True) is False


def test_exclude_unverified_on_with_shorter_verified_flags_returns_false_safe() -> None:
    """Pairing mismatch → safest behavior is exclude-all (fail closed
    on the build-exit decision)."""
    assert (
        should_fail_on_severity(
            ["critical", "high"],
            "any",
            exclude_unverified=True,
            verified_flags=[True],  # one fewer than severities
        )
        is False
    )


def test_exclude_unverified_on_with_longer_verified_flags_returns_false_safe() -> None:
    """The mismatch guard must cover BOTH directions. A too-long list
    used to slip past the length check and hit ``zip(strict=True)``,
    raising ValueError out of a function documented as total."""
    assert (
        should_fail_on_severity(
            ["critical"],
            "any",
            exclude_unverified=True,
            verified_flags=[True, True],  # one more than severities
        )
        is False
    )


def test_exclude_unverified_signature_accepts_legacy_severities_only_call() -> None:
    """Existing callers that don't pass the new keyword args must keep
    working unchanged — backward-compatible API guarantee."""
    assert should_fail_on_severity(["critical"], "critical") is True
    assert should_fail_on_severity([], "any") is False
    assert should_fail_on_severity(["low"], "critical") is False
