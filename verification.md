# OpenAI-only implementation verification - 25 October 2026

## Current evidence

- The user reports successfully testing their own OpenAI API key in the application. The key was not inspected or copied by the agent.
- 41 automated checks pass in the installed development environment. Core graph/SDK/UI checks use simulated model responses; they are not proof of a complete live OpenAI proposal evaluation. Optional historical transport checks may skip on a clean runtime without their separate dependencies.
- Four named fictional supplier PDFs contain three pages each and extract successfully.
- The F01-F15 workflow, deterministic scores/ranks, transactions, bounded retry, source quote checks, session ownership and checkpoint recovery have automated evidence.
- Local app offers only OpenAI API-key authentication. Backend policy blocks unsupported providers in local/public client creation, new runs and run recovery. Public mode offers gpt-4o-mini, gpt-4.1-mini and gpt-4.1 through the shared allowlist.
- Connection-test regression checks accept plain OK/fenced text and reject empty output; actual scorecards still pass strict F05 JSON/evidence checks.
- Key normalization, fixed official endpoint, safe error reporting and canary-secret isolation checks pass.

## Remaining evidence and limits

A complete independently recorded live OpenAI four-supplier run, a new model-specific sample export and current screenshots have not been captured in this revision. Existing historical result/image files are preserved and are not displayed as OpenAI examples. Do not edit their provider metadata to imply otherwise.

The public GitHub repository is https://github.com/deepakpolepalli/20261025-rfp. The user supplied the hosted application URL https://rfp-demo.streamlit.app/. A complete hosted live evaluation with a user key and filesystem lifecycle remain deployment checks. Session ownership is a classroom isolation measure, not production authentication. Recovery needs the original owner/session identity and surviving files; no cross-session recovery portal is implemented.

Exact quotation matching verifies provenance, not score fairness or semantic support. Fresh model evaluations may differ; fixed validated scores replay deterministically. Industry targets remain explicitly illustrative and do not determine rank. gpt-4o-mini is retained as requested despite its documented deprecated status; model access failures are explicit.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

For a new full model run, the user can run scripts/run_sample.py and enter a key through getpass, or evaluate the four fixtures in the UI and download the completed JSON. API calls incur the user's normal provider usage. No shared key or .env file is used.

## GitHub handoff checks - 29 October 2026

- Original development tree: 41 passed. Exact release snapshot: 36 passed, 1 skipped; historical transport files are excluded and their remaining optional check skips. No live API key was used.
- Deployment requirements resolve successfully using pip dry-run with installed packages ignored. This is a dependency-resolution check, not a hosted deployment test.
- Exact staged/index content passed scripts/audit_publication.py, including extracted text and metadata in the four fictional PDFs. A separate negative check confirmed that a synthetic credential is blocked without printing its value.
- Git ignore rules exclude local.md, environment files, secret files, runtime databases/uploads, historical exports/screenshots and retired helpers. Only reviewed source/docs/config/tests and fictional fixtures are published.
- Commit identity uses the account's GitHub noreply email. Automated pattern checks reduce exposure risk but cannot detect every possible sensitive value.
- Community Cloud settings: branch main, entry point streamlit_public.py, Python 3.12, no server secrets. Hosted connection/evaluation/export checks remain for the user after deployment.

## Cloud model and criteria correction - 29 October 2026

The uploaded main branch matched the local source. The differences were caused by the public entry point policy, which had restricted the model list and disabled editing. Both modes now offer gpt-4o-mini, gpt-4.1-mini and gpt-4.1 by default. Public criteria, runs, checkpoints and artifacts now use separate session directories. Weight edits apply only to that visitor and future runs. New sessions start with seeded criteria. Operator overrides remain supported.

47 tests pass in the installed development environment. New checks cover selecting GPT-4.1 in the public UI, backend acceptance of all three models, saved weights persisting within the session, isolation from other sessions, new-session defaults, invalid-total rejection, operator disablement and immutable run snapshots. These are simulated/local regression checks; they do not prove a billed live model evaluation.

The exact Git release snapshot passes 42 tests with 1 optional historical-helper check skipped; excluded development-only transport tests account for the difference from the installed local tree.
