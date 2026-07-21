"""Tests for SOC-008-C: secret-scrubbing log filter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from strix.telemetry.logging import setup_scan_logging
from strix.telemetry.secrets import scrub


if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("text", "leaked_substring"),
    [
        ("Authorization: Bearer sk-abcdef0123456789ABCDEF", "sk-abcdef0123456789ABCDEF"),
        ("Authorization: Basic dXNlcjpwYXNzd29yZA==", "dXNlcjpwYXNzd29yZA=="),
        ("key is sk-proj-abcdefghijklmnopqrstuvwx", "sk-proj-abcdefghijklmnopqrstuvwx"),
        ("aws key AKIAIOSFODNN7EXAMPLE in the output", "AKIAIOSFODNN7EXAMPLE"),
        ("token ghp_abcdefghijklmnopqrstuvwxyz012345", "ghp_abcdefghijklmnopqrstuvwxyz012345"),
        ('api_key="sk-live-abcdefghijklmnop"', "sk-live-abcdefghijklmnop"),
        ("api_key=abcdef0123456789", "abcdef0123456789"),
        ("password: SuperSecretValue1", "SuperSecretValue1"),
        ("SECRET=topsecretvalue", "topsecretvalue"),
    ],
)
def test_scrub_redacts_secret_shaped_substrings(text: str, leaked_substring: str) -> None:
    result = scrub(text)
    assert leaked_substring not in result
    assert "[REDACTED]" in result


@pytest.mark.parametrize(
    "text",
    [
        "The user's password field was empty.",
        "Testing for CWE-798 hard-coded credentials in the target's config.",
        "Sent 42 requests to the API, 3 returned 401.",
        "",
        "Nothing sensitive here at all.",
    ],
)
def test_scrub_does_not_touch_ordinary_text(text: str) -> None:
    assert scrub(text) == text


def test_scrub_preserves_key_name_for_diagnosability() -> None:
    result = scrub("api_key=sk-abcdefghijklmnopqrst")
    assert result.startswith("api_key=")
    assert "[REDACTED]" in result


def test_scrub_is_idempotent() -> None:
    once = scrub("Authorization: Bearer sk-abcdefghijklmnopqrst")
    twice = scrub(once)
    assert once == twice


def test_setup_scan_logging_redacts_secret_in_written_file(tmp_path: Path) -> None:
    teardown = setup_scan_logging(tmp_path, debug=True)
    try:
        logging.getLogger("strix.telemetry.test_logging_scrub").info(
            "Authorization: Bearer sk-abcdefghijklmnopqrst"
        )
    finally:
        teardown()

    contents = (tmp_path / "strix.log").read_text(encoding="utf-8")
    assert "sk-abcdefghijklmnopqrst" not in contents
    assert "[REDACTED]" in contents


def test_setup_scan_logging_preserves_ordinary_message_and_percent_args(tmp_path: Path) -> None:
    teardown = setup_scan_logging(tmp_path, debug=True)
    try:
        logging.getLogger("strix.telemetry.test_logging_scrub").info(
            "Scan started for target=%s mode=%s", "example.com", "deep"
        )
    finally:
        teardown()

    contents = (tmp_path / "strix.log").read_text(encoding="utf-8")
    assert "Scan started for target=example.com mode=deep" in contents


def test_setup_scan_logging_is_idempotent_for_same_run_dir(tmp_path: Path) -> None:
    first = setup_scan_logging(tmp_path, debug=True)
    second = setup_scan_logging(tmp_path, debug=True)
    try:
        logging.getLogger("strix.telemetry.test_logging_scrub").error("scan failed once")
        assert first is not second
        logging.getLogger("strix.telemetry.test_logging_scrub").error("scan failed twice")
    finally:
        second()
        first()

    contents = (tmp_path / "strix.log").read_text(encoding="utf-8")
    assert contents.count("scan failed once") == 1
    assert contents.count("scan failed twice") == 1
