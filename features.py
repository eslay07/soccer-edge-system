# ============================================================
#  SOCCER EDGE SYSTEM — features.py
#  Construye el vector de features para cada partido
# ============================================================

import sqlite3
import pandas as pd
import numpy as np
from config import DB_PATH


# ─────────────────────────────────────────────
#  FEATURES QUE USA EL MODELO
# ─────────────────────────────────────────────
#
#  FORMA RECIENTE (últimos N partidos):
#    - Win rate local/visitante
#    - Goles marcados promedio
#    - Goles recibidos promedio
#    - Puntos de los últimos 5 partidos
#
#  H2H (historial directo):
#    - Win rate home en el H2H
#    - Goles promedio en el H2H
#
#  MERCADO (señales sharp):
#    - Prob. implícita home / away / draw (sin vig)
#    - Movimiento de línea (apertura vs cierre)
#    - % de cuotas por encima del promedio
#
#  CONTEXTO:
#    - Importancia del partido (liga / copa)
#    - Ventaja de local
#    - Días de descanso entre partidos
# ─────────────────────────────────────────────


def calcular_forma(partidos: list, equipo: str, n: int = 5) -> dict:
    """
    Calcula forma reciente de un equipo en sus últimos N partidos.
    partidos: lista de dicts con keys [home, away, goles_home, goles_away, resultado_home]
    resultado_home: 'W', 'D', 'L' desde perspectiva local
    """
    juegos = []
    for p in partidos:
        if p["home"] == equipo:
            juegos.append({
                "gf": p["goles_home"],
                "gc": p["goles_away"],
                "res": p["resultado_home"]
            })
        elif p["away"] == equipo:
            juegos.append({
                "gf": p["goles_away"],
                "gc": p["goles_home"],
                "res": "W" if p["resultado_home"] == "L" else ("L" if p["resultado_home"] == "W" else "D")
            })

    juegos = juegos[-n:]
    if not juegos:
        return {"wins": 0, "draws": 0, "losses": 0, "gf_avg": 0, "gc_avg": 0, "puntos": 0}

    wins   = sum(1 for j in juegos if j["res"] == "W")
    draws  = sum(1 for j in juegos if j["res"] == "D")
    losses = sum(1 for j in juegos if j["res"] == "L")
    gf_avg = np.mean([j["gf"] for j in juegos])
    gc_avg = np.mean([j["gc"] for j in juegos])
    puntos = (wins * 3 + draws) / (len(juegos) * 3)  # normalizado 0-1

    return {
        "wins":   wins   / n,
        "draws":  draws  / n,
        "losses": losses / n,
        "gf_avg": round(gf_avg, 3),
        "gc_avg": round(gc_avg, 3),
        "puntos": round(puntos, 3),
    }


def calcular_h2h(partidos_h2h: list, home: str) -> dict:
    """Historial directo entre los dos equipos."""
    if not partidos_h2h:
        return {"h2h_win_rate": 0.33, "h2h_goles_avg": 2.5, "h2h_partidos": 0}

    wins_home = 0
    goles_totales = []
    for p in partidos_h2h:
        goles_totales.append(p["goles_home"] + p["goles_away"])
        if p["home"] == home and p["resultado_home"] == "W":
            wins_home += 1
        elif p["away"] == home and p["resultado_home"] == "L":
            wins_home += 1

    n = len(partidos_h2h)
    return {
        "h2h_win_rate":   round(wins_home / n, 3),
        "h2h_goles_avg":  round(np.mean(goles_totales), 3),
        "h2h_partidos":   n,
    }


def construir_feature_vector(
    home: str,
    away: str,
    forma_home: dict,
    forma_away: dict,
    h2h: dict,
    prob_implicita_home: float,
    prob_implicita_away: float,
    prob_implicita_draw: float,
    mov_linea_home: float = 0.0,   # cambio en prob desde apertura a cierre
    dias_descanso_home: int = 7,
    dias_descanso_away: int = 7,
) -> dict:
    """
    Combina todas las features en un dict listo para XGBoost.
    """
    return {
        # Forma home
        "home_wins":   forma_home["wins"],
        "home_draws":  forma_home["draws"],
        "home_losses": forma_home["losses"],
        "home_gf":     forma_home["gf_avg"],
        "home_gc":     forma_home["gc_avg"],
        "home_puntos": forma_home["puntos"],

        # Forma away
        "away_wins":   forma_away["wins"],
        "away_draws":  forma_away["draws"],
        "away_losses": forma_away["losses"],
        "away_gf":     forma_away["gf_avg"],
        "away_gc":     forma_away["gc_avg"],
        "away_puntos": forma_away["puntos"],

        # Diferencial (home - away)
        "diff_puntos": forma_home["puntos"]  - forma_away["puntos"],
        "diff_gf":     forma_home["gf_avg"]  - forma_away["gf_avg"],
        "diff_gc":     forma_home["gc_avg"]  - forma_away["gc_avg"],

        # H2H
        "h2h_win_rate":  h2h["h2h_win_rate"],
        "h2h_goles_avg": h2h["h2h_goles_avg"],
        "h2h_partidos":  min(h2h["h2h_partidos"], 10) / 10,  # normalizado

        # Mercado (señal sharp)
        "mkt_home": prob_implicita_home,
        "mkt_away": prob_implicita_away,
        "mkt_draw": prob_implicita_draw,
        "mkt_mov":  mov_linea_home,   # positivo = mercado mueve hacia home

        # Contexto
        "ventaja_local":     1.0,
        "dias_home":         min(dias_descanso_home, 14) / 14,
        "dias_away":         min(dias_descanso_away, 14) / 14,
        "fatiga_diff":       (dias_descanso_home - dias_descanso_away) / 14,
    }
