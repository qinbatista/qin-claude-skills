#!/usr/bin/env python3
"""Sync the user's global Claude Code skills with GitHub, and render the root READMEs.

Claude Code edition of the Codex `sync_global_skills.py`. Path mapping per PORTING.md:
`~/.codex/skills/` -> `~/.claude/skills/`; remote mirror `qinbatista/qin-codex-skills` ->
`qinbatista/qin-claude-skills`. The approved public mirror set grew from Codex's eight
skills to nine: the same eight ported skills plus the pre-existing `auto-model-for-claude`.

README generation is intentionally static: `render_readme()` copies the durable templates
in `assets/readme/github-readme-template*.md` verbatim. Unlike the Codex original, it does
not scan a sibling skill's internal registry file to fill in a dynamic table -- the nine
skill folders here may not all exist (or agree on an internal API) at any given time, and
the README content this port is asked to produce does not require that dynamic table.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


DEFAULT_REPOSITORY = "qinbatista/qin-claude-skills"
DEFAULT_STATE_FILE = Path.home() / ".claude" / "state" / "management-skill-sync.json"
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
data/cache/
local/
.venv/
venv/
node_modules/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
"""
EXCLUDED_PARTS = {
    ".git",
    ".github",
    ".DS_Store",
    "__pycache__",
    "cache",
    "outputs",
    "work",
    "local",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".log")
SENSITIVE_NAME_PATTERNS = (
    ".env",
    ".env.*",
    "auth.json",
    "auth*.json",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_rsa.*",
    "id_ed25519",
    "id_ed25519.*",
    "*credential*.json",
    "*credentials*.json",
    "*secret*.json",
    "*token*.json",
    "*cookie*.json",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
)
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
    re.compile(r"(?<![A-Za-z0-9])[A-Z]:\\Users\\[^\\\r\n]+\\", re.IGNORECASE),
)
PRIMARY_SKILL_ORDER = [
    "task-analyze-skill",
    "workflow-skill",
    "prompt-skill",
    "code-skill",
    "project-memory-skill",
    "verify-skill",
    "optimization-skill",
    "management-skill",
    "auto-model-for-claude",
]
APPROVED_GLOBAL_SKILL_NAMES = set(PRIMARY_SKILL_ORDER)
ENGLISH_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.md"
CHINESE_README_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "readme" / "github-readme-template.zh.md"


