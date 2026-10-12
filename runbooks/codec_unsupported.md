# Runbook: Unsupported Input Codec (error_code: CODEC_UNSUPPORTED)

## Symptom
Job fails almost immediately (progress_pct near 0) with an error like
"Decoder not found for codec_id" or "no decoder for stream". Frequently
seen on legacy AVI/WMV deliveries using old codecs (Indeo, Cinepak, early
DivX/XviD variants) that mainline ffmpeg builds no longer ship decoders
for.

## Root cause
The encode farm's ffmpeg build doesn't include a decoder for the source
codec. This is almost never a transient failure — retrying the same job
on any node will fail the same way.

## Fix
1. Confirm the codec with `ffprobe -show_streams <input>` — note the exact
   `codec_name`/`codec_tag`.
2. Check the legacy-codec allowlist; if the codec is on it, route the job
   to the legacy transcode pool (older ffmpeg build with the extra
   decoders compiled in) instead of the standard farm.
3. If the codec is not on the allowlist, this is a delivery problem, not an
   encoding problem: bounce the job back to content ops and request a
   re-delivery in a supported container/codec (ProRes, DNxHR, or H.264 in
   MOV/MXF).
4. Do not blindly retry — it wastes a worker slot for a guaranteed failure.

## When to escalate
If the same unsupported codec shows up across multiple partners, propose
adding it to the legacy pool's supported list rather than handling each
occurrence manually.
