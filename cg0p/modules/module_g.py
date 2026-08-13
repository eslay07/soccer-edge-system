# ============================================================
#  CG-0P — modules/module_g.py
#  MÓDULO G — BTTS (Both Teams To Score) (Prioridad 5)
#  Sub-mercados: G1 (BTTS Sí/No FT), G3 (BTTS 1T)
# ============================================================

from ..core.devig import calculate_edge
from ..config.constants import CALIBRATION_TAXES


TAXES = {
    "G1_si": CALIBRATION_TAXES["G1_btts_si"],   # -1.5
    "G1_no": CALIBRATION_TAXES["G1_btts_no"],   # -2.0
    "G3":    CALIBRATION_TAXES["G3_btts_1t"],   # -3.0
}

THRESHOLD_SI = 0.65
THRESHOLD_NO = 0.70


def _estimate_btts_probability(match_data: dict) -> tuple:
    """
    Estima la probabilidad de BTTS usando xG y datos históricos.

    Returns:
        (p_btts_si: float, p_btts_no: float)
    """
    xg_home = match_data.get("home_xg", 1.3)
    xg_away = match_data.get("away_xg", 1.1)

    # Probabilidad de que cada equipo marque (Poisson aproximado)
    import math
    p_home_scores = 1.0 - math.exp(-xg_home)  # P(goals >= 1)
    p_away_scores = 1.0 - math.exp(-xg_away)

    # Ajuste con historial BTTS
    btts_pct_home = match_data.get("home_btts_pct_last10", 0.5)
    btts_pct_away = match_data.get("away_btts_pct_last10", 0.5)
    btts_hist_avg = (btts_pct_home + btts_pct_away) / 2.0

    # Ponderación: 60% xG, 40% histórico
    p_btts_si = (p_home_scores * p_away_scores) * 0.60 + btts_hist_avg * 0.40
    p_btts_no = 1.0 - p_btts_si

    return round(p_btts_si, 4), round(p_btts_no, 4)


def _apply_btts_flags(p_btts_si: float, match_data: dict) -> tuple:
    """
    Aplica los flags del módulo G a la probabilidad BTTS Sí.

    Returns:
        (p_ajustada: float, flags_applied: list)
    """
    flags_applied = []
    p = p_btts_si

    xg_home = match_data.get("home_xg", 1.3)
    xg_away = match_data.get("away_xg", 1.1)
    cs_home = match_data.get("home_clean_sheet_pct", 0.3)
    cs_away = match_data.get("away_clean_sheet_pct", 0.3)
    low_block = match_data.get("low_block_confirmed", False)
    no_motiv  = match_data.get("no_motivation_team", False)

    # xGDominance: ambos equipos con xG alto
    if xg_home >= 1.50 and xg_away >= 1.20:
        bonus = 0.03
        p = min(p + bonus, 0.99)
        flags_applied.append(f"xGDominance: +3 pp (xG {xg_home:.2f}/{xg_away:.2f})")

    # CleanSheetRisk: algún equipo tiene mucha hoja en blanco
    max_cs = max(cs_home, cs_away)
    if max_cs >= 0.45:
        penalty = 0.03
        p = max(p - penalty, 0.01)
        flags_applied.append(f"CleanSheetRisk: -3 pp (CS {max_cs:.0%})")

    # LowBlock
    if low_block:
        penalty = 0.02
        p = max(p - penalty, 0.01)
        flags_applied.append("LowBlock: -2 pp")

    # NoMotivation
    if no_motiv:
        penalty = 0.02
        p = max(p - penalty, 0.01)
        flags_applied.append("NoMotivacion: -2 pp xG")

    return p, flags_applied


def _kill_switches_btts(match_data: dict, h2h: dict,
                         direction: str) -> tuple:
    """
    Verifica kill-switches del módulo G.

    Returns:
        (paper_trigger: bool, reason: str)
    """
    # Sin xG verificado
    if not match_data.get("xg_verified", True):
        return True, "Sin xG verificado ambos equipos → PAPER"

    # CleanSheetRisk en ambos equipos
    cs_home = match_data.get("home_clean_sheet_pct", 0)
    cs_away = match_data.get("away_clean_sheet_pct", 0)
    if cs_home >= 0.45 and cs_away >= 0.45:
        return True, "CleanSheetRisk ON en ambos equipos → PAPER"

    # H2H: BTTS <= 1 vez en últimos 3 y pick es BTTS Sí
    if direction == "si":
        btts_h2h = h2h.get("btts_results", [])
        if len(btts_h2h) >= 3:
            btts_count = sum(1 for x in btts_h2h[:3] if x)
            if btts_count <= 1:
                return False, ""  # No kill, pero aplicar -4 pp (lo hacemos en edge)

    return False, ""


def evaluate_module_g(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo G — BTTS.

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []

    if "btts" not in markets:
        return candidates

    mkt        = markets["btts"]
    odds_si    = mkt.get("odds_over", 0)
    odds_no    = mkt.get("odds_under", 0)
    p_si_mkt   = mkt.get("p_over", 0.5)
    p_no_mkt   = mkt.get("p_under", 0.5)

    p_btts_si_raw, p_btts_no_raw = _estimate_btts_probability(match_data)
    p_btts_si, flags_si = _apply_btts_flags(p_btts_si_raw, match_data)
    p_btts_no = 1.0 - p_btts_si

    # ── BTTS Sí ───────────────────────────────────────────
    edge_si  = calculate_edge(p_btts_si, p_si_mkt) + TAXES["G1_si"]
    patches_si  = list(flags_si)
    paper_tr_si = False

    kill_ok, kill_reason = _kill_switches_btts(match_data, h2h, "si")
    if kill_ok:
        paper_tr_si = True
        patches_si.append(kill_reason)

    # H2H BTTS <= 1/3: -4 pp
    btts_h2h = h2h.get("btts_results", [])
    if len(btts_h2h) >= 3:
        btts_count = sum(1 for x in btts_h2h[:3] if x)
        if btts_count <= 1:
            edge_si -= 4.0
            patches_si.append(f"H2H BTTS solo {btts_count}/3: -4.0 pp")

    candidates.append({
        "module":         "G",
        "sub_market":     "G1",
        "team":           "total",
        "direction":      "si",
        "market":         "btts_si",
        "market_label":   "BTTS Sí",
        "odds":           odds_si,
        "p_implied":      p_si_mkt,
        "p_model":        p_btts_si,
        "edge_pp":        edge_si,
        "patches_applied":patches_si,
        "paper_trigger":  paper_tr_si,
        "current_market": "btts_si",
    })

    # ── BTTS No ───────────────────────────────────────────
    edge_no  = calculate_edge(p_btts_no, p_no_mkt) + TAXES["G1_no"]
    patches_no  = []
    paper_tr_no = False

    kill_ok_no, kill_reason_no = _kill_switches_btts(match_data, h2h, "no")
    if kill_ok_no:
        paper_tr_no = True
        patches_no.append(kill_reason_no)

    candidates.append({
        "module":         "G",
        "sub_market":     "G1",
        "team":           "total",
        "direction":      "no",
        "market":         "btts_no",
        "market_label":   "BTTS No",
        "odds":           odds_no,
        "p_implied":      p_no_mkt,
        "p_model":        p_btts_no,
        "edge_pp":        edge_no,
        "patches_applied":patches_no,
        "paper_trigger":  paper_tr_no,
        "current_market": "btts_no",
    })

    return candidates
