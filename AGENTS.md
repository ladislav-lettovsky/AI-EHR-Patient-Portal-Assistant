# ai-ehr-assistant — AI Agent Memory

## What this is

A LangGraph-powered patient-portal assistant that answers clinical questions
about EHR data (labs, meds, allergies, visit notes). It combines a
ReAct agent loop with deterministic safety guardrails — a separate validator
node and a policy-override node — so every response is cross-checked for
PHI leakage, cross-patient access, and unsafe clinical content before it
reaches the user.

## Stack

- Python 3.12+, `uv` for dependency management, `just` as the task runner
- LangGraph (state-machine orchestration), LangChain, langchain-openai
- OpenAI GPT-4o-mini (generator + policy classifier) and GPT-4o (validator)
- SQLite (synthetic EHR data via `src/ehr_assistant/db.py`), pandas
- Pydantic for tool I/O and structured LLM outputs
- Testing: pytest 8, with `integration` marker for live-LLM tests
- Linting: ruff; Type checking: `ty` (Astral); Pre-commit hooks enabled

## Commands you can run without asking

- `just fmt` — format code
- `just lint` — ruff check
- `just lint-fix` — ruff check with --fix
- `just type` — ty check
- `just test` — full pytest run (deterministic only; integration auto-skipped
  without an API key)
- `just check` — lint + type + test (the same command CI runs)
- `uv sync`, `uv sync --extra dev`
- `uv run python -m ehr_assistant [--flags]`
- `uv run ehr-assistant [--patient-id ... --query ...]`
- Read-only git: `git status`, `git diff`, `git log`, `git branch`

## Commands with preconditions

- `git commit` is allowed on a non-`main` branch **only after `just check`
  passes with no errors**. On `main`, always ask first.
- After any update to local `main` (PR merge, `git pull`, fast-forward, etc.),
  immediately `git switch` to a parking branch — by convention `scratch`,
  forked from the new `main` tip. This keeps the working copy off `main` so
  no edits or commits land there by accident. Create real work branches
  (`feat/<name>`, `fix/<name>`, `chore/<name>`, ...) from `main`, not from
  `scratch`. If `scratch` is missing or stale, recreate it with
  `git switch -c scratch` from the current `main`.

## Commands that need explicit approval

- `uv add`, `uv remove` (dependency changes)
- `git push`, `git reset --hard`
- `gh pr create`, `gh pr merge`
- Anything touching `.env`, `.github/workflows/`, or `data/`
- Any code change that alters the PHI-access rules (see invariants below)

## Architectural invariants (do not violate without explicit discussion)

1. **Every patient-scoped tool MUST use the session `patient_id`** —
   `src/ehr_assistant/tools/__init__.py::PATIENT_SCOPED_TOOLNAMES` lists the
   seven tools that read patient-specific data. The agent node
   (`agent/nodes.py::agent_node`) rewrites `tool_call["args"]["patient_id"]`
   to the session's `patient_id` before executing. Never add a new
   patient-reading tool without also adding it to `PATIENT_SCOPED_TOOLNAMES`.
   This is the cross-patient-access guardrail.

2. **Policy classification runs twice, deliberately** — once as an in-loop
   LLM tool (`tools/policy.py::policy_route`) and once as a final-pass
   override (`agent/nodes.py::final_policy_override_node`). The second pass
   is not redundant; it catches cases where the agent ignored the routing
   signal. Do not collapse into one pass.

3. **The validator node is non-negotiable** — `validator_node` runs BEFORE
   `final_policy_override_node`. The ordering matters: validator catches
   hallucinated clinical claims; policy catches unsafe advice. Keep the edge
   `validate → policy → END`.

4. **Emergency short-circuit is detected in `agent_node`, not downstream** —
   when a query mentions an emergency (chest pain, stroke signs, etc.), the
   agent produces a templated triage response immediately so the loop
   terminates on the next step. Never move this logic out of `agent_node`.

5. **Configuration comes from environment variables** — model names, API
   keys, base URLs, log levels all live in `.env` and are read via
   `ehr_assistant.config`. Never hardcode these.

6. **Logging, not printing** — every module uses
   `logger = logging.getLogger(__name__)` at the top. The `reporting/`
   package (terminal formatters, JSON writer) is the only exception —
   that code legitimately writes to stdout for end-user display.

7. **Tool results are capped for prompt-size control** — `_cap_limit()` in
   `agent/nodes.py` truncates the `limit` argument on every tool call. If
   you add a tool that returns large result sets, honor the `limit` contract.

## Where things live

