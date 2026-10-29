# Agentic RFP Evaluation and Supplier Ranking

Version 1.3 | 25 October 2026 | Local implementation and verification

**Current delivery phase: P6 - GitHub publication and Community Cloud handoff.** The local Streamlit application, F01-F15 LangGraph workflow, SQLite persistence, four sample PDFs and JSON export are implemented. OpenAI API-key authentication is the only active model route. The user reports successfully testing their OpenAI key. Automated checks cover the application and provider boundaries; a complete live OpenAI four-supplier run has not been independently captured in this revision. GitHub publication is authorized; Community Cloud deployment will be performed by the user. See [verification.md](verification.md).

## 1. Purpose and design recommendation

Build a Streamlit application for procurement analysts that evaluates 4-5 fictional vendor proposals consistently, explains the evidence behind each score, compares suppliers within a batch and produces a reproducible leaderboard.

Use **Python + Streamlit + SQLite + LangGraph + OpenAI BYOK**. Every user supplies an OpenAI API key in the UI. The default model option is **gpt-4o-mini**; local configuration also allows gpt-4.1-mini and gpt-4.1, while public mode fixes the option to gpt-4o-mini. Keep one Evaluation Agent and deterministic graph orchestration; a separate agent swarm or service stack is unnecessary.

The LLM judges proposal content. Deterministic Python validates results and owns every formula, benchmark, tie-break and final rank. A leaderboard is decision support, not a contract award.

## 2. Requirements authority and design principles

Primary assignment: `Agentic_RFP_Evaluation_Mini_Project.pdf`, six pages, titled “Agentic RFP Evaluation and Supplier Ranking.” The PDF specifies an individual submission with a one-day timeline. Effort estimates below are planning assumptions, not a guarantee.

Additional user requirements: mandatory LangGraph with explicit states/workflow; 4-5 vendor uploads; raw/weighted scores; peer and industry benchmark comparisons with justifications/gap analysis; RAG deferred outside the current mini-project scope; GitHub-sourced Streamlit Community Cloud deployment; OpenAI BYOK for every run and no committed credentials.

Design principles: capability-first development, narrow tools, explicit phase boundaries and independent verification. Keep the implementation focused on this RFP evaluator and its stated requirements.

Coordination: `PRD.md` owns requirements, assumptions and the current phase; `architecture.md` owns implementation contracts and phase gates; `AGENTS.md` owns coding conduct; `agent.md` points to that single instruction source. Update the PRD before changing product behaviour. Never silently override the assignment or the user's LangGraph requirement.

## 3. Users and end-to-end workflow

- Evaluator: sees active criteria, uploads proposals, supplies metadata, evaluates a batch and inspects explanations.
- Instructor/user managing criteria: changes activation and weights in SQLite through the supplied seed/configuration script; a criteria editing UI is optional.
- Reviewer: reproduces arithmetic from the saved validated scores and criteria snapshot.

Required flow, in PDF order: start/load criteria -> upload PDFs and metadata -> create batch -> reload/freeze latest active criteria -> extract each proposal -> call LLM independently -> validate/normalize -> calculate absolute scores -> peer benchmarks/gaps/relative percentages -> PPI and tie-break ranking -> persist under one `RFP_RUN_ID` -> display/export.

## 4. Requirements and traceability

The matrix records local implementation status. Acceptance checks define the expected behaviour; actual observed evidence is in verification.md. A local pass does not establish public deployment or live OpenAI verification. IDs remain stable throughout coding and documentation.

