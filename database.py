"""SQLite persistence for diagnostic sessions."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from config import CATEGORY_BY_ID, get_database_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    category TEXT NOT NULL,
    manufacturer TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    age_range TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL,
    symptoms TEXT NOT NULL DEFAULT '[]',
    onset TEXT NOT NULL DEFAULT '',
    unusual_signs TEXT NOT NULL DEFAULT '[]',
    error_code TEXT NOT NULL DEFAULT '',
    report_json TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'moderate',
    difficulty TEXT NOT NULL DEFAULT '',
    professional_recommended INTEGER NOT NULL DEFAULT 0,
    professional_urgency TEXT NOT NULL DEFAULT 'routine',
    hazards_json TEXT NOT NULL DEFAULT '[]',
    safety_notices_json TEXT NOT NULL DEFAULT '[]',
    advanced_withheld INTEGER NOT NULL DEFAULT 0,
    image_analysis_json TEXT,
    ai_model TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_diagnostics_created_at ON diagnostics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_diagnostics_category ON diagnostics(category);
"""


@contextmanager
def _connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or get_database_path()
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA busy_timeout=5000;")
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(db_path: Path | None = None) -> None:
    with _connect(db_path) as connection:
        connection.executescript(_SCHEMA)


def _json(value: Any, fallback: str = "[]") -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return fallback


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def save_diagnostic(
    *,
    category: str,
    manufacturer: str,
    model: str,
    age_range: str,
    description: str,
    symptoms: list[str],
    onset: str,
    unusual_signs: list[str],
    error_code: str,
    report: dict,
    hazards: list[dict],
    safety_notices: list[str],
    advanced_withheld: bool,
    ai_model: str,
    image_analysis: dict | None = None,
    db_path: Path | None = None,
) -> int:
    professional = report.get("professional_repair") or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO diagnostics (
                created_at, category, manufacturer, model, age_range, description,
                symptoms, onset, unusual_signs, error_code, report_json, summary,
                severity, difficulty, professional_recommended, professional_urgency,
                hazards_json, safety_notices_json, advanced_withheld,
                image_analysis_json, ai_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                category,
                manufacturer.strip(),
                model.strip(),
                age_range,
                description.strip(),
                _json(symptoms),
                onset,
                _json(unusual_signs),
                error_code.strip(),
                _json(report, "{}"),
                str(report.get("summary", "")),
                str(report.get("severity", "moderate")),
                str(report.get("difficulty", "")),
                1 if professional.get("recommended") else 0,
                str(professional.get("urgency", "routine")),
                _json(hazards),
                _json(safety_notices),
                1 if advanced_withheld else 0,
                _json(image_analysis, "null") if image_analysis else None,
                ai_model,
            ),
        )
        return int(cursor.lastrowid)


def update_image_analysis(diagnostic_id: int, analysis: dict, db_path: Path | None = None) -> bool:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "UPDATE diagnostics SET image_analysis_json = ? WHERE id = ?",
            (_json(analysis, "{}"), int(diagnostic_id)),
        )
        return cursor.rowcount > 0


def _row_to_diagnostic(row: sqlite3.Row) -> dict:
    report = _loads(row["report_json"], {})
    professional = report.get("professional_repair") or {}
    return {
        "id": int(row["id"]),
        "created_at": row["created_at"],
        "input": {
            "category": row["category"],
            "category_label": CATEGORY_BY_ID.get(row["category"], {}).get("label", row["category"]),
            "manufacturer": row["manufacturer"],
            "model": row["model"],
            "age_range": row["age_range"],
            "description": row["description"],
            "symptoms": _loads(row["symptoms"], []),
            "onset": row["onset"],
            "unusual_signs": _loads(row["unusual_signs"], []),
            "error_code": row["error_code"],
        },
        "report": report,
        "hazards": _loads(row["hazards_json"], []),
        "safety_notices": _loads(row["safety_notices_json"], []),
        "advanced_withheld": bool(row["advanced_withheld"]),
        "image_analysis": _loads(row["image_analysis_json"], None),
        "model": row["ai_model"],
        "severity": row["severity"],
        "difficulty": row["difficulty"],
        "professional_recommended": bool(row["professional_recommended"]),
        "professional_urgency": professional.get("urgency", row["professional_urgency"]),
    }


def get_diagnostic(diagnostic_id: int, db_path: Path | None = None) -> dict | None:
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM diagnostics WHERE id = ?", (int(diagnostic_id),)).fetchone()
    return _row_to_diagnostic(row) if row else None


