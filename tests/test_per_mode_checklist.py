"""Tests for SOC-011 improvement #2a — per-scan-mode vulnerability-class
checklist injected into the root task.

Spec:
  * `quick` includes only top-3 OWASP classes (A01-A03).
  * `standard` includes A01-A07.
  * `deep` includes A01-A10 plus a business-logic class.
  * Unknown mode falls back to `standard` (no scan abort).
  * Checklist block is present in `build_root_task` output whenever the
    scan_config references a target — meaning the agent always has a
    coverage target.
  * The reference to ``vulnerability_class`` field documents where the
    coverage report downstream will map findings back from.
"""

from __future__ import annotations

import pytest

from strix.core.inputs import (
    _SCAN_MODE_CHECKLISTS,
    _format_checklist_block,
    build_root_task,
    get_scan_mode_checklist,
)


# --- Pure checklist resolution ------------------------------------------


def test_quick_mode_checklist_is_top_three_owasp() -> None:
    checklist = get_scan_mode_checklist("quick")
    assert [cid for cid, _ in checklist] == ["A01", "A02", "A03"]


def test_standard_mode_checklist_covers_a01_to_a07() -> None:
    checklist = get_scan_mode_checklist("standard")
    assert [cid for cid, _ in checklist] == ["A01", "A02", "A03", "A04", "A05", "A06", "A07"]


def test_deep_mode_checklist_adds_a08_a10_and_business_logic() -> None:
    checklist = get_scan_mode_checklist("deep")
    ids = [cid for cid, _ in checklist]
    assert ids[:10] == ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]
    assert ids[-1] == "BIZ"
    assert "Business-logic" in checklist[-1][1]


def test_deep_is_strict_superset_of_standard() -> None:
    std = get_scan_mode_checklist("standard")
    deep = get_scan_mode_checklist("deep")
    assert set(std).issubset(set(deep))


def test_standard_is_strict_superset_of_quick() -> None:
    quick = get_scan_mode_checklist("quick")
    std = get_scan_mode_checklist("standard")
    assert set(quick).issubset(set(std))


@pytest.mark.parametrize("unknown", ["", None, "ultra", "extreme"])
def test_unknown_or_missing_mode_falls_back_to_standard_safe(unknown: str | None) -> None:
    """Bad mode names must never abort a scan; ``standard`` is the safe
    baseline (matches the rest of the framework's permissive-fallback
    convention for non-critical options)."""
    assert get_scan_mode_checklist(unknown) == get_scan_mode_checklist("standard")


@pytest.mark.parametrize(
    "mode,expected", [("QUICK", "quick"), ("Standard", "standard"), ("DEEP", "deep")]
)
def test_mode_lookups_are_case_insensitive(mode: str, expected: str) -> None:
    """Operators (or run.json loaded from prior resumed scans) may pass
    a differently-cased mode — the helper must normalize and still hit
    the right table."""
    assert get_scan_mode_checklist(mode) == get_scan_mode_checklist(expected)


def test_returns_copy_not_internal_reference() -> None:
    """``get_scan_mode_checklist`` MUST return a fresh list — the caller
    (``_format_checklist_block``) iterates it; a returned reference would
    let a future caller accidentally mutate the module-level table."""
    first = get_scan_mode_checklist("deep")
    first.append(("EVIL", "we should not be able to mutate the table"))
    second = get_scan_mode_checklist("deep")
    assert ("EVIL", "we should not be able to mutate the table") not in second


# --- Checklist block formatting -----------------------------------------


def test_checklist_block_lists_every_class_id_and_description() -> None:
    block = _format_checklist_block("deep")
    for class_id, desc in _SCAN_MODE_CHECKLISTS["deep"]:
        assert class_id in block
        assert desc in block


def test_checklist_block_prose_is_clean_for_an_llm_reader() -> None:
    """This text goes straight into the model's root task, so it must
    read as plain prose: balanced parentheses and no RST-style double
    backticks (which the model sees literally, not as formatting)."""
    block = _format_checklist_block("deep")
    assert block.count("(") == block.count(")")
    assert "``" not in block


def test_checklist_block_is_separated_by_a_blank_line() -> None:
    """Every other section of the root task is preceded by a blank line;
    without one the checklist header runs straight into the last target
    bullet."""
    task = build_root_task(_minimal_scan_config("quick"))
    assert "\n\nVulnerability-class coverage checklist" in task


def test_checklist_block_documents_vulnerability_class_field_usage() -> None:
    """The block must instruct the agent to set ``vulnerability_class`` on
    filed findings — otherwise the coverage report downstream has no
    data to map findings to checklist classes."""
    block = _format_checklist_block("standard")
    assert "vulnerability_class" in block
    assert "A03" in block


# --- build_root_task integration ----------------------------------------


def _minimal_scan_config(scan_mode: str) -> dict:
    return {
        "targets": [{"type": "web_application", "details": {"target_url": "http://localhost"}}],
        "scan_mode": scan_mode,
    }


def test_build_root_task_includes_checklist_for_every_mode() -> None:
    for mode in ("quick", "standard", "deep"):
        task = build_root_task(_minimal_scan_config(mode))
        assert "Vulnerability-class coverage checklist" in task
        # Spot-check one class ID per mode.
        for class_id, _ in _SCAN_MODE_CHECKLISTS[mode]:
            assert class_id in task


def test_build_root_task_checklist_grows_with_mode_depth() -> None:
    quick_task = build_root_task(_minimal_scan_config("quick"))
    deep_task = build_root_task(_minimal_scan_config("deep"))

    # Deep task should reference MORE class IDs than quick task.
    def _count(task: str, ids: list[str]) -> int:
        return sum(1 for cid in ids if cid in task)

    quick_ids = [cid for cid, _ in _SCAN_MODE_CHECKLISTS["quick"]]
    deep_ids = [cid for cid, _ in _SCAN_MODE_CHECKLISTS["deep"]]
    assert _count(deep_task, deep_ids) > _count(quick_task, quick_ids)


def test_build_root_task_still_lists_targets_and_instructions() -> None:
    """The checklist must be ADDITIVE — must not displace the existing
    targets/special-instructions content of the root task."""
    cfg = _minimal_scan_config("deep")
    cfg["user_instructions"] = "Focus on authentication flows"
    task = build_root_task(cfg)
    assert "URLs:" in task
    assert "http://localhost" in task
    assert "Focus on authentication flows" in task
    assert "Special instructions:" in task


def test_build_root_task_handles_missing_scan_mode() -> None:
    """A scan_config without ``scan_mode`` must not crash — fall back to
    standard's checklist (the safe baseline)."""
    cfg = {"targets": _minimal_scan_config("standard")["targets"]}
    task = build_root_task(cfg)
    assert "Vulnerability-class coverage checklist" in task
    assert "A07" in task  # standard includes A07


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