| ID | Requirement | Source | Phase | Acceptance check  Local status |
|---|---|---|---|---|---|
| R01 | Use Streamlit, SQLite, JSON-capable LLM and LangGraph orchestration. | PDF pp.1-2; user | P1/P3/P4 | Installed environment starts; compiled StateGraph drives evaluation, not a hidden UI loop. | Implemented; local checks passed |
| R02 | Load/display active criteria, description, weight and maximum score from SQLite. Activation/weight changes require no prompt edits. | pp.2,4,6 | P1/P4 | Deactivate/change a criterion in DB; next run/UI reflects it. | Implemented; local checks passed |
| R03 | Accept 4-5 PDFs with supplier name, submission date and historical experience rating per file. | p.2 | P2/P4 | Reject invalid metadata and map each file to exactly one supplier. | Implemented; local checks passed |
| R04 | Create supplier entries and one batch/run ID; reload latest active criteria at evaluation start. | pp.2-3 | P1/P3 | One immutable criteria snapshot is shared by every supplier in the run. | Implemented; local checks passed |
| R05 | Extract clean PDF text and preserve source locations. | pp.2-3 | P2 | Four fixtures extract usable page text; empty/scanned/encrypted/corrupt inputs fail clearly. | Implemented; local checks passed |
| R06 | Evaluate each proposal independently using every active criterion; score, justification, evidence, risks and summary returned as JSON. | pp.2,5 | P3 | Real-model run produces separate scorecards; no competitor content in supplier prompts. | Implemented; local checks passed |
| R07 | Prompt uses only supplied evidence, requires scores in range and JSON only. | p.5 | P3 | Prompt assembled from criteria snapshot; injection fixture cannot change workflow/ranking rules. | Implemented; local checks passed |
| R08 | Validate/normalize missing, malformed and out-of-range model output; record warnings. | pp.2-3 | P2/P3 | Missing criteria, invalid types, duplicates, unknown IDs, invalid JSON and clipping cases follow section 6. | Implemented; local checks passed |
| R09 | Calculate absolute weighted score with active weights totalling 100%. | p.4 | P1 | Fixed calculation fixtures match section 7; invalid criteria block evaluation. | Implemented; local checks passed |
| R10 | Calculate best valid per-criterion benchmark, gap, relative %, weighted PPI; handle zero benchmark. | p.4 | P1 | Positive and all-zero benchmarks match section 7 without division by zero. | Implemented; local checks passed |
| R11 | Sort by descending PPI, earlier date, higher historical experience, ascending supplier name; then assign sequential ranks. | p.4 | P1 | Each tie-break level and near-equal precision case tested separately. | Implemented; local checks passed |
| R12 | Persist criteria, run and complete supplier results using minimum table fields. | p.4 | P1/P3 | DB reload reproduces leaderboard and JSON; result write is atomic and duplicate-safe. | Implemented; local checks passed |
| R13 | Provide Criteria, Supplier input, Leaderboard, Detailed scorecard and Run details sections. | p.6 | P4 | Every field from section 8 is visible in a complete UI walkthrough. | Implemented; local checks passed |
| R14 | Download complete run as valid JSON, including warnings and tie-break explanation. | pp.2,6 | P4 | Download parses and reconciles to saved SQLite result. | Implemented; local checks passed |
| R15 | Create at least four fictional supplier PDFs, each 2-4 pages, same procurement request, specified supplier profiles and sections. | p.5 | P2 | Page count/content review passes all four named suppliers in section 9. | Implemented; local checks passed |
| R16 | Supply complete source, clear folders, requirements.txt and DB creation/seed script. | p.6 | P1-P5 | Fresh environment can install, seed and run using README. | Implemented; local checks passed |
| R17 | Deploy complete working app to Streamlit Community Cloud via GitHub; submit public app URL. | p.6 | P6 | Public URL opens; deployed real-model successful run, error case and export work. | Pending public deployment |
| R18 | README covers setup, architecture, formulas, assumptions and actual screenshots. | p.6 | P5/P6 | Instructions reproduced; screenshots reflect running app, URL recorded after deployment. | README ready; current screenshots/public URL pending |
| R19 | Include sample JSON from one completed run and short demo of success plus a validation/error case. | p.6 | P5/P6 | Artifacts agree with stored run; demo evidence identified. | OpenAI full-run export/demo capture pending |
| R20 | Same validated scorecards and metadata produce identical arithmetic/order; each score traces to criterion, weight, evidence and rule. | p.6 | P1/P5 | Replay saved validated inputs without LLM reproduces metrics/ranks exactly. | Implemented; local checks passed |
| R21 | Explicit LangGraph state, nodes labelled deterministic/no-LLM or LLM-based/non-deterministic, conditional routing, bounded retry and checkpoint/resume. | user | P3/P5 | State/transition contracts in architecture implemented; fault/resume test avoids redoing completed supplier evaluations. | Implemented; local checks passed |
| R22 | Show raw scores, criterion weighted contributions, peer comparison and separate industry benchmark scoring/gaps with source labels. | user | P1/P4 | Hand-calculated reference metrics match; illustrative targets clearly labelled; industry baseline changes cannot change peer rank. | Implemented; local checks passed |
| R23 | OpenAI-only API-key authentication in local/public modes. No committed/persisted credentials or shared key clients. | user | P3-P6 | Key required; allowed model and official API endpoint; no other provider or server-key fallback; keys absent from DB/checkpoints/logs/exports. | Implemented; user reports key test passed |
| R24 | Deferred feature expansion outside the mini-project PDF. | future only | Deferred | No additional retrieval feature is required by this delivery. | Deferred |

