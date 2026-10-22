"""Core logic: audit events, human approvals, and prediction monitoring."""
from __future__ import annotations
import json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

def utc_now():
    return datetime.now(timezone.utc).isoformat()

class GovernanceHarness:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "data/governance.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, session_id TEXT,
                event TEXT NOT NULL, source_ref TEXT, tool TEXT, decision TEXT,
                human_review TEXT, actor TEXT, result TEXT, metadata_json TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS predictions (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, predicted REAL NOT NULL,
                actual REAL, model_version TEXT NOT NULL, segment TEXT, error REAL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, request TEXT NOT NULL,
                proposal TEXT NOT NULL, status TEXT NOT NULL, reviewer TEXT, review_note TEXT
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, feature TEXT NOT NULL,
                value TEXT NOT NULL
            )""")

    def audit(self, event, session_id=None, source_ref=None, tool=None, decision=None,
              human_review="not_required", actor="system", result=None, metadata=None):
        event_id = str(uuid.uuid4())
        # Never pass API keys or full personal records in metadata.
        safe_metadata = metadata or {}
        with self._connect() as c:
            c.execute("""INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (event_id, utc_now(), session_id, event, source_ref, tool, decision,
                 human_review, actor, result, json.dumps(safe_metadata, ensure_ascii=False)))
        return event_id

    def propose_reservation(self, request, proposal, source_ref="agenda_centro_cultural.md"):
        proposal_id = str(uuid.uuid4())
        with self._connect() as c:
            c.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?)",
                (proposal_id, utc_now(), request[:500], proposal[:1000], "pending", None, None))
        self.audit("reservation_proposed", source_ref=source_ref, tool="reservation_simulator",
                   decision=proposal[:300], human_review="pending", result="awaiting_human_review")
        return proposal_id

    def review_proposal(self, proposal_id, approved, reviewer, note=""):
        status = "approved" if approved else "rejected"
        with self._connect() as c:
            row = c.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row:
                raise ValueError("Propuesta inexistente.")
            if row["status"] != "pending":
                raise ValueError("La propuesta ya fue revisada; no se puede revisar dos veces.")
            c.execute("UPDATE proposals SET status=?, reviewer=?, review_note=? WHERE id=?",
                      (status, reviewer[:120], note[:500], proposal_id))
        # Approval only simulates a reservation; no external action is executed.
        result = "simulated_reservation_confirmed" if approved else "proposal_not_executed"
        self.audit("reservation_human_review", tool="reservation_simulator",
                   decision=status, human_review=status, actor=reviewer[:120], result=result,
                   metadata={"proposal_id": proposal_id, "note": note[:300]})
        return status

    def get_proposals(self, status=None):
        with self._connect() as c:
            if status:
                rows = c.execute("SELECT * FROM proposals WHERE status=? ORDER BY timestamp DESC", (status,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM proposals ORDER BY timestamp DESC").fetchall()
        return [dict(r) for r in rows]

    def record_prediction(self, predicted, model_version="demo-v1", segment="general", actual=None):
        pid = str(uuid.uuid4())
        error = None if actual is None else float(predicted) - float(actual)
        with self._connect() as c:
            c.execute("INSERT INTO predictions VALUES (?,?,?,?,?,?,?)",
                (pid, utc_now(), float(predicted), None if actual is None else float(actual),
                 model_version[:80], segment[:120], error))
        self.audit("prediction_recorded", event if False else None, tool="attendance_forecast",
                   decision=f"predicted={predicted}", result="actual_pending" if actual is None else f"error={error:.3f}")
        return pid

    def attach_actual(self, prediction_id, actual):
        with self._connect() as c:
            row = c.execute("SELECT * FROM predictions WHERE id=?", (prediction_id,)).fetchone()
            if not row:
                raise ValueError("Predicción inexistente.")
            if row["actual"] is not None:
                raise ValueError("La predicción ya tiene resultado real.")
            error = float(row["predicted"]) - float(actual)
            c.execute("UPDATE predictions SET actual=?, error=? WHERE id=?",
                      (float(actual), error, prediction_id))
        self.audit("actual_result_attached", tool="attendance_forecast",
                   decision=f"actual={actual}", result=f"error={error:.3f}")
        return error

    def predictions(self, limit=100):
        with self._connect() as c:
            rows = c.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]

    def performance_summary(self):
        rows = self.predictions(1000)
        measured = [r for r in rows if r["actual"] is not None]
        if not measured:
            return {"n": 0, "mae": None, "rmse": None}
        errors = [float(r["predicted"]) - float(r["actual"]) for r in measured]
        return {"n": len(errors), "mae": mean(abs(e) for e in errors),
                "rmse": (mean(e*e for e in errors))**0.5}

    def observe(self, feature, value):
        with self._connect() as c:
            c.execute("INSERT INTO observations VALUES (?,?,?,?)",
                      (str(uuid.uuid4()), utc_now(), feature[:120], str(value)[:300]))
        self.audit("input_observed", tool="input_monitor", decision=f"{feature} observed",
                   result="observation_saved")

    def drift_report(self, feature):
        with self._connect() as c:
            rows = c.execute("SELECT value FROM observations WHERE feature=? ORDER BY timestamp DESC LIMIT 100",
                             (feature,)).fetchall()
        values = [r["value"] for r in rows]
        if len(values) < 10:
            return {"feature": feature, "n": len(values), "signal": False,
                    "message": "Se necesitan al menos 10 observaciones para una señal exploratoria."}
        recent = values[:max(5, len(values)//2)]
        older = values[max(5, len(values)//2):]
        from collections import Counter
        rc, oc = Counter(recent), Counter(older)
        categories = set(rc) | set(oc)
        distance = 0.5 * sum(abs(rc[k]/len(recent) - oc[k]/len(older)) for k in categories) if older else 0
        signal = distance >= 0.30
        self.audit("drift_check", tool="input_monitor", decision=f"distance={distance:.3f}",
                   result="investigate" if signal else "no_signal",
                   metadata={"feature": feature, "n": len(values)})
        return {"feature": feature, "n": len(values), "distance": round(distance, 3),
                "signal": signal, "message": "Señal exploratoria; no demuestra deterioro del rendimiento."}

    def audit_events(self, limit=200):
        with self._connect() as c:
            rows = c.execute("SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]
