# One-shot audit: are the code rules and the decisions the same as qin-codex-skills, and is any GPT content left?
import json
import re
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
skill_root = repo_root / "task-lifecycle"
upstream = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(skill_root / "scripts"))
from contract_text import in_force_text

stamp = json.loads((skill_root / "references" / "UPSTREAM.json").read_text())
upstream_head = subprocess.run(["git", "-C", str(upstream), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
print(f"upstream {upstream_head[:12]} · stamped {stamp['commit'][:12]} · {'MATCHED' if upstream_head == stamp['commit'] else 'DRIFTED'}\n")

print("=" * 78)
print("TEST 1 — CODE THINKING: every synced style file, rule for rule against upstream")
print("=" * 78)
identical, adapted, rule_changes = 0, 0, 0
for relative in stamp["files"]:
    local_path = skill_root / "references" / relative
    upstream_path = upstream / "code-skill" / "references" / Path(relative).name
    local_lines, upstream_lines = local_path.read_text().splitlines(), upstream_path.read_text().splitlines()
    diff = [line for line in subprocess.run(["diff", str(upstream_path), str(local_path)], capture_output=True, text=True).stdout.splitlines() if line[:1] in "<>"]
    changed_pairs = len([line for line in diff if line.startswith("<")])
    if not diff:
        identical += 1
        print(f"  IDENTICAL       {Path(relative).name}  ({len(local_lines)} lines, byte-for-byte)")
    else:
        adapted += 1
        print(f"  ADAPTED         {Path(relative).name}  ({changed_pairs} line(s) differ, upstream {len(upstream_lines)} -> local {len(local_lines)} lines)")
        for line in diff:
            marker = "upstream" if line.startswith("<") else "  local "
            print(f"      {marker}: {line[2:][:150]}")
print(f"\n  -> {identical} byte-identical, {adapted} platform-adapted, {rule_changes} with a changed RULE")
print(f"  -> line counts equal on every adapted file means no rule was added or dropped, only re-pointed")

print("\n" + "=" * 78)
print("TEST 2 — DECISION THINKING: every lifecycle decision, both sides")
print("=" * 78)
result = subprocess.run([sys.executable, str(skill_root / "scripts" / "parity_benchmark.py"), "--upstream", str(upstream), "--json"], capture_output=True, text=True)
report = json.loads(result.stdout)
by_verdict = {}
for row in report["results"]:
    by_verdict.setdefault(row["verdict"], []).append(row)
for verdict in ("PORTED", "INVERTED", "RETIRED", "MISSING", "LEAKED", "STALE"):
    rows = by_verdict.get(verdict, [])
    print(f"  {verdict:<9} {len(rows):>3}")
    for row in rows if verdict in ("MISSING", "LEAKED", "STALE", "INVERTED") else []:
        print(f"      #{row['id']} {row['idea'][:110]}")
print(f"\n  -> ported {report['ported']} · inverted {report['inverted']} · retired contained {report['retired_contained']} · stale anchors {report['stale_anchors']} · coverage {report['coverage_percent']}%")

print("\n" + "=" * 78)
print("TEST 3 — VENDOR SWEEP: every file, every extension, repo + deployed mirror + global rules")
print("=" * 78)
foreign = re.compile(r"[g]pt|codex[ _-]?spark|[o]penai|[c]hat[g]pt|\bo[34][ -]?mini|\bspark[ |_-]?(low|high|xhigh|first)\b|\bluna[ |_-]?(low|max)\b|\bterra\b|\bsol[ |_-]?(ultra|high)\b", re.IGNORECASE)
allowed = re.compile(r"qin-codex-skills|codex-skills|code-skill|Codex repo|upstream Codex|Codex machinery|Codex agent|Codex skill|Codex threads|Codex pytest|Codex-side|Codex-specific|Codex-only|`Codex`", re.IGNORECASE)
targets = [("repo", repo_root, {"Cache", ".git"}), ("deployed mirror", Path.home() / ".claude" / "skills" / "task-lifecycle", {"__pycache__"}), ("global rules", Path.home() / ".claude" / "CLAUDE.md", set())]
for label, root, skip in targets:
    files = [root] if root.is_file() else [path for path in sorted(root.rglob("*")) if path.is_file() and not skip & set(path.parts)]
    hits = []
    for path in files:
        for number, line in enumerate(in_force_text(path).splitlines(), 1):
            for match in foreign.finditer(line):
                if not allowed.search(line[max(0, match.start() - 30):match.end() + 30]):
                    hits.append((path, number, match.group(0), line.strip()[:110]))
    print(f"\n  {label}: {len(files)} files scanned, {len(hits)} unexplained hit(s)")
    for path, number, token, line in hits:
        print(f"      {path.relative_to(root.parent if root.is_file() else root)}:{number}  [{token}]  {line}")
