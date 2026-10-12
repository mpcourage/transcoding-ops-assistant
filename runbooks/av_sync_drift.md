# Runbook: Audio/Video Sync Drift in Output (error_code: AV_SYNC_DRIFT)

## Symptom
QC flags growing audio/video drift over the course of the output (e.g.
180ms by segment 14), even though the job otherwise completed or failed a
late-stage QC check. Error message often mentions a variable frame rate
(VFR) source or a frame-rate switch mid-file.

## Root cause
The source is variable frame rate (common with multi-camera live
switches, e.g. 23.976 to 29.97) and the transcode pipeline assumed
constant frame rate (CFR) when building output segment boundaries. Without
explicit frame-rate normalization, small per-frame timing errors
accumulate into visible drift over the length of the file.

## Fix
1. Probe the source frame rate profile:
   `ffprobe -show_entries frame=pkt_duration_time -select_streams v:0`
   and look for inconsistent durations.
2. If VFR is confirmed, re-run the job with explicit CFR normalization
   (`-vsync cfr -r <target_fps>`) rather than relying on default pass-
   through behavior.
3. Re-run audio resampling in the same pass so audio and video timestamps
   are rebuilt against the same normalized clock, not patched
   independently.
4. Re-verify with the QC drift check before marking the job complete.

## When to escalate
If VFR sources are recurring from a specific live-capture source (e.g. a
particular camera feed or switcher), escalate to the ingest/capture team —
normalizing frame rate at the transcode stage is a workaround, not a fix
for the upstream capture issue.
