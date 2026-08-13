# ============================================================
#  CG-0P — tracking/history.py
#  Gestión del historial de picks con SQLite
# ============================================================

import sqlite3
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent.parent / "cg0p_picks.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    conn = _get_conn()
    c = conn.cursor()

    # Tabla principal de picks CG-0P
    c.execute("""
        CREATE TABLE IF NOT EXISTS cg0p_picks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_analisis  TEXT NOT NULL,
            liga            TEXT,
            partido         TEXT NOT NULL,
            fecha_partido   TEXT,
            modulo          TEXT NOT NULL,
            sub_mercado     TEXT,
            mercado_label   TEXT NOT NULL,
            cuota           REAL NOT NULL,
            prob_implicita  REAL,
            prob_modelo     REAL,
            edge_pp         REAL,
            ev              REAL,
            robustez        INTEGER,
            chaos_index     INTEGER,
            decision        TEXT NOT NULL,
            stake           REAL DEFAULT 0,
            patches         TEXT,
            resultado       TEXT,
            pl_unidades     REAL,
            notas           TEXT
        )
    """)

    # Tabla PAPER-A
    c.execute("""
        CREATE TABLE IF NOT EXISTS cg0p_paper_a (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_analisis  TEXT NOT NULL,
            liga            TEXT,
            partido         TEXT NOT NULL,
            modulo          TEXT,
            mercado_label   TEXT NOT NULL,
            cuota           REAL,
            edge_pp         REAL,
            prob_modelo     REAL,
            resultado       TEXT,
            habria_sido     TEXT
        )
    """)

    # Tabla de calibración por módulo
    c.execute("""
        CREATE TABLE IF NOT EXISTS cg0p_calibracion (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT,
            modulo      TEXT,
            edge_calc   REAL,
            edge_real   REAL,
            acierto     INTEGER,
            brier_score REAL
        )
    """)

    # Tabla de patches aplicados (auditoría)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cg0p_patch_audit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT,
            pick_id     INTEGER,
            patch_id    TEXT,
            penalty_pp  REAL,
            resultado   TEXT
        )
    """)

    conn.commit()
    conn.close()


class PickHistory:
    """Gestiona el historial de picks del sistema CG-0P."""

    def __init__(self):
        init_db()

    def save_pick(self, match_result: dict, pick: dict) -> int:
        """
        Guarda un pick o PAPER-A en la base de datos.

        Args:
            match_result: resultado del pipeline (partido + metadata)
            pick:         dict del pick individual

        Returns:
            id del registro insertado
        """
        conn = _get_conn()
        c    = conn.cursor()

        patches_json = json.dumps(pick.get("patches_applied", []))
        decision     = pick.get("decision", "PASS")

        if decision == "EJECUTAR":
            c.execute("""
                INSERT INTO cg0p_picks
                (fecha_analisis, liga, partido, fecha_partido,
                 modulo, sub_mercado, mercado_label, cuota,
                 prob_implicita, prob_modelo, edge_pp, ev,
                 robustez, chaos_index, decision, stake, patches)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                datetime.now().isoformat(),
                match_result.get("league", ""),
                match_result.get("match", ""),
                match_result.get("date", ""),
                pick.get("module", ""),
                pick.get("sub_market", ""),
                pick.get("market_label", ""),
                pick.get("odds", 0),
                pick.get("p_implied", 0),
                pick.get("p_model", 0),
                pick.get("edge_pp", 0),
                pick.get("ev", 0),
                pick.get("stress_test", {}).get("robustness", 0),
                match_result.get("chaos_index", 0),
                decision,
                pick.get("stake", 0),
                patches_json,
            ))
        elif decision == "PAPER-A":
            c.execute("""
                INSERT INTO cg0p_paper_a
                (fecha_analisis, liga, partido, modulo, mercado_label,
                 cuota, edge_pp, prob_modelo)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                datetime.now().isoformat(),
                match_result.get("league", ""),
                match_result.get("match", ""),
                pick.get("module", ""),
                pick.get("market_label", ""),
                pick.get("odds", 0),
                pick.get("edge_pp", 0),
                pick.get("p_model", 0),
            ))

        row_id = c.lastrowid
        conn.commit()
        conn.close()
        return row_id

    def resolve_pick(self, pick_id: int, resultado: str,
                     pl_unidades: float, notas: str = "") -> bool:
        """
        Resuelve un pick con su resultado real.

        Args:
            pick_id:     id del pick en la DB
            resultado:   "W" (hit) | "L" (miss) | "V" (void/push)
            pl_unidades: ganancia/pérdida en unidades
            notas:       observaciones post-match

        Returns:
            True si se actualizó correctamente
        """
        conn = _get_conn()
        c    = conn.cursor()
        c.execute("""
            UPDATE cg0p_picks
            SET resultado=?, pl_unidades=?, notas=?
            WHERE id=?
        """, (resultado, pl_unidades, notas, pick_id))
        updated = c.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def get_pending_picks(self) -> list:
        """Devuelve picks sin resolver."""
        conn = _get_conn()
        c    = conn.cursor()
        c.execute("""
            SELECT id, fecha_analisis, partido, modulo, mercado_label,
                   cuota, edge_pp, ev, stake
            FROM cg0p_picks
            WHERE resultado IS NULL AND decision='EJECUTAR'
            ORDER BY fecha_analisis DESC
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_resolved_picks(self, limit: int = 50) -> list:
        """Devuelve picks resueltos con sus resultados."""
        conn = _get_conn()
        c    = conn.cursor()
        c.execute("""
            SELECT id, fecha_analisis, partido, modulo, mercado_label,
                   cuota, edge_pp, ev, decision, stake, resultado, pl_unidades
            FROM cg0p_picks
            WHERE resultado IS NOT NULL
            ORDER BY fecha_analisis DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_statistics(self) -> dict:
        """Calcula estadísticas globales del sistema."""
        conn = _get_conn()
        c    = conn.cursor()

        c.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN resultado='W' THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN resultado='L' THEN 1 ELSE 0 END) as misses,
                SUM(CASE WHEN resultado='V' THEN 1 ELSE 0 END) as voids,
                SUM(pl_unidades) as pl_total,
                AVG(edge_pp) as edge_promedio,
                SUM(stake) as stake_total
            FROM cg0p_picks
            WHERE resultado IS NOT NULL
        """)
        row = dict(c.fetchone())

        total = row["total"] or 0
        hits  = row["hits"]  or 0
        pl    = row["pl_total"] or 0.0
        stake = row["stake_total"] or 0.0

        win_rate = (hits / total * 100) if total > 0 else 0.0
        roi      = (pl / stake * 100) if stake > 0 else 0.0

        # Por módulo
        c.execute("""
            SELECT modulo,
                   COUNT(*) as total,
                   SUM(CASE WHEN resultado='W' THEN 1 ELSE 0 END) as hits,
                   SUM(pl_unidades) as pl
            FROM cg0p_picks
            WHERE resultado IS NOT NULL
            GROUP BY modulo
        """)
        by_module = {r["modulo"]: dict(r) for r in c.fetchall()}

        conn.close()

        return {
            "total_picks":     total,
            "hits":            hits,
            "misses":          row["misses"] or 0,
            "voids":           row["voids"] or 0,
            "win_rate_pct":    round(win_rate, 1),
            "roi_pct":         round(roi, 1),
            "pl_total":        round(pl, 2),
            "edge_promedio_pp":round(row["edge_promedio"] or 0, 1),
            "by_module":       by_module,
        }

    def get_paper_a_history(self, limit: int = 20) -> list:
        """Devuelve el historial de PAPER-A."""
        conn = _get_conn()
        c    = conn.cursor()
        c.execute("""
            SELECT id, fecha_analisis, partido, modulo,
                   mercado_label, cuota, edge_pp, resultado, habria_sido
            FROM cg0p_paper_a
            ORDER BY fecha_analisis DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def add_pick_history_entry(self, entry: dict) -> None:
        """Agrega una entrada manual al historial de picks (para importar datos históricos)."""
        conn = _get_conn()
        c    = conn.cursor()
        c.execute("""
            INSERT INTO cg0p_picks
            (fecha_analisis, liga, partido, fecha_partido, modulo,
             mercado_label, cuota, edge_pp, decision, stake, resultado, pl_unidades, notas)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            entry.get("fecha_analisis", datetime.now().isoformat()),
            entry.get("liga", ""),
            entry.get("partido", ""),
            entry.get("fecha_partido", ""),
            entry.get("modulo", ""),
            entry.get("mercado_label", ""),
            entry.get("cuota", 0),
            entry.get("edge_pp", 0),
            entry.get("decision", "EJECUTAR"),
            entry.get("stake", 1.0),
            entry.get("resultado"),
            entry.get("pl_unidades"),
            entry.get("notas", ""),
        ))
        conn.commit()
        conn.close()
