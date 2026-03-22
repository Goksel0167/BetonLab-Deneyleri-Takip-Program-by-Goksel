"""
Veritabanı yönetim modülü - SQLite tabanlı, 500+ kayıt kapasiteli
"""
import sqlite3
import json
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


def _resolve_db_path() -> str:
    # Allow overriding the SQLite location for cloud platforms (e.g. Railway volume mount).
    env_db_path = os.getenv("BETONLAB_DB_PATH")
    if env_db_path:
        return os.path.abspath(env_db_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "betonlab.db")


DB_PATH = _resolve_db_path()


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sieve_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_date TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    sample_weight REAL,
                    operator TEXT,
                    source TEXT,
                    sieve_results TEXT NOT NULL,
                    evaluation TEXT,
                    status TEXT DEFAULT 'UYGUN',
                    notes TEXT,
                    week_number INTEGER,
                    year INTEGER,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS pollution_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_date TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    operator TEXT,
                    source TEXT,
                    bypass_open INTEGER DEFAULT 0,
                    washing_water_dirty INTEGER DEFAULT 0,
                    washing_water_insufficient INTEGER DEFAULT 0,
                    mb_value REAL,
                    sand_equivalent REAL,
                    clay_lumps REAL,
                    fine_content REAL,
                    evaluation TEXT,
                    status TEXT DEFAULT 'UYGUN',
                    notes TEXT,
                    week_number INTEGER,
                    year INTEGER,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS concrete_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_code TEXT NOT NULL,
                    concrete_class TEXT NOT NULL,
                    cement_type TEXT,
                    cement_content REAL,
                    water_cement_ratio REAL,
                    aggregate_0_2 REAL DEFAULT 0,
                    aggregate_0_5 REAL DEFAULT 0,
                    aggregate_5_12 REAL DEFAULT 0,
                    aggregate_12_22 REAL DEFAULT 0,
                    aggregate_0_315 REAL DEFAULT 0,
                    admixture_type TEXT,
                    admixture_content REAL DEFAULT 0,
                    target_slump REAL,
                    target_strength REAL,
                    actual_strength REAL,
                    consistency_class TEXT,
                    exposure_class TEXT,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS weekly_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_start TEXT NOT NULL,
                    week_end TEXT NOT NULL,
                    week_number INTEGER,
                    year INTEGER,
                    report_data TEXT NOT NULL,
                    overall_status TEXT DEFAULT 'UYGUN',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS daily_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date TEXT NOT NULL,
                    log_type TEXT NOT NULL,
                    reference_id INTEGER,
                    message TEXT,
                    severity TEXT DEFAULT 'INFO',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE INDEX IF NOT EXISTS idx_sieve_date ON sieve_analyses(test_date);
                CREATE INDEX IF NOT EXISTS idx_sieve_type ON sieve_analyses(aggregate_type);
                CREATE INDEX IF NOT EXISTS idx_sieve_week ON sieve_analyses(year, week_number);
                CREATE INDEX IF NOT EXISTS idx_pollution_date ON pollution_tests(test_date);
                CREATE INDEX IF NOT EXISTS idx_pollution_type ON pollution_tests(aggregate_type);
                CREATE INDEX IF NOT EXISTS idx_recipe_class ON concrete_recipes(concrete_class);
                CREATE INDEX IF NOT EXISTS idx_weekly_week ON weekly_reports(year, week_number);
            """)

    # ─── ELEK ANALİZİ CRUD ───────────────────────────────────────────────────

    def save_sieve_analysis(self, data, evaluation: dict) -> int:
        test_date = datetime.strptime(data.test_date, "%Y-%m-%d").date()
        week_num = test_date.isocalendar()[1]
        year = test_date.year
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO sieve_analyses
                (test_date, aggregate_type, sample_weight, operator, source,
                 sieve_results, evaluation, status, notes, week_number, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.test_date, data.aggregate_type, data.sample_weight,
                data.operator, data.source,
                json.dumps(data.sieve_results, ensure_ascii=False),
                json.dumps(evaluation, ensure_ascii=False),
                evaluation.get("status", "UYGUN"),
                data.notes, week_num, year
            ))
            return cur.lastrowid

    def get_sieve_analyses(self, limit=100, offset=0, aggregate_type=None, start_date=None, end_date=None):
        query = "SELECT * FROM sieve_analyses WHERE 1=1"
        params = []
        if aggregate_type:
            query += " AND aggregate_type = ?"
            params.append(aggregate_type)
        if start_date:
            query += " AND test_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND test_date <= ?"
            params.append(end_date)
        query += " ORDER BY test_date DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([min(limit, 500), offset])

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._parse_sieve_row(r) for r in rows]

    def get_sieve_analysis_by_id(self, record_id: int):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sieve_analyses WHERE id=?", (record_id,)).fetchone()
            return self._parse_sieve_row(row) if row else None

    def count_sieve_analyses(self, aggregate_type=None):
        query = "SELECT COUNT(*) FROM sieve_analyses"
        params = []
        if aggregate_type:
            query += " WHERE aggregate_type=?"
            params.append(aggregate_type)
        with self._get_conn() as conn:
            return conn.execute(query, params).fetchone()[0]

    def delete_sieve_analysis(self, record_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM sieve_analyses WHERE id=?", (record_id,))

    def _parse_sieve_row(self, row) -> dict:
        if not row:
            return None
        d = dict(row)
        d["sieve_results"] = json.loads(d["sieve_results"]) if d.get("sieve_results") else {}
        d["evaluation"] = json.loads(d["evaluation"]) if d.get("evaluation") else {}
        return d

    # ─── KİRLİLİK TESTİ CRUD ────────────────────────────────────────────────

    def save_pollution_test(self, data, evaluation: dict) -> int:
        test_date = datetime.strptime(data.test_date, "%Y-%m-%d").date()
        week_num = test_date.isocalendar()[1]
        year = test_date.year
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO pollution_tests
                (test_date, aggregate_type, operator, source, bypass_open,
                 washing_water_dirty, washing_water_insufficient, mb_value,
                 sand_equivalent, clay_lumps, fine_content, evaluation, status,
                 notes, week_number, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.test_date, data.aggregate_type, data.operator, data.source,
                int(data.bypass_open), int(data.washing_water_dirty),
                int(data.washing_water_insufficient), data.mb_value,
                data.sand_equivalent, data.clay_lumps, data.fine_content,
                json.dumps(evaluation, ensure_ascii=False),
                evaluation.get("status", "UYGUN"),
                data.notes, week_num, year
            ))
            return cur.lastrowid

    def get_pollution_tests(self, limit=100, offset=0, aggregate_type=None, start_date=None, end_date=None):
        query = "SELECT * FROM pollution_tests WHERE 1=1"
        params = []
        if aggregate_type:
            query += " AND aggregate_type=?"
            params.append(aggregate_type)
        if start_date:
            query += " AND test_date>=?"
            params.append(start_date)
        if end_date:
            query += " AND test_date<=?"
            params.append(end_date)
        query += " ORDER BY test_date DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([min(limit, 500), offset])
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._parse_pollution_row(r) for r in rows]

    def get_pollution_test_by_id(self, record_id: int):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM pollution_tests WHERE id=?", (record_id,)).fetchone()
            return self._parse_pollution_row(row) if row else None

    def count_pollution_tests(self, aggregate_type=None):
        query = "SELECT COUNT(*) FROM pollution_tests"
        params = []
        if aggregate_type:
            query += " WHERE aggregate_type=?"
            params.append(aggregate_type)
        with self._get_conn() as conn:
            return conn.execute(query, params).fetchone()[0]

    def _parse_pollution_row(self, row) -> dict:
        if not row:
            return None
        d = dict(row)
        d["evaluation"] = json.loads(d["evaluation"]) if d.get("evaluation") else {}
        return d

    # ─── BETON REÇETESİ CRUD ────────────────────────────────────────────────

    def save_concrete_recipe(self, data) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO concrete_recipes
                (recipe_code, concrete_class, cement_type, cement_content,
                 water_cement_ratio, aggregate_0_2, aggregate_0_5, aggregate_5_12,
                 aggregate_12_22, aggregate_0_315, admixture_type, admixture_content,
                 target_slump, target_strength, consistency_class, exposure_class, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.recipe_code, data.concrete_class, data.cement_type,
                data.cement_content, data.water_cement_ratio,
                data.aggregate_0_2, data.aggregate_0_5, data.aggregate_5_12,
                data.aggregate_12_22, data.aggregate_0_315,
                data.admixture_type, data.admixture_content,
                data.target_slump, data.target_strength,
                data.consistency_class, data.exposure_class, data.notes
            ))
            return cur.lastrowid

    def get_concrete_recipes(self, limit=100, offset=0, concrete_class=None):
        query = "SELECT * FROM concrete_recipes WHERE is_active=1"
        params = []
        if concrete_class:
            query += " AND concrete_class=?"
            params.append(concrete_class)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([min(limit, 500), offset])
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_concrete_recipe_by_id(self, record_id: int):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM concrete_recipes WHERE id=? AND is_active=1", (record_id,)).fetchone()
            return dict(row) if row else None

    def count_concrete_recipes(self, concrete_class=None):
        query = "SELECT COUNT(*) FROM concrete_recipes WHERE is_active=1"
        params = []
        if concrete_class:
            query += " AND concrete_class=?"
            params.append(concrete_class)
        with self._get_conn() as conn:
            return conn.execute(query, params).fetchone()[0]

    def update_concrete_recipe(self, record_id: int, data):
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE concrete_recipes SET
                recipe_code=?, concrete_class=?, cement_type=?, cement_content=?,
                water_cement_ratio=?, aggregate_0_2=?, aggregate_0_5=?,
                aggregate_5_12=?, aggregate_12_22=?, aggregate_0_315=?,
                admixture_type=?, admixture_content=?, target_slump=?,
                target_strength=?, consistency_class=?, exposure_class=?,
                notes=?, updated_at=datetime('now','localtime')
                WHERE id=?
            """, (
                data.recipe_code, data.concrete_class, data.cement_type,
                data.cement_content, data.water_cement_ratio,
                data.aggregate_0_2, data.aggregate_0_5, data.aggregate_5_12,
                data.aggregate_12_22, data.aggregate_0_315,
                data.admixture_type, data.admixture_content,
                data.target_slump, data.target_strength,
                data.consistency_class, data.exposure_class, data.notes,
                record_id
            ))

    def delete_concrete_recipe(self, record_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE concrete_recipes
                SET is_active=0, updated_at=datetime('now','localtime')
                WHERE id=? AND is_active=1
                """,
                (record_id,)
            )
            return cur.rowcount > 0

    # ─── HAFTALIK RAPOR ───────────────────────────────────────────────────────

    def get_weekly_reports(self, limit=12):
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM weekly_reports ORDER BY week_start DESC LIMIT ?", (limit,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["report_data"] = json.loads(d["report_data"])
                result.append(d)
            return result

    def save_weekly_report(self, week_start: str, report_data: dict) -> int:
        ws = datetime.strptime(week_start, "%Y-%m-%d").date()
        we = ws + timedelta(days=6)
        week_num = ws.isocalendar()[1]
        year = ws.year
        overall = report_data.get("overall_status", "UYGUN")
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO weekly_reports (week_start, week_end, week_number, year, report_data, overall_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                week_start, we.isoformat(), week_num, year,
                json.dumps(report_data, ensure_ascii=False), overall
            ))
            return cur.lastrowid

    def get_sieve_analyses_for_week(self, week_start: str, week_end: str) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sieve_analyses WHERE test_date BETWEEN ? AND ? ORDER BY test_date",
                (week_start, week_end)
            ).fetchall()
            return [self._parse_sieve_row(r) for r in rows]

    def get_pollution_tests_for_week(self, week_start: str, week_end: str) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pollution_tests WHERE test_date BETWEEN ? AND ? ORDER BY test_date",
                (week_start, week_end)
            ).fetchall()
            return [self._parse_pollution_row(r) for r in rows]

    # ─── DASHBOARD & İSTATİSTİK ──────────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        with self._get_conn() as conn:
            today = date.today().isoformat()
            week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()

            total_sieve = conn.execute("SELECT COUNT(*) FROM sieve_analyses").fetchone()[0]
            total_pollution = conn.execute("SELECT COUNT(*) FROM pollution_tests").fetchone()[0]
            total_recipes = conn.execute("SELECT COUNT(*) FROM concrete_recipes WHERE is_active=1").fetchone()[0]

            sieve_this_week = conn.execute(
                "SELECT COUNT(*) FROM sieve_analyses WHERE test_date>=?", (week_start,)
            ).fetchone()[0]
            pollution_this_week = conn.execute(
                "SELECT COUNT(*) FROM pollution_tests WHERE test_date>=?", (week_start,)
            ).fetchone()[0]

            nonconform_sieve = conn.execute(
                "SELECT COUNT(*) FROM sieve_analyses WHERE status!='UYGUN'"
            ).fetchone()[0]
            nonconform_pollution = conn.execute(
                "SELECT COUNT(*) FROM pollution_tests WHERE status!='UYGUN'"
            ).fetchone()[0]

            recent_sieve = conn.execute(
                "SELECT test_date, aggregate_type, status FROM sieve_analyses ORDER BY id DESC LIMIT 5"
            ).fetchall()
            recent_pollution = conn.execute(
                "SELECT test_date, aggregate_type, status FROM pollution_tests ORDER BY id DESC LIMIT 5"
            ).fetchall()

            return {
                "totals": {
                    "sieve_analyses": total_sieve,
                    "pollution_tests": total_pollution,
                    "concrete_recipes": total_recipes,
                },
                "this_week": {
                    "sieve_analyses": sieve_this_week,
                    "pollution_tests": pollution_this_week,
                },
                "non_conformities": {
                    "sieve": nonconform_sieve,
                    "pollution": nonconform_pollution,
                },
                "recent_sieve": [dict(r) for r in recent_sieve],
                "recent_pollution": [dict(r) for r in recent_pollution],
            }

    def get_trend_data(self, aggregate_type: str, days: int = 30) -> list:
        start = (date.today() - timedelta(days=days)).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT test_date, sieve_results, status
                FROM sieve_analyses
                WHERE aggregate_type=? AND test_date>=?
                ORDER BY test_date
            """, (aggregate_type, start)).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["sieve_results"] = json.loads(d["sieve_results"])
                result.append(d)
            return result

    def get_pollution_trend(self, days: int = 30) -> list:
        start = (date.today() - timedelta(days=days)).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT test_date, aggregate_type, mb_value, sand_equivalent,
                       fine_content, clay_lumps, status
                FROM pollution_tests
                WHERE test_date>=?
                ORDER BY test_date
            """, (start,)).fetchall()
            return [dict(r) for r in rows]

    def get_record_counts(self) -> dict:
        with self._get_conn() as conn:
            return {
                "sieve_analyses": conn.execute("SELECT COUNT(*) FROM sieve_analyses").fetchone()[0],
                "pollution_tests": conn.execute("SELECT COUNT(*) FROM pollution_tests").fetchone()[0],
                "concrete_recipes": conn.execute("SELECT COUNT(*) FROM concrete_recipes").fetchone()[0],
                "weekly_reports": conn.execute("SELECT COUNT(*) FROM weekly_reports").fetchone()[0],
            }
