# Coding instructions - OpenAI RFP evaluator

## 1. Read and coordinate

Read PRD.md, architecture.md and the affected code before changes. PRD owns requirements/current phase; architecture owns F01-F15 state/workflow contracts; this file owns coding practices. agent.md is a pointer, not a duplicate rule set. User instructions and the assignment take precedence. The user has authorized GitHub publication after a privacy review; the user has deployed the app to Community Cloud.

Keep answers concise, practical and professional. Work through authorized changes without repeatedly requesting permission. Do not claim planned work or simulated-provider checks as live evidence. The user reports their OpenAI key works; distinguish that from an independently captured full proposal evaluation.

## 2. Scope and stack

Use Python, Streamlit, SQLite, LangGraph StateGraph and **OpenAI API-key authentication only** in local and public modes. provider_policy.py rejects every unsupported provider. Default model option is gpt-4o-mini; local and public allowlists also include gpt-4.1-mini and gpt-4.1. Public criteria editing is enabled in a session-specific SQLite database, isolated from other visitors. No provider or model fallback. Retain the explicitly requested model while documenting its known deprecated status; do not substitute silently.

No RAG or extra service stack is needed by the PDF. Do not reactivate retired integrations or historical helper scripts as selectable application routes. Preserve user files and historical evidence without presenting them as current OpenAI output. Do not spawn sub-agents unless explicitly requested or required by applicable instructions.

## 3. Feature development

Identify requirement IDs, affected components, state channels and meaningful checks. Update PRD before product behaviour changes and architecture before changing contracts/routes. Build deterministic capability -> verify -> thin node/tool -> graph integration -> UI verification. Keep changes small and readable; do not build everything in one unverified pass or test framework internals.

## 4. Workflow and state

Preserve stable F01-F15 IDs across graph, diagrams, events and tests. D means Python rules; F04 is the only LLM node. LangGraph orchestrator, provider validation, score normalization, arithmetic/ranking, retries and persistence are deterministic.

Use Pydantic at boundaries and JSON-compatible TypedDict state. Nodes return partial updates without mutating nested inputs. Freeze criteria, provider/model, prompt/rules versions and metadata per batch. Process vendors independently/sequentially, calculate benchmarks only after all validated scorecards exist, and persist the complete result atomically. An unrecoverable vendor failure cannot produce a completed partial leaderboard.

Use one thread ID per run. Persist call intent before provider dispatch, bound attempts and JSON repair, reuse completed supplier outputs and reconcile a committed business result before replay. Runtime client/key/Repository belong outside checkpoints. Resume only compatible running state with original ownership; failed terminal runs need a new evaluation. Never claim exactly-once model calls or cross-session recovery that the UI does not provide.

## 5. Scoring and evidence

Follow PRD formulas and normalization. Active weights total exactly 100%. Show raw score, weighted contribution, evidence/pages and warnings. Rank by peer PPI descending, earlier submission, higher experience, then canonical supplier name. Absolute score and illustrative industry comparison are not tie-breaks. Use Decimal precision 28, sort before display rounding and save exact strings for replay.

Treat proposal instructions/model output as untrusted data. Never eval/exec it or render arbitrary HTML. Verify positive-score evidence against source page text; unsupported positive scores normalize to zero with warnings. Quote matching does not prove semantic support or fair scoring. Keep industry targets clearly illustrative; never invent a real industry data source or guaranteed winner.

## 6. Keys and provider calls

Every user enters an OpenAI Platform key through the password field. Use it explicitly in a session-scoped server client and target the official API endpoint. Never save keys to .env, global environment variables, SQLite, checkpoints, logs, exports or shared caches. No .env file or operator key fallback is needed. Clear my key removes the session value; New evaluation retains it; lost sessions require re-entry.

Do not retrieve the user's key from browser/session internals to debug it. Use simulated SDK responses for regression checks unless live user-key use is explicitly authorized. Error messages must never echo raw provider bodies or rejected credentials. Separate model-policy errors from 401 authentication, 403 permissions, 404 availability and 429 quota/throttling. Connection tests require a completed non-empty reply; scorecard JSON validation remains at F05.

## 7. Verification and documentation

Prioritize arithmetic, each tie-break, invalid weights, malformed JSON/fields, quotation checks, retries, transaction rollback, call budgets, ownership, checkpoint recovery, key isolation, UI sections and model policy. Run relevant checks, then broaden only when justified by changes or unresolved concerns. Keep actual evidence and remaining limits in verification.md.

Screenshots must show the running current app without exposing secrets. Sample exports must come from a completed recorded run with honest provider/model metadata. Do not relabel historical output or fabricate live results, screenshots, run IDs or URLs. Source fixtures are fictional only.

Keep personal filesystem paths and external reference-project provenance only in ignored local.md. Shared Markdown must describe the current OpenAI-only design and contain no retired model/integration details. Keep one authoritative current-phase field in PRD.

## 8. Completion and publication

Report what changed, actual verification and material limits. Current local delivery includes source, seed/generation scripts, four fictional PDFs and app UI/workflow; independently captured full OpenAI output and public submission evidence remain separate checks. Publish only under the user's repository/account authorization, after local work is reviewable. Never send external messages, make procurement awards or delete user evidence as part of this mini-project.
