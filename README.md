# Transcoding Operations Assistant

An on-call assistant for a video transcoding pipeline. It answers operator
questions about job status and failures, grounding every fix in an actual
runbook rather than inventing troubleshooting steps.

## Architecture

```
operator question
      │
      ▼
 assistant.py  ── Claude tool-use loop (claude-sonnet-4-5)
      │
      ├─ get_job_status / list_jobs ──► mock_api.py   (job-status API)
      │
      └─ search_runbooks / get_runbook ──► retrieval.py (TF-IDF over runbooks/*.md)
```

- **mock_api.py** — stands in for a real job-status REST service. 10 seeded
  jobs covering the common failure modes below, so the assistant has
  realistic data to reason over.
- **runbooks/** — 6 markdown runbooks, one per failure mode, each with
  symptom / root cause / fix / escalation sections.
- **retrieval.py** — from-scratch TF-IDF + cosine similarity, stdlib only.
  No embedding API, no vector DB, no network call — deliberate for a
  corpus this size, and it means retrieval evals run with zero API cost.
  Includes a calibrated relevance floor (score < 0.1 → no match) so
  unrelated questions get "no runbook found" instead of a confident wrong
  answer.
- **tools.py** — the Claude tool schemas and the dispatcher that wires
  both systems together.
- **assistant.py** — the CLI chat loop.
- **eval/** — scenario-based eval. Retrieval scenarios run with no API key
  (pure function checks); conversation scenarios run the full assistant
  and check both *which tool got called* and *what the final answer says*.

## Failure modes covered

| error_code | runbook | root cause |
|---|---|---|
| (none, status=stuck) | `stuck_queued_job.md` | zombied worker / hung read |
| `HDR_TONEMAP_FAIL` | `hdr_tonemap_failure.md` | missing HDR mastering metadata |
| `CODEC_UNSUPPORTED` | `codec_unsupported.md` | legacy codec, no decoder in farm build |
| `ENCODE_OOM` | `gpu_oom.md` | NVENC session limit / scheduler over-pack |
| `AV_SYNC_DRIFT` | `av_sync_drift.md` | VFR source, no CFR normalization |
| `OUTPUT_CORRUPT` | `output_corrupt.md` | interrupted finalize/mux step |

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python assistant.py
```

Try: `job-1004 failed, how do I fix it?` or `what's failing right now?`

## Running the eval suite

```bash
python eval/run_eval.py
```

Retrieval scenarios (7) always run and need no API key — they catch
retrieval regressions directly. Conversation scenarios (10) run live
against the assistant when `ANTHROPIC_API_KEY` is set, and check both the
tool-call path and the grounding of the final answer.

## Status against the plan

- [x] Step 1 — job-status API and runbook retrieval connected via Claude
  tool use.
- [x] Step 2 — eval suite with realistic questions and failure scenarios
  (retrieval: 7/7 passing with no API key; conversation suite ready to run
  once a key is supplied).
- [ ] Step 3 — demo to users, incorporate feedback.
- [ ] Step 4 — deploy, measure usage/time saved.
- [ ] Step 5 — case study.

## Case study (fill in after steps 3-4)

**Problem.** <1-2 sentences: what operators were doing manually before this
— e.g. grepping error codes against a wiki, pinging platform on-call for
known failure modes.>

**Approach.** Tool-use agent over two systems operators already had
(job-status API, runbook wiki) rather than a fine-tuned model or a new
knowledge base — kept the system of record in both cases, assistant is
just the retrieval+reasoning layer on top.

**Why TF-IDF, not embeddings, for retrieval.** <Fill in after real usage:
did the runbook corpus stay small enough that this held up, or did you
have to swap in a real embedding index? Either answer is a legitimate
result — record which.>

**Results.** <Fill in after deploy: time-to-resolution before/after,
% of incidents resolved without escalating to platform on-call, operator
adoption rate.>

**What I'd do differently.** <Fill in after user feedback — e.g. operators
wanted job history/trends, not just point-in-time status; or the
escalation routing needed to be a tool call, not just a runbook section.>
