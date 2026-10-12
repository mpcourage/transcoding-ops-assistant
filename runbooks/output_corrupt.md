# Runbook: Corrupt Output File / Failed QC (error_code: OUTPUT_CORRUPT)

## Symptom
Job reaches progress_pct 100 and finishes encoding, but the QC pass fails
on the output — common signatures are "moov atom missing", "playback
fails at segment boundary", or a player refusing to open the file at all.

## Root cause
Almost always an interrupted or non-atomic finalize step: the encoder
wrote the media data but the process was killed, the node rebooted, or a
downstream copy was interrupted before the container's finalize/moov-write
step completed. The encode itself usually succeeded — it's the muxing or
the final write/copy that didn't finish cleanly.

## Fix
1. Check the worker node's logs around `updated_at` for an OOM kill,
   process restart, or disk-full event during finalize.
2. Do not attempt to "repair" the corrupt output file — always re-run the
   full job from the source. Partial repairs on streaming containers
   (MP4/MOV) are unreliable for production delivery.
3. If disk space on the worker was the cause, clear scratch space on that
   node before requeuing, or route to a node with more free scratch
   capacity.
4. Add a post-encode integrity check (e.g. `ffprobe` full-file read) before
   marking any job complete, if one isn't already in the pipeline — this
   catches the corruption before it reaches downstream QC.

## When to escalate
If OUTPUT_CORRUPT clusters on one node, treat it as a hardware/disk issue
on that node and pull it from the pool pending a health check.