## 5. Scope and operating assumptions

These are explicit project decisions where the PDF is silent; they are not additional assignment mandates.

- One evaluation batch per execution; sequential supplier processing. UI accepts 4-5 suppliers as requested; supplied demo uses all four named suppliers. Smaller internal calculation fixtures are allowed for testing only.
- Submission date is a valid ISO calendar date, with no hidden time-of-day ordering. Experience rating is a user-entered finite number from 0 to 10; it affects ties only, not content scores.
- Supplier names are trimmed, non-empty and unique after Unicode normalization and case-folding within a batch. Canonical normalized names define ascending tie order. Preserve original display names. Duplicate identical files within a batch are rejected with a helpful message.
- Initial limits: 4-5 PDFs, 10 MiB per file, 40 pages per file and 120,000 extracted characters per supplier. Validate before provider calls. Never silently truncate a proposal; reject over-limit input. Check actual model token capacity before calling; lower limits if needed.
- Text-based PDFs only for MVP; OCR is outside scope. Explain how to provide a readable PDF when extraction fails.
- Any invalid criteria configuration or unrecoverable supplier failure blocks the whole batch leaderboard. Save failure details; do not silently omit a supplier or present a partial ranking as complete.
- Normalized zero rows for missing/invalid criterion scores remain in completed scorecards with visible warnings; a completed run can have warnings. Supplier-level parse/extraction/provider failure is different and fails the batch after bounded retry.
- No actual supplier data, procurement decisions, emails, external browsing by the model or autonomous award actions. Public demo accepts synthetic content only and exposes no cross-session run browser.
- **Core evaluation uses complete extracted proposal text**, with page labels and verified evidence quotes. No retrieval subsystem is needed for the core mini-project. Long-document retrieval and interactive Q&A are deferred; fail clearly on unsupported input size rather than silently truncating or enabling a new retrieval mode.
- **Provider:** OpenAI only, in local and public modes. No provider switch or fallback. The user enters a key in a password field; the server creates a request-scoped client using that key explicitly.
- **Models:** gpt-4o-mini is the default option. Local choices include gpt-4.1-mini and gpt-4.1; the allowlist is configurable. Public mode allows gpt-4o-mini only. Model selection and prompt version remain fixed within one run; changing model starts a new evaluation.
- **Credentials:** key stays in server-side session memory/runtime client only. Never save it to .env, global environment variables, SQLite, graph checkpoints, logs or exports. No server key is used as fallback. Clear my key removes the session value; New evaluation retains it. Re-enter after session loss. No .env file is required.
- **Connection test:** a completed non-empty model reply confirms connectivity; it is not parsed as a scorecard. Strict JSON/schema/evidence validation applies at F05 during actual proposal evaluation.
- **User verification:** the user reports their OpenAI key works. This is evidence of their connection check, not an independently observed complete proposal evaluation. New full-run exports must record the actual OpenAI model and validated evidence.
- Cloud URL publication is part of eventual submission. Hosting credentials, repository, model key and deployment availability remain dependencies for P6; do not fabricate them.

