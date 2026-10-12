# Runbook: Job Stuck in Processing With No Progress

## Symptom
A job's status is `stuck` or `processing`, but `progress_pct` has not moved
across multiple status polls (5+ minutes with no change), and no error_code
is set.

## Likely causes
1. Worker node lost its heartbeat to the orchestrator but didn't release the
   job lock (zombie worker).
2. The input file read is hanging on a slow or throttled source (S3
   multipart stall, NFS mount timeout).
3. The encoder process deadlocked waiting on a GPU context that was never
   released by a previous job.

## Diagnosis
- Check `worker_node` on the job and look up that node's last heartbeat
  timestamp in the fleet dashboard.
- If the node heartbeat is stale (>2 min), treat it as zombied.
- If the node is healthy, check the encoder process's `strace`/`py-spy`
  output for a blocking read syscall on the input path.

## Fix
1. Requeue the job to a different worker node (`requeue_job`), do not retry
   on the same node without a reboot.
2. If the same input file stalls on a second node too, suspect the source
   object itself — re-upload or re-mux the source before retrying.
3. File a fleet ticket if the same worker node zombies more than twice in a
   week; it likely needs a kernel/driver update.

## When to escalate
Escalate to the platform on-call if more than 3 jobs are stuck
simultaneously — this usually means the orchestrator's lease renewal is
broken, not a single bad worker.
