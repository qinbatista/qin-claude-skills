from pathlib import Path
import unittest


PROMPT_SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"
GLOBAL_ENTRY_RULE_PATH = Path(__file__).resolve().parents[2] / "task-analyze-skill" / "assets" / "global-claude-entry-rule.md"


class PromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompt_skill = PROMPT_SKILL_PATH.read_text(encoding="utf-8")
        cls.global_entry_rule = GLOBAL_ENTRY_RULE_PATH.read_text(encoding="utf-8")

    def test_global_prompt_gate_is_mandatory_and_owned_by_the_selected_producer(self):
        for contract_text in ["Always use for every task", "100% global prompt-task gate across projects", "Do not trigger merely because an ordinary request is text", "Prompt-in-code also uses its owning code executor"]:
            self.assertIn(contract_text, self.prompt_skill)
        for contract_text in ["Producer owns files/skills/Mini Test"]:
            self.assertIn(contract_text, self.global_entry_rule)

    def test_claude_native_examples_in_description(self):
        for contract_text in ["Claude Projects", "CLAUDE.md", ".claude/agents definitions"]:
            self.assertIn(contract_text, self.prompt_skill)

    def test_core_contract_is_complete(self):
        for contract_name in ["Objective", "Context and inputs", "Requirements and constraints", "Output contract", "Success criteria", "Failure conditions", "Verification"]:
            self.assertIn(contract_name, self.prompt_skill)

    def test_playbook_controls_are_conditional(self):
        for control_name in ["Role", "Workflow and tool order", "Autonomy and ambiguity", "Reasoning effort", "Verbosity", "Delimiters", "Few-shot examples"]:
            self.assertIn(control_name, self.prompt_skill)
        self.assertIn("Use these controls deliberately instead of inserting them into every prompt", self.prompt_skill)

    def test_all_25_playbook_topics_have_an_explicit_policy(self):
        requirement_markers = {"objective": "Objective", "context": "Context and inputs", "role": "| Role |", "requirements": "Requirements and constraints", "constraints": "Requirements and constraints", "success criteria": "Success criteria", "failure conditions": "Failure conditions", "output format": "Output contract", "ask instead of guess": "Ask only when missing information would materially change", "negative instructions": "Negative instructions are appropriate", "step-by-step workflow": "Workflow and tool order", "verification": "Verification", "consistency": "Consistency And Priority", "tool usage": "tool purpose, required evidence, fallback, and stop condition", "agent workflow": "plan -> execute -> review -> finalize", "agent autonomy": "Autonomy and ambiguity", "reasoning level": "Reasoning effort", "verbosity": "Verbosity", "delimiters": "Delimiters", "few-shot examples": "Few-shot examples", "structured layout": "Recommended Prompt Shape", "explicit instructions": "Prefer explicit and measurable instructions", "measurable constraints": "measurable word, section, item, or detail target", "planning before execution": "plan dependencies internally before execution", "validate before finishing": "when final target-output validation matters"}
        for requirement_name, marker in requirement_markers.items():
            self.assertIn(marker, self.prompt_skill, requirement_name)

    def test_result_first_and_target_validation_are_separate(self):
        self.assertIn("Present the completed prompt or instruction artifact immediately", self.prompt_skill)
        self.assertIn("It does not test prompt cases; representative trials or repeated fresh runs happen only when the user explicitly requests testing", self.prompt_skill)
        self.assertIn("before returning", self.prompt_skill)

    def test_conflict_resolutions_are_explicit(self):
        for required_rule in ["Ask only when missing information would materially change", "Do not expose private chain-of-thought", "Do not make every task follow a visible step-by-step", "examples as illustrations", "Prefer explicit and measurable instructions"]:
            self.assertIn(required_rule, self.prompt_skill)

    def test_code_executor_scope_does_not_claim_unowned_languages(self):
        self.assertNotIn("JavaScript", self.prompt_skill)
        self.assertIn("code-skill owns Python and C#", self.prompt_skill)

    def test_ending_lifecycle_uses_background_agent(self):
        self.assertIn("background Agent task", self.prompt_skill)
        self.assertIn("run_in_background: true", self.prompt_skill)

if __name__ == "__main__":
    unittest.main()
