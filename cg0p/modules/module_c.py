# ============================================================
#  CG-0P — modules/module_c.py
#  MÓDULO C — Corners 1T Team (Prioridad 2)
#  Evalúa corners de primera mitad por equipo.
# ============================================================

from ..core.devig import calculate_edge
from ..core.poisson import calculate_lambda, poisson_probability
from ..config.constants import CALIBRATION_TAXES


TAX_BASE = CALIBRATION_TAXES["C_corners_1t_team"]   # -1.0 pp


def _check_posesion_esteril(team_side: str, match_data: dict) -> bool:
    """
    Detecta si un equipo tiene patrón de Posesión Estéril (PE).
    Alta posesión pero pocos corners y bajo xG.
    """
    if team_side == "home":
        possession = match_data.get("home_possession", 50.0)
        corners    = match_data.get("home_corners_avg", 5.0)
        xg         = match_data.get("home_xg", 1.5)
    else:
        possession = match_data.get("away_possession", 50.0)
        corners    = match_data.get("away_corners_avg", 4.5)
        xg         = match_data.get("away_xg", 1.2)

    return possession >= 55.0 and corners <= 4.5 and xg <= 1.2


def _check_visitor_surge_1h(match_data: dict) -> tuple:
    """
    Verifica si aplica el flag VisitorSurge1H (PATCH_v1.2.7).

    Returns:
        (active: bool, conditions_met: int, penalty_pp: float)
    """
    conditions_met = sum([
        match_data.get("away_losing_streak", 0) >= 3,
        match_data.get("away_manager_under_pressure", False),
        match_data.get("away_squad_quality_percentile", 0) >= 50,
        match_data.get("h2h_competitive", False),
    ])
    active = conditions_met >= 2
    penalty = -4.0 if active else 0.0
    return active, conditions_met, penalty


