"""Tests for the SOC deploy shell scripts (soc-deploy-basic/-files/-repo).

Covers the SOC-013 contract:
- argument normalization: verbs with/without ``--``, path in any position,
  verb-only forms default to in-place (cwd) — all forms exactly equivalent;
- ``verify`` mode: read-only audit of a deployed target's .cursorrules and
  .work.soc/ skeleton, exit 1 on hard failures;
- fat-client pointer: in-place soc-deploy-files writes SOC_SOURCE at the local
  copy and the deploy self-verifies.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BASIC = REPO_ROOT / "scripts" / "soc-deploy-basic.sh"
FILES = REPO_ROOT / "scripts" / "soc-deploy-files.sh"
REPO = REPO_ROOT / "scripts" / "soc-deploy-repo.sh"
BASH = shutil.which("bash") or "/bin/bash"


def run(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    # Args are test-controlled constants (repo scripts + tmp_path targets).
    return subprocess.run(  # noqa: S603
        [BASH, str(script), *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def deploy_thin(target: Path) -> subprocess.CompletedProcess[str]:
    result = run(BASIC, str(target))
    assert result.returncode == 0, result.stderr + result.stdout
    return result


# --- soc-deploy-basic: deploy + auto-verify ---------------------------------


def test_basic_deploy_creates_block_skeleton_and_verifies(tmp_path: Path) -> None:
    result = deploy_thin(tmp_path)
    cursorrules = (tmp_path / ".cursorrules").read_text()
    assert "SOC_DESIGN_OS_BEGIN" in cursorrules
    assert f"SOC_SOURCE={REPO_ROOT}" in cursorrules
    assert "REPLACE_SOCSOURCE" not in cursorrules
    assert (tmp_path / ".work.soc/context/HANDOFF_SOC.md").is_file()
    assert (tmp_path / ".work.soc/plans/NEXT_SOC.md").is_file()
    assert (tmp_path / ".work.soc/plans/UNKNOWNS_SOC.md").is_file()
    assert "verify: all checks passed" in result.stdout


def test_basic_deploy_is_idempotent_no_overwrite(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    handoff = tmp_path / ".work.soc/context/HANDOFF_SOC.md"
    handoff.write_text("operator content")
    result = deploy_thin(tmp_path)
    assert handoff.read_text() == "operator content"
    assert result.stdout.count("SOC block already present") == 1


# --- soc-deploy-basic: argument normalization --------------------------------


def test_basic_update_forms_are_equivalent(tmp_path: Path) -> None:
    """`path update`, `path --update`, `--update path`, and in-place `update`
    must all succeed and produce the same verified end state."""
    deploy_thin(tmp_path)
    forms = [
        ((str(tmp_path), "update"), None),
        ((str(tmp_path), "--update"), None),
        (("--update", str(tmp_path)), None),
        (("update",), tmp_path),
        (("--update",), tmp_path),
    ]
    for args, cwd in forms:
        result = run(BASIC, *args, cwd=cwd)
        assert result.returncode == 0, f"form {args} failed: {result.stderr}{result.stdout}"
        assert "verify: all checks passed" in result.stdout
        assert "merge candidates" in result.stdout


def test_basic_status_forms(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    for args, cwd in [
        (("status", str(tmp_path)), None),
        (("--status", str(tmp_path)), None),
        ((str(tmp_path), "status"), None),
        (("status",), tmp_path),
    ]:
        result = run(BASIC, *args, cwd=cwd)
        assert result.returncode == 0, f"form {args} failed"
        assert "SOC block: present" in result.stdout
        assert "(reachable)" in result.stdout


def test_basic_rejects_unknown_flag_and_double_path(tmp_path: Path) -> None:
    assert run(BASIC, str(tmp_path), "--frobnicate").returncode == 1
    assert run(BASIC, str(tmp_path), str(tmp_path)).returncode == 1


def test_basic_missing_target_errors() -> None:
    result = run(BASIC, "/nonexistent-path-xyz")
    assert result.returncode == 1
    assert "does not exist" in result.stderr


# --- soc-deploy-basic: verify failure modes ----------------------------------


def test_verify_fails_on_placeholder_soc_source(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    cursorrules = tmp_path / ".cursorrules"
    cursorrules.write_text(
        cursorrules.read_text().replace(f"SOC_SOURCE={REPO_ROOT}", "SOC_SOURCE=REPLACE_SOCSOURCE")
    )
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 1
    assert "REPLACE_SOCSOURCE" in result.stdout


def test_verify_fails_on_unreachable_soc_source(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    cursorrules = tmp_path / ".cursorrules"
    cursorrules.write_text(
        cursorrules.read_text().replace(
            f"SOC_SOURCE={REPO_ROOT}", "SOC_SOURCE=/nonexistent/.ai.soc"
        )
    )
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 1
    assert "SOC_SOURCE unreachable" in result.stdout


def test_verify_fails_on_stale_skill_handles(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    cursorrules = tmp_path / ".cursorrules"
    cursorrules.write_text(cursorrules.read_text() + "\n**Sessions:** `@session-soc`\n")
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 1
    assert "stale skill handles" in result.stdout


def test_verify_ignores_soc_prefixed_handles(tmp_path: Path) -> None:
    """soc-deploy-basic / soc-session must NOT trip the stale-handle check."""
    deploy_thin(tmp_path)
    result = run(BASIC, str(tmp_path), "verify")
    assert result.returncode == 0
    assert "no stale skill handles" in result.stdout


def test_verify_fails_on_missing_work_skeleton(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    (tmp_path / ".work.soc/plans/NEXT_SOC.md").unlink()
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 1
    assert "NEXT_SOC.md missing" in result.stdout


def test_verify_fails_when_nothing_deployed(tmp_path: Path) -> None:
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 1
    assert ".cursorrules missing" in result.stdout


def test_verify_fails_deploy_when_target_goes_stale(tmp_path: Path) -> None:
    """A deploy/update whose end state does not verify must exit non-zero."""
    deploy_thin(tmp_path)
    cursorrules = tmp_path / ".cursorrules"
    cursorrules.write_text(cursorrules.read_text() + "\n`@deploy-files` legacy handle\n")
    result = run(BASIC, str(tmp_path), "--update")
    assert result.returncode == 1
    assert "verification FAILED" in result.stderr


def test_verify_reports_sister_frameworks(tmp_path: Path) -> None:
    result = deploy_thin(tmp_path)
    # Master repo lives next to its sisters: all three must be detected.
    assert "sister framework .ai: installed" in result.stdout
    assert "sister framework .ai.ui: installed" in result.stdout
    assert "sister framework .ai.biz: installed" in result.stdout


def test_verify_tolerates_backtick_quoted_soc_source(tmp_path: Path) -> None:
    """Targets commonly write the pointer inline as `` `SOC_SOURCE=/path` `` —
    the decoration must not break reachability checks."""
    deploy_thin(tmp_path)
    cursorrules = tmp_path / ".cursorrules"
    cursorrules.write_text(
        cursorrules.read_text().replace(f"SOC_SOURCE={REPO_ROOT}", f"`SOC_SOURCE={REPO_ROOT}`")
    )
    result = run(BASIC, "verify", str(tmp_path))
    assert result.returncode == 0, result.stdout
    assert "(reachable, skills registry present)" in result.stdout


# --- soc-deploy-files: fat-client --------------------------------------------


def test_files_inplace_fat_client_self_contained(tmp_path: Path) -> None:
    result = run(FILES, ".", cwd=tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    local_soc = tmp_path / ".ai.soc"
    assert (local_soc / "skills/README.md").is_file()
    # Deploy scripts included so the target can self-verify / self-update.
    assert (local_soc / "scripts/soc-deploy-basic.sh").is_file()
    # SOC_SOURCE points at the LOCAL copy, not the original source.
    cursorrules = (tmp_path / ".cursorrules").read_text()
    assert f"SOC_SOURCE={local_soc}" in cursorrules
    assert "fat-client, self-contained" in result.stdout
    assert "verify: all checks passed" in result.stdout
    # .github and .cursorrules must NOT be copied into the vendored tree.
    assert not (local_soc / ".github").exists()
    assert not (local_soc / ".cursorrules").exists()


def test_files_update_forms_equivalent(tmp_path: Path) -> None:
    run(FILES, ".", cwd=tmp_path)
    for args in [(".", "update"), (".", "--update"), ("--update", ".")]:
        result = run(FILES, *args, cwd=tmp_path)
        assert result.returncode == 0, f"form {args} failed: {result.stderr}{result.stdout}"


def test_files_outbound_copy_does_not_scaffold(tmp_path: Path) -> None:
    target = tmp_path / "outbound"
    target.mkdir()
    result = run(FILES, str(target))
    assert result.returncode == 0, result.stderr + result.stdout
    assert (target / ".ai.soc/skills/README.md").is_file()
    assert not (target / ".work.soc").exists()
    assert not (target / ".cursorrules").exists()


# --- soc-deploy-repo ----------------------------------------------------------


def test_repo_status_forms() -> None:
    for args in [("status",), ("--status",)]:
        result = run(REPO, *args)
        assert result.returncode == 0
        assert "soc-deploy-repo status" in result.stdout


def test_repo_verify_delegates_to_basic(tmp_path: Path) -> None:
    deploy_thin(tmp_path)
    for args in [("verify", str(tmp_path)), (str(tmp_path), "--verify")]:
        result = run(REPO, *args)
        assert result.returncode == 0, f"form {args} failed"
        assert "verify: all checks passed" in result.stdout


def test_repo_archive_deploys_and_verifies(tmp_path: Path) -> None:
    target = tmp_path / "repo-copy"
    result = run(REPO, "archive", str(target))
    assert result.returncode == 0, result.stderr + result.stdout
    assert (target / ".cursorrules").is_file()
    assert (target / ".github").is_dir()
    assert (target / "skills/README.md").is_file()
    assert not (target / ".git").exists()
    assert "verify: all checks passed" in result.stdout


def test_repo_unknown_mode_errors(tmp_path: Path) -> None:
    assert run(REPO, "--frobnicate", str(tmp_path)).returncode == 1


# --- master repo self-verification --------------------------------------------


def test_master_repo_verifies_as_fat_client() -> None:
    result = run(BASIC, "verify", str(REPO_ROOT))
    assert result.returncode == 0, result.stdout
    assert "fat-client local resolution" in result.stdout
