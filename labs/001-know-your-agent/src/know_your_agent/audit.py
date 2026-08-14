"""Generate a response-only audit identifier. Nothing is persisted."""

from __future__ import annotations

import uuid


def new_audit_id() -> str:
    return "aud-" + uuid.uuid4().hex
