"""
RASTRO — Histórico anônimo local (SQLite).

Modelo A (sem contas): cada navegador recebe um cookie de identidade
opaco (`rastro_hid`); os resumos de análise são gravados sob esse
identificador. Nenhuma URL completa, HTML ou texto integral de página
é persistido — apenas o recorte exibido no histórico/relatório.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

COOKIE_NAME = "rastro_hid"
HISTORY_LIMIT = 100
_OWNER_HEX_LENGTH = 32


def _db_path() -> str:
    return os.getenv("RASTRO_DB_PATH", "data/rastro.db")


def _connect() -> sqlite3.Connection:
    path = _db_path()
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS history_items (
                id         TEXT PRIMARY KEY,
                owner      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload    TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_owner "
            "ON history_items(owner, created_at DESC)"
        )


def is_owner_token(value: str | None) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _OWNER_HEX_LENGTH
        and all(c in "0123456789abcdef" for c in value)
    )


def new_owner_token() -> str:
    return uuid.uuid4().hex


def add_history_item(owner: str, payload: dict) -> str:
    """Grava um resumo para o dono e aplica a retenção (mantém os mais novos)."""
    item_id = uuid.uuid4().hex
    payload = dict(payload)
    payload["id"] = item_id
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO history_items (id, owner, created_at, payload) VALUES (?, ?, ?, ?)",
            (item_id, owner, created_at, json.dumps(payload, ensure_ascii=False)),
        )
        conn.execute(
            """
            DELETE FROM history_items
            WHERE owner = ? AND id NOT IN (
                SELECT id FROM history_items
                WHERE owner = ? ORDER BY created_at DESC LIMIT ?
            )
            """,
            (owner, owner, HISTORY_LIMIT),
        )
    return item_id


def list_history(owner: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT payload FROM history_items WHERE owner = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (owner, HISTORY_LIMIT),
        ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def delete_history_item(owner: str, item_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM history_items WHERE owner = ? AND id = ?",
            (owner, item_id),
        )
    return cursor.rowcount > 0


def delete_history(owner: str) -> int:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM history_items WHERE owner = ?", (owner,))
    return cursor.rowcount
