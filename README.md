# ProcureIQ - OpenAI RFP Evaluator

A **Streamlit + LangGraph + SQLite** mini-project. Upload 4-5 synthetic supplier proposals, evaluate criterion scores with evidence, compare suppliers and download a complete result.

**OpenAI is the only model provider. Every user supplies their own API key.** gpt-4o-mini is the default model option; local choices also include gpt-4.1-mini and gpt-4.1. Public mode fixes the option to gpt-4o-mini.

## Current status

The local app implements all five sections, F01-F15 workflow, bounded retries, SQLite checkpoints/recovery, configurable criteria, deterministic calculations/ranking, evidence validation and JSON download. Four fictional three-page PDFs are included.

The user reports successfully testing their OpenAI API key. Automated SDK/UI tests use simulated responses and do not expose a real key. A complete independently recorded OpenAI four-proposal run and public deployment are still pending; see [verification.md](verification.md).

## Setup and run

Use Python 3.12 from the project directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/init_db.py
python -m streamlit run app.py
```

Open the printed localhost URL. The seed is idempotent and preserves saved criteria edits. Runtime DBs/artifacts are ignored under data/.

To run tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Use the app

1. Inspect **Criteria** and confirm active weights total 100%.
2. Select an allowed **GPT model** and enter your **OpenAI API key** in the sidebar.
3. Click **Test connection**; it verifies that the selected model returns a non-empty response.
4. Open **Supplier input & evaluate**. Use the four included PDFs or upload 4-5 synthetic text PDFs and enter each supplier's metadata.
5. Click **Evaluate proposals**. Inspect **Leaderboard**, **Detailed scorecards** and **Run details**.
6. Download complete JSON from Run details.

New evaluation resets the batch but keeps your key. Clear my key removes it. A restarted/lost session requires re-entry. Recorded examples are offered only when their metadata identifies an OpenAI run; older artifacts are not presented as current model results.

## How the key is used

**Password input -> server-side session memory -> OpenAI(api_key=key) -> Responses API at F04.** No .env file is required or loaded. The key is never written to global environment variables, SQLite, checkpoints, logs, files or downloads. The server uses the official OpenAI endpoint and no shared fallback credential. API usage is billed to the key owner's account. Serve a published UI over HTTPS.

The API request uses store=False; this setting is not a guarantee about all provider retention. Model/schema/evidence rules remain the same for every allowed model. Provider/model settings are frozen per batch; a model change starts a new run.

| Operator setting | Behaviour |
|---|---|
| RFP_DATA_DIR | Runtime directory; defaults to data/ under the app. |
| RFP_OPENAI_MODELS | Local allowlist, default gpt-4o-mini,gpt-4.1-mini,gpt-4.1. |
| RFP_DEPLOYMENT_MODE | local by default; streamlit_public.py forces public. |
| RFP_ALLOW_CRITERIA_EDIT | true locally; public mode always disables editing. |

No server API key or secret file is needed for the public route. OpenAI's [model documentation](https://developers.openai.com/api/docs/models/gpt-4o-mini) marks gpt-4o-mini deprecated; it is retained as requested. Access/model errors are explicit and never trigger silent substitution.

## Workflow and storage

```text
F01 freeze criteria/model -> F02 select vendor -> F03 extract complete PDF
-> F04 OpenAI evaluation -> F05 validate -> F06 save scorecard -> F07 next vendor
-> F08 weighted scores -> F09 peer PPI -> F10 separate industry comparison
-> F11 rank -> F12 atomic persistence -> F13 finalize
F14 prepares permitted retries; F15 records failure without a partial leaderboard.
```

Only F04 uses an LLM. The orchestrator and conditional routes are Python rules. F02-F07 repeat for each vendor. SQLite business records hold criteria, frozen runs, supplier metadata, attempted calls/responses, scorecards, events and complete results. Separate SQLite checkpoints hold graph state. Original PDFs and page-aware extracted text remain private artifact files referenced by hashes/paths. Keys/SDK clients remain outside checkpoint state.

## Formulas and assumptions

- Weighted criterion contribution = `(score / maximum) * weight`; absolute score is their sum out of 100.
- Peer benchmark = best validated criterion score in the batch; gap = score minus benchmark.
- Relative % = `100 * score / benchmark`; zero benchmark gives zero with a warning.
- PPI = `sum(weight * relative %) / 100`.
- Rank by full-precision PPI descending, earlier submission date, higher historical experience, then normalized supplier name ascending. Assign sequential ranks after sorting.

Use Decimal precision 28 and two-decimal display; saved validated scores replay deterministically, but new model judgments may differ. Absolute score and industry index are not tie-breaks.

Industry targets are **illustrative classroom values**, not observed industry averages: technical/implementation/commercial/security/support = 7/7/6/8/7 out of 10. Show separate industry gaps and a weighted relative index; these never change rank. Missing/incompatible positive-weight targets make the index unavailable.

Supported inputs: 4-5 text-based PDFs, maximum 10 MiB/file, 40 pages/file and 120,000 extracted characters plus conservative model context checks. No OCR or silent text truncation. Experience is 0-10 and affects ties only. Invalid active weights are rejected rather than normalized. Positive scores without a verified exact quotation become zero with warnings. Quote matching proves traceability, not fair judgment; human procurement review remains necessary. RAG is outside this mini-project scope.

## Fixtures and actual sample output

Four synthetic PDFs live in fixtures/proposals/. Recreate them with:

```bash
python scripts/generate_proposals.py
```

To create a new OpenAI result from the four fixtures:

```bash
python scripts/run_sample.py --model gpt-4o-mini
```

The script prompts privately for a key using getpass and makes real billed API calls. It saves a completed result to sample_output/completed_run.json only after successful evaluation; the key is not saved. Existing historical artifacts are preserved but do not prove an OpenAI evaluation. See [DEMO.md](DEMO.md) for the live walkthrough.

## Deploy from GitHub to Streamlit Community Cloud

Preview the restricted public route locally with `python -m streamlit run streamlit_public.py`. It uses visitor keys and gpt-4o-mini only, disables criteria writes and never uses an operator-funded provider. GitHub repository: [deepakpolepalli/20261025-rfp](https://github.com/deepakpolepalli/20261025-rfp) (private). The user will deploy the app. Choose streamlit_public.py as the Community Cloud entry point and verify success/error/export on the actual URL. Do not configure a shared server OpenAI key. SQLite/filesystem retention across hosting restarts is not guaranteed; download completed results.

## Troubleshooting

- Model-policy error: choose an allowed model; rerun/restart after imported policy changes.
- HTTP 401: OpenAI rejected authentication. Check that the Platform key is active and belongs to the intended project. Surrounding whitespace is trimmed; quoted/header-form keys are rejected.
- HTTP 403/404: check project/model permissions and availability. HTTP 429: quota/billing or throttling, shown distinctly.
- Connection checks accept plain text and fenced replies. Actual proposal output must pass strict JSON/schema/evidence validation at F05.

Design: [PRD.md](PRD.md), [architecture.md](architecture.md), [AGENTS.md](AGENTS.md). Assignment: Agentic_RFP_Evaluation_Mini_Project.pdf. Personal reference paths stay only in ignored local.md.

### Community Cloud settings

1. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from the GitHub repository. Grant Streamlit access to the private repository if prompted.
2. Select branch **main** and main file **streamlit_public.py**.
3. In Advanced settings, choose **Python 3.12**. Leave Secrets empty: every visitor enters their own key in the application.
4. Deploy, test the connection, evaluate the four fictional PDFs and download the result.

See the [official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). The root requirements.txt supplies runtime dependencies. Database tables and seeded criteria are created automatically on first use; do not upload a local database.

### Repository privacy

The publication excludes personal notes, environment files, credentials, virtual environments, runtime data, uploaded documents, historical result exports/screenshots and retired development helpers. Only the four deliberately fictional proposal PDFs are included. API keys remain in server-side session memory and are sent to OpenAI for authentication; proposal text is sent to OpenAI for evaluation. Use synthetic documents for the classroom demo.

Before each push, run `python scripts/audit_publication.py --staged`. This scans the staged content without printing matched secret values. Ignore rules protect untracked files; the audit also checks explicitly staged files. This automated check does not guarantee that every possible sensitive value can be detected.
