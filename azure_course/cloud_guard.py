"""Explicit effect guard; never grants permission or discovers credentials."""
import os
from urllib.parse import urlparse


def require_effects() -> None:
    if os.environ.get("AZURE_COURSE_EFFECTS") != "approved-disposable-lab":
        raise PermissionError("Azure effects not admitted")


def endpoint(name: str, suffix: str) -> str:
    value = os.environ[name]
    parsed = urlparse(value)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(suffix):
        raise ValueError("unexpected Azure endpoint")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("endpoint must contain no credential/query/fragment")
    return value.rstrip("/")
