# Three-minute OpenAI demonstration

## 1. Configuration and criteria

Select a GPT model, enter your own OpenAI key and click Test connection. Show the five SQLite-backed criteria and 100% active-weight total. The key stays masked and is not saved.

## 2. Evaluate four proposals

Use the included fictional PDFs and supplier metadata, then click Evaluate proposals. Observe F01-F15 progress. Open Leaderboard and Detailed scorecards; show an exact quotation/page, raw score, weighted contribution and peer gap. Python calculates PPI, tie-breaks and ranks. Industry comparisons are illustrative and separate from ranking.

## 3. Trace and export

Open Run details, show run ID/model/frozen criteria/events and download JSON. Explain that saved validated scores replay deterministically, while new model judgments may change. Do not present historical artifacts as a new OpenAI run.

## 4. Error case

Clear my key and click Test connection. A missing-key error should appear with no fallback request. Alternatively, change one criterion weight from 30 to 29 and try saving; the invalid 99% total is rejected without overwriting the valid configuration.

Public publication remains deferred. Full live output/screenshots should be captured only after the actual successful OpenAI evaluation.
