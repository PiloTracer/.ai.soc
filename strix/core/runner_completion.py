"""SOC-011 — fallback completion-envelope synthesis.

When a non-interactive Strix scan ends with a text-only final turn that does
not carry ``scan_completed=true``, the runner used to log the condition and
return — silently dropping the executive report, SARIF export, completion
panel, and the ``--fail-on`` exit code, even when the agent had already
filed real vulnerability reports via ``create_vulnerability_report``.

This module salvages that run. The agent's failure to call ``finish_scan``
is still logged as a process error (so the operator can spot the prompt
regression), but the artifact side is recovered by:

1. Pulling the active ``ReportState`` via ``get_global_report_state``.
2. Building a minimal four-section executive summary from the filed
   vulnerability reports (count by severity, top titles).
3. Delegating to ``ReportState.update_scan_final_fields`` so the same
   persistence path is used as a real ``finish_scan`` call —
   ``penetration_test_report.md``, ``vulnerabilities.<md|json|csv>``,
   ``vulnerabilities.sarif``, and ``run.json`` all write the same way.

If ``ReportState`` has no filed vulnerabilities OR is missing, the helper
is a no-op: synthesizing an "all clear" report from zero data would be a
lie, and silently inventing state when none exists would mask a deeper
broken pipeline. Either case still returns ``False`` so the caller (and
unit tests) can distinguish "salvaged" from "nothing to salvage."

This module is intentionally side-effect-light: it only mutates the active
``ReportState`` it locates through ``get_global_report_state``. It does NOT
read files, fork agents, or run anything in the sandbox.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4


logger = logging.getLogger(__name__)


_SEVERITY_ORDER = ("critical", "high", "medium", "low", "info", "unknown")


def _severity_rank(sev: Any) -> int:
    s = str(sev or "unknown").lower().strip()
    try:
        return _SEVERITY_ORDER.index(s)
    except ValueError:
        return _SEVERITY_ORDER.index("unknown")


def _format_executive_summary(reports: list[dict[str, Any]]) -> str:
    by_sev: dict[str, int] = {}
    for r in reports:
        sev = str(r.get("severity") or "unknown").lower()
        by_sev[sev] = by_sev.get(sev, 0) + 1
    ordered = sorted(by_sev.items(), key=lambda kv: _severity_rank(kv[0]))
    counts = ", ".join(f"{count} {sev}" for sev, count in ordered) or "0 findings"
    top = sorted(
        reports,
        key=lambda r: (_severity_rank(r.get("severity")), str(r.get("title", ""))),
    )[:5]
    bullets = "\n".join(
        f"- [{(r.get('severity') or 'unknown').upper()}] {r.get('title', 'Untitled')}" for r in top
    )
    return (
        "Synthesized from filed findings — root agent ended the scan "
        "without calling finish_scan. The findings below were filed via "
        "create_vulnerability_report and have been preserved verbatim.\n\n"
        f"Filed findings: {len(reports)} ({counts}).\n\nTop findings:\n{bullets}"
    )


def synthesize_completion_from_findings(
    *,
    scan_id: str | None = None,
    final_output: Any = None,
) -> bool:
    """Recover a non-interactive scan that ended without ``finish_scan``.

    Returns ``True`` iff a completion envelope was actually written onto
    the active ``ReportState`` (i.e. one exists and has ≥1 filed finding).
    Returns ``False`` — explicitly, not via raise — when there is nothing
    to salvage, so the caller is free to keep going without try/except.
    """
    # Imported here (not top-level) to avoid ``strix.report.state`` ↔
    # ``strix.core.runner`` import cycles; the runner already pulls in
    # ``strix.report`` via its main callers, so a deferred import is
    # cheaper and clearer. Use module-attribute access (not ``from …
    # import …``) so unit tests can monkeypatch ``get_global_report_state``
    # on the source module and have the helper see the patched version.
    # ``noqa: PLC0415`` mirrors the per-file ignores pyproject.toml already
    # grants sibling files (strix/core/runner.py, strix/report/usage.py,
    # strix/config/models.py) for the same load-bearing local-import
    # pattern; using an inline noqa here keeps the protected pyproject.toml
    # untouched (see .cursorrules "Do NOT Modify Unless Explicitly Asked").
    import strix.report.state as _report_state_mod  # noqa: PLC0415

    report_state = _report_state_mod.get_global_report_state()
    if report_state is None:
        logger.warning(
            "synthesize_completion_from_findings(scan_id=%s): no global "
            "ReportState — nothing to synthesize. The scan likely never "
            "reached its first agent turn.",
            scan_id,
        )
        return False

    filed = list(report_state.vulnerability_reports or [])
    if not filed:
        logger.warning(
            "synthesize_completion_from_findings(scan_id=%s): %d filed "
            "findings — refusing to fabricate an 'all clear' report. "
            "Instruct the agent to actually call finish_scan, or fix the "
            "prompt regression that produced this empty run.",
            scan_id,
            len(filed),
        )
        return False

    exec_summary = _format_executive_summary(filed)
    methodology = (
        "Methodology record unavailable — root agent terminated without "
        "calling finish_scan. Filed findings are preserved with their own "
        "PoC descriptions and code locations; consult individual "
        "vulnerability reports for testing detail."
    )
    tech_analysis = (
        f"Consolidated analysis unavailable (root agent ended the scan "
        f"prematurely). {len(filed)} finding(s) were filed individually — "
        f"see vulnerability IDs " + ", ".join(r.get("id", "?") for r in filed) + "."
    )
    recs = (
        "Recommendations could not be consolidated because the root agent "
        "did not emit a finish_scan call. Review each filed finding's "
        "own remediation_steps and retest guidance. Re-run with "
        "``--resume <RUN_NAME> --instruction 'Call finish_scan now'`` to "
        "produce a proper consolidated report."
    )

    # Tag the synthesized record so anyone reading run.json can tell this
    # came from the fallback path, not from a real finish_scan call.
    report_state.run_record.setdefault("synthesized_completion", {})["source"] = (
        "runner.synthesize_completion_from_findings"
    )
    report_state.run_record["synthesized_completion"]["filed_finding_count"] = len(filed)
    report_state.run_record["synthesized_completion"]["final_output_preview"] = str(
        final_output or ""
    )[:300]
    report_state.run_record["synthesized_completion"]["synth_id"] = uuid4().hex[:8]

    try:
        report_state.update_scan_final_fields(
            executive_summary=exec_summary,
            methodology=methodology,
            technical_analysis=tech_analysis,
            recommendations=recs,
            synthesized=True,
        )
    except Exception:
        logger.exception(
            "synthesize_completion_from_findings(scan_id=%s): "
            "update_scan_final_fields raised — failing to write the "
            "synthesized report. Filed findings are still persisted on "
            "disk via create_vulnerability_report's earlier save; the "
            "operator can read vulnerabilities.* directly.",
            scan_id,
        )
        return False

    logger.info(
        "synthesize_completion_from_findings(scan_id=%s): synthesized a "
        "completion envelope from %d filed finding(s). Executive report, "
        "SARIF, vulnerabilities.*, and run.json were all written via the "
        "normal ReportState path.",
        scan_id,
        len(filed),
    )
    return True
