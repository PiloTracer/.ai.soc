"""Tests for SOC-011 #3a — ``verified`` / ``verification_evidence`` /
``vulnerability_class`` fields on filed vulnerability reports.

Spec:
  * New findings filed through ``add_vulnerability_report`` carry
    ``verified`` (default null when not supplied) in the persisted dict.
  * ``vulnerability_class`` is uppercased when supplied.
  * ``verification_evidence`` is included only when supplied.
  * Pre-SOC-011 findings hydrated from disk on resume (without these
    fields) keep working — the absence is preserved, not synthesized.

The create_vulnerability_report TOOL validation (``verified=False``
requires ``verification_evidence``) is covered by a direct call to its
private ``_do_create`` here so we don't need a full SDK RunContext.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import pytest

from strix.core.paths import set_output_dir
from strix.report.state import ReportState, set_global_report_state
from strix.tools.reporting.tool import _do_create


if TYPE_CHECKING:
    from pathlib import Path


_VALID_BREAKDOWN = {
    "attack_vector": "N",
    "attack_complexity": "L",
    "privileges_required": "N",
    "user_interaction": "N",
    "scope": "U",
    "confidentiality": "H",
    "integrity": "H",
    "availability": "H",
}


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path: Path) -> None:
    set_output_dir(tmp_path)
    state = ReportState(run_name="vc-test")
    set_global_report_state(state)
    yield
    set_output_dir(None)


def _file_finding(state: ReportState, **kwargs: Any) -> dict[str, Any]:
    rid = state.add_vulnerability_report(
        title=kwargs.pop("title", "T"),
        severity=kwargs.pop("severity", "high"),
        description="d",
        impact="i",
        target="t",
        technical_analysis="ta",
        poc_description="pd",
        poc_script_code="print(1)",
        remediation_steps="rs",
        **kwargs,
    )
    return next(r for r in state.vulnerability_reports if r["id"] == rid)


# --- ReportState.add_vulnerability_report --------------------------------


def test_report_state_default_verified_is_null_preserving_legacy_absence() -> None:
    """Pre-SOC-011 in-memory findings didn't have ``verified`` at all.
    SOC-011 makes it first-class but the persisted dict now carries
    ``verified: null`` so the SARIF writer can distinguish "agent
    asserted true" from "agent did not assert" (see test_sarif_export
    test_write_sarif_omits_verified_property_when_field_absent)."""
    state = ReportState(run_name="x")
    report = _file_finding(state)
    assert "verified" in report
    assert report["verified"] is None


def test_report_state_records_verified_true() -> None:
    state = ReportState(run_name="x")
    report = _file_finding(state, verified=True, verification_evidence="HTTP 200")
    assert report["verified"] is True
    assert report["verification_evidence"] == "HTTP 200"


def test_report_state_records_verified_false_with_evidence() -> None:
    state = ReportState(run_name="x")
    report = _file_finding(
        state,
        verified=False,
        verification_evidence="attempted PoC; response signature mismatch",
    )
    assert report["verified"] is False
    assert report["verification_evidence"] == "attempted PoC; response signature mismatch"


def test_report_state_uppercases_vulnerability_class() -> None:
    """When the agent supplies ``vulnerability_class='a03'`` we persist
    ``A03`` so the coverage report doesn't fragment ``a03`` and ``A03``
    into two bins."""
    state = ReportState(run_name="x")
    report = _file_finding(state, vulnerability_class="a03")
    assert report["vulnerability_class"] == "A03"


def test_report_state_omits_vulnerability_class_when_not_supplied() -> None:
    state = ReportState(run_name="x")
    report = _file_finding(state)
    assert "vulnerability_class" not in report
    assert "verification_evidence" not in report


def test_report_state_vulnerability_class_strips_whitespace() -> None:
    state = ReportState(run_name="x")
    report = _file_finding(state, vulnerability_class="  A05  ")
    assert report["vulnerability_class"] == "A05"


def test_report_state_persisted_json_round_trips_new_fields() -> None:
    """End-to-end: what gets written to vulnerabilities.json on disk must
    carry the new fields so a resumed scan re-reads them verbatim."""
    state = ReportState(run_name="x")
    set_global_report_state(state)
    _file_finding(
        state,
        verified=False,
        verification_evidence="attempted; mismatch",
        vulnerability_class="A07",
    )
    state.save_run_data()
    run_dir = state.get_run_dir()
    with (run_dir / "vulnerabilities.json").open(encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["verified"] is False
    assert data[0]["verification_evidence"] == "attempted; mismatch"
    assert data[0]["vulnerability_class"] == "A07"


# --- create_vulnerability_report tool validation --------------------------


def _call_do_create(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "t",
        "description": "d",
        "impact": "i",
        "target": "t",
        "technical_analysis": "ta",
        "poc_description": "pd",
        "poc_script_code": "print(1)",
        "remediation_steps": "rs",
        "cvss_breakdown": dict(_VALID_BREAKDOWN),
        "endpoint": None,
        "method": None,
        "cve": None,
        "cwe": None,
        "code_locations": None,
    }
    base.update(overrides)
    return asyncio.run(_do_create(**base))


def test_tool_do_create_defaults_verified_to_not_asserted() -> None:
    """The default must be "agent did not assert", NOT an optimistic
    true. A bare ``verified: true`` that came from a default — with no
    evidence behind it — reads to a SARIF consumer as a reproduction
    claim, which invites over-trust in an unexamined finding."""
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create()
    assert result["success"] is True
    filed = state.vulnerability_reports[-1]
    assert filed["verified"] is None
    assert "verification_evidence" not in filed


def test_tool_do_create_rejects_verified_false_without_evidence() -> None:
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(verified=False, verification_evidence="")
    assert result["success"] is False
    assert any("verification_evidence is REQUIRED" in e for e in result["errors"])


def test_tool_do_create_rejects_verified_true_without_evidence() -> None:
    """Asserting verification in the positive direction needs evidence
    too — an unauditable claim is worse than no claim."""
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(verified=True)
    assert result["success"] is False
    assert any(
        "verification_evidence is REQUIRED when verified=true" in e for e in result["errors"]
    )


def test_tool_do_create_accepts_verified_true_with_evidence() -> None:
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(
        verified=True,
        verification_evidence="GET /admin as user_b returned HTTP 200 with admin payload",
    )
    assert result["success"] is True
    filed = state.vulnerability_reports[-1]
    assert filed["verified"] is True
    assert "HTTP 200" in filed["verification_evidence"]


def test_tool_do_create_rejects_vulnerability_class_starting_with_digit() -> None:
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(vulnerability_class="3A")
    assert result["success"] is False
    assert any("must start with a letter" in e for e in result["errors"])


def test_tool_do_create_accepts_verified_false_with_evidence() -> None:
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(
        verified=False,
        verification_evidence="attempted PoC; response signature did not match",
    )
    assert result["success"] is True
    filed = state.vulnerability_reports[-1]
    assert filed["verified"] is False
    assert "did not match" in filed["verification_evidence"]


def test_tool_do_create_accepts_free_form_vulnerability_class() -> None:
    """Beyond OWASP-style IDs, agents may use free-form class names like
    ``BUSINESS_LOGIC`` — letter-first must be the only constraint."""
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(vulnerability_class="business-logic-abuse")
    assert result["success"] is True
    filed = state.vulnerability_reports[-1]
    assert filed["vulnerability_class"] == "BUSINESS-LOGIC-ABUSE"


def test_tool_do_create_omits_vulnerability_class_when_none() -> None:
    state = ReportState(run_name="x")
    set_global_report_state(state)
    result = _call_do_create(vulnerability_class=None)
    assert result["success"] is True
    filed = state.vulnerability_reports[-1]
    assert "vulnerability_class" not in filed


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
