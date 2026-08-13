# ============================================================
#  CG-0P — modules/module_a.py
#  MÓDULO A — Goles Alt Totals (Prioridad 6, Limitado)
#  Solo elegible U5.5+ con CI <= 2
# ============================================================

from ..core.devig import calculate_edge
from ..core.poisson import poisson_probability
from ..config.constants import CALIBRATION_TAXES, CI_ULTRA_COLCHON, CI_UNDERS_FINOS


TAX_BASE = CALIBRATION_TAXES["A_goals_alt_totals"]   # -0.5 pp
MIN_PROB_UNDER = 0.72
LADDER = [6.5, 5.5, 4.5, 3.5]  # Escalera de unders permitidos


def _eligible_for_module_a(chaos_index: int, threshold: float) -> tuple:
    """
    Verifica si el mercado es elegible para Módulo A.

    Returns:
        (eligible: bool, reason: str)
    """
    if chaos_index >= CI_ULTRA_COLCHON:
        if threshold <= 4.5:
            return False, f"CI={chaos_index} >= {CI_ULTRA_COLCHON}: NUNCA Under 4.5"
        return True, "Ultra-colchón permitido (CI alto)"

    if chaos_index >= CI_UNDERS_FINOS:
        if threshold <= 4.5:
            return False, f"CI={chaos_index} >= {CI_UNDERS_FINOS}: no unders finos, solo colchón alto"
        return True, "Solo colchón alto (CI moderado-alto)"

    # CI <= 2: solo U5.5+
    if threshold < 5.5:
        return False, f"CI={chaos_index}: solo U5.5+ elegibles (threshold={threshold})"

    return True, "Elegible (CI bajo)"


def evaluate_module_a(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo A — Goles Alt Totals.

    Busca Unders de goles con líneas altas (U5.5, U6.5).

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []
    ci = match_data.get("chaos_index", 0)

    # Lambda de goles esperados
    xg_home    = match_data.get("home_xg", 1.3)
    xg_away    = match_data.get("away_xg", 1.1)
    xga_home   = match_data.get("home_xga", 1.2)
    xga_away   = match_data.get("away_xga", 1.0)

    # Lambda ajustado (mixtura xG del equipo y xGA del rival)
    lam_home = (xg_home + xga_away) / 2.0
    lam_away = (xg_away + xga_home) / 2.0
    lam_total = lam_home + lam_away

    match_data["expected_goals_total"] = lam_total

    # Recorrer la escalera de unders
    for threshold in LADDER:
        market_key = f"goals_under_{int(threshold * 10)}"  # "goals_under_55"

        # También buscar con formato alternativo
        alt_keys = [
            market_key,
            f"goals_u{int(threshold)}5",
            f"alt_goals_under_{threshold}",
            "goals_alt_totals",
        ]

        mkt = None
        for k in alt_keys:
            if k in markets:
                mkt = markets[k]
                break

        if mkt is None:
            continue

        eligible, reason = _eligible_for_module_a(ci, threshold)
        if not eligible:
            candidates.append({
                "module":         "A",
                "direction":      "under",
                "market":         f"goals_under_{threshold}",
                "market_label":   f"Under {threshold} Goles",
                "threshold":      threshold,
                "odds":           mkt.get("odds_under", 0),
                "p_model":        0,
                "edge_pp":        -99.0,
                "patches_applied":[f"No elegible: {reason}"],
                "paper_trigger":  True,
                "current_market": f"goals_under_{threshold}",
            })
            continue

        odds_under  = mkt.get("odds_under", 0)
        p_under_mkt = mkt.get("p_under", 0.5)

        p_model_under = poisson_probability(lam_total, threshold, "under")

        edge_pp  = calculate_edge(p_model_under, p_under_mkt) + TAX_BASE
        patches  = []
        paper_tr = False

        # p_final mínimo 72% para Unders
        if p_model_under < MIN_PROB_UNDER:
            paper_tr = True
            patches.append(
                f"p_model={p_model_under:.0%} < {MIN_PROB_UNDER:.0%} mínimo → PAPER"
            )

        candidates.append({
            "module":         "A",
            "team":           "total",
            "direction":      "under",
            "market":         f"goals_under_{threshold}",
            "market_label":   f"Under {threshold} Goles",
            "threshold":      threshold,
            "odds":           odds_under,
            "p_implied":      p_under_mkt,
            "p_model":        p_model_under,
            "lambda":         lam_total,
            "edge_pp":        edge_pp,
            "patches_applied":patches,
            "paper_trigger":  paper_tr,
            "current_market": f"goals_under_{threshold}",
            "expected_goals": lam_total,
            "chaos_index":    ci,
        })

        # Si encontramos un Under elegible con edge suficiente, no seguir escalera
        # (buscamos la línea más segura primero)
        if not paper_tr and edge_pp >= 7.0:
            break

    return candidates
