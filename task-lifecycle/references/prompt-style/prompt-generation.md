# Prompt Generation

The workflow in this file targets AI prompt-related work embedded in code: creation, review, testing, editing, add/update/remove/rewrite, improvement, or standardization. Current examples are Python and C#. Prompts that are not embedded in code (standalone prompts, durable AI instructions) skip the embedded-prompt workflow and follow the General Prompt Contract at the end of this file — every prompt follows one of the two. Ordinary code style, architecture, debugging, and non-prompt prose stay with the code-style rules.

Create compact Python prompt assignments or C# prompt constants ready to paste into code:

```python
prompt = f"""
...
"""
```

```csharp
const string prompt = """
...
""";
```

## Workflow

Always apply the General Prompt Contract at the end of this file first. A missing or skipped prompt-contract pass is a prompt-task routing failure. This workflow only specializes that normative contract for prompts stored in executable Python or C#; it never weakens the objective, context/input roles, requirements/constraints, output contract, measurable success/failure conditions, or verification gates.

1. Use `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution` internally. Do not print this planning scaffold in the generated prompt or user-facing result.
2. Identify objective, context/input roles, variables, target audience, requirements, constraints, output contract, measurable success criteria, observable failure conditions, and verification.
3. For an existing prompt, read it seriously and identify the failing or missing behavior before changing wording.
4. Choose a function prompt for direct AI operations such as get, extract, change, check, fix, convert, compare, or return structured output.
5. Choose a content prompt for text humans will read, such as descriptions, summaries, explanations, factory notes, doctor-facing notes, customer copy, or reviewer notes.
6. Use the smallest applicable canonical structure. For an embedded function prompt that is the compact shape: one opening sentence stating the objective and each input's role, numbered required behaviors, a `Rules:` list of hard boundaries, one before-returning verification line, one closing `Return only ...` output line, and named data blocks last. Use explicit `Objective:`/`Requirements:`/`Success criteria:` headings only when a prompt is too complex for the compact form; existing project headings may stay when they express the same contract clearly.
7. Add role, ordered workflow/tools, autonomy, reasoning level, verbosity, delimiters, or examples only when each one changes behavior or removes a real ambiguity.
8. Keep the prompt complete and concise. Add missing logic when the prompt does not cover the task goal; merge overlapping rules instead of appending repeated warnings.
9. State durable rules at the highest useful level. Do not add obvious prohibitions, near-duplicate warnings, or case-by-case exclusions.
10. Treat examples, bad outputs, and edge cases as test evidence. Include only the minimum labeled example needed to define a reusable boundary; explicit rules remain authoritative.
11. For Python f-strings, escape literal JSON braces as `{{` and `}}`; real interpolation placeholders stay single-braced, such as `{image_width}`.
12. Apply the owning language's bounded Quick Check before presentation: a smallest safe local smoke for light code, or syntax plus changed prompt variable/constant and direct-reference checks for heavy/API paths. Do not run external prompt trials in Quick Check.
13. Present `CODE READY` with Quick Check evidence, then launch a detached background Agent (`End Task-{concise related task name}`) and return without waiting. In that background Ending Agent, test the prompt with representative input/output scenarios. Use repeated fresh runs for stochastic production prompts: default 3 and 5 for critical image, structured-data, or reliability claims. Report artifact creation separately from semantic/file/visual acceptance, and reopen with a corrected prompt if validation fails.

## Function Prompt Shape

```python
prompt = f"""
You are <one concrete operation> on <target>. SOURCE_TEXT is <source role>; the attached image, when present, is <image role>.

Do <N> things:
1. <required behavior>
2. <required behavior>

Rules:
- <hard boundary or missing-value behavior>
- <prohibition that rejects a plausible wrong output>

Before returning, check <the measurable acceptance evidence> and fix any rule the draft breaks.

Return only valid JSON with this exact shape:
{{
  "<key>": "<value>"
}}

<SOURCE_TEXT>
{source_text}
</SOURCE_TEXT>
""".strip()
```

When an enforced response schema already defines the container, replace the inline JSON example with one `Return only the structured object with <top-level keys>.` line.

