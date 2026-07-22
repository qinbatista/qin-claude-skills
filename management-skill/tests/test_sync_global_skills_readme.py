import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_global_skills.py"
MODULE_SPEC = importlib.util.spec_from_file_location("sync_global_skills", MODULE_PATH)
sync_global_skills = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(sync_global_skills)

MANAGEMENT_SKILL_ROOT = Path(__file__).resolve().parents[1]
README_ASSET_DIR = MANAGEMENT_SKILL_ROOT / "assets" / "readme"

# Concurrent agents are porting the other eight skill folders at the same time this suite
# runs, so these tests never read the live sibling folders in qin-claude-skills. Every test
# below builds its own throwaway fixture skill tree instead (per the task brief: "your sync
# script tests should use fixture directories, not the live repo state").


def make_fixture_skill(root, name):
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: fixture skill for tests\n---\n# {name}\n", encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "placeholder.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    return skill_dir


def make_fixture_skill_set(root):
    for name in sync_global_skills.PRIMARY_SKILL_ORDER:
        make_fixture_skill(root, name)
    return [root / name for name in sync_global_skills.PRIMARY_SKILL_ORDER]


def svg_character_width_factor(character):
    if character.isspace():
        return 0.32
    if character in "ilI1.,:;!|'`·":
        return 0.28
    if character in "MW@#%&":
        return 0.85
    if ord(character) > 127:
        import unicodedata

        return 1.0 if unicodedata.east_asian_width(character) in "WFA" else 0.65
    if character.isupper():
        return 0.63
    if character.islower() or character.isdigit():
        return 0.52
    return 0.45


def svg_bounds_issues(svg_path):
    root = ElementTree.parse(svg_path).getroot()
    viewbox_x, viewbox_y, viewbox_width, viewbox_height = [float(value) for value in root.attrib["viewBox"].split()]
    viewbox_right = viewbox_x + viewbox_width
    viewbox_bottom = viewbox_y + viewbox_height
    issues = []
    pending = [(root, 0.0, 0.0, 16.0, "start")]
    while pending:
        element, inherited_x, inherited_y, inherited_font_size, inherited_anchor = pending.pop()
        translate_x = inherited_x
        translate_y = inherited_y
        translate_match = re.fullmatch(r"translate\(([-\d.]+)(?:[ ,]+([-\d.]+))?\)", element.attrib.get("transform", ""))
        if translate_match:
            translate_x += float(translate_match.group(1))
            translate_y += float(translate_match.group(2) or 0)
        font_size = float(element.attrib.get("font-size", inherited_font_size))
        text_anchor = element.attrib.get("text-anchor", inherited_anchor)
        tag_name = element.tag.rsplit("}", 1)[-1]
        if tag_name == "rect":
            left = translate_x + float(element.attrib.get("x", 0))
            top = translate_y + float(element.attrib.get("y", 0))
            right = left + float(element.attrib.get("width", 0))
            bottom = top + float(element.attrib.get("height", 0))
            if left < viewbox_x or top < viewbox_y or right > viewbox_right or bottom > viewbox_bottom:
                issues.append(f"rect ({left}, {top}, {right}, {bottom})")
        elif tag_name == "line":
            line_x = [translate_x + float(element.attrib[key]) for key in ("x1", "x2")]
            line_y = [translate_y + float(element.attrib[key]) for key in ("y1", "y2")]
            if min(line_x) < viewbox_x or max(line_x) > viewbox_right or min(line_y) < viewbox_y or max(line_y) > viewbox_bottom:
                issues.append(f"line ({line_x}, {line_y})")
        elif tag_name == "text" and "x" in element.attrib and "y" in element.attrib:
            visible_text = "".join(element.itertext()).strip()
            text_x = translate_x + float(element.attrib["x"])
            text_y = translate_y + float(element.attrib["y"])
            estimated_width = font_size * sum(svg_character_width_factor(character) for character in visible_text) + 12.0
            text_left = text_x - estimated_width / 2 if text_anchor == "middle" else text_x - estimated_width if text_anchor == "end" else text_x
            text_right = text_left + estimated_width
            if text_left < viewbox_x or text_right > viewbox_right or text_y - font_size * 1.1 < viewbox_y or text_y + font_size * 0.25 > viewbox_bottom:
                issues.append(f"text {visible_text!r} ({text_left}, {text_right}, {text_y})")
        for child in element:
            pending.append((child, translate_x, translate_y, font_size, text_anchor))
    return issues


