# ============================================================
#  CG-0P — modules/module_d.py
#  MÓDULO D — Hándicap Corners (Prioridad 4)
# ============================================================

from ..core.devig import calculate_edge
from ..config.constants import CALIBRATION_TAXES


TAX_BASE = CALIBRATION_TAXES["D_handicap_corners"]   # -1.5 pp


def evaluate_module_d(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo D — Hándicap Corners.

    Solo válido con dominancia unilateral clara.

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []

    if "corner_handicap" not in markets:
        return candidates

    mkt         = markets["corner_handicap"]
    odds_home   = mkt.get("odds_over", 0)
    odds_away   = mkt.get("odds_under", 0)
    p_home      = mkt.get("p_over", 0.5)
    p_away      = mkt.get("p_under", 0.5)
    handicap    = mkt.get("threshold", -2.5)

    home_team   = match_data.get("home_team", "Local")
    away_team   = match_data.get("away_team", "Visitante")

    # ── Verificar dominancia unilateral clara ─────────────
    home_corners = match_data.get("home_corners_avg", 5.0)
    away_corners = match_data.get("away_corners_avg", 4.5)
    home_conceded = match_data.get("home_corners_conceded", 5.0)
    away_conceded = match_data.get("away_corners_conceded", 5.0)

    # Proyección de corners por equipo
    proj_home = (home_corners + away_conceded) / 2.0
    proj_away = (away_corners + home_conceded) / 2.0
    diff = abs(proj_home - proj_away)
    dominance_unilateral = diff >= 2.0  # ≥ 2 corners de diferencia esperada

    # ── FC check ──────────────────────────────────────────
    fc_active = (
        match_data.get("home_early_goal_prob", 0) >= 0.30
        and match_data.get("home_corners_when_winning", 999) <= 4.0
    )

    # ── SpikeRisk bilateral ───────────────────────────────
    spike_risk = (
        match_data.get("home_late_goal_rate", 0) >= 0.35
        and match_data.get("away_late_goal_rate", 0) >= 0.35
    )

    # ── Árbitro/VAR ───────────────────────────────────────
    ref_var_high = match_data.get("referee_penalties_avg", 0) >= 0.25

    for team_side in ("home", "away"):
        if team_side == "home":
            p_model  = min(proj_home / max(proj_home + proj_away, 0.1), 0.99)
            p_market = p_home
            odds     = odds_home
            label    = f"{home_team} Hándicap CK {handicap:+.1f}"
        else:
            p_model  = min(proj_away / max(proj_home + proj_away, 0.1), 0.99)
            p_market = p_away
            odds     = odds_away
            label    = f"{away_team} Hándicap CK {-handicap:+.1f}"

        edge_pp = calculate_edge(p_model, p_market) + TAX_BASE
        patches = []
        paper_tr = False

        if fc_active:
            paper_tr = True
            patches.append("FC ON → PAPER")

        if not dominance_unilateral:
            paper_tr = True
            patches.append(f"Sin dominancia unilateral (diff={diff:.1f} CK) → PAPER")

        if spike_risk:
            paper_tr = True
            patches.append("SpikeRisk alto bilateral → PAPER")

        if ref_var_high:
            edge_pp -= 1.0
            patches.append(f"Ref/VAR alto: -1.0 pp → cap 0.5u")

        candidates.append({
            "module":         "D",
            "team":           team_side,
            "direction":      "over" if team_side == "home" else "under",
            "market":         "corner_handicap",
            "market_label":   label,
            "threshold":      handicap,
            "odds":           odds,
            "p_implied":      p_market,
            "p_model":        p_model,
            "edge_pp":        edge_pp,
            "patches_applied":patches,
            "paper_trigger":  paper_tr,
            "current_market": "corner_handicap",
        })

    return candidates
