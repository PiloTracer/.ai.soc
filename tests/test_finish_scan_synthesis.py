"""Tests for SOC-011 improvement #1 — finish-scan synthesis.

Spec: when a non-interactive Strix scan ends with a text-only final turn
(no ``scan_completed=true``) AND ``ReportState`` has >=1 filed
vulnerability report, ``synthesize_completion_from_findings`` MUST
write a minimal four-section executive report through the normal
``ReportState.update_scan_final_fields`` path so that
``penetration_test_report.md``, ``vulnerabilities.<md|json|csv|sarif>``,
and ``run.json`` are all still produced. The synthesized completion
MUST be tagged in ``run.json`` so a reader can distinguish a real
``finish_scan`` call from the fallback.
"""

from __future__ import annotations

import asyncio
import json
import types
from pathlib import Path
from typing import Any

import pytest

import strix.tools.notes.tools as notes_tools
import strix.tools.todo.tools as todo_tools
from strix.core import runner, runner_completion
from strix.core.agents import AgentCoordinator
from strix.core.paths import get_output_dir, set_output_dir
from strix.core.runner_completion import synthesize_completion_from_findings
from strix.report.state import ReportState, get_global_report_state, set_global_report_state


@pytest.fixture(autouse=True)
def _isolate_report_state(tmp_path: Path) -> None:
    """Each test gets a fresh global ReportState + isolated output dir so
    save_run_data writes artifacts under a tmp path, never the real tree."""
    set_output_dir(tmp_path)
    state = ReportState(run_name="synth-test")
    set_global_report_state(state)
    yield
    set_global_report_state(state)  # restore is harmless; tests don't run parallel
    set_output_dir(None)


def _file_finding(state: ReportState, *, title: str, severity: str) -> str:
    return state.add_vulnerability_report(
        title=title,
        severity=severity,
        description="d",
        impact="i",
        target="t",
        technical_analysis="ta",
        poc_description="poc",
        poc_script_code="print('poc')",
        remediation_steps="rs",
    )


# --- Behavior matrix ------------------------------------------------------


def test_returns_false_when_no_global_report_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # Drop the global state the fixture set up; helper must tolerate missing state.
    monkeypatch.setattr(
        "strix.report.state.get_global_report_state",
        lambda: None,
    )
    assert synthesize_completion_from_findings(scan_id="x") is False


def test_returns_false_when_no_findings_filed() -> None:
    # Inventing an "all clear" report from zero data would be dishonest.
    assert synthesize_completion_from_findings(scan_id="x") is False
    state = get_global_report_state()
    assert state is not None
    assert state.scan_results is None
    assert "synthesized_completion" not in state.run_record


def test_synthesizes_when_filed_findings_exist() -> None:
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="SQLi in login", severity="critical")
    _file_finding(state, title="XSS in /search", severity="high")
    _file_finding(state, title="Missing rate-limit", severity="low")

    ok = synthesize_completion_from_findings(
        scan_id="x",
        final_output="I'm done here.",
    )

    assert ok is True
    assert state.scan_results is not None
    assert state.scan_results["scan_completed"] is True
    assert state.scan_results["success"] is True
    # ...but the same object must disclose that this envelope was
    # reconstructed, so a consumer reading scan_results.success can't
    # mistake a salvaged run for a clean agent termination.
    assert state.scan_results["synthesized"] is True
    # Executive summary must reference real filed counts (3 findings).
    assert state.final_scan_result is not None
    assert "Filed findings: 3" in state.final_scan_result
    assert "SQLi in login" in state.final_scan_result
    assert "XSS in /search" in state.final_scan_result
    # Methodology/tech-analysis/recommendations are explicit placeholders
    # so a reader can tell this synthesis is fallback, not a real finish.
    assert "finish_scan" in state.final_scan_result


def test_records_synthesis_marker_in_run_json() -> None:
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="Anything", severity="medium")

    synthesize_completion_from_findings(scan_id="x", final_output="bye")

    marker = state.run_record.get("synthesized_completion")
    assert isinstance(marker, dict)
    assert marker["source"] == "runner.synthesize_completion_from_findings"
    assert marker["filed_finding_count"] == 1
    assert marker["final_output_preview"] == "bye"
    assert isinstance(marker["synth_id"], str) and len(marker["synth_id"]) == 8


def test_executive_summary_orders_findings_by_severity() -> None:
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="Low finding", severity="low")
    _file_finding(state, title="Critical finding", severity="critical")
    _file_finding(state, title="High finding", severity="high")

    synthesize_completion_from_findings(scan_id="x")
    summary = state.final_scan_result
    assert summary is not None
    # Top findings section must list critical before high before low.
    assert summary.index("Critical finding") < summary.index("High finding")
    assert summary.index("High finding") < summary.index("Low finding")
    assert "1 critical, 1 high, 1 low" in summary


def test_artifacts_are_written_to_run_dir() -> None:
    """End-to-end persistence check: synthesized completion must leave the
    same artifacts on disk a real finish_scan call would (executive report,
    SARIF, vulns json/csv)."""
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="Anything", severity="high")

    synthesize_completion_from_findings(scan_id="x")

    run_dir = state.get_run_dir()
    assert (run_dir / "penetration_test_report.md").exists()
    assert (run_dir / "vulnerabilities.json").exists()
    assert (run_dir / "vulnerabilities.csv").exists()
    assert (run_dir / "vulnerabilities.sarif").exists()
    assert (run_dir / "run.json").exists()
    # run.json must carry the synthetic marker so a reader can tell.
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert record.get("synthesized_completion", {}).get("source") == (
        "runner.synthesize_completion_from_findings"
    )
    assert record.get("status") == "completed"
    assert record.get("scan_results", {}).get("scan_completed") is True


