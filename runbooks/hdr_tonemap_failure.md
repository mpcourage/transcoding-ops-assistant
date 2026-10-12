# Runbook: HDR Tone-Mapping Failure (error_code: HDR_TONEMAP_FAIL)

## Symptom
Job fails with an error referencing `libplacebo`, `tone-map`, `BT.2390`, or
missing mastering display metadata. Common on HDR10 sources being
transcoded to an HDR or SDR-fallback output profile.

## Root cause
The tone-mapping filter needs HDR mastering display metadata (max/min
luminance, color primaries) embedded in the source. Some HDR10 masters are
missing this metadata or have it malformed, so the filter can't build the
BT.2390 tone-map LUT and aborts instead of guessing.

## Fix
1. Probe the source for HDR metadata:
   `ffprobe -show_frames -select_streams v:0 -read_intervals "%+#1"` and
   check for `mastering_display_metadata` / `content_light_level` side data.
2. If metadata is missing, inject standard HDR10 defaults
   (1000 nits max, 0.0001 nits min, BT.2020 primaries) via
   `ffmpeg ... -metadata:s:v:0 ...` or a mux-level patch before re-submitting.
3. If metadata is present but malformed, re-mux from the original master
   rather than patching — malformed metadata often means an upstream mux
   step stripped or corrupted it.
4. Retry the job only after the probe confirms clean metadata; retrying
   without fixing the source will fail identically every time.

## When to escalate
If more than one title from the same content partner hits this, escalate to
the ingest team — their delivery spec may not be enforcing HDR10 metadata
requirements at intake.
