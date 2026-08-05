import subprocess
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
scripts_root = skill_root / "scripts"
check_only = "--check-only" in sys.argv


def run_script(script_name, *arguments):
    return subprocess.run([sys.executable, str(scripts_root / script_name), *arguments], capture_output=True, text=True)


structure = run_script("validate_skill.py")
print(f"structure: {'PASS' if structure.returncode == 0 else 'FAIL'} — {(structure.stdout or structure.stderr).strip().splitlines()[0]}")

platform_gate = run_script("skill_platform_check.py", "check", "--skills-root", str(skill_root.parent), "--baseline", str(skill_root / "assets" / "skill-platform-baseline.json"))
print(f"platform: {'PASS' if platform_gate.returncode == 0 else 'FAIL'} — {(platform_gate.stdout + platform_gate.stderr).strip() or 'no new findings'}")

style_sync = run_script("sync_check.py")
print(f"style-sync: {(style_sync.stdout or style_sync.stderr).strip()}")

mirror = run_script("deploy_local.py", "--check")
mirror_ok = mirror.returncode == 0
mirror_tail = mirror.stdout.strip().splitlines()[-1] if mirror.stdout.strip() else "no output"
repaired = False
if mirror.returncode == 2 and structure.returncode == 0 and not check_only:
    print("mirror: STALE — repairing from source")
    repair = run_script("deploy_local.py")
    print(repair.stdout.strip())
    recheck = run_script("deploy_local.py", "--check")
    mirror_ok, repaired = recheck.returncode == 0, True
    mirror_tail = recheck.stdout.strip().splitlines()[-1] if recheck.stdout.strip() else mirror_tail
mirror_state = "PASS" if mirror_ok else ("STALE (run without --check-only to repair)" if check_only and mirror.returncode == 2 else "FAIL")
print(f"mirror: {mirror_state}{' (repaired)' if repaired else ''} — {mirror_tail}")

healthy = structure.returncode == 0 and platform_gate.returncode == 0 and mirror_ok
repo_broken_hint = " — a broken repo is repaired through the SKILL.md section 5 fix loop, not by this script" if structure.returncode != 0 or platform_gate.returncode != 0 else ""
print(f"SELF-CHECK: {'PASS' if healthy else 'FAIL' + repo_broken_hint}")
sys.exit(0 if healthy else 1)
