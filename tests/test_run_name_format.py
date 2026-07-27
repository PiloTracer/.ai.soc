"""Regression tests for ``generate_run_name`` format.

Operator specification (recorded in HANDOFF_SOC SOC-010):

    YYYYMMDD-[target-path or domain:port]-shorthash

Examples (operator-supplied):

    /mnt/work/Projects/system-erp     -> 20260721-system-erp_b38e
    http://localhost:13000            -> 20260721-localhost-13000_27b7

Format parts:
  * date prefix  = ``%Y%m%d`` of ``datetime.now(UTC)`` (8 digits).
  * slug         = lowercased, ``[^a-z0-9]+``→``-`` collapse of the original
    target label the operator typed — so ``localhost:13000`` keeps its
    colon-as-hyphen form, preserving operator-readable identification.
  * separator    = ``_`` (single underscore) between slug and shorthash.
  * shorthash    = ``secrets.token_hex(2)`` = exactly 4 lowercase hex digits.

These tests intentionally hard-pin every part of the format so a future
refactor can't silently change the directory layout the operator relies on.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import pytest

from strix.interface.utils import generate_run_name, rewrite_localhost_targets


_RUN_NAME_PATTERN = re.compile(r"^(?P<date>\d{8})-(?P<slug>[a-z0-9-]+)_(?P<hash>[0-9a-f]{4})$")


def _targets(target_type: str, details: dict[str, Any], original: str) -> list[dict[str, Any]]:
    return [{"type": target_type, "details": details, "original": original}]


def _assert_format(run_name: str) -> dict[str, str]:
    match = _RUN_NAME_PATTERN.match(run_name)
    assert match is not None, (
        f"run name '{run_name}' does not match YYYYMMDD-slug_<4hex>: {run_name!r}"
    )
    groups = match.groupdict()
    assert groups["date"] == datetime.now(UTC).strftime("%Y%m%d")
    return groups


def test_local_code_path_uses_basename_slug() -> None:
    operator_path = "/mnt/work/Projects/system-erp"
    targets = _targets("local_code", {"target_path": operator_path}, operator_path)
    run_name = generate_run_name(targets)
    groups = _assert_format(run_name)
    assert groups["slug"] == "system-erp", (
        f"local_code slug should be the basename of the operator's path "
        f"(operator example: /mnt/work/Projects/system-erp -> system-erp), "
        f"got {groups['slug']!r}"
    )
    assert run_name.startswith(datetime.now(UTC).strftime("%Y%m%d") + "-system-erp_")


def test_web_application_url_uses_netloc_slug() -> None:
    targets = _targets(
        "web_application",
        {"target_url": "http://localhost:13000"},
        "http://localhost:13000",
    )
    run_name = generate_run_name(targets)
    groups = _assert_format(run_name)
    assert groups["slug"] == "localhost-13000", (
        f"web target slug should preserve the operator-typed netloc with "
        f"colon collapsed to hyphen (operator example: localhost-13000), "
        f"got {groups['slug']!r}"
    )
    assert run_name.startswith(datetime.now(UTC).strftime("%Y%m%d") + "-localhost-13000_")


def test_run_name_hash_is_exactly_4_lowercase_hex_chars() -> None:
    # Use a non-"/tmp" synthetic path to avoid ruff S108 (the literal "/tmp"
    # is fine functionally here — we never touch the filesystem — but the
    # linter can't tell).
    synthetic_path = "/var/opt/soc-synthetic-target"
    targets = _targets(
        "local_code",
        {"target_path": synthetic_path},
        synthetic_path,
    )
    for _ in range(20):
        run_name = generate_run_name(targets)
        groups = _assert_format(run_name)
        assert re.fullmatch(r"[0-9a-f]{4}", groups["hash"]), (
            f"shorthash must be exactly 4 lowercase hex digits, got {groups['hash']!r}"
        )


def test_run_name_does_not_differ_when_rewrite_localhost_changes_internal_host() -> None:
    """``rewrite_localhost_targets`` rewrites the networking host
    (``localhost``->``host.docker.internal``) AFTER ``parse_arguments`` runs,
    but ``generate_run_name`` reads ``original`` (the operator-typed URL) for
    identification. The slug therefore still reads ``localhost-13000`` — the
    exact operator-readable identifier — even after the rewrite."""
    targets = _targets(
        "web_application",
        {"target_url": "http://localhost:13000"},
        "http://localhost:13000",
    )
    pre_rewrite = generate_run_name(targets)
    rewrite_localhost_targets(targets, "host.docker.internal")
    post_rewrite = generate_run_name(targets)

    pre_groups = _assert_format(pre_rewrite)
    post_groups = _assert_format(post_rewrite)
    assert pre_groups["slug"] == post_groups["slug"] == "localhost-13000"


def test_repository_url_uses_repo_basename_slug() -> None:
    targets = _targets(
        "repository",
        {"target_repo": "git@github.com:org/widget.git"},
        "git@github.com:org/widget.git",
    )
    run_name = generate_run_name(targets)
    groups = _assert_format(run_name)
    assert groups["slug"] == "widget"


def test_ip_address_target_uses_dot_collapsed_slug() -> None:
    targets = _targets(
        "ip_address",
        {"target_ip": "192.168.1.42"},
        "192.168.1.42",
    )
    run_name = generate_run_name(targets)
    groups = _assert_format(run_name)
    assert groups["slug"] == "192-168-1-42"


def test_empty_targets_info_falls_back_to_pentest_slug() -> None:
    run_name = generate_run_name(None)
    groups = _assert_format(run_name)
    assert groups["slug"] == "pentest"


def test_multi_target_uses_first_target_label() -> None:
    """Per ``_derive_target_label_for_run_name`` the first element of
    ``targets_info`` drives the slug; later targets don't change the run-dir
    path the operator's expected to look under."""
    targets = [
        *_targets(
            "local_code",
            {"target_path": "/mnt/work/Projects/system-erp"},
            "/mnt/work/Projects/system-erp",
        ),
        *_targets(
            "web_application", {"target_url": "http://localhost:13000"}, "http://localhost:13000"
        ),
    ]
    run_name = generate_run_name(targets)
    groups = _assert_format(run_name)
    assert groups["slug"] == "system-erp"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
