# ============================================================
#  SOCCER EDGE SYSTEM — database.py
#  SQLite para almacenar picks, resultados y aprendizaje
# ============================================================

import sqlite3
from datetime import datetime
from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def inicializar_db():
    """Crea las tablas si no existen."""
    conn = get_conn()
    c = conn.cursor()

    # Tabla principal de picks
    c.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_analisis  TEXT NOT NULL,
            liga            TEXT NOT NULL,
            partido         TEXT NOT NULL,
            fecha_partido   TEXT NOT NULL,
            mercado         TEXT NOT NULL,
            seleccion       TEXT NOT NULL,
            cuota_tomada    REAL NOT NULL,
            prob_implicita  REAL NOT NULL,
            prob_modelo     REAL NOT NULL,
            edge_pct        REAL NOT NULL,
            kelly_units     REAL NOT NULL,
            stake           REAL NOT NULL,
            es_pick         INTEGER NOT NULL,  -- 1=Pick, 0=Pass
            motivo_pass     TEXT,
            resultado       TEXT,              -- 'W', 'L', 'P' (push), NULL=pendiente
            pl_unidades     REAL,              -- P&L en unidades
            screenshot_path TEXT
        )
    """)

    # Tabla de aprendizaje: registro de errores de calibración
    c.execute("""
        CREATE TABLE IF NOT EXISTS calibracion (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            liga        TEXT NOT NULL,
            mercado     TEXT NOT NULL,
            edge_calc   REAL NOT NULL,   -- edge que calculamos
            edge_real   REAL NOT NULL,   -- edge que resultó ser real
            acierto     INTEGER NOT NULL -- 1 o 0
        )
    """)

    # Tabla de sesiones / resumen diario
    c.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT NOT NULL,
            picks_total INTEGER,
            picks_w     INTEGER,
            picks_l     INTEGER,
            picks_p     INTEGER,
            roi_sesion  REAL,
            bankroll    REAL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada.")


def guardar_pick(pick: dict):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO picks (
            fecha_analisis, liga, partido, fecha_partido,
            mercado, seleccion, cuota_tomada, prob_implicita,
            prob_modelo, edge_pct, kelly_units, stake,
            es_pick, motivo_pass, screenshot_path
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        pick["liga"], pick["partido"], pick["fecha_partido"],
        pick["mercado"], pick["seleccion"], pick["cuota"],
        pick["prob_implicita"], pick["prob_modelo"], pick["edge_pct"],
        pick["kelly_units"], pick["stake"],
        1 if pick["es_pick"] else 0,
        pick.get("motivo_pass"), pick.get("screenshot_path")
    ))
    conn.commit()
    pick_id = c.lastrowid
    conn.close()
    return pick_id


def resolver_pick(pick_id: int, resultado: str, pl_unidades: float):
    """Actualiza el resultado de un pick (W/L/P) y registra calibración."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE picks SET resultado=?, pl_unidades=? WHERE id=?
    """, (resultado, pl_unidades, pick_id))

    # Registrar en calibración
    c.execute("SELECT liga, mercado, edge_pct FROM picks WHERE id=?", (pick_id,))
    row = c.fetchone()
    if row:
        liga, mercado, edge_calc = row
        edge_real = pl_unidades  # simplificado: ganancia real como proxy
        acierto = 1 if resultado == "W" else 0
        c.execute("""
            INSERT INTO calibracion (fecha, liga, mercado, edge_calc, edge_real, acierto)
            VALUES (?,?,?,?,?,?)
        """, (datetime.now().isoformat(), liga, mercado, edge_calc, edge_real, acierto))

    conn.commit()
    conn.close()
    print(f"✅ Pick #{pick_id} resuelto como {resultado} | P&L: {pl_unidades:+.2f} u")


def obtener_estadisticas():
    """Retorna stats globales del sistema."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN resultado='W' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN resultado='L' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN resultado='P' THEN 1 ELSE 0 END) as pushes,
            ROUND(SUM(pl_unidades), 2) as pl_total,
            ROUND(AVG(edge_pct), 2) as edge_promedio
        FROM picks WHERE es_pick=1 AND resultado IS NOT NULL
    """)
    row = c.fetchone()
    conn.close()
    if row and row[0] > 0:
        total, wins, losses, pushes, pl_total, edge_prom = row
        roi = (pl_total / total * 100) if total else 0
        tasa_acierto = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        return {
            "total_picks": total,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "pl_total": pl_total,
            "roi_pct": round(roi, 2),
            "tasa_acierto_pct": round(tasa_acierto, 2),
            "edge_promedio": edge_prom,
        }
    return None