## 6. Validation and evidence policy

Input validation is deterministic. Active criteria must exist, have unique IDs, non-empty names/descriptions, finite positive maximum scores and non-negative finite weights summing exactly to 100 when parsed as decimal values. Zero-weight active criteria are allowed; an all-zero weight set is not. Seeds use 30/20/20/20/10 and max score 10.

| Model-result issue | Required treatment |
|---|---|
| Invalid JSON, wrong top-level structure or unusable criteria list | One corrective JSON call with same supplier text/snapshot; if still invalid, fail supplier and batch. Do not invent a full zero scorecard. |
| Missing active criterion | Insert score 0, empty evidence, “No valid model assessment returned”, warning and normalized status. |
| Missing/non-numeric/bool/non-finite score | Normalize to 0 with warning. Numeric strings may be parsed as Decimal with a coercion warning. |
| Finite score outside 0..DB max_score | Clip to range, keep raw value, record warning and adjusted status. |
| Unknown criterion ID | Drop it with warning; never modify active criteria from output. |
| Duplicate criterion ID | Treat that criterion as invalid and normalize it to 0 with warning, rather than selecting the most favourable value. |
| Supplier name or max_score mismatch | Use uploaded metadata and criteria snapshot; retain mismatch warning. Model cannot redefine either. |
| Missing/wrong-type justification/evidence | Normalize text to empty/default with warning. Positive score requires verifiable supporting evidence or becomes 0. |
| Evidence quote absent from extracted text | Mark unverified and set affected score to 0; exact matching after documented whitespace normalization. Never manufacture supporting text. |
| Malformed risks/summary | Normalize to empty list/text with warning; reject nested executable/HTML payload interpretation. |

Evidence field stays compatible with the brief's JSON string. Prompt requests a short quotation and page label; the validator resolves the quote against extracted page text and records page numbers separately. Quote matching checks traceability, not whether the claim warrants the score; human review remains necessary. Missing proposal information can legitimately score zero and explain the absence without a supporting quote. Preserve raw response privately within local synthetic run records for audit, alongside normalized values and warnings; never execute it or render raw HTML.

Retry budget: at most three provider calls per supplier across all causes, including one corrective JSON call; two transport retries maximum, bounded timeout/backoff. No infinite agent/tool loops. Already parseable field defects use deterministic normalization, not repeated model calls.

## 7. Scoring and ranking contract

For active criterion c and supplier s, let score `x[s,c]`, maximum `m[c]`, weight percentage `w[c]` and benchmark `b[c]` be the validated values.

- Raw criterion score: `x[s,c]`; criterion weighted contribution: `a[s,c] = (x[s,c] / m[c]) * w[c]`.
- Absolute weighted score out of 100: `A[s] = sum(a[s,c])`. Show both raw and weighted values.
- Benchmark: `b[c] = max(x[s,c])` across all completed validated supplier scorecards in this batch. Normalized zero contributes zero; excluded unknown fields never contribute.
- Gap in score points: `g[s,c] = x[s,c] - b[c]`.
- Relative performance: `r[s,c] = 100 * x[s,c] / b[c]` if `b[c] > 0`; otherwise **0 for every supplier**, with a zero-benchmark warning. Keep criterion weight; do not redistribute it.
- PPI out of 100: `PPI[s] = sum(w[c] * r[s,c]) / 100`.
- Sort key: `(-PPI, submission_date, -experience_rating, canonical_supplier_name)`. Assign ranks `1,2,3,...` only after sorting. Absolute score is displayed but is not a tie-break.

