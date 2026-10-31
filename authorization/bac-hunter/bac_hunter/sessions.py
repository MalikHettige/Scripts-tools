"""Load the session/privilege-level config: two or more named identities,
each with the auth material (cookie header and/or bearer token and/or
arbitrary extra headers) used to replay requests as that identity.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # optional; only needed for .yml/.yaml config files
except ImportError:
    yaml = None


@dataclass
class Session:
    name: str
    level: int  # lower = less privileged; used to decide escalation direction
    cookie: str | None = None
    bearer: str | None = None
    headers: dict = field(default_factory=dict)
    # Optional: object IDs known to belong to THIS session, e.g. its own
    # user_id/order_id. Used by the object_id_swap strategy to try "my
    # token + someone else's known object id" instead of just guessing
    # neighboring numeric IDs.
    object_ids: list = field(default_factory=list)

    def apply(self, headers: dict) -> dict:
        """Return a copy of `headers` with this session's auth swapped in,
        replacing whatever Cookie/Authorization the original request had.
        """
        out = dict(headers)
        for k in list(out.keys()):
            if k.lower() in ("cookie", "authorization"):
                del out[k]
        if self.cookie:
            out["Cookie"] = self.cookie
        if self.bearer:
            out["Authorization"] = f"Bearer {self.bearer}" if not self.bearer.lower().startswith("bearer ") else self.bearer
        out.update(self.headers)
        return out


def load_sessions(path: str) -> list[Session]:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yml", ".yaml")):
        if yaml is None:
            raise RuntimeError("PyYAML not installed; `pip install pyyaml` or use a .json config instead.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    sessions_raw = data.get("sessions") if isinstance(data, dict) else data
    if not sessions_raw or len(sessions_raw) < 2:
        raise ValueError("Config must define at least 2 sessions (privilege levels) to diff against each other.")

    sessions = []
    for i, s in enumerate(sessions_raw):
        sessions.append(Session(
            name=s.get("name", f"session_{i}"),
            level=s.get("level", i),
            cookie=s.get("cookie"),
            bearer=s.get("bearer") or s.get("token"),
            headers=s.get("headers", {}) or {},
            object_ids=[str(x) for x in (s.get("object_ids") or [])],
        ))
    sessions.sort(key=lambda s: s.level)
    return sessions
