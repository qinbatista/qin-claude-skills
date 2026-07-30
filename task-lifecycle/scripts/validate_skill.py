import json
import re
import sys
from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
problems = []


def require(condition, message):
    if not condition:
        problems.append(message)


skill_text = (skill_root / "SKILL.md").read_text()
frontmatter = re.match(r"---\nname: (?P<name>[a-z0-9-]+)\ndescription: (?P<description>.+)\n---\n", skill_text)
require(frontmatter is not None, "SKILL.md frontmatter must be exactly name + one-line description")
if frontmatter:
    require(frontmatter.group("name") == skill_root.name, f"frontmatter name {frontmatter.group('name')} != directory {skill_root.name}")
    require(len(frontmatter.group("description")) <= 1024, "description exceeds 1024 characters")

for heading in ["## 1. Connect Obsidian", "## 2. Plan", "## 3. Announce", "## 4. Execute", "## 5. Verify", "## 6. Cache discipline", "## 7. Post-task optimization", "## 8. Record memory", "## 9. Final report"]:
    require(heading in skill_text, f"SKILL.md missing section: {heading}")

for reference_path in sorted(set(re.findall(r"references/[A-Za-z0-9/._-]+\.(?:md|json)", skill_text))):
    require((skill_root / reference_path).is_file(), f"SKILL.md references missing file: {reference_path}")

stamp = json.loads((skill_root / "references" / "UPSTREAM.json").read_text())
for field in ["repo", "commit", "files"]:
    require(field in stamp, f"UPSTREAM.json missing field: {field}")
for synced_file in stamp.get("files", []):
    synced_path = skill_root / "references" / synced_file
    require(synced_path.is_file() and synced_path.stat().st_size > 0, f"UPSTREAM.json lists missing/empty file: {synced_file}")
for synced_script in stamp.get("synced_scripts", []):
    require((skill_root / "scripts" / synced_script).is_file(), f"UPSTREAM.json lists missing script: {synced_script}")

require((skill_root / "scripts" / "sync_check.py").is_file(), "scripts/sync_check.py missing")
require((skill_root / "references" / "obsidian-memory.md").is_file(), "references/obsidian-memory.md missing")

if problems:
    print("FAIL")
    for problem in problems:
        print(f"- {problem}")
    sys.exit(1)
print(f"PASS: task-lifecycle skill structure valid ({len(stamp['files'])} synced style files)")
