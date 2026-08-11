import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_text import strip_inert_blocks

# --skill-root lets the release gate point this validator at a synthetic known-bad skill and require it to reject one.
skill_root_argument = sys.argv[sys.argv.index("--skill-root") + 1] if "--skill-root" in sys.argv and len(sys.argv) > sys.argv.index("--skill-root") + 1 else ""
skill_root = Path(skill_root_argument).resolve() if skill_root_argument else Path(__file__).resolve().parent.parent
problems = []


def require(condition, message):
    if not condition:
        problems.append(message)


if not (skill_root / "SKILL.md").is_file() or not (skill_root / "references" / "UPSTREAM.json").is_file():
    print("FAIL\n- SKILL.md or references/UPSTREAM.json is missing")
    sys.exit(1)

skill_text = strip_inert_blocks((skill_root / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
frontmatter = re.match(r"---\nname: (?P<name>[a-z0-9-]+)\ndescription: (?P<description>.+)\n---\n", skill_text)
require(frontmatter is not None, "SKILL.md frontmatter must be exactly name + one-line description")
if frontmatter:
    require(frontmatter.group("name") == skill_root.name, f"frontmatter name {frontmatter.group('name')} != directory {skill_root.name}")
    require(len(frontmatter.group("description")) <= 1024, "description exceeds 1024 characters")

known_heading_suffixes = ["", " (after PASS)", " — result first, real, scaled, looped"]
for heading in ["## 1. Connect Obsidian", "## 2. Plan", "## 3. Announce", "## 4. Execute", "## 5. Verify", "## 6. Cache discipline", "## 7. Post-task optimization", "## 8. Record memory", "## 9. Final report"]:
    heading_lines = [line for line in skill_text.splitlines() if line.startswith(heading)]
    require(len(heading_lines) == 1 and heading_lines[0] in [heading + suffix for suffix in known_heading_suffixes], f"SKILL.md must contain exactly one section headed exactly: {heading}")

for reference_path in sorted(set(re.findall(r"references/[A-Za-z0-9/._-]+\.(?:md|json)", skill_text))):
    require((skill_root / reference_path).is_file(), f"SKILL.md references missing file: {reference_path}")

try:
    stamp = json.loads((skill_root / "references" / "UPSTREAM.json").read_text(encoding="utf-8", errors="replace"))
except ValueError as error:
    print(f"FAIL\n- references/UPSTREAM.json is not valid JSON: {error}")
    sys.exit(1)
for field in ["repo", "commit", "files"]:
    require(field in stamp, f"UPSTREAM.json missing field: {field}")
for synced_file in stamp.get("files", []):
    synced_path = skill_root / "references" / synced_file
    require(synced_path.is_file() and synced_path.stat().st_size > 0, f"UPSTREAM.json lists missing/empty file: {synced_file}")
for synced_script in stamp.get("synced_scripts", []):
    require((skill_root / "scripts" / synced_script).is_file(), f"UPSTREAM.json lists missing script: {synced_script}")

require((skill_root / "scripts" / "sync_check.py").is_file(), "scripts/sync_check.py missing")
require((skill_root / "scripts" / "deploy_local.py").is_file(), "scripts/deploy_local.py missing")
require((skill_root / "scripts" / "self_check.py").is_file(), "scripts/self_check.py missing")
require((skill_root / "scripts" / "release_gate.py").is_file(), "scripts/release_gate.py missing")
require((skill_root / "assets" / "retained-capability-catalog.json").is_file(), "assets/retained-capability-catalog.json missing")
require((skill_root / "scripts" / "parity_benchmark.py").is_file(), "scripts/parity_benchmark.py missing")
require((skill_root / "assets" / "idea-parity-benchmark.json").is_file(), "assets/idea-parity-benchmark.json missing")
require((skill_root / "references" / "obsidian-memory.md").is_file(), "references/obsidian-memory.md missing")

if problems:
    print("FAIL")
    for problem in problems:
        print(f"- {problem}")
    sys.exit(1)
print(f"PASS: task-lifecycle skill structure valid ({len(stamp['files'])} synced style files)")
