"""Tool schemas (Claude tool-use format) and dispatch for the ops assistant.

Connects the two systems a transcoding operator actually needs mid-incident:
job status (mock_api) and runbook retrieval (retrieval). Claude decides
when to call which; this module just defines the contract and executes it.
"""
from __future__ import annotations

from pathlib import Path

from mock_api import MockJobStatusAPI
from retrieval import RunbookIndex

_api = MockJobStatusAPI()
_index = RunbookIndex(Path(__file__).parent / "runbooks")

TOOL_SCHEMAS = [
    {
        "name": "get_job_status",
        "description": (
            "Look up full status detail for one transcoding job by job_id, "
            "including status, progress, error_code/error_message if failed, "
            "worker_node, and retry count."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "e.g. 'job-1004'"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "list_jobs",
        "description": (
            "List recent transcoding jobs, optionally filtered by status "
            "(queued, processing, completed, failed, stuck). Use this when "
            "the operator asks about jobs in general rather than one job_id, "
            "e.g. 'what's failing right now' or 'any stuck jobs'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["queued", "processing", "completed", "failed", "stuck"],
                },
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "search_runbooks",
        "description": (
            "Semantic search over the operations runbook corpus. Use this "
            "to find the right troubleshooting procedure for an error_code, "
            "symptom, or failure description before answering 'how do I fix "
            "this' questions. Returns titles, paths, and short snippets — "
            "call get_runbook with the path to read the full procedure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_runbook",
        "description": "Fetch the full markdown text of one runbook by its path (from search_runbooks results).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
]


def dispatch(name: str, tool_input: dict) -> dict:
    if name == "get_job_status":
        job = _api.get_job(tool_input["job_id"])
        if job is None:
            return {"error": f"no such job_id: {tool_input['job_id']}"}
        return job

    if name == "list_jobs":
        return {
            "jobs": _api.list_jobs(
                status_filter=tool_input.get("status_filter"),
                limit=tool_input.get("limit", 20),
            )
        }

    if name == "search_runbooks":
        return {"results": _index.search(tool_input["query"], k=tool_input.get("k", 3))}

    if name == "get_runbook":
        text = _index.get_full_text(tool_input["path"])
        if text is None:
            return {"error": f"no such runbook path: {tool_input['path']}"}
        return {"path": tool_input["path"], "text": text}

    return {"error": f"unknown tool: {name}"}
