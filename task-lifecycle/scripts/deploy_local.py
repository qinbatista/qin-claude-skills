# Source-first deploy. Supported platforms: macOS, Linux, Windows (pure pathlib + sys.executable, no shell).
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
deploy_root = Path.home() / ".claude" / "skills" / skill_root.name
check_only = "--check" in sys.argv

gate = subprocess.run([sys.executable, str(skill_root / "scripts" / "release_gate.py")], capture_output=True, text=True)
gate_output = (gate.stdout + gate.stderr).strip()
if gate.returncode != 0 or not gate_output:
    print(gate_output or "release gate produced no output — refusing to deploy")
    sys.exit(gate.returncode or 1)
print(gate_output.splitlines()[-1])
if deploy_root.exists() and not deploy_root.is_dir():
    print(f"REFUSED: the deploy target {deploy_root} exists but is not a directory; remove it and rerun")
    sys.exit(1)

source_files = sorted(path for path in skill_root.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
changed_files = [path.relative_to(skill_root) for path in source_files if not (deploy_root / path.relative_to(skill_root)).is_file() or not filecmp.cmp(path, deploy_root / path.relative_to(skill_root), shallow=False)]
deployed_files = sorted(path for path in deploy_root.rglob("*") if path.is_file() and "__pycache__" not in path.parts) if deploy_root.is_dir() else []
stale_files = [path.relative_to(deploy_root) for path in deployed_files if not (skill_root / path.relative_to(deploy_root)).is_file()]

if not check_only:
    for relative_path in changed_files:
        (deploy_root / relative_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_root / relative_path, deploy_root / relative_path)
    for relative_path in stale_files:
        (deploy_root / relative_path).unlink()
        emptied_parent = (deploy_root / relative_path).parent
        while emptied_parent != deploy_root and emptied_parent.is_dir() and not any(emptied_parent.iterdir()):
            emptied_parent.rmdir()
            emptied_parent = emptied_parent.parent

mode = "CHECK" if check_only else "DEPLOYED"
print(f"{mode}: {len(changed_files)} changed, {len(stale_files)} stale -> {deploy_root}")
for relative_path in changed_files:
    print(f"- update {relative_path}")
for relative_path in stale_files:
    print(f"- remove {relative_path}")
sys.exit(2 if check_only and (changed_files or stale_files) else 0)