Use Decimal arithmetic with a fixed precision of 28 significant digits and ROUND_HALF_EVEN, in stable criterion-ID order. Sort using full computed Decimal PPI before display rounding. Persist exact computed decimal strings in result_json; SQLite REAL summary columns are display/query convenience and must not drive replay. Display two decimal places. Equal displayed values may have different full-precision PPIs; explain this in run details. The unique canonical-name rule eliminates unresolved complete ties.

Worked check with two criteria (weights 60/40, maxima 10): supplier A scores 8/5, B scores 6/10. Benchmarks are 8/10; A absolute = 68, relative = 100/50, PPI = 80; B absolute = 76, relative = 75/100, PPI = 85. B ranks first. This illustrates why absolute score and PPI must not be confused. Separate tie fixtures verify date, experience and name ordering.

Reproducibility means replaying the same **validated** scorecards, criteria snapshot, metadata and rules version produces the same metrics and ordering. Fresh LLM calls are new evaluations and can differ.

### Separate industry benchmark comparison

This user-added comparison is separate from the PDF's peer benchmark. Store a versioned reference target `t[c]` per active criterion on the same maximum-score scale, with sector, date, methodology and provenance. Industry gap = `x[s,c] - t[c]`; industry relative % = `100*x[s,c]/t[c]` for positive targets; Industry Benchmark Index = `sum(w[c]*industry_relative[s,c])/100`. Values above 100 are valid and not clipped. Missing/zero/incompatible targets are unavailable, with a reason; any unavailable positive-weight target makes the overall industry index unavailable. Do not redistribute weights. This metric never changes peer PPI or the required ranking key.

No real industry dataset was supplied. Default to **Illustrative classroom baseline**, explicitly labelled throughout UI/export: technical 7, implementation 7, commercial 6, security 8, support 7, all out of 10. These are invented teaching targets, not measured industry averages. Real baseline mode requires a comparable supplied source and criterion mapping; otherwise show unavailable. Snapshot the baseline with the run, and never ask the LLM to invent it.

## 8. Screens and export

| Section | Required contents |
|---|---|
| Criteria | Active name/description, weight, max score, total weight; invalid-config message. |
| Supplier input | Multiple uploads, file-to-metadata mapping, names/dates/experience, validation messages, OpenAI-only provider display and required key/model controls, Evaluate button and graph progress. |
| Leaderboard | Sequential rank, supplier, absolute weighted score, peer PPI, separate industry index/source label, date, experience. |
| Detailed scorecard | Raw criterion score/max, weighted contribution, peer benchmark/gap/relative %, industry target/gap/relative % and source label, weight, evidence/page, justification and normalization warnings. |
| Run details | RFP_RUN_ID, status, provider/model/settings (no key), criteria snapshot, F01-F15 events, warnings, reproducibility caveat, tie-break explanation and JSON download. |

Export includes BYOK-safe provider metadata (never keys), industry baseline snapshot/provenance and metrics, RAG excluded from core scope, schema/rules/prompt versions, run ID/timestamps/status, criteria snapshot and hash, file hashes, supplier metadata, raw and normalized criterion scores, evidence/page verification, warnings, risks, summaries, all calculations, sort keys and ranking explanations, model identity/settings/usage and safe node event summaries. No keys, environment dumps, raw PDF bytes, hidden reasoning or checkpoint internals in download. Complete export and DB result must agree.

## 9. Synthetic proposal specification

Common fictional procurement request: a supplier onboarding and procurement analytics portal with SSO, ERP integration, reporting, role-based access, audit logs, migration, training and post-launch support. Define a shared request and a clear 0-10 scoring rubric before generating proposals; store both with fixtures. This scenario and rubric are project assumptions.

| Supplier | Required relative profile |
|---|---|
| Apex Systems | Strong technical design/security, higher price, moderate schedule. |
| BrightPath Tech | Lowest price, fast timeline, weak compliance detail, limited experience. |
| NexaWorks | Balanced proposal, strongest implementation plan/support. |
| Orbit Digital | Strong experience/references, vague integration plan, medium price. |