def evaluate_module_c(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo C — Corners 1T Team.

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []
    match_data["h2h"] = h2h

    # Verificar VisitorSurge1H una vez para el visitante
    vs_active, vs_conditions, vs_penalty = _check_visitor_surge_1h(match_data)

    # Early goal any team (para P-G1-1T)
    eg_any = max(
        match_data.get("home_early_goal_prob", 0.0),
        match_data.get("away_early_goal_prob", 0.0),
    )
    eg_before_35 = match_data.get("early_goal_before_35_prob", eg_any * 1.2)

    for team_side in ("home", "away"):
        market_key = f"1h_corners_{team_side}"
        if market_key not in markets:
            continue

        mkt        = markets[market_key]
        odds_over  = mkt["odds_over"]
        odds_under = mkt["odds_under"]
        p_over_mkt = mkt["p_over"]
        p_under_mkt= mkt["p_under"]
        threshold  = mkt.get("threshold", 2.5)

        team_name = match_data.get(
            "home_team" if team_side == "home" else "away_team", team_side
        )

        # ── Lambda para 1T (aprox. 40-45% del FT) ─────────
        if team_side == "home":
            ft_avg   = match_data.get("home_corners_avg", 5.0)
            opp_conc = match_data.get("away_corners_conceded", 5.0)
        else:
            ft_avg   = match_data.get("away_corners_avg", 4.5)
            opp_conc = match_data.get("home_corners_conceded", 5.0)

        lam_ft = calculate_lambda(
            team_avg=ft_avg,
            opponent_conceded_avg=opp_conc,
        )
        lam_1h = lam_ft * 0.42  # 1T representa ~42% de los corners totales

        p_model_over  = poisson_probability(lam_1h, threshold, "over")
        p_model_under = poisson_probability(lam_1h, threshold, "under")

        # ── PE check ──────────────────────────────────────
        pe_active = _check_posesion_esteril(team_side, match_data)

        # ── OVER 1H ───────────────────────────────────────
        edge_over  = calculate_edge(p_model_over, p_over_mkt) + TAX_BASE
        patches_o  = []
        paper_tr_o = False

        if pe_active:
            paper_tr_o = True
            patches_o.append("PE ON → PAPER (Posesión Estéril)")

        # EG alto antes del minuto 15
        eg_prob_15 = match_data.get(f"{'home' if team_side == 'home' else 'away'}_early_goal_prob_15", 0.0)
        if eg_prob_15 >= 0.30:
            edge_over += -1.0
            patches_o.append(f"EG_High (<15'): -1.0 pp (p={eg_prob_15:.0%})")

        candidates.append({
            "module":         "C",
            "team":           team_side,
            "direction":      "over",
            "market":         "1h_corners_over",
            "market_label":   f"{team_name} Over {threshold} CK 1T",
            "threshold":      threshold,
            "odds":           odds_over,
            "p_implied":      p_over_mkt,
            "p_model":        p_model_over,
            "lambda":         lam_1h,
            "edge_pp":        edge_over,
            "patches_applied":patches_o,
            "paper_trigger":  paper_tr_o,
            "current_market": "1h_corners_over",
            "early_goal_any_team_prob": eg_before_35,
            "bet_team_role":  "neutral",
        })

        # ── UNDER 1H ──────────────────────────────────────
        edge_under  = calculate_edge(p_model_under, p_under_mkt) + TAX_BASE
        patches_u   = []
        paper_tr_u  = False

        # P-G1-1T: si gol antes del min 35 del equipo que quedaría perdiendo
        # Para simplificar: si equipo_apostado es visitante y marca antes
        # el local podría reaccionar (o viceversa)
        if eg_before_35 >= 0.30:
            bet_role = _determine_bet_role(team_side, match_data)
            if bet_role == "likely_losing":
                paper_tr_u = True
                patches_u.append(
                    f"P-G1-1T: gol < 35' ({eg_before_35:.0%}) equipo perdería → PAPER"
                )

        # VisitorSurge1H solo aplica al Under 1H del visitante
        if team_side == "away" and vs_active:
            edge_under += vs_penalty
            patches_u.append(
                f"VisitorSurge1H: {vs_penalty:+.1f} pp ({vs_conditions}/4 cond.)"
            )
            if edge_under < 7.0:
                paper_tr_u = True
                patches_u.append("VisitorSurge1H → PAPER (edge < 7 pp post-penalización)")

        candidates.append({
            "module":         "C",
            "team":           team_side,
            "direction":      "under",
            "market":         "1h_corners_under",
            "market_label":   f"{team_name} Under {threshold} CK 1T",
            "threshold":      threshold,
            "odds":           odds_under,
            "p_implied":      p_under_mkt,
            "p_model":        p_model_under,
            "lambda":         lam_1h,
            "edge_pp":        edge_under,
            "patches_applied":patches_u,
            "paper_trigger":  paper_tr_u,
            "current_market": "1h_corners_under",
            "early_goal_any_team_prob": eg_before_35,
            "bet_team_role":  _determine_bet_role(team_side, match_data),
            "visitor_losing_streak":    match_data.get("away_losing_streak", 0),
            "visitor_manager_under_pressure": match_data.get("away_manager_under_pressure", False),
            "visitor_squad_quality_percentile": match_data.get("away_squad_quality_percentile", 0),
            "h2h_competitive": match_data.get("h2h_competitive", False),
        })

    return candidates


def _determine_bet_role(team_side: str, match_data: dict) -> str:
    """
    Determina si el equipo apostado es 'likely_losing', 'likely_winning' o 'neutral'.
    Se basa en las probabilidades implícitas del mercado principal.
    """
    # Usar odds de victoria como proxy
    if team_side == "home":
        win_prob = match_data.get("home_win_prob", 0.45)
    else:
        win_prob = match_data.get("away_win_prob", 0.30)

    if win_prob < 0.35:
        return "likely_losing"
    elif win_prob > 0.55:
        return "likely_winning"
    return "neutral"
