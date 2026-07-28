"""Standalone reproduction script for Issue #43: Agent session state not cleared between reviews.

This script demonstrates how Orchestrator reuses `profile_id` as the session key,
causing stale tool execution results from prior reviews to leak into subsequent review sessions.
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock

# Add root project directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Gracefully handle missing dependencies if running outside project venv
if importlib.util.find_spec("structlog") is None:
    sys.modules["structlog"] = MagicMock()

if importlib.util.find_spec("redis") is None:
    sys.modules["redis"] = MagicMock()

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeRedis:
    """In-memory dictionary mock for redis.Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, time: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class DummyTool:
    """Dummy tool for orchestrator execution."""

    def __init__(self, name: str, mock_data: dict) -> None:
        self.name = name
        self.mock_data = mock_data

    def execute(self, tool_input: dict) -> dict:
        return self.mock_data


def main() -> int:
    print("=" * 60)
    print("REPRODUCING ISSUE #43: Session state leak across reviews")
    print("=" * 60)

    # 1. Setup mock storage and orchestrator
    fake_redis = FakeRedis()
    session_store = SessionStore(fake_redis)  # type: ignore[arg-type]  # in-memory test double

    tools = {
        "readme_scorer": DummyTool("readme_scorer", {"score": 95, "feedback": "Great README"}),
        "skill_extractor": DummyTool("skill_extractor", {"skills": ["Python", "FastAPI"]}),
    }

    orchestrator = Orchestrator(tools=tools, session_store=session_store)
    profile_id = "user_profile_43"

    # 2. Run 1: User submits profile with README only
    print("\n--- RUN 1: Review request with README content ---")
    profile_data_run1 = {"readme_content": "# My Portfolio Project\nA cool open-source project."}
    result_1 = orchestrator.run(profile_id, profile_data_run1)

    print("Run 1 Tool Results:", result_1["tool_results"])
    session_state_after_run1 = session_store.get(profile_id)
    print("SessionStore state after Run 1:", session_state_after_run1)
    assert session_state_after_run1 is not None, "Run 1 should persist session state"
    assert "readme_scorer" in session_state_after_run1, "Run 1 should store readme_scorer result"

    # 3. Run 2: SAME user submits a subsequent review with RESUME only (no README content)
    print("\n--- RUN 2: Subsequent review request with RESUME content only (No README) ---")
    profile_data_run2 = {
        "resume_text": "Jane Doe - Senior Software Engineer with 5 years experience."
    }
    result_2 = orchestrator.run(profile_id, profile_data_run2)

    print("Run 2 Tool Results (from execution plan):", result_2["tool_results"])
    session_state_after_run2 = session_store.get(profile_id)
    print("SessionStore state after Run 2:", session_state_after_run2)
    assert session_state_after_run2 is not None, "Run 2 should persist session state"

    # 4. Check for bug condition
    print("\n" + "=" * 60)
    print("ANALYSIS OF SESSION STORE STATE:")
    print("=" * 60)

    if "readme_scorer" in session_state_after_run2:
        print("[BUG REPRODUCED SUCCESSFULLY]")
        print("Stale result 'readme_scorer' from Run 1 persists in SessionStore after Run 2!")
        print(
            f"Details: Session state key for '{profile_id}' contains: {list(session_state_after_run2.keys())}"
        )
        print(
            "Reason: Orchestrator passes profile_id directly as session_id to SessionStore.get()/set(),"
        )
        print(
            "        so session_state is loaded from the previous review and merged with new results."
        )
        return 0
    else:
        print("[BUG NOT REPRODUCED]")
        print("Session state was clean for Run 2.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
