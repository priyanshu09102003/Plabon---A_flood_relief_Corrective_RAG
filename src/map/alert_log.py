"""
Alert threshold crossing log for the Assam flood dashboard.

Tracks when a station's alert level *changes* (e.g. NORMAL -> WARNING,
WARNING -> DANGER) and persists a lightweight history so the dashboard
can show "this station crossed into DANGER 12 minutes ago" instead of
only ever showing the current snapshot.

"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "alert_log.db"

ALERT_RANK = {"NORMAL": 0, "WARNING": 1, "DANGER": 2, "EXTREME": 3}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            station_name TEXT NOT NULL,
            river TEXT NOT NULL,
            from_alert TEXT NOT NULL,
            to_alert TEXT NOT NULL,
            risk_pct REAL NOT NULL,
            direction TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS last_known_alert (
            station_id TEXT PRIMARY KEY,
            alert TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def record_snapshot(current_data: dict) -> list[dict]:
    """Call this once per refresh with the live current_data dict.
    Compares each station's alert level to its last known level; any
    change is written to the log. Returns the list of new events from
    this call (empty list if nothing changed), so the UI can surface a
    toast/banner for fresh crossings without re-reading the whole log.
    """
    conn = _get_conn()
    new_events: list[dict] = []
    now = datetime.now().isoformat(timespec="seconds")

    for sid, s in current_data.items():
        row = conn.execute(
            "SELECT alert FROM last_known_alert WHERE station_id = ?", (sid,)
        ).fetchone()
        prev_alert = row[0] if row else None
        curr_alert = s["alert"]

        if prev_alert is not None and prev_alert != curr_alert:
            direction = "ESCALATION" if ALERT_RANK[curr_alert] > ALERT_RANK[prev_alert] else "DE-ESCALATION"
            conn.execute(
                """INSERT INTO alert_events
                   (station_id, station_name, river, from_alert, to_alert, risk_pct, direction, timestamp)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (sid, s["name"], s["river"], prev_alert, curr_alert, s["pct_of_danger"], direction, now),
            )
            new_events.append({
                "station_id": sid, "station_name": s["name"], "river": s["river"],
                "from_alert": prev_alert, "to_alert": curr_alert,
                "risk_pct": s["pct_of_danger"], "direction": direction, "timestamp": now,
            })

        conn.execute(
            "INSERT INTO last_known_alert (station_id, alert) VALUES (?, ?) "
            "ON CONFLICT(station_id) DO UPDATE SET alert = excluded.alert",
            (sid, curr_alert),
        )

    conn.commit()
    conn.close()
    return new_events


def get_recent_events(limit: int = 20) -> list[dict]:
    """Most recent threshold-crossing events, newest first."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT station_name, river, from_alert, to_alert, risk_pct, direction, timestamp
           FROM alert_events ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "station_name": r[0], "river": r[1], "from_alert": r[2],
            "to_alert": r[3], "risk_pct": r[4], "direction": r[5], "timestamp": r[6],
        }
        for r in rows
    ]