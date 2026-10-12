# Runbook: GPU Encoder Out of Memory (error_code: ENCODE_OOM)

## Symptom
Job fails partway through (often 50-90% progress) with a CUDA or NVENC
out-of-memory error, referencing the session limit on the GPU device.

## Root cause
Most GPUs used for hardware encode (NVENC) cap the number of concurrent
encode sessions per device (commonly 3-8 depending on card/driver tier).
If the scheduler over-packs a node — e.g. after a burst of high-priority
jobs gets forced onto one box — a job can be admitted into a session slot
that then gets reclaimed, or genuinely exceed the device's session limit.

## Fix
1. Check how many concurrent NVENC sessions were active on `worker_node`
   at the failure timestamp (fleet metrics: `nvenc_sessions_active`).
2. If the node was over its session cap, this is a scheduler bug, not a
   content problem — requeue the job as-is to a less-loaded node.
3. If the node was within its normal cap, check whether this specific
   output_profile (typically 4K HEVC) uses an unusually large encode
   buffer — consider capping B-frame lookahead or bumping to a node with
   more VRAM for 4K HEVC jobs specifically.
4. Retrying on the same node without checking load will likely fail again
   if the node is still over-packed.

## When to escalate
If ENCODE_OOM clusters around a specific time window, escalate to platform
— it usually means the scheduler's admission control isn't accounting for
per-node session limits correctly.
