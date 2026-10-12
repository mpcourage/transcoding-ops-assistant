"""Mock transcoding job-status API.

Stands in for a real pipeline's status endpoint (e.g. a REST service in
front of an FFmpeg/GPU encode farm). Same shape an operations assistant
would hit in production: list/filter jobs, fetch one job's full detail.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class Job:
    job_id: str
    status: str  # queued | processing | completed | failed | stuck
    progress_pct: int
    input_file: str
    output_profile: str
    worker_node: str
    created_at: str
    updated_at: str
    retries: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    eta_seconds: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _ts(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat(
        timespec="seconds"
    )


class MockJobStatusAPI:
    """In-memory stand-in for the real job-status service."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._seed()

    def _seed(self) -> None:
        seed_jobs = [
            Job(
                job_id="job-1001",
                status="completed",
                progress_pct=100,
                input_file="s3://media-in/trailer_4k_v3.mov",
                output_profile="hls-1080p-h264",
                worker_node="encoder-07",
                created_at=_ts(120),
                updated_at=_ts(95),
                retries=0,
            ),
            Job(
                job_id="job-1002",
                status="processing",
                progress_pct=63,
                input_file="s3://media-in/ep12_master.mxf",
                output_profile="dash-4k-hevc",
                worker_node="encoder-03",
                created_at=_ts(40),
                updated_at=_ts(1),
                retries=0,
                eta_seconds=540,
            ),
            Job(
                job_id="job-1003",
                status="stuck",
                progress_pct=12,
                input_file="s3://media-in/live_event_cam2.ts",
                output_profile="hls-720p-h264",
                worker_node="encoder-11",
                created_at=_ts(180),
                updated_at=_ts(175),
                retries=0,
                error_code=None,
                error_message=None,
            ),
            Job(
                job_id="job-1004",
                status="failed",
                progress_pct=34,
                input_file="s3://media-in/promo_hdr10.mov",
                output_profile="dash-4k-hevc-hdr",
                worker_node="encoder-05",
                created_at=_ts(90),
                updated_at=_ts(85),
                retries=2,
                error_code="HDR_TONEMAP_FAIL",
                error_message="libplacebo: failed to generate tone-map LUT for BT.2390, source mastering display metadata missing",
            ),
            Job(
                job_id="job-1005",
                status="failed",
                progress_pct=2,
                input_file="s3://media-in/ad_spot_final.avi",
                output_profile="hls-1080p-h264",
                worker_node="encoder-02",
                created_at=_ts(60),
                updated_at=_ts(59),
                retries=0,
                error_code="CODEC_UNSUPPORTED",
                error_message="ffmpeg: Decoder not found for codec_id=61 (Indeo 5), input container AVI",
            ),
            Job(
                job_id="job-1006",
                status="failed",
                progress_pct=78,
                input_file="s3://media-in/documentary_master.mov",
                output_profile="dash-4k-hevc",
                worker_node="encoder-09",
                created_at=_ts(55),
                updated_at=_ts(50),
                retries=1,
                error_code="ENCODE_OOM",
                error_message="CUDA error: out of memory (device 0, nvenc session limit reached)",
            ),
            Job(
                job_id="job-1007",
                status="completed",
                progress_pct=100,
                input_file="s3://media-in/sitcom_s2e4.mxf",
                output_profile="hls-1080p-h264",
                worker_node="encoder-01",
                created_at=_ts(200),
                updated_at=_ts(160),
                retries=0,
            ),
            Job(
                job_id="job-1008",
                status="failed",
                progress_pct=55,
                input_file="s3://media-in/concert_multicam.mov",
                output_profile="hls-1080p-h264",
                worker_node="encoder-04",
                created_at=_ts(70),
                updated_at=_ts(65),
                retries=1,
                error_code="AV_SYNC_DRIFT",
                error_message="Output audio drifts 180ms by end of segment 14; detected VFR source (23.976-29.97 switch) without frame-rate normalization",
            ),
            Job(
                job_id="job-1009",
                status="queued",
                progress_pct=0,
                input_file="s3://media-in/news_package_0912.mxf",
                output_profile="hls-720p-h264",
                worker_node="unassigned",
                created_at=_ts(5),
                updated_at=_ts(5),
                retries=0,
                eta_seconds=None,
            ),
            Job(
                job_id="job-1010",
                status="failed",
                progress_pct=100,
                input_file="s3://media-in/short_film_final.mov",
                output_profile="hls-1080p-h264",
                worker_node="encoder-06",
                created_at=_ts(45),
                updated_at=_ts(30),
                retries=0,
                error_code="OUTPUT_CORRUPT",
                error_message="QC check failed: moov atom missing in output MP4, playback fails at segment boundary",
            ),
        ]
        for job in seed_jobs:
            self._jobs[job.job_id] = job

    def list_jobs(self, status_filter: Optional[str] = None, limit: int = 20) -> list[dict]:
        jobs = list(self._jobs.values())
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        jobs.sort(key=lambda j: j.updated_at, reverse=True)
        return [j.to_dict() for j in jobs[:limit]]

    def get_job(self, job_id: str) -> Optional[dict]:
        job = self._jobs.get(job_id)
        return job.to_dict() if job else None
