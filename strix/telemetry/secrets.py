"""Secret redaction for log output (SOC-008-C).

``strix/telemetry/logging.py`` writes tool output, LLM traces, and shell
output verbatim to ``{run_dir}/strix.log`` and stderr. Nothing upstream
scrubs secret-shaped substrings before they land there, so an API key or
bearer token that passes through a log call is preserved on disk. ``scrub``
is a narrow, high-confidence, regex-based redactor — not a general secrets
scanner — applied to every log record via ``_SecretScrubFilter`` in
``logging.py``.
"""

from __future__ import annotations

import re


_REDACTED = "[REDACTED]"

# Matches by well-known, high-confidence shape only. False negatives (a
# secret that doesn't match any pattern) are acceptable; false positives on
# ordinary prose are not, so patterns stay specific rather than broad.
_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Authorization headers: keep the scheme, redact the credential.
    re.compile(r"(?i)\b(Authorization\s*:\s*Bearer)\s+\S+"),
    re.compile(r"(?i)\b(Authorization\s*:\s*Basic)\s+\S+"),
    # Provider API key shapes.
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),  # OpenAI-style
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key ID
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),  # GitHub tokens
    # Generic ``key = value`` / ``key: value`` credential assignments, in code,
    # shell output, JSON, or env-style text. Captures the key name so the
    # redacted line stays diagnosable (e.g. ``api_key=[REDACTED]``).
    re.compile(
        r"(?i)\b((?:api[_-]?key|secret|token|password|passwd|pwd)\s*[=:]\s*)"
        r"(['\"]?)([^\s'\",;]+)\2"
    ),
)


def scrub(text: str) -> str:
    """Redact high-confidence secret-shaped substrings from ``text``.

    Idempotent and safe to call on text with no secrets (returned unchanged).
    Only touches ``str`` — callers are responsible for stringifying other
    types before calling this.
    """
    if not text:
        return text
    result = text
    for pattern in _PATTERNS:
        result = pattern.sub(_redact_match, result)
    return result


_KEY_VALUE_GROUP_COUNT = 3  # (prefix, quote, value) — see the generic key=value pattern above


def _redact_match(match: re.Match[str]) -> str:
    groups = match.groups()
    if not groups:
        return _REDACTED
    if len(groups) >= _KEY_VALUE_GROUP_COUNT:
        # Generic ``key = value`` pattern: keep the key name + operator +
        # quote, redact only the value.
        prefix, quote = groups[0], groups[1]
        return f"{prefix}{quote}{_REDACTED}{quote}"
    # Authorization-header patterns: groups are (scheme,) — keep the scheme.
    return f"{groups[0]} {_REDACTED}"