def run_command(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def repository_git_url(repository):
    if repository.startswith(("git@", "ssh://", "https://")):
        return repository
    if shutil.which("gh"):
        return run_command(["gh", "repo", "view", repository, "--json", "sshUrl", "--jq", ".sshUrl"]).stdout.strip()
    return f"git@github.com:{repository}.git"


def clone_repository(repository, sandbox):
    repository_dir = sandbox / "repo"
    run_command(["git", "clone", "--depth", "1", repository_git_url(repository), str(repository_dir)])
    return repository_dir


def repository_head(repository_dir):
    return run_command(["git", "rev-parse", "HEAD"], cwd=repository_dir).stdout.strip()


def repository_timestamp(repository_dir):
    return int(run_command(["git", "log", "-1", "--format=%ct"], cwd=repository_dir).stdout.strip())


def ignored_names(directory, names):
    return {name for name in names if name in EXCLUDED_PARTS or name.endswith(EXCLUDED_SUFFIXES)}


def symlink_issues(paths):
    issues = []
    for root in paths:
        _, root_issues = _scan_tree(Path(root))
        issues.extend(root_issues)
    return sorted(issues, key=lambda path: path.as_posix())


def _scan_tree(root):
    files = []
    issues = []
    if root.is_symlink():
        return files, [root]
    if not root.exists():
        return files, issues
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = directory / entry.name
                if entry.is_symlink():
                    issues.append(path)
                    continue
                relative_path = path.relative_to(root)
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif not any(part in EXCLUDED_PARTS for part in relative_path.parts) and not path.name.endswith(EXCLUDED_SUFFIXES) and entry.is_file(follow_symlinks=False):
                    files.append(path)
    return files, issues


def assert_no_symlinks(paths, label="skill source tree"):
    issues = symlink_issues(paths)
    if issues:
        message = f"Refusing {label} containing symlinks:\n"
        message += "\n".join(f"- {path}" for path in issues)
        raise RuntimeError(message)


def all_skill_directories(skills_dir):
    return sorted(
        [path for path in Path(skills_dir).iterdir() if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").exists()],
        key=lambda path: path.name,
    )


def skill_directories(skills_dir):
    return [Path(skills_dir) / name for name in PRIMARY_SKILL_ORDER if (Path(skills_dir) / name / "SKILL.md").exists()]


def included_files(skill_dir):
    skill_dir = Path(skill_dir)
    files, issues = _scan_tree(skill_dir)
    if issues:
        message = "Refusing skill tree containing symlinks:\n"
        message += "\n".join(f"- {path}" for path in sorted(issues, key=lambda path: path.as_posix()))
        raise RuntimeError(message)
    return sorted(files, key=lambda path: path.relative_to(skill_dir).as_posix())


def sensitive_name(relative_path):
    lower_path = relative_path.as_posix().lower()
    lower_name = relative_path.name.lower()
    return any(fnmatch.fnmatch(lower_name, pattern) or fnmatch.fnmatch(lower_path, pattern) for pattern in SENSITIVE_NAME_PATTERNS)


def secret_value_issue(path):
    try:
        text = path.read_text(errors="ignore")
    except UnicodeDecodeError:
        return ""
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return ""


def public_safety_issues(skill_paths):
    issues = []
    for skill_path in skill_paths:
        files, symlink_paths = _scan_tree(skill_path)
        for symlink_path in symlink_paths:
            try:
                relative_path = symlink_path.relative_to(skill_path)
            except ValueError:
                relative_path = Path(symlink_path.name)
            issues.append(f"{skill_path.name}/{relative_path.as_posix()}: symlink")
        if symlink_paths:
            continue
        for path in sorted(files, key=lambda path: path.relative_to(skill_path).as_posix()):
            relative_path = path.relative_to(skill_path)
            mirror_path = f"{skill_path.name}/{relative_path.as_posix()}"
            if sensitive_name(relative_path):
                issues.append(f"{mirror_path}: sensitive filename")
                continue
            matched_pattern = secret_value_issue(path)
            if matched_pattern:
                issues.append(f"{mirror_path}: secret-like content matched {matched_pattern}")
    return issues


def assert_public_safe(skill_paths):
    issues = public_safety_issues(skill_paths)
    if issues:
        message = "Refusing to push private or secret-looking data to the public skill mirror:\n"
        message += "\n".join(f"- {issue}" for issue in issues)
        raise RuntimeError(message)


def assert_approved_global_skill_set(skill_paths):
    observed_names = {path.name for path in skill_paths}
    unexpected_names = sorted(observed_names - APPROVED_GLOBAL_SKILL_NAMES)
    missing_names = sorted(APPROVED_GLOBAL_SKILL_NAMES - observed_names)
    if unexpected_names or missing_names:
        message = "Refusing to mirror global skills because the approved mirror selection must contain exactly:\n"
        message += "\n".join(f"- {skill_name}" for skill_name in PRIMARY_SKILL_ORDER)
        if unexpected_names:
            message += "\nUnexpected folders found:\n" + "\n".join(f"- {skill_name}" for skill_name in unexpected_names)
        if missing_names:
            message += "\nRequired folders missing:\n" + "\n".join(f"- {skill_name}" for skill_name in missing_names)
        message += "\nUnrelated local skill folders are intentionally ignored and preserved. Check the approved nine before publishing."
        raise RuntimeError(message)


def assert_repository_skill_set(repository_dir):
    observed_names = {path.name for path in all_skill_directories(repository_dir)}
    if observed_names != APPROVED_GLOBAL_SKILL_NAMES:
        unexpected_names = sorted(observed_names - APPROVED_GLOBAL_SKILL_NAMES)
        missing_names = sorted(APPROVED_GLOBAL_SKILL_NAMES - observed_names)
        message = "Refusing to pull because the remote mirror must contain exactly the approved nine skills."
        if unexpected_names:
            message += "\nUnexpected remote skills:\n" + "\n".join(f"- {name}" for name in unexpected_names)
        if missing_names:
            message += "\nMissing remote skills:\n" + "\n".join(f"- {name}" for name in missing_names)
        raise RuntimeError(message)


def snapshot_hash(skill_paths):
    digest = hashlib.sha256()
    for skill_path in skill_paths:
        digest.update(f"skill:{skill_path.name}\n".encode())
        for path in included_files(skill_path):
            digest.update(f"file:{skill_path.name}/{path.relative_to(skill_path).as_posix()}\n".encode())
            digest.update(path.read_bytes())
            digest.update(b"\n")
    return digest.hexdigest()


def latest_local_timestamp(skill_paths):
    latest_timestamp = 0
    for skill_path in skill_paths:
        for path in included_files(skill_path):
            latest_timestamp = max(latest_timestamp, int(path.stat().st_mtime))
    return latest_timestamp


def read_sync_state(state_file):
    if not state_file.exists():
        return {}
    return json.loads(state_file.read_text())


def write_sync_state(state_file, repository, remote_head, local_hash, remote_hash):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "repository": repository,
                "remote_head": remote_head,
                "local_hash": local_hash,
                "remote_hash": remote_hash,
                "synced_at": int(time.time()),
            },
            indent=2,
        )
        + "\n"
    )


