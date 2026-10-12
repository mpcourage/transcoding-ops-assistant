"""Realistic eval scenarios for the transcoding ops assistant.

Each scenario is one of two kinds:
- "retrieval": checks the runbook index alone (query -> expected runbook).
  No API key needed, catches retrieval regressions directly.
- "conversation": a full operator question, checked against the live
  assistant (needs ANTHROPIC_API_KEY) for correct tool use and that the
  final answer is grounded in the right runbook/job data.
"""

RETRIEVAL_SCENARIOS = [
    {
        "name": "stuck_no_progress",
        "query": "job stuck in processing, progress not moving, no error code",
        "expected_runbook": "stuck_queued_job.md",
    },
    {
        "name": "hdr_tonemap",
        "query": "libplacebo tone-map failure BT.2390 mastering display metadata missing",
        "expected_runbook": "hdr_tonemap_failure.md",
    },
    {
        "name": "codec_unsupported",
        "query": "decoder not found for codec_id, Indeo 5, AVI container",
        "expected_runbook": "codec_unsupported.md",
    },
    {
        "name": "gpu_oom",
        "query": "CUDA out of memory nvenc session limit reached",
        "expected_runbook": "gpu_oom.md",
    },
    {
        "name": "av_sync_drift",
        "query": "audio video drift 180ms variable frame rate source",
        "expected_runbook": "av_sync_drift.md",
    },
    {
        "name": "output_corrupt",
        "query": "moov atom missing playback fails at segment boundary",
        "expected_runbook": "output_corrupt.md",
    },
    {
        "name": "no_match_unrelated",
        "query": "billing invoice discrepancy for last month's encoding minutes",
        "expected_runbook": None,  # should NOT confidently match any runbook
    },
]

# Realistic operator questions, with what a correct answer must demonstrate.
CONVERSATION_SCENARIOS = [
    {
        "name": "simple_status_lookup",
        "question": "What's the status of job-1002?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["processing", "63"],
    },
    {
        "name": "stuck_job_diagnosis",
        "question": "job-1003 looks stuck, what should I do?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["zombie", "requeue"],
    },
    {
        "name": "hdr_failure_fix",
        "question": "job-1004 failed, how do I fix it?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["metadata", "mastering"],
    },
    {
        "name": "unsupported_codec_fix",
        "question": "Why did job-1005 fail and what's the fix?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["codec", "legacy"],
    },
    {
        "name": "gpu_oom_fix",
        "question": "job-1006 died with a CUDA error, what's going on?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["session", "node"],
    },
    {
        "name": "list_failing_jobs",
        "question": "What's failing right now across the fleet?",
        "expects_tool": "list_jobs",
        "expected_keywords": ["job-1004", "job-1005", "job-1006"],
    },
    {
        "name": "sync_drift_fix",
        "question": "QC flagged job-1008 for audio drift, what's the root cause?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["variable frame rate", "cfr", "vfr"],
    },
    {
        "name": "nonexistent_job",
        "question": "What's happening with job-9999?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["no such job", "not found", "doesn't exist", "don't have"],
    },
    {
        "name": "corrupt_output_fix",
        "question": "job-1010 finished but QC rejected the output, why?",
        "expects_tool": "get_job_status",
        "expected_keywords": ["moov", "re-run", "finalize"],
    },
    {
        "name": "out_of_scope_question",
        "question": "Can you also tell me this month's AWS bill for the encode farm?",
        "expects_tool": None,
        "expected_keywords": ["don't have", "can't", "no tool", "not able"],
    },
]