- `src/ehr_assistant/` — production package (src layout)
  - `agent/` — LangGraph graph + nodes
    - `state.py` — `AgentState` TypedDict (messages, patient_id, max_steps, etc.)
    - `graph.py` — 4-node compiled graph (`agent → tool → validate → policy`)
    - `nodes.py` — agent/tool/validator/policy-override node functions
    - `prompts.py` — system + validation prompts
  - `tools/` — LangChain `@tool` functions, 11 total across 3 files
    - `patient.py` — 7 patient-scoped tools (labs, meds, notes, allergies, encounters)
    - `education.py` — 3 general lookup tools (lab/med explanations, trusted sources)
    - `policy.py` — `policy_route` safety classifier
    - `__init__.py` — `TOOLS` registry + toolname constant sets
  - `reporting/` — `terminal.py` (audit log printer), `json_writer.py` (results file)
  - `config.py` — centralized settings from env vars
  - `data.py`, `db.py` — synthetic EHR fixtures and SQLite access
  - `runner.py` — CLI entry point with `TEST_CASES` (TypedDict) + single-patient mode
  - `utils.py` — small helpers (`norm_text`, `to_json`)
- `data/` — SQLite DB + seed CSVs + policy rules + trusted sources
- `tests/` — pytest test suite, organized by component (nodes / tools / policy / integration)
- `results/` — JSON output per run (git-ignored)
- `.scratch/` — ephemeral work zone (git-ignored except `.gitkeep`)

## LangGraph conventions for this repo

- State is `AgentState` in `agent/state.py` — a TypedDict, not a dataclass.
  LangGraph compiles TypedDict states natively.
- Nodes receive `AgentState`, return partial `dict[str, Any]` updates.
- The LLMs are lazy-initialized inside node functions (see `_get_llm_*`
  helpers). Never instantiate `ChatOpenAI(...)` at module top level — it
  breaks testing with mocks and triggers API-key checks at import time.
- LLM helpers that use `.bind_tools(...)` or `.with_structured_output(...)`
  return a `Runnable`, not a `ChatOpenAI`. Annotate accordingly.
- Tool calls are force-scoped to the session `patient_id` via `_cap_limit`
  and the patient-id rewrite in `agent_node` — not by trusting the LLM's
  tool_call args.

## Testing conventions

- Deterministic tests (no API) are the default and live in `tests/test_*.py`.
  They use fakes/mocks for `ChatOpenAI` so no network calls happen.
- Integration tests are marked `@pytest.mark.integration` and are SKIPPED
  without `OPENAI_API_KEY`. They live in `tests/test_integration.py`.
- `just test` runs the full suite; CI injects a fake key so the integration
  tests remain skipped there too.
- New features require at least one deterministic test in the matching
  `test_<component>.py` file. LLM-backed code paths should be exercised
  with mocked `invoke()` return values that match the Pydantic schema.

## Type checking with `ty`

- To suppress a finding: `# ty: ignore[<rule-name>]` — where `<rule-name>`
  is the exact code from the ty diagnostic header (e.g.,
  `invalid-argument-type`, `invalid-return-type`, `unknown-argument`).
- Library-stub limitations (LangChain's `ChatOpenAI`, LangGraph's
  `StateGraph` generics) are the most common legitimate suppression cases.
  Annotate intent in a comment above the suppression when it isn't obvious.

## Ephemeral / scratch work

Use `.scratch/` at the repo root for any exploratory, diagnostic, or
throwaway work — quick Python snippets, draft queries, debug logs, or
scratch notes. The directory is git-ignored (except `.gitkeep`), so
nothing here is ever committed.

- Create on demand: `mkdir -p .scratch`
- Preferred file names: `<topic>.py`, `<topic>.md`, `<topic>.sql`, etc.
- Do NOT place exploratory files at the repo root — always use `.scratch/`
- Clean up periodically (nothing persists beyond your working session)

Examples of good `.scratch/` use:

- `.scratch/try_new_prompt.py` — testing a policy-prompt variation
- `.scratch/poke_db.py` — interactive SQLite exploration
- `.scratch/validator_debug.md` — notes while tracing a validation miss

## Before saying "done"

1. `just check` passes (ruff + ty + pytest, no integration tests)
2. Any new public function has a test and a type-annotated signature
3. No new `print()` calls in production code paths (reporting/ excepted)
4. New patient-reading tools are registered in `PATIENT_SCOPED_TOOLNAMES`
5. If the change affects behavior, `README.md` reviewed and updated
6. Diff against `main` looks like what you'd want in a PR review
