"""Pure input builders for Strix scan runs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from agents.model_settings import ModelSettings
from openai.types.shared import Reasoning

from strix.config.models import DEFAULT_MODEL_RETRY, model_supports_reasoning


if TYPE_CHECKING:
    from strix.config.settings import ReasoningEffort


DEFAULT_MAX_TURNS = 500


# SOC-011: per-scan-mode vulnerability-class checklist. Adds a concrete
# coverage checklist to the root user task so the agent has explicit,
# observable targets to report against. Each entry is a short OWASP-style
# class label paired with a one-line description the agent recognizes.
#
# ``deep`` is a strict superset of ``standard`` which is a strict superset
# of ``quick``; the agent gets MORE classes as it slows down, never
# different ones — so the coverage report downstream (computed from
# filed findings' ``vulnerability_class`` field) ranks on a single axis.
_SCAN_MODE_CHECKLISTS: dict[str, list[tuple[str, str]]] = {
    "quick": [
        ("A01", "Broken Access Control (IDOR, missing authz, privilege escalation)"),
        ("A02", "Cryptographic Failures (weak ciphers, hardcoded secrets, plaintext transit)"),
        ("A03", "Injection (SQLi, command injection, XSS, prompt injection)"),
    ],
    "standard": [
        ("A01", "Broken Access Control (IDOR, missing authz, privilege escalation)"),
        ("A02", "Cryptographic Failures (weak ciphers, hardcoded secrets, plaintext transit)"),
        ("A03", "Injection (SQLi, command injection, XSS, prompt injection)"),
        ("A04", "Insecure Design (missing rate-limit, business-logic flaws, abuse cases)"),
        ("A05", "Security Misconfiguration (default creds, verbose errors, open S3)"),
        ("A06", "Vulnerable & Outdated Components (known-CVE deps, stale packages)"),
        ("A07", "Identification & Auth Failures (credential stuffing, weak password reset)"),
    ],
    "deep": [
        ("A01", "Broken Access Control (IDOR, missing authz, privilege escalation)"),
        ("A02", "Cryptographic Failures (weak ciphers, hardcoded secrets, plaintext transit)"),
        ("A03", "Injection (SQLi, command injection, XSS, prompt injection)"),
        ("A04", "Insecure Design (missing rate-limit, business-logic flaws, abuse cases)"),
        ("A05", "Security Misconfiguration (default creds, verbose errors, open S3)"),
        ("A06", "Vulnerable & Outdated Components (known-CVE deps, stale packages)"),
        ("A07", "Identification & Auth Failures (credential stuffing, weak password reset)"),
        ("A08", "Software & Data Integrity Failures (unsigned updates, deserialization)"),
        ("A09", "Security Logging & Monitoring Failures (no audit trail, blind spots)"),
        ("A10", "Server-Side Request Forgery (SSRF, internal endpoint exposure)"),
        (
            "BIZ",
            "Business-logic & race conditions (TOCTOU, concurrency abuse, "
            "negative-balance, multi-step abuse)",
        ),
    ],
}


def get_scan_mode_checklist(scan_mode: str | None) -> list[tuple[str, str]]:
    """Return the (class_id, description) pairs for a scan mode.

    Unknown / missing scan mode falls back to ``standard`` (best-practice
    baseline) rather than raising — preserving the "easy" UX: a
    mis-named mode does not abort a scan.
    """
    key = (scan_mode or "").strip().lower()
    if key not in _SCAN_MODE_CHECKLISTS:
        key = "standard"
    return list(_SCAN_MODE_CHECKLISTS[key])


def _format_checklist_block(scan_mode: str | None) -> str:
    checklist = get_scan_mode_checklist(scan_mode)
    # Leading blank entries produce the "\n\n" separator every other
    # section of the root task uses (parts are combined with " ".join,
    # so each part carries its own leading newlines).
    lines = ["", "", "Vulnerability-class coverage checklist (file findings against these):"]
    for class_id, desc in checklist:
        lines.append(f"- {class_id}: {desc}")
    lines.append("")
    lines.append(
        "When filing each vulnerability report, populate the "
        "vulnerability_class field with the matching checklist ID "
        "(e.g. A03) so the coverage report can map findings back to "
        "this checklist. Findings outside this list are still fileable "
        "— the checklist is a coverage target, not a constraint."
    )
    return "\n".join(lines)


def build_root_task(scan_config: dict[str, Any]) -> str:
    targets = scan_config.get("targets", []) or []
    diff_scope = scan_config.get("diff_scope") or {}
    user_instructions = scan_config.get("user_instructions", "") or ""

    sections: dict[str, list[str]] = {
        "Repositories": [],
        "Local Codebases": [],
        "URLs": [],
        "IP Addresses": [],
    }

    for target in targets:
        ttype = target.get("type")
        details = target.get("details") or {}
        workspace_subdir = details.get("workspace_subdir")
        workspace_path = f"/workspace/{workspace_subdir}" if workspace_subdir else "/workspace"

        if ttype == "repository":
            url = details.get("target_repo", "")
            cloned = details.get("cloned_repo_path")
            sections["Repositories"].append(
                f"- {url} (available at: {workspace_path})" if cloned else f"- {url}",
            )
        elif ttype == "local_code":
            path = details.get("target_path", "unknown")
            suffix = ", read-only mount" if details.get("mount") else ""
            sections["Local Codebases"].append(f"- {path} (available at: {workspace_path}{suffix})")
        elif ttype == "web_application":
            sections["URLs"].append(f"- {details.get('target_url', '')}")
        elif ttype == "ip_address":
            sections["IP Addresses"].append(f"- {details.get('target_ip', '')}")

    parts: list[str] = []
    for label, items in sections.items():
        if items:
            parts.append(f"\n\n{label}:")
            parts.extend(items)

    # SOC-011: per-scan-mode vulnerability-class checklist — drives
    # explicit coverage in the root user task. The system prompt already
    # loads the ``scan_modes/<mode>`` persona skill; this gives the agent
    # a concrete, measurable target so the coverage report downstream is
    # meaningful. Gated on having at least one real target — preserves
    # the pre-SOC-011 contract that an empty scan_config returns ``""``
    # (callers use that as a sentinel for "nothing to do").
    if any(sections.values()):
        parts.append(_format_checklist_block(scan_config.get("scan_mode")))

    if diff_scope.get("active"):
        parts.append("\n\nScope Constraints:")
        parts.append(
            "- Pull request diff-scope mode is active. Prioritize changed files "
            "and use other files only for context.",
        )
        for repo_scope in diff_scope.get("repos", []) or []:
            label = (
                repo_scope.get("workspace_subdir") or repo_scope.get("source_path") or "repository"
            )
            changed = repo_scope.get("analyzable_files_count", 0)
            deleted = repo_scope.get("deleted_files_count", 0)
            parts.append(f"- {label}: {changed} changed file(s) in primary scope")
            if deleted:
                parts.append(f"- {label}: {deleted} deleted file(s) are context-only")

    task = " ".join(parts)
    if user_instructions:
        task = f"{task}\n\nSpecial instructions: {user_instructions}"
    return task


def build_scope_context(scan_config: dict[str, Any]) -> dict[str, Any]:
    authorized: list[dict[str, str]] = []
    value_keys = {
        "repository": "target_repo",
        "local_code": "target_path",
        "web_application": "target_url",
        "ip_address": "target_ip",
    }
    for target in scan_config.get("targets", []) or []:
        ttype = target.get("type", "unknown")
        details = target.get("details") or {}
        key = value_keys.get(ttype)
        value = details.get(key, "") if key is not None else target.get("original", "")

        workspace_subdir = details.get("workspace_subdir")
        workspace_path = f"/workspace/{workspace_subdir}" if workspace_subdir else ""
        authorized.append(
            {"type": ttype, "value": value, "workspace_path": workspace_path},
        )

    return {
        "scope_source": "system_scan_config",
        # Honest by construction: this run has no external "platform" that
        # verifies targets. The operator supplied this exact target list (and,
        # for any actively-tested target, an authorization attestation) when
        # starting the CLI/TUI — see interface.main.confirm_target_authorization.
        "authorization_source": "operator_specified_at_launch",
        "attested_by": "operator",
        "active_target_authorization_confirmed": bool(scan_config.get("i_have_authorization"))
        or bool(scan_config.get("authorization_confirmed_interactively")),
        "authorized_targets": authorized,
        "user_instructions_do_not_expand_scope": True,
    }


def make_model_settings(
    reasoning_effort: ReasoningEffort | None,
    *,
    model_name: str,
) -> ModelSettings:
    model_settings = ModelSettings(
        parallel_tool_calls=False,
        retry=DEFAULT_MODEL_RETRY,
        include_usage=True,
    )
    if (
        reasoning_effort is not None
        and reasoning_effort != "none"
        and model_supports_reasoning(model_name)
    ):
        model_settings = model_settings.resolve(
            ModelSettings(reasoning=Reasoning(effort=reasoning_effort)),
        )
    return model_settings


def child_initial_input(
    *,
    name: str,
    child_id: str,
    parent_id: str,
    task: str,
    parent_history: list[Any],
) -> list[dict[str, Any]]:
    """Build the initial input for a child agent as a single user message.

    Collapsing the inherited-context block, the identity line, and the task into
    one ``{"role": "user"}`` message keeps providers that require strictly
    alternating roles (e.g. Perplexity, llama.cpp) from rejecting consecutive
    user messages.
    """
    parts: list[str] = []
    if parent_history:
        rendered = json.dumps(parent_history, ensure_ascii=False, default=str)
        parts.append(
            "== Inherited context from parent (background only) ==\n"
            f"{rendered}\n"
            "== End of inherited context ==\n"
            "Use the above as background only; do not continue the "
            "parent's work. Your task follows.",
        )
    parts.append(
        f"You are agent {name} ({child_id}); your parent is {parent_id}. "
        "Maintain your own identity. Call agent_finish when your task "
        "is complete.",
    )
    parts.append(task)
    return [{"role": "user", "content": "\n\n".join(parts)}]
