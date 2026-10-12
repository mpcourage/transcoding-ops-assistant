"""Run the eval suite.

Retrieval scenarios always run (stdlib only, no API key).
Conversation scenarios run live through the assistant only if
ANTHROPIC_API_KEY is set; otherwise they're listed as skipped so it's
obvious what hasn't been verified yet.

Usage: python eval/run_eval.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scenarios import RETRIEVAL_SCENARIOS, CONVERSATION_SCENARIOS  # noqa: E402


def run_retrieval_evals() -> tuple[int, int]:
    from retrieval import RunbookIndex

    index = RunbookIndex(Path(__file__).resolve().parent.parent / "runbooks")
    passed = 0
    print("== Retrieval scenarios ==")
    for sc in RETRIEVAL_SCENARIOS:
        results = index.search(sc["query"], k=3)
        top_path = Path(results[0]["path"]).name if results else None
        expected = sc["expected_runbook"]
        ok = top_path == expected
        status = "PASS" if ok else "FAIL"
        passed += ok
        print(f"[{status}] {sc['name']}: top={top_path!r} expected={expected!r}")
    print(f"-> {passed}/{len(RETRIEVAL_SCENARIOS)} retrieval scenarios passed\n")
    return passed, len(RETRIEVAL_SCENARIOS)


def run_conversation_evals() -> tuple[int, int]:
    print("== Conversation scenarios ==")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "SKIPPED: ANTHROPIC_API_KEY not set. "
            f"{len(CONVERSATION_SCENARIOS)} conversation scenarios not run.\n"
        )
        return 0, 0

    import anthropic
    from assistant import run_turn, SYSTEM_PROMPT  # noqa: F401
    from assistant import MODEL
    from tools import TOOL_SCHEMAS, dispatch

    client = anthropic.Anthropic()
    passed = 0
    for sc in CONVERSATION_SCENARIOS:
        messages = [{"role": "user", "content": sc["question"]}]
        tools_called = []

        # inline loop so we can observe which tools were called
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            if response.stop_reason != "tool_use":
                final_text = "".join(
                    b.text for b in response.content if b.type == "text"
                )
                break
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tools_called.append(block.name)
                result = dispatch(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        expects_tool = sc["expects_tool"]
        tool_ok = expects_tool in tools_called if expects_tool else not tools_called
        keyword_ok = any(
            kw.lower() in final_text.lower() for kw in sc["expected_keywords"]
        )
        ok = tool_ok and keyword_ok
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {sc['name']} (tools_called={tools_called})")
        if not ok:
            print(f"    answer: {final_text[:200]}")

    print(f"-> {passed}/{len(CONVERSATION_SCENARIOS)} conversation scenarios passed\n")
    return passed, len(CONVERSATION_SCENARIOS)


if __name__ == "__main__":
    r_passed, r_total = run_retrieval_evals()
    c_passed, c_total = run_conversation_evals()
    total_passed, total = r_passed + c_passed, r_total + c_total
    print(f"TOTAL: {total_passed}/{total} passed" + (
        "" if c_total else " (conversation suite skipped)"
    ))
