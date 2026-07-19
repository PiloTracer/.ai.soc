"""Tests for SOC-008-A: the target-authorization confirmation gate."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from strix.interface.main import confirm_target_authorization
from strix.interface.utils import gated_targets_for_authorization, needs_authorization_confirmation


def _target(target_type: str, **details: Any) -> dict[str, Any]:
    original = details.get("target_url") or details.get("target_ip") or details.get("target_path")
    return {"type": target_type, "details": details, "original": original}


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (_target("web_application", target_url="https://example.com"), True),
        (_target("web_application", target_url="http://192.168.1.5:8080"), True),
        (_target("web_application", target_url="http://localhost:3000"), False),
        (_target("web_application", target_url="http://127.0.0.1:3000"), False),
        (_target("web_application", target_url="http://[::1]:3000"), False),
        (_target("ip_address", target_ip="203.0.113.5"), True),
        (_target("ip_address", target_ip="127.0.0.1"), False),
        (_target("local_code", target_path="/home/user/project"), False),
        (_target("repository", target_repo="https://github.com/user/repo"), False),
    ],
)
def test_needs_authorization_confirmation(target: dict[str, Any], expected: bool) -> None:
    assert needs_authorization_confirmation(target) is expected


def test_needs_authorization_confirmation_handles_malformed_url() -> None:
    target = _target("web_application", target_url="not a valid url")
    # Malformed/unparseable host is treated as non-loopback (fail closed, not open).
    assert needs_authorization_confirmation(target) is True


def test_gated_targets_for_authorization_filters_correctly() -> None:
    targets = [
        _target("local_code", target_path="/repo"),
        _target("web_application", target_url="https://example.com"),
        _target("web_application", target_url="http://localhost:3000"),
        _target("ip_address", target_ip="203.0.113.5"),
    ]
    gated = gated_targets_for_authorization(targets)
    assert [t["original"] for t in gated] == ["https://example.com", "203.0.113.5"]


def _make_args(**overrides: Any) -> argparse.Namespace:
    defaults: dict[str, Any] = {
        "targets_info": [],
        "non_interactive": True,
        "i_have_authorization": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _make_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(prog="soc")


def test_confirm_authorization_noop_when_nothing_gated() -> None:
    args = _make_args(targets_info=[_target("local_code", target_path="/repo")])
    parser = _make_parser()
    confirm_target_authorization(args, parser)
    assert args.authorization_confirmed_interactively is False


def test_confirm_authorization_noop_when_only_loopback_targets() -> None:
    args = _make_args(targets_info=[_target("web_application", target_url="http://localhost:3000")])
    parser = _make_parser()
    confirm_target_authorization(args, parser)
    assert args.authorization_confirmed_interactively is False


def test_confirm_authorization_passes_with_flag_set() -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        i_have_authorization=True,
    )
    parser = _make_parser()
    confirm_target_authorization(args, parser)  # must not raise / exit


def test_confirm_authorization_non_interactive_without_flag_errors() -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        non_interactive=True,
        i_have_authorization=False,
    )
    parser = _make_parser()
    with pytest.raises(SystemExit) as exc_info:
        confirm_target_authorization(args, parser)
    assert exc_info.value.code == 2  # argparse's error() exit code


def test_confirm_authorization_non_interactive_error_names_targets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        non_interactive=True,
        i_have_authorization=False,
    )
    parser = _make_parser()
    with pytest.raises(SystemExit):
        confirm_target_authorization(args, parser)
    stderr = capsys.readouterr().err
    assert "https://example.com" in stderr
    assert "--i-have-authorization" in stderr


def test_confirm_authorization_interactive_accept(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        non_interactive=False,
        i_have_authorization=False,
    )
    parser = _make_parser()
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    confirm_target_authorization(args, parser)
    assert args.authorization_confirmed_interactively is True


def test_confirm_authorization_interactive_decline_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        non_interactive=False,
        i_have_authorization=False,
    )
    parser = _make_parser()
    monkeypatch.setattr("builtins.input", lambda _prompt: "no")
    with pytest.raises(SystemExit) as exc_info:
        confirm_target_authorization(args, parser)
    assert exc_info.value.code == 1


def test_confirm_authorization_interactive_eof_treated_as_decline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _make_args(
        targets_info=[_target("web_application", target_url="https://example.com")],
        non_interactive=False,
        i_have_authorization=False,
    )
    parser = _make_parser()

    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)
    with pytest.raises(SystemExit) as exc_info:
        confirm_target_authorization(args, parser)
    assert exc_info.value.code == 1