class ApprovedSkillSetTest(unittest.TestCase):
    def test_approved_public_mirror_is_exactly_nine_including_auto_model_for_claude(self):
        expected_order = [
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
        self.assertEqual(sync_global_skills.PRIMARY_SKILL_ORDER, expected_order)
        self.assertEqual(sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES, set(expected_order))
        with tempfile.TemporaryDirectory() as temp_dir:
            repository_dir = Path(temp_dir)
            for skill_name in expected_order:
                (repository_dir / skill_name).mkdir()
                (repository_dir / skill_name / "SKILL.md").write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
            sync_global_skills.assert_repository_skill_set(repository_dir)
            (repository_dir / "auto-model-for-claude" / "SKILL.md").unlink()
            with self.assertRaisesRegex(RuntimeError, "auto-model-for-claude"):
                sync_global_skills.assert_repository_skill_set(repository_dir)

    def test_default_repository_and_state_file_point_at_claude_code_paths(self):
        self.assertEqual(sync_global_skills.DEFAULT_REPOSITORY, "qinbatista/qin-claude-skills")
        self.assertIn(".claude", sync_global_skills.DEFAULT_STATE_FILE.parts)
        self.assertNotIn(".codex", sync_global_skills.DEFAULT_STATE_FILE.parts)

    def test_unrelated_local_skill_is_ignored_and_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            make_fixture_skill_set(staged_skills)
            for unrelated_name in ("chronicle", "apple-design", "emil-design-eng"):
                unrelated = staged_skills / unrelated_name
                unrelated.mkdir()
                (unrelated / "SKILL.md").write_text(f"---\nname: {unrelated_name}\ndescription: local only\n---\n", encoding="utf-8")
            selected = sync_global_skills.skill_directories(staged_skills)
            self.assertEqual([path.name for path in selected], sync_global_skills.PRIMARY_SKILL_ORDER)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            copied_names = sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertEqual(copied_names, sync_global_skills.PRIMARY_SKILL_ORDER)
            self.assertTrue((staged_skills / "chronicle").exists())
            self.assertTrue((staged_skills / "apple-design").exists())
            self.assertFalse((repository_dir / "chronicle").exists())
            self.assertFalse((repository_dir / "apple-design").exists())

    def test_snapshot_rejects_incomplete_skill_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            for name in sync_global_skills.PRIMARY_SKILL_ORDER[:-1]:  # drop auto-model-for-claude
                make_fixture_skill(staged_skills, name)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            with self.assertRaisesRegex(RuntimeError, "auto-model-for-claude"):
                sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)