def test_returns_false_when_update_scan_final_fields_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Edge case: if the persistence call raises (e.g. disk full), the
    helper must not crash the runner — return False, log, and let the
    filed findings stand on their own (they were saved at file time)."""
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="A", severity="low")

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("simulated disk full")

    monkeypatch.setattr(state, "update_scan_final_fields", _boom)
    assert synthesize_completion_from_findings(scan_id="x") is False


def test_short_or_missing_final_output_does_not_crash() -> None:
    state = get_global_report_state()
    assert state is not None
    _file_finding(state, title="A", severity="low")
    # None, empty, and very-long inputs should all be tolerated; the
    # final_output_preview is capped at 300 chars.
    assert synthesize_completion_from_findings(scan_id="x", final_output=None) is True
    # Re-file to reset internal synthesized flag and try empty
    state.scan_results = None
    state.final_scan_result = None
    _file_finding(state, title="B", severity="low")
    assert synthesize_completion_from_findings(scan_id="x", final_output="") is True
    state.scan_results = None
    state.final_scan_result = None
    _file_finding(state, title="C", severity="low")
    long_text = "x" * 10_000
    synthesize_completion_from_findings(scan_id="x", final_output=long_text)
    assert state.run_record["synthesized_completion"]["final_output_preview"] == "x" * 300


def test_real_finish_scan_is_not_marked_synthesized() -> None:
    """The disclosure flag must be specific to the fallback path — a
    genuine finish_scan call has to leave ``synthesized`` false or the
    marker means nothing."""
    state = get_global_report_state()
    assert state is not None
    state.update_scan_final_fields(
        executive_summary="es",
        methodology="m",
        technical_analysis="ta",
        recommendations="r",
    )
    assert state.scan_results is not None
    assert state.scan_results["synthesized"] is False


def test_runner_invokes_synthesis_when_scan_ends_without_finish_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Call-site wiring: the deferred import inside
    ``runner.run_strix_scan``'s ``if not scan_completed`` branch must
    actually reach the helper. Unit-testing the helper alone can't catch
    a broken import path or a mis-nested branch."""
    calls: list[dict[str, Any]] = []

    def _spy(**kwargs: Any) -> bool:
        calls.append(kwargs)
        return True

    monkeypatch.setattr(runner_completion, "synthesize_completion_from_findings", _spy)

    _run_scan_with_final_output(monkeypatch, final_output="I have finished looking around.")

    assert len(calls) == 1
    assert calls[0]["final_output"] == "I have finished looking around."
    assert calls[0]["scan_id"] == "scan-synth-test"


def test_runner_skips_synthesis_on_real_finish_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    """The happy path must be untouched: a proper ``scan_completed=true``
    final output must NOT trigger the salvage path."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        runner_completion,
        "synthesize_completion_from_findings",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    _run_scan_with_final_output(monkeypatch, final_output=json.dumps({"scan_completed": True}))

    assert calls == []


def _run_scan_with_final_output(monkeypatch: pytest.MonkeyPatch, *, final_output: Any) -> None:
    """Drive ``runner.run_strix_scan`` far enough to reach the
    post-agent-loop completion branch, stubbing every external
    dependency (sandbox, model, session)."""
    run_dir = get_output_dir() or Path()
    monkeypatch.setattr(runner, "run_dir_for", lambda _scan_id: run_dir)
    monkeypatch.setattr(runner, "runtime_state_dir", lambda _run_dir: run_dir)
    monkeypatch.setattr(runner, "setup_scan_logging", lambda _run_dir: lambda: None)
    monkeypatch.setattr(runner, "set_scan_id", lambda _scan_id: None)

    settings = types.SimpleNamespace(
        llm=types.SimpleNamespace(model="openai/gpt-4o", reasoning_effort="high")
    )
    monkeypatch.setattr(runner, "load_settings", lambda: settings)
    monkeypatch.setattr(runner, "configure_sdk_model_defaults", lambda _settings: None)
    monkeypatch.setattr(
        runner, "uses_chat_completions_tool_schema", lambda _model, _settings: False
    )
    monkeypatch.setattr(todo_tools, "hydrate_todos_from_disk", lambda _state_dir: None)
    monkeypatch.setattr(notes_tools, "hydrate_notes_from_disk", lambda _state_dir: None)

    async def _create_or_reuse(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"client": object(), "session": object(), "caido_client": None}

    async def _cleanup(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(runner.session_manager, "create_or_reuse", _create_or_reuse)
    monkeypatch.setattr(runner.session_manager, "cleanup", _cleanup)
    monkeypatch.setattr(runner, "build_root_task", lambda _scan_config: "task")
    monkeypatch.setattr(runner, "build_scope_context", lambda _scan_config: "")
    monkeypatch.setattr(runner, "make_model_settings", lambda *_a, **_k: object())
    monkeypatch.setattr(runner, "build_strix_agent", lambda **_k: object())
    monkeypatch.setattr(runner, "make_child_factory", lambda **_k: lambda **_kk: object())
    monkeypatch.setattr(runner, "open_agent_session", lambda _root_id, _db: object())

    async def _loop(*_args: Any, **_kwargs: Any) -> Any:
        return types.SimpleNamespace(final_output=final_output)

    monkeypatch.setattr(runner, "run_agent_loop", _loop)

    asyncio.run(
        runner.run_strix_scan(
            scan_config={"targets": [], "scan_mode": "deep"},
            scan_id="scan-synth-test",
            image="img",
            coordinator=AgentCoordinator(),
            interactive=False,
        )
    )


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
