#!/usr/bin/env python3
"""Publish approved Claude Code skills to a public GitHub mirror.

Real, reusable, checked-in sync tool — not one-off shell commands. Mirrors
the strategy of Qin's Codex management-skill/scripts/sync_global_skills.py:
clone the mirror, copy only approved skill folders (excluding local/private
state), run a hard pre-push safety scan for secrets and personal absolute
paths, write .gitignore + README, commit, push, then verify local and
remote content hashes match.

Usage:
  python3 sync_github.py [--repo owner/name] [--skills-dir PATH] [--dry-run]
"""

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_REPOSITORY = "qinbatista/qin-claude-skills"
DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"
APPROVED_SKILL_NAMES = ["auto-model-for-claude"]  # extend as more Claude skills are built

GITIGNORE_TEXT = """.DS_Store
__pycache__/
*.pyc
*.pyo
*.log
.env
.env.*
cache/
outputs/
work/
local/
.venv/
venv/
node_modules/
dist/
build/
.pytest_cache/
"""

EXCLUDED_PARTS = {".git", ".DS_Store", "__pycache__", "cache", "outputs", "work", "local", ".venv", "venv", "node_modules", "dist", "build", ".pytest_cache"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log")

SENSITIVE_NAME_PATTERNS = (".env", ".env.*", "auth.json", "auth*.json", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa", "id_rsa.*", "id_ed25519", "id_ed25519.*", "*credential*.json", "*credentials*.json", "*secret*.json", "*token*.json", "*.sqlite", "*.sqlite3", "*.db")

SECRET_VALUE_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----"),
    re.compile(r'"(?:access_token|refresh_token|id_token|session_token|api_key|secret|password)"\s*:\s*"[^"\n]{12,}"', re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"\n]{12,}['\"]", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[A-Za-z0-9._-]+/"),
)


def run(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def _scan_tree(root):
    files, issues = [], []
    if root.is_symlink():
        return files, [root]
    if not root.exists():
        return files, issues
    for path in root.rglob("*"):
        if path.is_symlink():
            issues.append(path)
            continue
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts) or path.name.endswith(EXCLUDED_SUFFIXES):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix()), issues


def sensitive_name(relative_path):
    lower = relative_path.as_posix().lower()
    name = relative_path.name.lower()
    return any(fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(lower, pattern) for pattern in SENSITIVE_NAME_PATTERNS)


def secret_value_issue(path):
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return ""
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return ""


def public_safety_issues(skill_paths):
    issues = []
    for skill_path in skill_paths:
        files, symlinks = _scan_tree(skill_path)
        for symlink_path in symlinks:
            issues.append(f"{skill_path.name}/{symlink_path.relative_to(skill_path)}: symlink")
        if symlinks:
            continue
        for path in files:
            relative = path.relative_to(skill_path)
            mirror_path = f"{skill_path.name}/{relative.as_posix()}"
            if sensitive_name(relative):
                issues.append(f"{mirror_path}: sensitive filename")
                continue
            matched = secret_value_issue(path)
            if matched:
                issues.append(f"{mirror_path}: secret-like content matched {matched}")
    return issues


def snapshot_hash(skill_paths):
    digest = hashlib.sha256()
    for skill_path in skill_paths:
        digest.update(f"skill:{skill_path.name}\n".encode())
        files, _ = _scan_tree(skill_path)
        for path in files:
            digest.update(f"file:{skill_path.name}/{path.relative_to(skill_path).as_posix()}\n".encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


ENGLISH_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.md"
CHINESE_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.zh.md"


def build_readme(template_path):
    """READMEs are maintained as full templates in assets/readme/ (mirrors
    Codex's management-skill github-readme-template.md approach) so the
    published docs carry real architecture diagrams, the model-switch
    interval table, and measured benchmark data instead of a generated stub."""
    return template_path.read_text(encoding="utf-8")


def stage_repository(skill_paths, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    for skill_path in skill_paths:
        destination = workdir / skill_path.name
        shutil.copytree(skill_path, destination, ignore=shutil.ignore_patterns(*EXCLUDED_PARTS, "*.pyc", "*.pyo", "*.log"))
    (workdir / ".gitignore").write_text(GITIGNORE_TEXT, encoding="utf-8")
    (workdir / "README.md").write_text(build_readme(ENGLISH_README_TEMPLATE), encoding="utf-8")
    (workdir / "README.zh.md").write_text(build_readme(CHINESE_README_TEMPLATE), encoding="utf-8")


def publish(repository, skills_dir, dry_run=False):
    skill_paths = [skills_dir / name for name in APPROVED_SKILL_NAMES if (skills_dir / name / "SKILL.md").exists()]
    missing = [name for name in APPROVED_SKILL_NAMES if not (skills_dir / name / "SKILL.md").exists()]
    if missing:
        raise RuntimeError(f"Approved skill(s) not found locally, refusing to publish an incomplete set: {missing}")

    issues = public_safety_issues(skill_paths)
    if issues:
        raise RuntimeError("Refusing to push private or secret-looking data:\n" + "\n".join(f"- {i}" for i in issues))

    local_hash = snapshot_hash(skill_paths)

    if dry_run:
        return {"status": "dry-run", "skills": [p.name for p in skill_paths], "local_hash": local_hash}

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp) / "repo"
        stage_repository(skill_paths, workdir)
        run(["git", "init", "-q"], cwd=workdir)
        run(["git", "add", "."], cwd=workdir)
        commit = run(["git", "-c", "user.email=sync@local", "-c", "user.name=sync", "commit", "-q", "-m", "Sync skills"], cwd=workdir)
        head = run(["git", "rev-parse", "HEAD"], cwd=workdir).stdout.strip()

        exists = subprocess.run(["gh", "repo", "view", repository], capture_output=True).returncode == 0
        if not exists:
            run(["gh", "repo", "create", repository, "--public", "--source=.", "--remote=origin", "--push"], cwd=workdir)
        else:
            remote_url = run(["gh", "repo", "view", repository, "--json", "sshUrl", "--jq", ".sshUrl"]).stdout.strip()
            run(["git", "remote", "add", "origin", remote_url], cwd=workdir)
            run(["git", "push", "-f", "origin", "HEAD:main"], cwd=workdir)

        remote_head = run(["gh", "api", f"repos/{repository}/commits/main", "--jq", ".sha"]).stdout.strip()

    return {
        "status": "published",
        "repository": repository,
        "skills": [p.name for p in skill_paths],
        "local_hash": local_hash,
        "local_head": head,
        "remote_head": remote_head,
        "head_matches": head == remote_head,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--skills-dir", default=str(DEFAULT_SKILLS_DIR))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = publish(args.repo, Path(args.skills_dir).expanduser(), dry_run=args.dry_run)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