## Human-Reading Content Prompt Shape

```python
prompt = f"""
Role:
<only when a domain perspective changes the content>

Objective:
Write <content type> for <audience/use case> from <source/input>.

Context and inputs:
- <source role, audience, environment, or limitation>

Requirements:
- Emphasize <most important qualities> first.

Constraints:
- <hard boundary>

Output contract:
<exact content format and measurable length>

Success criteria:
- <observable audience/content requirement>

Failure conditions:
- <observable rejection condition>

Verification:
- Check <required facts, coverage, and format> before returning.

<SOURCE>
{source_text}
</SOURCE>
"""
```

## Guardrails

- Do not expand a compact embedded function prompt into ceremonial `Success criteria:`/`Failure conditions:`/`Verification:` heading blocks that restate its rules; fold acceptance into `Rules:` and the single before-returning check line.
- Do not add persona text such as `You are...` unless a domain perspective or responsibility materially changes the result.
- Let the output schema define the container shape and fields instead of repeating verbose JSON warnings.
- Do not add sibling-case warnings for cases the user did not mention.
- Do not add obvious prohibitions that already follow from the objective, requirements/constraints, or output contract.
- Do not add vague filler such as "be accurate" when a concrete rule can say what accuracy requires.
- Do not use blanket `ask instead of guess`, maximum reasoning, long responses, mandatory visible planning, or many few-shot examples. Define the bounded behavior that the task actually needs.
- Use named delimiters when executable prompt strings contain multiple source blocks, examples, or instruction/data boundaries; state each block's role.
- Request concise rationale, evidence, or checks when needed, never private chain-of-thought.
- Do add necessary logic when the prompt lacks it. Do not keep adding repeated prompt rules to cover every observed failure; replace the weak block with a complete working rule that matches the prompt goal.
- Return the optimized Python assignment or C# constant directly when the user asks for prompt code only.

## General Prompt Contract

This section carries the global prompt-format contract that the Workflow above applies first. It was merged from the retired standalone `prompt-skill`; only prompt-format rules are imported — no lifecycle, routing, or skill-dispatch content. For prompts embedded in code, the compact Function Prompt Shape above remains canonical; never expand it into ceremony-heading blocks.

### Core Contract

Every production prompt must make the following behavior explicit when it materially affects the result:

1. **Objective** — the concrete final outcome; never make the model infer the job.
2. **Context and inputs** — relevant environment, audience, source material, variable placeholders, reference roles, and known limitations.
3. **Requirements and constraints** — required behavior, prohibited behavior, authority/autonomy boundary, and instruction priority.
4. **Output contract** — exact artifact, schema, count, layout, format, destination, and response length where applicable.
5. **Success criteria** — measurable conditions that make the result usable.
6. **Failure conditions** — observable conditions that reject the result even when an artifact was produced.
7. **Verification** — checks performed before acceptance and the evidence or receipt that records them.

Role, workflow steps, reasoning effort, verbosity, examples, and delimiters are optional controls. Add them only when they improve behavior; do not add ceremonial sections or persona filler.

### Conditional Controls

Use these controls deliberately instead of inserting them into every prompt:

| Control | Use it when | Rule |
|---|---|---|
| Role | A domain perspective, audience, or decision standard changes the result | Name the useful expertise and responsibility; omit fictional biography and generic `You are helpful` text. |
| Workflow and tool order | Sequence, dependencies, or side effects affect correctness | State the minimum ordered actions, allowed tools, stop condition, and fallback. Do not force a visible plan for a one-step task. |
| Autonomy and ambiguity | The model may need to choose, assume, ask, or act | Define what it may decide, when a bounded assumption is acceptable, and which missing facts require a question. |
| Reasoning effort | Risk or complexity justifies more analysis | Request only the necessary effort and concise rationale/checks; never request private chain-of-thought or maximum reasoning by default. |
| Verbosity | Length, audience, or review cost matters | Give a measurable word, section, item, or detail target instead of `brief but detailed`. |
| Delimiters | Multiple instruction, source, example, or data blocks could be confused | Use named tags or fenced blocks and state each block's role and authority. |
| Few-shot examples | A schema, style, boundary, or edge case remains ambiguous after direct rules | Use the fewest representative examples, label input/output clearly, and make explicit rules authoritative over examples. |

