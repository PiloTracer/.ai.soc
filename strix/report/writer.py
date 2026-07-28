"""Artifact writers for Strix scan reports."""

from __future__ import annotations

import csv
import json
import logging
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strix.core.paths import run_record_path


logger = logging.getLogger(__name__)

# Public: reused by strix.interface.main for --fail-on severity-threshold comparisons
# (SOC-008-F), so this stays the single source of truth for severity ranking.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

# SOC-008-E: SARIF 2.1.0, for CI / GitHub code scanning ingestion. Verified
# against the minimum shape GitHub's code-scanning ingestion requires
# (docs.github.com/.../sarif-support + the OASIS SARIF 2.1.0 spec,
# checked 2026-07-18): ``$schema`` + ``version`` +
# ``runs[].tool.driver.{name,rules[]}`` + ``runs[].results[]``.
_SARIF_SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
_SARIF_VERSION = "2.1.0"
_SARIF_TOOL_NAME = "ai-soc"

_SEVERITY_TO_SARIF_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def read_run_record(run_dir: Path) -> dict[str, Any]:
    path = run_record_path(run_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"run.json at {path} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise TypeError(f"run.json at {path} is not an object")
    return data


def write_run_record(run_dir: Path, run_record: dict[str, Any]) -> None:
    _atomic_write_text(
        run_record_path(run_dir),
        json.dumps(run_record, ensure_ascii=False, indent=2, default=str),
    )


def write_executive_report(run_dir: Path, final_scan_result: str) -> None:
    path = run_dir / "penetration_test_report.md"
    with path.open("w", encoding="utf-8") as f:
        f.write("# Security Penetration Test Report\n\n")
        f.write(f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"{final_scan_result}\n")
    logger.info("Saved final penetration test report to: %s", path)


def write_vulnerabilities(
    run_dir: Path,
    vulnerability_reports: list[dict[str, Any]],
    saved_vuln_ids: set[str],
) -> int:
    vuln_dir = run_dir / "vulnerabilities"
    vuln_dir.mkdir(exist_ok=True)

    new_reports = [r for r in vulnerability_reports if r["id"] not in saved_vuln_ids]

    for report in new_reports:
        (vuln_dir / f"{report['id']}.md").write_text(
            render_vulnerability_md(report),
            encoding="utf-8",
        )
        saved_vuln_ids.add(report["id"])

    sorted_reports = sorted(
        vulnerability_reports,
        key=lambda r: (SEVERITY_ORDER.get(r["severity"], 5), r["timestamp"]),
    )
    csv_path = run_dir / "vulnerabilities.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["id", "title", "severity", "timestamp", "file"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for report in sorted_reports:
            writer.writerow(
                {
                    "id": report["id"],
                    "title": report["title"],
                    "severity": report["severity"].upper(),
                    "timestamp": report["timestamp"],
                    "file": f"vulnerabilities/{report['id']}.md",
                },
            )

    _atomic_write_text(
        run_dir / "vulnerabilities.json",
        json.dumps(vulnerability_reports, ensure_ascii=False, indent=2, default=str),
    )

    if new_reports:
        logger.info(
            "Saved %d new vulnerability report(s) to: %s",
            len(new_reports),
            vuln_dir,
        )
    logger.info("Updated vulnerability index: %s", csv_path)
    return len(new_reports)


def _sarif_rule_id(report: dict[str, Any]) -> str:
    cwe = report.get("cwe")
    if cwe:
        return str(cwe)
    slug = re.sub(r"[^a-z0-9]+", "-", str(report.get("title", "")).lower()).strip("-")
    return slug or "untitled-finding"


def _sarif_locations(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Physical locations for a SARIF result.

    Prefers ``code_locations`` (white-box findings with file/line evidence);
    falls back to a bare ``artifactLocation`` on ``target`` (black-box web
    findings with no source line) so every finding still gets *a* location.
    """
    locations: list[dict[str, Any]] = []
    code_locations: list[dict[str, Any]] = report.get("code_locations") or []
    for loc in code_locations:
        file_path = loc.get("file")
        if not file_path:
            continue
        physical_location: dict[str, Any] = {"artifactLocation": {"uri": file_path}}
        region: dict[str, Any] = {}
        if loc.get("start_line") is not None:
            region["startLine"] = loc["start_line"]
        if loc.get("end_line") is not None:
            region["endLine"] = loc["end_line"]
        if region:
            physical_location["region"] = region
        locations.append({"physicalLocation": physical_location})

    if locations:
        return locations

    target = report.get("target")
    if target:
        return [{"physicalLocation": {"artifactLocation": {"uri": str(target)}}}]
    return []


def write_sarif(run_dir: Path, vulnerability_reports: list[dict[str, Any]]) -> None:
    """Write ``vulnerabilities.sarif`` (SARIF 2.1.0) alongside the existing
    ``.md``/``.csv``/``.json`` artifacts, for CI / GitHub code scanning
    ingestion. No new dependency — a hand-built dict serialized via
    ``json.dumps``, same pattern as the other writers in this module.
    """
    rules_by_id: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for report in vulnerability_reports:
        rule_id = _sarif_rule_id(report)
        rules_by_id.setdefault(
            rule_id,
            {
                "id": rule_id,
                "shortDescription": {"text": str(report.get("title", "Untitled finding"))},
            },
        )

        severity = str(report.get("severity", "medium")).lower()
        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": _SEVERITY_TO_SARIF_LEVEL.get(severity, "warning"),
            "message": {"text": str(report.get("description") or report.get("title") or "")},
        }
        locations = _sarif_locations(report)
        if locations:
            result["locations"] = locations
        # SOC-011 #3b: carry ``verified`` / ``vulnerability_class`` /
        # ``verification_evidence`` into SARIF result.properties so a CI
        # consumer (GitHub code scanning, DefectDojo, etc.) can filter
        # unverified findings or split by class. The properties dict is
        # built incrementally — pre-SOC-011 writes only put
        # ``security-severity`` here; we just add the new keys.
        properties: dict[str, Any] = {}
        cvss = report.get("cvss")
        if cvss is not None:
            properties["security-severity"] = str(cvss)
        if "verified" in report and report["verified"] is not None:
            # SARIF properties values must be primitives; bool is fine.
            properties["verified"] = bool(report["verified"])
        if report.get("vulnerability_class"):
            properties["vulnerability_class"] = str(report["vulnerability_class"])
        if report.get("verification_evidence"):
            properties["verification_evidence"] = str(report["verification_evidence"])
        if properties:
            result["properties"] = properties
        results.append(result)

    sarif_log = {
        "$schema": _SARIF_SCHEMA_URI,
        "version": _SARIF_VERSION,
        "runs": [
            {
                "tool": {"driver": {"name": _SARIF_TOOL_NAME, "rules": list(rules_by_id.values())}},
                "results": results,
            },
        ],
    }

    sarif_path = run_dir / "vulnerabilities.sarif"
    _atomic_write_text(sarif_path, json.dumps(sarif_log, ensure_ascii=False, indent=2, default=str))
    logger.info("Updated SARIF export: %s", sarif_path)


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def render_vulnerability_md(report: dict[str, Any]) -> str:  # noqa: PLR0912, PLR0915
    lines: list[str] = [
        f"# {report.get('title', 'Untitled Vulnerability')}\n",
        f"**ID:** {report.get('id', 'unknown')}",
        f"**Severity:** {report.get('severity', 'unknown').upper()}",
        f"**Found:** {report.get('timestamp', 'unknown')}",
    ]

    metadata: list[tuple[str, Any]] = [
        ("Target", report.get("target")),
        ("Endpoint", report.get("endpoint")),
        ("Method", report.get("method")),
        ("CVE", report.get("cve")),
        ("CWE", report.get("cwe")),
    ]
    cvss = report.get("cvss")
    if cvss is not None:
        metadata.append(("CVSS", cvss))
    for label, value in metadata:
        if value:
            lines.append(f"**{label}:** {value}")

    lines.append("")
    lines.append("## Description\n")
    lines.append(report.get("description") or "No description provided.")
    lines.append("")

    if report.get("impact"):
        lines.append("## Impact\n")
        lines.append(str(report["impact"]))
        lines.append("")

    if report.get("technical_analysis"):
        lines.append("## Technical Analysis\n")
        lines.append(str(report["technical_analysis"]))
        lines.append("")

    if report.get("poc_description") or report.get("poc_script_code"):
        lines.append("## Proof of Concept\n")
        if report.get("poc_description"):
            lines.append(str(report["poc_description"]))
            lines.append("")
        if report.get("poc_script_code"):
            lines.append("```")
            lines.append(str(report["poc_script_code"]))
            lines.append("```")
            lines.append("")

    if report.get("code_locations"):
        lines.append("## Code Analysis\n")
        for i, loc in enumerate(report["code_locations"]):
            file_ref = loc.get("file", "unknown")
            line_ref = ""
            if loc.get("start_line") is not None:
                if loc.get("end_line") and loc["end_line"] != loc["start_line"]:
                    line_ref = f" (lines {loc['start_line']}-{loc['end_line']})"
                else:
                    line_ref = f" (line {loc['start_line']})"
            lines.append(f"**Location {i + 1}:** `{file_ref}`{line_ref}")
            if loc.get("label"):
                lines.append(f"  {loc['label']}")
            if loc.get("snippet"):
                lines.append(f"  ```\n  {loc['snippet']}\n  ```")
            if loc.get("fix_before") or loc.get("fix_after"):
                lines.append("\n  **Suggested Fix:**")
                lines.append("```diff")
                if loc.get("fix_before"):
                    lines.extend(f"- {ln}" for ln in str(loc["fix_before"]).splitlines())
                if loc.get("fix_after"):
                    lines.extend(f"+ {ln}" for ln in str(loc["fix_after"]).splitlines())
                lines.append("```")
            lines.append("")

    if report.get("remediation_steps"):
        lines.append("## Remediation\n")
        lines.append(str(report["remediation_steps"]))
        lines.append("")

    return "\n".join(lines)
