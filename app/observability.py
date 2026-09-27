"""In-process observability: which agent handled each /chat call, how long
it took, and this process's own CPU/memory usage.

Why in-memory instead of Prometheus/Grafana?
  Real infra for one demo process is overkill. This is the same tradeoff
  rate_limiter.py documents for Redis vs in-memory, just the other
  direction — here there's only one process to watch, so there's nothing
  to synchronize.

# ponytail: counters and recent-calls live in this process's memory, reset
# on restart, and only see this worker's traffic. Fine for the single
# uvicorn worker this project runs. If this ever runs with >1 worker,
# move `_counts`/`_recent_calls` into Redis (same pattern as
# rate_limiter.py) so every worker reports the same numbers.
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

import psutil

_process = psutil.Process()
_process.cpu_percent()  # first call always returns 0.0 — prime it so later reads are real
_started_at = time.time()

AGENT_NAMES = {
    "account": "Account Agent",
    "transaction": "Transaction Agent",
    "service": "Service Agent",
}


@dataclass
class AgentCall:
    timestamp: float
    intent: str
    agent: Optional[str]
    latency_ms: float


_MAX_HISTORY = 200
_recent_calls: deque[AgentCall] = deque(maxlen=_MAX_HISTORY)
_counts: dict[str, int] = {}


def record_agent_call(intent: str, latency_ms: float) -> None:
    """Call once per /chat request, after the reply is ready."""
    _recent_calls.appendleft(AgentCall(time.time(), intent, AGENT_NAMES.get(intent), latency_ms))
    _counts[intent] = _counts.get(intent, 0) + 1


def snapshot(recent_limit: int = 20) -> dict:
    mem = _process.memory_info()
    return {
        "uptime_seconds": round(time.time() - _started_at, 1),
        "cpu_percent": _process.cpu_percent(),
        "memory_mb": round(mem.rss / (1024 * 1024), 1),
        "total_calls": sum(_counts.values()),
        "agent_counts": dict(_counts),
        "recent_calls": [
            {
                "timestamp": c.timestamp,
                "intent": c.intent,
                "agent": c.agent,
                "latency_ms": round(c.latency_ms, 1),
            }
            for c in list(_recent_calls)[:recent_limit]
        ],
    }


if __name__ == "__main__":
    # ponytail minimum self-check — not a pytest suite, just proves the
    # counters and snapshot shape hold up.
    record_agent_call("account", 812.3)
    record_agent_call("unknown", 340.1)
    snap = snapshot()
    assert snap["agent_counts"] == {"account": 1, "unknown": 1}
    assert snap["total_calls"] == 2
    assert snap["recent_calls"][0]["agent"] is None  # unknown has no sub-agent
    assert snap["recent_calls"][1]["agent"] == "Account Agent"
    assert snap["memory_mb"] > 0
    print("observability self-check passed")
