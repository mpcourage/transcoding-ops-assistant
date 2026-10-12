"""CLI chat loop for the transcoding operations assistant.

Needs ANTHROPIC_API_KEY in the environment. Run: python assistant.py
"""
from __future__ import annotations

import os
import sys

import anthropic

from tools import TOOL_SCHEMAS, dispatch

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """\
You are an operations assistant for a video transcoding pipeline. You help \
on-call operators diagnose and resolve failing or stuck jobs.

Rules:
- When asked about a specific job, call get_job_status. When asked about \
jobs in general ("what's failing", "any stuck jobs"), call list_jobs.
- When a job has failed or is stuck, search_runbooks using the error_code \
or symptom before giving fix instructions. Don't invent troubleshooting \
steps that aren't in a runbook.
- Call get_runbook to read the full procedure before summarizing it — \
snippets from search_runbooks are too short to answer from directly.
- Always ground your answer in the actual tool results. If no runbook \
matches, say so plainly instead of guessing.
- Be concise and operational: lead with the diagnosis and the fix, not \
background explanation.
"""


def run_turn(client: anthropic.Anthropic, messages: list[dict]) -> str:
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            messages.append({"role": "assistant", "content": response.content})
            return text

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [tool] {block.name}({block.input})", file=sys.stderr)
            result = dispatch(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    messages: list[dict] = []
    print("Transcoding ops assistant. Ctrl-D to exit.")
    while True:
        try:
            user_input = input("\n> ")
        except EOFError:
            break
        messages.append({"role": "user", "content": user_input})
        reply = run_turn(client, messages)
        print(f"\n{reply}")


if __name__ == "__main__":
    main()