def list_diagnostics(
    *,
    search: str = "",
    category: str = "",
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list[Any] = []
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append(
            "(description LIKE ? OR manufacturer LIKE ? OR model LIKE ? OR summary LIKE ? OR error_code LIKE ?)"
        )
        params.extend([term] * 5)
    if category:
        clauses.append("category = ?")
        params.append(category)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(int(limit), 250)))

    query = f"""
        SELECT id, created_at, category, manufacturer, model, age_range, description,
               onset, error_code, summary, severity, difficulty, professional_recommended,
               professional_urgency, symptoms, hazards_json, image_analysis_json
        FROM diagnostics
        {where}
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
    """
    with _connect(db_path) as connection:
        rows = connection.execute(query, params).fetchall()

    items = []
    for row in rows:
        hazards = _loads(row["hazards_json"], [])
        items.append(
            {
                "id": int(row["id"]),
                "created_at": row["created_at"],
                "category": row["category"],
                "category_label": CATEGORY_BY_ID.get(row["category"], {}).get("label", row["category"]),
                "manufacturer": row["manufacturer"],
                "model": row["model"],
                "description": row["description"],
                "summary": row["summary"],
                "severity": row["severity"],
                "difficulty": row["difficulty"],
                "professional_recommended": bool(row["professional_recommended"]),
                "professional_urgency": row["professional_urgency"],
                "symptoms": _loads(row["symptoms"], []),
                "hazards": hazards,
                "has_image_analysis": bool(row["image_analysis_json"]),
            }
        )
    return items


def delete_diagnostic(diagnostic_id: int, db_path: Path | None = None) -> bool:
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM diagnostics WHERE id = ?", (int(diagnostic_id),))
        return cursor.rowcount > 0


def clear_diagnostics(db_path: Path | None = None) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM diagnostics")
        return max(cursor.rowcount, 0)


def get_stats(db_path: Path | None = None) -> dict:
    with _connect(db_path) as connection:
        totals = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   COUNT(DISTINCT category) AS categories,
                   COALESCE(SUM(professional_recommended), 0) AS professional,
                   MAX(created_at) AS last_activity
            FROM diagnostics
            """
        ).fetchone()
        category_rows = connection.execute(
            "SELECT category, COUNT(*) AS count FROM diagnostics GROUP BY category ORDER BY count DESC, category ASC"
        ).fetchall()
        recent_rows = connection.execute(
            """
            SELECT id, created_at, category, manufacturer, model, summary, severity, symptoms
            FROM diagnostics ORDER BY datetime(created_at) DESC, id DESC LIMIT 5
            """
        ).fetchall()
        activity_rows = connection.execute(
            "SELECT created_at FROM diagnostics WHERE datetime(created_at) >= datetime('now', '-6 days')"
        ).fetchall()

    category_counts = [
        {
            "id": row["category"],
            "label": CATEGORY_BY_ID.get(row["category"], {}).get("label", row["category"]),
            "count": int(row["count"]),
        }
        for row in category_rows
    ]

    day_counts = {i: 0 for i in range(6, -1, -1)}
    today = datetime.now(timezone.utc).date()
    for row in activity_rows:
        try:
            created = datetime.fromisoformat(row["created_at"]).date()
        except (TypeError, ValueError):
            continue
        delta = (today - created).days
        if delta in day_counts:
            day_counts[delta] += 1
    activity = [
        {
            "offset": offset,
            "label": (today - timedelta(days=offset)).strftime("%a"),
            "date": (today - timedelta(days=offset)).isoformat(),
            "count": day_counts[offset],
        }
        for offset in range(6, -1, -1)
    ]

    recent = [
        {
            "id": int(row["id"]),
            "created_at": row["created_at"],
            "category": row["category"],
            "category_label": CATEGORY_BY_ID.get(row["category"], {}).get("label", row["category"]),
            "manufacturer": row["manufacturer"],
            "model": row["model"],
            "summary": row["summary"],
            "severity": row["severity"],
            "symptoms": _loads(row["symptoms"], []),
        }
        for row in recent_rows
    ]

    return {
        "total": int(totals["total"]),
        "category_count": int(totals["categories"]),
        "professional_count": int(totals["professional"]),
        "last_activity": totals["last_activity"],
        "categories": category_counts,
        "activity": activity,
        "recent": recent,
    }
