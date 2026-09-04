"""Password helpers. Stable and rarely changed, so BugRisk should rank it LOW."""
from __future__ import annotations

import hashlib
import hmac
import os


def hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Return (salt, digest) using PBKDF2-HMAC-SHA256."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt, digest


def verify_password(password: str, salt: bytes, expected: bytes) -> bool:
    """Constant-time password check."""
    _, digest = hash_password(password, salt)
    return hmac.compare_digest(digest, expected)