Every PDF is 2-4 pages and includes executive summary/understanding, solution/implementation, timeline/team/milestones, price table/assumptions, security/compliance/risks, support/experience/references. Intentionally vary detail and omissions within sections; mark every proposal and reference fictional. Use one currency/comparable scope and explicit taxes, recurring charges and assumptions. Do not preassign scores or a guaranteed winner. Metadata experience ratings are separate from the LLM's evidence-based Support & Experience criterion.

## 10. Delivery phases and evidence

P1-P4 have local implementation evidence; P5 has a real saved result, automated checks and browser captures. OpenAI live verification and P6 publication remain open. The detailed node contracts and phase tasks live in architecture.md. Update the single current-phase field above when actual work starts; record changes with actual evidence in verification.md. A later user request to implement multiple phases authorizes progressing through their gates without repeatedly asking for permission.

| Phase | Planned outcome | Dependency / exit gate | Indicative effort |
|---|---|---|---|
| P0 | PRD, architecture, agent instructions and traceability. | Initial design completed; user subsequently requested full local implementation. | This task |
| P1 | Schema/seed, typed contracts, validation and deterministic scoring/ranking tools including separate industry comparison. | Hand-calculated fixtures, tie-break and DB transaction checks pass. | 1.5 h |
| P2 | Four synthetic PDFs, extraction and normalization. | Page/content checks, evidence matching and malformed response cases pass without live LLM. | 1.5 h |
| P3 | OpenAI client, versioned prompt, F01-F15 workflow and SQLite checkpoints. | Graph, bounded failures, provider policy, key isolation and recovery checks pass; user reports connection success. | Implemented locally |
| P4 | Complete Streamlit sections, progress and download. | All four proposals complete one saved/exportable run; reruns do not duplicate it. | 1 h |
| P5 | Integration regression, screenshots, README, sample JSON and demo. | R01-R16 and R18-R23 have evidence; real-model evidence labelled separately from mocks. | 1 h |
| P6 | GitHub-sourced Community Cloud deployment and public URL. | Public entry point uses visitor OpenAI key and gpt-4o-mini; success/error/export verified on the published app. | Deferred for now |
| Deferred; not a current phase | Features outside the mini-project PDF. | Separate request required. | Not estimated |

These roughly eight implementation hours assume credentials and hosting access are ready. Do not drop deployment or error handling to fit the estimate; report blockers honestly.

## 11. Rubric and submission completion

| PDF rubric | Marks | Main requirements |
|---|---:|---|
| Agentic workflow/tool use | 20 | R01, R04, R21 |
| PDF extraction/prompting | 15 | R05-R07, R15 |
| Validation/scoring | 20 | R08-R10 |
| Peer ranking/tie-breaks | 20 | R10-R11, R20 |
| SQLite/persistence | 10 | R02, R12 |
| Streamlit UI | 10 | R03, R13-R14 |
| Documentation/testing | 5 | R16, R18-R19 |

Final submission requires source + requirements.txt; schema/seed script; four 2-4-page PDFs; public working Community Cloud URL; README with setup/architecture/formulas/assumptions/screenshots; completed-run JSON; short successful/error demo. Local success alone does not complete submission.

## 12. Current decisions and evidence

OpenAI is the only active provider. Local and public users supply their own key; gpt-4o-mini remains the requested default option. The LLM judges proposal content; all routing, validation, arithmetic and ranking use Python. Industry comparison is illustrative and separate from peer rank. RAG is outside the current mini-project scope.

On 25 October 2026 the user confirmed their OpenAI key works and requested removal of the previous provider choice and its design details. The app/client policy and all Markdown documents now reflect the OpenAI-only route. No key was requested through chat, inspected or written to files. Existing historical evidence files are preserved but are not offered as current OpenAI examples.

41 automated checks pass in the installed environment. Verification distinguishes simulated SDK/UI checks, the user-reported successful connection, and a complete live OpenAI RFP run that still needs to be captured. The user has authorized GitHub publication and will perform Community Cloud deployment. See verification.md and README.md for current commands and limits.