class SymlinkAndSafetyTest(unittest.TestCase):
    def test_external_file_symlink_is_rejected_even_when_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            link = skill_dir / "local" / "linked.txt"
            link.parent.mkdir()
            link.symlink_to(outside)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.included_files(skill_dir)

    def test_external_directory_symlink_is_rejected_even_when_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("outside", encoding="utf-8")
            link = skill_dir / "local"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.snapshot_hash([skill_dir])

    def test_public_safety_rejects_absolute_user_home_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"private path: {Path('/', 'Users', 'example', 'private', 'file.txt')}\n", encoding="utf-8")
            issues = sync_global_skills.public_safety_issues([skill_dir])
        self.assertEqual(len(issues), 1)
        self.assertIn("secret-like content", issues[0])

    def test_public_safety_rejects_credential_like_filenames(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            skill_dir.mkdir()
            (skill_dir / "credentials_work.json").write_text("{}", encoding="utf-8")
            issues = sync_global_skills.public_safety_issues([skill_dir])
        self.assertEqual(len(issues), 1)
        self.assertIn("sensitive filename", issues[0])

    def test_symlink_rejection_does_not_copy_outside_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            outside = root / "outside.txt"
            outside.write_text("must stay outside", encoding="utf-8")
            (source / "SKILL.md").write_text("source", encoding="utf-8")
            (source / "linked.txt").symlink_to(outside)
            (target / "sentinel.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                sync_global_skills.copy_skill_directory(source, target)
            self.assertEqual(outside.read_text(encoding="utf-8"), "must stay outside")
            self.assertEqual((target / "sentinel.txt").read_text(encoding="utf-8"), "keep")
            self.assertFalse((target / "linked.txt").exists())


class LocalFolderPreservationTest(unittest.TestCase):
    """Unlike the Codex original (which only preserved task-analyze-skill/local/), the
    Claude edition preserves local/ for every skill on pull -- auto-model-for-claude keeps
    private ledger data at local/ledger.jsonl too."""

    def test_pull_preserves_local_folder_for_any_skill_not_just_task_analyze(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = sandbox / "repository"
            local_dir = sandbox / "local"
            repository_dir.mkdir()
            local_dir.mkdir()
            make_fixture_skill_set(repository_dir)
            make_fixture_skill_set(local_dir)

            private_ledger = local_dir / "auto-model-for-claude" / "local" / "ledger.jsonl"
            private_ledger.parent.mkdir(parents=True)
            private_ledger.write_text('{"attempt": "private"}\n', encoding="utf-8")

            (repository_dir / "auto-model-for-claude" / "SKILL.md").write_text(
                (repository_dir / "auto-model-for-claude" / "SKILL.md").read_text(encoding="utf-8") + "\nremote update\n",
                encoding="utf-8",
            )
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertEqual(private_ledger.read_text(encoding="utf-8"), '{"attempt": "private"}\n')
            self.assertIn("remote update", (local_dir / "auto-model-for-claude" / "SKILL.md").read_text(encoding="utf-8"))

    def test_pull_preserves_unrelated_local_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            repository_dir = sandbox / "repository"
            local_dir = sandbox / "local"
            repository_dir.mkdir()
            local_dir.mkdir()
            make_fixture_skill_set(repository_dir)
            make_fixture_skill_set(local_dir)
            unrelated = local_dir / "chronicle"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("---\nname: chronicle\ndescription: local only\n---\n", encoding="utf-8")
            sync_global_skills.mirror_repository_to_local(repository_dir, local_dir)
            self.assertTrue(unrelated.exists())


class BuildReadmeTest(unittest.TestCase):
    def test_english_readme_is_the_durable_template_verbatim(self):
        readme = sync_global_skills.build_readme(language="en")
        template = sync_global_skills.ENGLISH_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        self.assertEqual(readme, template)

    def test_chinese_readme_is_the_durable_template_verbatim(self):
        readme = sync_global_skills.build_readme(language="zh")
        template = sync_global_skills.CHINESE_README_TEMPLATE.read_text(encoding="utf-8").rstrip() + "\n"
        self.assertEqual(readme, template)

    def test_english_readme_identity_and_contract(self):
        readme = sync_global_skills.build_readme(language="en")
        self.assertIn("# 🚀 Auto Best Model", readme)
        self.assertIn("Claude Code-only", readme)
        self.assertIn("https://github.com/qinbatista/qin-codex-skills", readme)
        self.assertIn("finish the job first", readme.lower())
        self.assertIn("score every task", readme.lower())
        self.assertIn("mandatory ending tasks", readme.lower())
        self.assertIn("small low-risk edits scoring 0\u201324 try `haiku`-low first", readme.lower())
        self.assertIn("all required checks must pass", readme.lower())
        self.assertIn("End Task-<task name>-<check>", readme)
        self.assertIn("haiku", readme)
        self.assertIn("sonnet", readme)
        self.assertIn("opus", readme)
        self.assertIn("fable", readme)
        self.assertIn("Claude Model Switch.md", readme)
        self.assertNotIn("plain `Model Switch.md`", readme)

    def test_english_readme_lists_exactly_nine_skills(self):
        readme = sync_global_skills.build_readme(language="en")
        skills_section = readme.split("## 🧩 Nine public Skills", 1)[1].split("\n## ", 1)[0]
        skill_rows = re.findall(r"^- \[`([^`]+)`\]\(\./([^/]+)/SKILL\.md\)", skills_section, re.M)
        self.assertEqual(len(skill_rows), 9)
        self.assertEqual({folder for _, folder in skill_rows}, sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES)
        for skill_name in sync_global_skills.PRIMARY_SKILL_ORDER:
            self.assertIn(f"./{skill_name}/SKILL.md", readme)

    def test_chinese_readme_lists_exactly_nine_skills_and_has_identity(self):
        readme = sync_global_skills.build_readme(language="zh")
        self.assertIn("# 🚀 Auto Best Model", readme)
        self.assertIn("仅限 Claude Code", readme)
        self.assertIn("九个公开 Skill", readme)
        skills_section = readme.split("## 🧩 九个公开 Skill", 1)[1].split("\n## ", 1)[0]
        skill_rows = re.findall(r"^- \[`([^`]+)`\]\(\./([^/]+)/SKILL\.md\)", skills_section, re.M)
        self.assertEqual(len(skill_rows), 9)
        self.assertEqual({folder for _, folder in skill_rows}, sync_global_skills.APPROVED_GLOBAL_SKILL_NAMES)

    def test_readme_benchmark_is_labeled_as_upstream_reference_not_claude_measurement(self):
        readme = sync_global_skills.build_readme(language="en")
        self.assertIn("upstream Codex-measured reference evidence", readme)
        self.assertIn("not a Claude Code measurement", readme)
        self.assertIn("Claude Code numbers are not yet measured", readme)
        self.assertIn("56.411% tokens / 67.873% time", readme)
        self.assertIn("35.072% / 53.681%", readme)

    def test_readme_never_embeds_private_paths_or_internals(self):
        for language in ("en", "zh"):
            readme = sync_global_skills.build_readme(language=language)
            self.assertNotIn("/Users/", readme)
            self.assertNotIn('"thread_id"', readme)
            self.assertNotIn('"receipt_path"', readme)
            self.assertNotIn("TASK_ANALYZE_PLAN_JSON", readme)

    def test_readme_svg_references_exist_on_disk(self):
        for readme_text, expected_references in (
            (
                sync_global_skills.build_readme(language="en"),
                {
                    "./management-skill/assets/readme/core-flow.svg",
                    "./management-skill/assets/readme/core-flow-mobile.svg",
                    "./management-skill/assets/readme/model-router.svg",
                    "./management-skill/assets/readme/model-router-mobile.svg",
                    "./management-skill/assets/readme/lifecycle-skill-benchmark.svg",
                },
            ),
            (
                sync_global_skills.build_readme(language="zh"),
                {
                    "./management-skill/assets/readme/core-flow-zh.svg",
                    "./management-skill/assets/readme/core-flow-zh-mobile.svg",
                    "./management-skill/assets/readme/model-router.svg",
                    "./management-skill/assets/readme/model-router-mobile.svg",
                    "./management-skill/assets/readme/lifecycle-skill-benchmark.svg",
                },
            ),
        ):
            local_references = set(re.findall(r'(?:src="|srcset="|\]\()(\./[^"#)]+)', readme_text))
            svg_references = {reference for reference in local_references if reference.lower().endswith(".svg")}
            self.assertEqual(svg_references, expected_references)
            for reference in local_references:
                referenced_path = MANAGEMENT_SKILL_ROOT.parent / reference.removeprefix("./")
                self.assertTrue(referenced_path.exists(), f"Missing README reference: {reference}")

    def test_repository_snapshot_writes_both_readmes_from_templates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir)
            staged_skills = sandbox / "skills"
            staged_skills.mkdir()
            make_fixture_skill_set(staged_skills)
            repository_dir = sandbox / "repository"
            repository_dir.mkdir()
            sync_global_skills.prepare_repository_snapshot(repository_dir, staged_skills)
            self.assertEqual((repository_dir / "README.md").read_text(encoding="utf-8"), sync_global_skills.build_readme(language="en"))
            self.assertEqual((repository_dir / "README.zh.md").read_text(encoding="utf-8"), sync_global_skills.build_readme(language="zh"))
            self.assertEqual((repository_dir / ".gitignore").read_text(encoding="utf-8"), sync_global_skills.GITIGNORE_TEXT)


class SvgAssetIntegrityTest(unittest.TestCase):
    NON_BENCHMARK_VISUAL_NAMES = (
        "qin-codex-skills-hero",
        "task-lifecycle",
        "model-router",
        "model-experience",
        "verification-topologies",
        "runtime-receipt",
        "core-flow",
        "core-flow-zh",
    )

    def test_readme_svgs_are_parseable_accessible_and_self_contained(self):
        svg_paths = sorted(README_ASSET_DIR.glob("*.svg"))
        self.assertEqual(len(svg_paths), 19)
        for svg_path in svg_paths:
            root = ElementTree.parse(svg_path).getroot()
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            self.assertIsNotNone(root.find("svg:title", namespace), svg_path.name)
            self.assertIsNotNone(root.find("svg:desc", namespace), svg_path.name)
            self.assertEqual(root.attrib.get("role"), "img", svg_path.name)
            self.assertIn("viewBox", root.attrib, svg_path.name)
            forbidden_tags = {element.tag.rsplit("}", 1)[-1] for element in root.iter() if element.tag.rsplit("}", 1)[-1] in {"script", "foreignObject"}}
            self.assertFalse(forbidden_tags, f"{svg_path.name}: {forbidden_tags}")
            for element in root.iter():
                for attribute, value in element.attrib.items():
                    if attribute.rsplit("}", 1)[-1] == "href":
                        self.assertFalse(value.startswith(("http://", "https://")), f"{svg_path.name}: external SVG reference {value}")

    def test_non_benchmark_diagram_text_and_shapes_stay_inside_viewboxes(self):
        for visual_name in self.NON_BENCHMARK_VISUAL_NAMES:
            for suffix in ("", "-mobile"):
                svg_path = README_ASSET_DIR / f"{visual_name}{suffix}.svg"
                self.assertEqual(svg_bounds_issues(svg_path), [], svg_path.name)

    def test_svgs_do_not_name_codex_or_gpt_models_except_the_frozen_upstream_benchmark(self):
        pattern = re.compile(r"codex|gpt-5|\bluna\b|\bterra\b|sol-ultra", re.IGNORECASE)
        for svg_path in sorted(README_ASSET_DIR.glob("*.svg")):
            text = svg_path.read_text(encoding="utf-8")
            if svg_path.name == "lifecycle-skill-benchmark.svg":
                # Frozen upstream Codex-measured reference evidence: kept byte-for-byte.
                self.assertIn("gpt-5.6-sol", text)
                continue
            self.assertNotRegex(text, pattern, svg_path.name)

    def test_model_router_svgs_use_the_claude_model_ladder(self):
        for filename in ("model-router.svg", "model-router-mobile.svg"):
            text = (README_ASSET_DIR / filename).read_text(encoding="utf-8")
            self.assertIn("SONNET", text.upper())
            self.assertIn("OPUS", text.upper())
            self.assertIn("FABLE", text.upper())
            self.assertIn("HAIKU", text.upper())

    def test_hero_svgs_name_the_claude_edition_repository(self):
        for filename in ("qin-codex-skills-hero.svg", "qin-codex-skills-hero-mobile.svg"):
            text = (README_ASSET_DIR / filename).read_text(encoding="utf-8")
            self.assertIn("qin-claude-skills", text)
            self.assertNotIn(">qin-codex-skills<", text)

    def test_model_experience_svgs_reference_claude_model_switch_page(self):
        for filename in ("model-experience.svg", "model-experience-mobile.svg"):
            text = (README_ASSET_DIR / filename).read_text(encoding="utf-8")
            self.assertIn("Claude Model Switch.md", text)


if __name__ == "__main__":
    unittest.main()
