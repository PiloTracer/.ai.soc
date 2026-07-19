"""Tests for SOC-008-E: SARIF 2.1.0 export of vulnerability reports."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from strix.report.writer import write_sarif


if TYPE_CHECKING:
    from pathlib import Path


def _report(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "vuln-0001",
        "title": "SQL Injection in login form",
        "severity": "high",
        "timestamp": "2026-07-18 00:00:00 UTC",
        "description": "The login form is vulnerable to SQL injection.",
        "target": "https://example.com/login",
    }
    base.update(overrides)
    return base


def test_write_sarif_creates_valid_top_level_shape(tmp_path: Path) -> None:
    write_sarif(tmp_path, [_report()])

    sarif_path = tmp_path / "vulnerabilities.sarif"
    assert sarif_path.exists()

    log = json.loads(sarif_path.read_text(encoding="utf-8"))
    assert log["version"] == "2.1.0"
    assert log["$schema"]
    assert len(log["runs"]) == 1

    run = log["runs"][0]
    assert run["tool"]["driver"]["name"] == "ai-soc"
    assert len(run["results"]) == 1
    assert len(run["tool"]["driver"]["rules"]) == 1


def test_write_sarif_maps_severity_to_sarif_level(tmp_path: Path) -> None:
    reports = [
        _report(title="Critical bug", severity="critical"),
        _report(title="High bug", severity="high"),
        _report(title="Medium bug", severity="medium"),
        _report(title="Low bug", severity="low"),
        _report(title="Info finding", severity="info"),
        _report(title="Unknown severity", severity="not-a-real-severity"),
    ]
    write_sarif(tmp_path, reports)

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    levels = [result["level"] for result in log["runs"][0]["results"]]
    assert levels == ["error", "error", "warning", "note", "note", "warning"]


def test_write_sarif_uses_cwe_as_rule_id_when_present(tmp_path: Path) -> None:
    write_sarif(tmp_path, [_report(cwe="CWE-89")])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    rule_ids = [rule["id"] for rule in log["runs"][0]["tool"]["driver"]["rules"]]
    assert rule_ids == ["CWE-89"]
    assert log["runs"][0]["results"][0]["ruleId"] == "CWE-89"


def test_write_sarif_falls_back_to_title_slug_without_cwe(tmp_path: Path) -> None:
    write_sarif(tmp_path, [_report(title="Reflected XSS in Search")])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    assert log["runs"][0]["results"][0]["ruleId"] == "reflected-xss-in-search"


def test_write_sarif_uses_code_locations_when_present(tmp_path: Path) -> None:
    report = _report(
        code_locations=[{"file": "app/views.py", "start_line": 42, "end_line": 45}],
    )
    write_sarif(tmp_path, [report])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    location = log["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "app/views.py"
    assert location["region"]["startLine"] == 42
    assert location["region"]["endLine"] == 45


def test_write_sarif_falls_back_to_target_url_without_code_locations(tmp_path: Path) -> None:
    write_sarif(tmp_path, [_report(target="https://example.com/login")])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    location = log["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
    assert location["artifactLocation"]["uri"] == "https://example.com/login"
    assert "region" not in location


def test_write_sarif_omits_locations_when_no_target_or_code_locations(tmp_path: Path) -> None:
    report = _report()
    del report["target"]
    write_sarif(tmp_path, [report])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    assert "locations" not in log["runs"][0]["results"][0]


def test_write_sarif_includes_cvss_as_security_severity_property(tmp_path: Path) -> None:
    write_sarif(tmp_path, [_report(cvss=9.8)])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    assert log["runs"][0]["results"][0]["properties"]["security-severity"] == "9.8"


def test_write_sarif_dedupes_rules_sharing_the_same_cwe(tmp_path: Path) -> None:
    reports = [
        _report(title="SQLi in login", cwe="CWE-89"),
        _report(title="SQLi in search", cwe="CWE-89"),
    ]
    write_sarif(tmp_path, reports)

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    assert len(log["runs"][0]["tool"]["driver"]["rules"]) == 1
    assert len(log["runs"][0]["results"]) == 2


def test_write_sarif_handles_empty_report_list(tmp_path: Path) -> None:
    write_sarif(tmp_path, [])

    log = json.loads((tmp_path / "vulnerabilities.sarif").read_text(encoding="utf-8"))
    assert log["runs"][0]["results"] == []
    assert log["runs"][0]["tool"]["driver"]["rules"] == []
