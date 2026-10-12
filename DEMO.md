# Operator Demo Script

A ~15-minute walkthrough for showing this to actual transcoding operators
and collecting structured feedback. Goal: find out whether this would
genuinely change how someone works an on-call shift, not just whether the
demo looks impressive.

## Before the session

- `export ANTHROPIC_API_KEY=...` and confirm `python3 assistant.py` starts
  cleanly.
- Have this doc open to read questions from, but let the operator drive
  the keyboard if they're willing — what they type unprompted is more
  informative than what you type for them.
- Mention up front: all job data is mocked (10 seeded jobs, 6 failure
  modes) — they're evaluating the *interaction model*, not real fleet
  data.

## Walkthrough (run these, narrate briefly before each)

1. **Simple status check** — grounds them in the basic loop.
   > "What's the status of job-1002?"

2. **A stuck job with no error code** — the ambiguous case, no error_code
   to pattern-match on.
   > "job-1003 looks stuck, what should I do?"
   Point out: it reasoned from symptom (no progress, no error) to the
   right runbook, not from an error code.

3. **A failed job with a fix** — the core value case.
   > "job-1004 failed, how do I fix it?"
   Ask the operator: does this match what *they'd* actually do, or is a
   step missing/wrong?

4. **Fleet-wide question** — different tool path (list_jobs vs
   get_job_status).
   > "What's failing right now?"

5. **Out-of-scope question** — tests whether it stays honest instead of
   guessing.
   > "What's our AWS bill for the encode farm this month?"
   It should decline, not invent a number. This is the one to watch
   closely — confident wrong answers are worse than no answer.

6. **Let them drive** — hand over the keyboard, give no prompt. What they
   ask unprompted tells you more than the scripted scenarios.

## Feedback questions (ask right after, while it's fresh)

1. For the job-1004 scenario: would you have trusted that fix enough to
   act on it directly, or would you still go verify the runbook yourself?
2. Compared to how you actually find this information today (wiki, Slack,
   asking a senior on-call) — faster, slower, about the same?
3. Did anything it said sound confident but wrong, or confident but
   incomplete?
4. What's the single most common on-call question this *doesn't* handle
   yet that you wish it did?
5. Would you want this to be able to take action (requeue a job, page
   someone) or should it stay read-only/advisory?
6. On a 1-5 scale: how comfortable would you be relying on this
   unsupervised during a real shift? Why that number and not higher?

## Capturing results

Log each session as one row: operator (role/tenure helps — a new hire's
reaction differs from a 5-year veteran's), date, scenarios run, the six
answers above, and anything they said verbatim that's worth quoting later.
This is the raw material for the case study's "Results" section — actual
quotes beat a summary.
