import datetime
import json
import subprocess
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
stamp_path = skill_root / "references" / "UPSTREAM.json"
stamp = json.loads(stamp_path.read_text())


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
