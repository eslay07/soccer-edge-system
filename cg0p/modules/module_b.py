# ============================================================
#  CG-0P — modules/module_b.py
#  MÓDULO B — Team Corners FT (Prioridad 1)
#  Evalúa corners de un equipo específico en el partido completo.
# ============================================================

from ..core.devig import calculate_edge, calculate_ev
from ..core.poisson import calculate_lambda, poisson_probability
from ..config.constants import CALIBRATION_TAXES


TAX_BASE = CALIBRATION_TAXES["B_team_corners_ft"]   # -1.0 pp
EG_HOME_PENALTY = -4.0                              # Si EG Home >= 25%


def _check_fc_bidireccional(team_side: str, match_data: dict) -> bool:
    """
    Verifica si aplica el Favorito Clínico Bidireccional (PATCH_FC_Bidireccional).
    Aplica a cualquier equipo que marque y administre, sin importar si es favorito.

    Returns:
        True si FC está activo (→ PAPER)
    """
    if team_side == "home":
        goal_prob      = match_data.get("home_early_goal_prob", 0.0)
        corners_when_w = match_data.get("home_corners_when_winning", 999)
    else:
        goal_prob      = match_data.get("away_early_goal_prob", 0.0)
        corners_when_w = match_data.get("away_corners_when_winning", 999)

    return goal_prob >= 0.30 and corners_when_w <= 4.0


def _calculate_team_lambda(team_side: str, match_data: dict,
                            markets: dict) -> tuple:
    """
    Calcula el lambda de corners para un equipo específico.

    Returns:
        (lambda_val, data_quality: str)
    """
    if team_side == "home":
        team_avg   = match_data.get("home_corners_avg", 5.0)
        opp_conced = match_data.get("away_corners_conceded", 5.0)
        recent_avg = match_data.get("home_corners_last5", None)
    else:
        team_avg   = match_data.get("away_corners_avg", 4.5)
        opp_conced = match_data.get("home_corners_conceded", 5.0)
        recent_avg = match_data.get("away_corners_last5", None)

    h2h_corners = match_data.get("h2h", {}).get("corners_home" if team_side == "home"
                                                 else "corners_away", None)
    h2h_avg = sum(h2h_corners) / len(h2h_corners) if h2h_corners else None

    lam = calculate_lambda(
        team_avg=team_avg,
        opponent_conceded_avg=opp_conced,
        recent_form_avg=recent_avg,
        h2h_avg=h2h_avg,
    )

    quality = "buena" if recent_avg is not None and h2h_avg is not None else "parcial"
    return lam, quality


def evaluate_module_b(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo B — Team Corners FT.

    Busca candidatos Over/Under corners de cada equipo.

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []
    match_data["h2h"] = h2h

    for team_side in ("home", "away"):
        market_key = f"team_corners_{team_side}"
        if market_key not in markets:
            continue

        mkt         = markets[market_key]
        odds_over   = mkt["odds_over"]
        odds_under  = mkt["odds_under"]
        p_over_mkt  = mkt["p_over"]
        p_under_mkt = mkt["p_under"]

        team_name = match_data.get(
            "home_team" if team_side == "home" else "away_team", team_side
        )

        # ── Lambda del equipo ──────────────────────────────
        lam, data_q = _calculate_team_lambda(team_side, match_data, markets)

        # Umbral de la línea (buscamos en el key del mercado)
        threshold = mkt.get("threshold", 4.5)

        # Probabilidades Poisson
        p_model_over  = poisson_probability(lam, threshold, "over")
        p_model_under = poisson_probability(lam, threshold, "under")

        # ── Verificar FC Bidireccional ─────────────────────
        fc_active = _check_fc_bidireccional(team_side, match_data)

        # ── Necesita 2 indicadores convergentes ───────────
        # Indicadores: lambda > umbral, H2H positivo, forma reciente
        indicators = 0
        if lam > threshold:
            indicators += 1
        if data_q == "buena":
            indicators += 1
        h2h_avg_corners = None
        if h2h and h2h.get("corners_home" if team_side == "home" else "corners_away"):
            vals = h2h["corners_home" if team_side == "home" else "corners_away"]
            h2h_avg_corners = sum(vals) / len(vals)
            if h2h_avg_corners > threshold:
                indicators += 1

        # ── Evaluar OVER ───────────────────────────────────
        edge_over = calculate_edge(p_model_over, p_over_mkt) + TAX_BASE

        # Penalización EG Home
        eg_prob = match_data.get(
            f"{'home' if team_side == 'home' else 'away'}_early_goal_prob", 0.0
        )
        patches_over = []
        paper_trigger_over = False

        if eg_prob >= 0.25:
            edge_over += EG_HOME_PENALTY
            patches_over.append(f"EG_Home_Pen: {EG_HOME_PENALTY:+.1f} pp (EG={eg_prob:.0%})")

        if fc_active:
            paper_trigger_over = True
            patches_over.append("FC_Bidireccional → PAPER")

        if indicators < 2:
            paper_trigger_over = True
            patches_over.append(f"Two-Key-Rule: solo {indicators}/2 indicadores → PAPER")

        uncertainty = 1 if data_q == "parcial" else 0
        candidates.append({
            "module":         "B",
            "team":           team_side,
            "direction":      "over",
            "market":         f"corners_over",
            "market_label":   f"{team_name} Over {threshold} CK",
            "threshold":      threshold,
            "odds":           odds_over,
            "p_implied":      p_over_mkt,
            "p_model":        p_model_over,
            "lambda":         lam,
            "edge_pp":        edge_over,
            "patches_applied":patches_over,
            "paper_trigger":  paper_trigger_over,
            "uncertainty":    uncertainty,
            "current_market": "corners_over",
            "team_early_goal_prob": eg_prob,
            "goal_before_30_prob":  match_data.get(f"{team_side}_early_goal_prob", 0.0),
            "corners_when_winning": match_data.get(f"{team_side}_corners_when_winning", 999),
        })

        # ── Evaluar UNDER ──────────────────────────────────
        edge_under = calculate_edge(p_model_under, p_under_mkt) + TAX_BASE
        patches_under = []
        paper_trigger_under = False

        uncertainty_u = 1 if data_q == "parcial" else 0
        candidates.append({
            "module":         "B",
            "team":           team_side,
            "direction":      "under",
            "market":         "corners_under",
            "market_label":   f"{team_name} Under {threshold} CK",
            "threshold":      threshold,
            "odds":           odds_under,
            "p_implied":      p_under_mkt,
            "p_model":        p_model_under,
            "lambda":         lam,
            "edge_pp":        edge_under,
            "patches_applied":patches_under,
            "paper_trigger":  paper_trigger_under,
            "uncertainty":    uncertainty_u,
            "current_market": "corners_under",
            "team_early_goal_prob": eg_prob,
            "goal_before_30_prob":  match_data.get(f"{team_side}_early_goal_prob", 0.0),
            "corners_when_winning": match_data.get(f"{team_side}_corners_when_winning", 999),
        })

    return candidates
