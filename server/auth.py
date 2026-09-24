"""Admin authentication: PBKDF2 password hashes and server-side sessions."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from . import config, db

_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"pbkdf2_sha256${_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(candidate, digest)


def ensure_admin() -> None:
    """Create the initial admin account when no users exist."""
    if db.one("SELECT id FROM users LIMIT 1"):
        return
    with db.tx() as con:
        con.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
            (config.ADMIN_USER, hash_password(config.ADMIN_PASSWORD), db.utcnow()),
        )


def login(username: str, password: str) -> str | None:
    user = db.one("SELECT id, password_hash FROM users WHERE username=?", (username.strip(),))
    if not user or not verify_password(password, user["password_hash"]):
        return None
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=config.SESSION_DAYS)
    with db.tx() as con:
        con.execute("DELETE FROM sessions WHERE expires_at < ?", (db.utcnow(),))
        con.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user["id"], expires.replace(microsecond=0).isoformat()),
        )
    return token


def logout(token: str | None) -> None:
    if not token:
        return
    with db.tx() as con:
        con.execute("DELETE FROM sessions WHERE token=?", (token,))


def user_for_token(token: str | None) -> dict | None:
    if not token:
        return None
    return db.one(
        "SELECT u.id, u.username, u.role FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token=? AND s.expires_at > ?",
        (token, db.utcnow()),
    )


def change_password(user_id: int, new_password: str) -> None:
    with db.tx() as con:
        con.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new_password), user_id))
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