def build_readme(language="en"):
    """Render a root README by reading the durable template verbatim.

    Unlike the Codex original, this performs no dynamic marker substitution: the nine
    public skills and the benchmark table are already static content in the template
    itself, so generation never depends on another skill folder's internal registry.
    """
    template_path = CHINESE_README_TEMPLATE if language == "zh" else ENGLISH_README_TEMPLATE
    return template_path.read_text(encoding="utf-8").rstrip() + "\n"


def copy_skill_directory(source_dir, target_dir, preserve_local=False):
    assert_no_symlinks([source_dir], "source skill tree")
    if target_dir.exists() or target_dir.is_symlink():
        assert_no_symlinks([target_dir], "target skill tree")
    local_source = target_dir / "local"
    if preserve_local and local_source.exists():
        assert_no_symlinks([local_source], "preserved local content")
        with tempfile.TemporaryDirectory(prefix="qin-claude-private-local-") as sandbox_name:
            preserved_local = Path(sandbox_name) / "local"
            shutil.copytree(local_source, preserved_local)
            shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir, ignore=ignored_names)
            shutil.copytree(preserved_local, target_dir / "local")
        return
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir, ignore=ignored_names)


def path_differs(source_dir, target_dir):
    if not target_dir.exists():
        return True
    with tempfile.TemporaryDirectory(prefix="qin-claude-skills-diff-") as sandbox_name:
        sandbox = Path(sandbox_name)
        copy_skill_directory(source_dir, sandbox / "source")
        copy_skill_directory(target_dir, sandbox / "target")
        return subprocess.run(["git", "diff", "--no-index", "--quiet", str(sandbox / "source"), str(sandbox / "target")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0


def print_lines(title, lines):
    print(title)
    for line in lines:
        print(f"- {line}")


def mirror_repository_to_local(repository_dir, skills_dir):
    assert_no_symlinks([repository_dir], "repository tree")
    assert_repository_skill_set(repository_dir)
    remote_paths = skill_directories(repository_dir)
    remote_names = {path.name for path in remote_paths}
    changed_names = []
    for path in skill_directories(skills_dir):
        if path.name not in remote_names:
            assert_no_symlinks([path], "local skill tree")
            shutil.rmtree(path)
            changed_names.append(path.name)
    for path in remote_paths:
        # Every skill may accumulate a gitignored `local/` folder with private, skill-owned
        # data (for example auto-model-for-claude's local/ledger.jsonl). Preserve it for all
        # nine skills, not just one, so a pull never destroys private learning data.
        if path_differs(path, skills_dir / path.name):
            copy_skill_directory(path, skills_dir / path.name, preserve_local=True)
            changed_names.append(path.name)
    return changed_names


def remote_changes(repository, skills_dir):
    with tempfile.TemporaryDirectory(prefix="qin-claude-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        remote_by_name = {path.name: path for path in skill_directories(repository_dir)}
        return [name for name in PRIMARY_SKILL_ORDER if name not in remote_by_name or path_differs(remote_by_name[name], skills_dir / name)]


def preuse(repository, skills_dir):
    changed_names = remote_changes(repository, skills_dir)
    if changed_names:
        print_lines("Remote skills differ from local global skills:", changed_names)
        print("Run pull before using or editing these skills unless local edits must be preserved.")
    else:
        print("Remote global skills are already reflected locally.")


def pull(repository, skills_dir):
    with tempfile.TemporaryDirectory(prefix="qin-claude-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        changed_names = mirror_repository_to_local(repository_dir, skills_dir)
        write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(repository_dir)))
        if changed_names:
            print_lines("Copied remote skills into ~/.claude/skills:", changed_names)
        else:
            print("No remote skill changes to copy.")


def prepare_repository_snapshot(repository_dir, skills_dir):
    assert_no_symlinks([repository_dir], "repository tree")
    skill_paths = skill_directories(skills_dir)
    assert_approved_global_skill_set(skill_paths)
    assert_no_symlinks(skill_paths, "approved source skill trees")
    assert_public_safe(skill_paths)
    for path in repository_dir.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    (repository_dir / ".gitignore").write_text(GITIGNORE_TEXT)
    copied_names = []
    (repository_dir / "README.md").write_text(build_readme(language="en"))
    (repository_dir / "README.zh.md").write_text(build_readme(language="zh"))
    for path in skill_paths:
        copy_skill_directory(path, repository_dir / path.name)
        copied_names.append(path.name)
    return copied_names


def push(repository, skills_dir, message, dry_run):
    with tempfile.TemporaryDirectory(prefix="qin-claude-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        copied_names = prepare_repository_snapshot(repository_dir, skills_dir)
        status_text = run_command(["git", "status", "--short"], cwd=repository_dir).stdout.strip()
        if dry_run:
            print_lines("Local skills selected for mirror:", copied_names)
            print(status_text or "No local-to-remote differences.")
            return
        if not status_text:
            write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(skills_dir)))
            print("No global skill changes to push.")
            return
        run_command(["git", "add", "-A"], cwd=repository_dir)
        branch_name = run_command(["git", "branch", "--show-current"], cwd=repository_dir).stdout.strip() or "main"
        run_command(["git", "checkout", "-B", branch_name], cwd=repository_dir)
        run_command(["git", "commit", "-m", message], cwd=repository_dir)
        run_command(["git", "push", "origin", f"HEAD:{branch_name}"], cwd=repository_dir)
        write_sync_state(DEFAULT_STATE_FILE, repository, repository_head(repository_dir), snapshot_hash(skill_directories(skills_dir)), snapshot_hash(skill_directories(skills_dir)))
        print(f"Pushed global skills to {repository}.")


def sync(repository, skills_dir, message):
    with tempfile.TemporaryDirectory(prefix="qin-claude-skills-") as sandbox_name:
        repository_dir = clone_repository(repository, Path(sandbox_name))
        local_paths = skill_directories(skills_dir)
        remote_paths = skill_directories(repository_dir)
        local_hash = snapshot_hash(local_paths)
        remote_hash = snapshot_hash(remote_paths)
        remote_head = repository_head(repository_dir)
        if local_hash == remote_hash:
            write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, local_hash, remote_hash)
            print("Local and remote global skills are already synced.")
            return
        state = read_sync_state(DEFAULT_STATE_FILE)
        local_changed = local_hash != state.get("local_hash")
        remote_changed = remote_head != state.get("remote_head") or remote_hash != state.get("remote_hash")
        if local_changed and not remote_changed:
            print("Local global skills are newer than the last synced state. Pushing to GitHub.")
            push(repository, skills_dir, message, False)
        elif remote_changed and not local_changed:
            print("Remote global skills are newer than the last synced state. Pulling into ~/.claude/skills.")
            changed_names = mirror_repository_to_local(repository_dir, skills_dir)
            write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, snapshot_hash(skill_directories(skills_dir)), remote_hash)
            print_lines("Copied remote skills into ~/.claude/skills:", changed_names)
        elif latest_local_timestamp(local_paths) >= repository_timestamp(repository_dir):
            print("Both sides differ; local files are newest. Pushing to GitHub.")
            push(repository, skills_dir, message, False)
        else:
            print("Both sides differ; remote commit is newest. Pulling into ~/.claude/skills.")
            changed_names = mirror_repository_to_local(repository_dir, skills_dir)
            write_sync_state(DEFAULT_STATE_FILE, repository, remote_head, snapshot_hash(skill_directories(skills_dir)), remote_hash)
            print_lines("Copied remote skills into ~/.claude/skills:", changed_names)


