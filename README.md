# AI-powered Electronic Health Record Patient Portal Assistant

[![CI](https://github.com/ladislav-lettovsky/ai-ehr-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/ladislav-lettovsky/ai-ehr-assistant/actions/workflows/ci.yml)

An AI-powered, guardrailed patient education and navigation assistant that explains Electronic Health Records (EHR) in plain language — built as a capstone project for the **UT Austin Postgraduate Program in AI / ML (Agentic AI specialization)**.

## Architecture

```
User Query
    │
    ▼
┌──────────┐     ┌──────┐
│  agent   │◄───►│ tool │   (ReAct loop)
└────┬─────┘     └──────┘
     │ draft_answer
     ▼
┌──────────┐
│ validate │   (7-dimension rubric)
└────┬─────┘
     │
     ▼
┌────────┐
│ policy │   (deterministic safety override)
└────┬───┘
     │
     ▼
    END
```

The system uses a **ReAct (Reasoning + Acting) pattern** orchestrated via LangGraph with four processing nodes:

| Node | Role |
|------|------|
| `agent` | ReAct agent — invokes the LLM with tools |
| `tool` | Executes LLM-requested tool calls |
| `validate` | Cross-checks claims against tool outputs (7-dimension rubric) |
| `policy` | Final safety override — deterministic enforcement |

## Features

- **11 specialized tools** — patient records (SQLite), lab/medication education (CSV), safety policy routing
- **Safety-first design** — emergency escalation, medication change refusal, PHI protection, prompt injection resistance
- **7-dimension validation** — guardrail adherence, factual groundedness, query resolution, literacy/language adherence, tone, actionability
- **Personalization** — responds in patient's preferred language, adjusts to health literacy level
- **CLI interface** — run individual queries or all 10 built-in test cases

## Quick Start

```bash
git clone https://github.com/ladislav-lettovsky/ai-ehr-assistant.git
cd ai-ehr-assistant

# Create virtual environment and install
uv venv .venv
source .venv/bin/activate
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

## CLI Usage

```bash
# Run all 10 built-in use cases
uv run -m ehr_assistant

# Run a single query
uv run -m ehr_assistant -p P001 -q "What does my Hemoglobin A1c result mean?"

# With audit report and JSON output
uv run -m ehr_assistant -p P001 -q "What are my medications?" --report --json-output results/

# Verbose logging
uv run -m ehr_assistant -p P001 -q "Summarize my last visit" -v

# Skip JSON output
uv run -m ehr_assistant --no-json
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `-p`, `--patient-id` | Patient ID (default: run all 10 test cases) |
| `-q`, `--query` | User query (required with `--patient-id`) |
| `--max-steps` | Max ReAct steps (default: 5) |
| `--json-output DIR` | Directory for JSON results (default: `results/`) |
| `--no-json` | Skip JSON output |
| `--report` | Show terminal audit report |
| `-v`, `--verbose` | Set log level to DEBUG |

## Test Cases

| # | Patient | Scenario | Expected Behavior |
|---|---------|----------|-------------------|
| 1 | P001 | Lab result explanation (HbA1c) | Educational answer with citations |
| 2 | P002 | Medication education (atorvastatin) | Side effects + red flags |
| 3 | P003 | Visit note summary | Summary in patient's language |
| 4 | P004 | Medication change request | Escalate to clinician |
| 5 | P005 | Emergency (chest pain + high K) | Emergency escalation |
| 6 | P006 | Third-party medication query | Privacy refusal |
| 7 | None | Non-healthcare query | Out-of-scope refusal |
| 8 | P004 | Cross-patient PHI access | PHI protection |
| 9 | "" | Prompt injection | Injection resistance |
| 10 | P001 | Empty query | Greeting / help prompt |

## Project Structure

```
ai-ehr-assistant/
├── src/
│   └── ehr_assistant/
│       ├── __init__.py              # Package version
│       ├── config.py                # Environment-based configuration
│       ├── db.py                    # SQLite connection management
│       ├── data.py                  # CSV DataFrame loaders (cached)
│       ├── utils.py                 # Shared helpers (norm_text, to_json)
│       ├── tools/
│       │   ├── __init__.py          # Tool registry + constant sets
│       │   ├── patient.py           # 7 patient-scoped EHR tools
│       │   ├── education.py         # 3 CSV-lookup education tools
│       │   └── policy.py            # Safety policy routing tool
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── state.py             # AgentState TypedDict + init_state()
│       │   ├── nodes.py             # Graph node functions
│       │   ├── graph.py             # build_graph() → compiled LangGraph
│       │   └── prompts.py           # System + validation prompts
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── json_writer.py       # Structured JSON output
│       │   └── terminal.py          # Terminal audit report
│       └── runner.py                # CLI entry point
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_tools.py                # Tool unit tests
│   ├── test_policy.py               # Policy routing tests (needs API key)
│   ├── test_nodes.py                # Node logic tests
│   └── test_integration.py          # End-to-end tests (needs API key)
├── data/                              # Data files (UT Austin course materials)
│   ├── health_portal.db
│   ├── medication_education.csv
│   ├── patient_friendly_lab_explanations.csv
│   ├── safety_policy_rules.csv
│   └── trusted_sources_catalog.csv
├── .scratch/                          # Sanctioned scratchpad for AI agents (git-kept, .gitignored contents)
├── .claude/                           # Claude Code project config
│   └── settings.json
├── .cursor/                           # Cursor IDE rules
│   └── rules/
│       ├── 00-always.mdc              # Always-on invariants + check gate
│       ├── langgraph.mdc              # LangGraph patterns (scoped)
│       ├── tests.mdc                  # Pytest conventions (scoped)
│       └── writing-rules.mdc          # Meta-guide for rule authoring
├── .github/workflows/ci.yml           # GitHub Actions CI (check + integration jobs)
├── AGENTS.md                          # AI agent memory — invariants, architecture, pitfalls
├── CLAUDE.md                          # Claude Code entry point → AGENTS.md
├── CONTRIBUTING.md                    # Contribution guide
├── LICENSE                            # MIT (source code only; see README Acknowledgments for data)
├── README.md                          # You are here
├── justfile                           # Task runner — `just check` = full quality gate
├── pyproject.toml                     # Project metadata, deps, ruff/ty/pytest config
├── uv.lock                            # Reproducible dependency lockfile
├── .pre-commit-config.yaml            # Ruff + ty pre-commit hooks
├── .env.example                       # Environment variable template
└── .gitignore
```

## Tech Stack

- **Agent Framework**: LangGraph, LangChain
- **LLMs**: OpenAI GPT-4o-mini (generator + policy classifier), GPT-4o (validator)
- **Data**: SQLite, Pandas, Pydantic
- **Runtime**: Python 3.12+
- **Package Management**: uv

## License & Acknowledgments

### Source code
The source code in this repository is released under the [MIT License](LICENSE).
Copyright (c) 2026 Ladislav Lettovsky.

### Data
The files under `data/` — `health_portal.db`, `medication_education.csv`,
`patient_friendly_lab_explanations.csv`, `safety_policy_rules.csv`, and
`trusted_sources_catalog.csv` — are course materials provided by the
**University of Texas at Austin Post-Graduate Program in Artificial Intelligence
& Machine Learning**. They are included here solely to make the demo
reproducible and are retained under their original course-provided terms.
They are **not** redistributed under the MIT License and are **not** covered
by the copyright notice above.

### Built with
- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) — LLM integrations
- [OpenAI](https://openai.com/) — underlying LLM

## Author

**Ladislav Lettovsky** — [GitHub](https://github.com/ladislav-lettovsky)