Negative instructions are appropriate for critical, plausible failures such as fabrication, unsafe actions, forbidden fields, or copying the wrong reference. Express ordinary behavior positively and measurably; do not build a prompt from a long history of `do not` warnings.

### Consistency And Priority

- Follow the active instruction hierarchy and keep one authoritative rule for each behavior.
- Resolve contradictions before delivery. When two preferences compete, use the objective, audience, output contract, and higher-authority instruction to choose one observable behavior.
- Define every placeholder, source role, unit, enum, count, and destination that affects acceptance.
- Prefer explicit and measurable instructions over vague quality language. Replace `make it good` with the property and check that prove good.
- Treat examples as illustrations, never as permission to override constraints or invent unavailable facts.

### Recommended Shape For Standalone Prompts

For durable AI instructions that are not embedded function prompts, use the smallest subset that fully controls the task:

```text
Role: <only when domain perspective matters>

Objective:
<one concrete outcome>

Context and inputs:
- <source or variable role>
- <environment or limitation>

Requirements:
- <required capability>

Constraints:
- <hard boundary or prohibition>

Workflow:
1. <ordered step only when order matters>

Autonomy and ambiguity:
- <what may be decided or assumed; what requires a question>

Effort and verbosity:
- <only when a measurable level or response limit matters>

Output contract:
<exact format, count, schema, layout, or file contract>

Success criteria:
- <measurable acceptance condition>

Failure conditions:
- <observable rejection condition>

Verification:
- <check and evidence>

Examples:
<only the minimum labeled examples needed to remove ambiguity>
```

The headings are a design aid, not a mandatory ceremony. Preserve a project's established prompt style when the same contract is explicit and testable.

### Image And Multimodal Prompts

- Assign every attachment one role: subject/structure, style, context, data-channel, or edit target. State what must not be copied from each reference.
- Make camera, pose, count, ordering, aspect ratio, crop, transparency/background, and file-mode requirements measurable.
- Separate semantic fidelity from file validity. Check both the visible image and the downloaded bytes.
- For isolated sprites, distinguish real RGBA from a baked checkerboard and reject detached shadows, glow, particles, or meaningful alpha outside the body.
- For sketch-to-image, count and preserve required structural strokes/parts before adding style detail.
- For image-to-image and variants, specify what is locked and what is allowed to change.
- For production stability, compare identical inputs across fresh runs and report automatic/file gates separately from manual visual gates.

### Structured Output Prompts

- Prefer a schema or one valid example over repeated prose about formatting.
- Define allowed missing-value behavior; never let the model invent unavailable values.
- Validate parsing, required fields, types, enums, naming, and cross-field consistency.

### Acceptance Checklist

Before accepting a production prompt, confirm:

- the objective and final artifact are unambiguous;
- every material input, placeholder, reference, and authority boundary is defined;
- requirements are explicit, constraints are non-conflicting, and measurable limits replace vague preferences;
- role, workflow, tools, autonomy, effort, verbosity, delimiters, and examples appear only when useful;
- the output contract defines format, count/schema/layout, missing-value behavior, and destination where relevant;
- success and failure conditions can reject a merely completed but incorrect artifact;
- verification checks the actual semantic, structural, file, visual, or side-effect requirements without requesting private chain-of-thought.
- when final target-output validation matters, the prompt tells the target model to check missing fields, invalid format or JSON, unsupported claims, inconsistent terminology, and requirement violations before returning; it corrects a failed check when possible or follows the defined failure contract.

### Additional Guardrails

- Do not require a plan in the user-visible response unless the user asked for one or planning is itself the deliverable.
- Do not make every task follow a visible step-by-step or `plan -> execute -> review` ceremony. Use ordered phases only when they change correctness or control risk.
- Do not claim stability from one attractive sample.
- Do not weaken acceptance criteria to make a failing prompt appear successful.
