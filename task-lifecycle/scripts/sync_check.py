import datetime
import json
import subprocess
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
stamp_path = skill_root / "references" / "UPSTREAM.json"
try:
    stamp = json.loads(stamp_path.read_text(encoding="utf-8", errors="replace"))
except (OSError, ValueError) as error:
    print(f"SKIPPED: references/UPSTREAM.json is unreadable ({error}); cannot compare against upstream")
    sys.exit(0)
if not stamp.get("repo") or not stamp.get("commit"):
    print("SKIPPED: references/UPSTREAM.json has no repo/commit stamp; cannot compare against upstream")
    sys.exit(0)


def remote_head(repo_url):
    try:
        listing = subprocess.run(["git", "ls-remote", repo_url, "HEAD"], capture_output=True, text=True, timeout=10)
    except Exception:
        return None
    if listing.returncode != 0 or not listing.stdout.strip():
        return None
    return listing.stdout.split()[0]


head = remote_head(stamp["repo"])
if head is None:
    print("SKIPPED: upstream unreachable, using local style rules")
    sys.exit(0)
if "--update" in sys.argv:
    stamp["commit"] = head
    stamp["synced_at"] = datetime.date.today().isoformat()
    stamp_path.write_text(json.dumps(stamp, indent=2) + "\n")
    print(f"UPDATED: sync stamp now {head[:12]} ({stamp['synced_at']})")
    sys.exit(0)
if head == stamp["commit"]:
    print(f"SAME: local style rules match upstream {head[:12]}")
    sys.exit(0)
print(f"DRIFTED: upstream {head[:12]} != synced {stamp['commit'][:12]} — re-sync references/ against {stamp['repo']}")
sys.exit(2)