def main():
    parser = argparse.ArgumentParser(description="Sync user global Claude Code skills with GitHub without putting .git in ~/.claude/skills.")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY)
    parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".claude" / "skills")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--message", default="Sync global Claude Code skills")
    subparsers.add_parser("preuse")
    subparsers.add_parser("pull")
    subparsers.add_parser("status")
    render_parser = subparsers.add_parser("render-readme")
    render_parser.add_argument("--output-en", type=Path, required=True)
    render_parser.add_argument("--output-zh", type=Path, required=True)
    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--message", default="Update global Claude Code skills")
    args = parser.parse_args()
    if args.command == "sync":
        sync(args.repo, args.skills_dir, args.message)
    elif args.command == "preuse":
        preuse(args.repo, args.skills_dir)
    elif args.command == "pull":
        pull(args.repo, args.skills_dir)
    elif args.command == "status":
        push(args.repo, args.skills_dir, "Update global Claude Code skills", True)
    elif args.command == "render-readme":
        output_en = args.output_en.expanduser().resolve()
        output_zh = args.output_zh.expanduser().resolve()
        output_en.write_text(build_readme(language="en"), encoding="utf-8")
        output_zh.write_text(build_readme(language="zh"), encoding="utf-8")
        print(f"Rendered public README: {output_en}")
        print(f"Rendered public README (zh): {output_zh}")
    elif args.command == "push":
        push(args.repo, args.skills_dir, args.message, False)


if __name__ == "__main__":
    main()
