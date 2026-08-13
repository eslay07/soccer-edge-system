# ============================================================
#  CG-0P — modules/module_f.py
#  MÓDULO F — Tarjetas (Prioridad 3)
#  Sub-mercados: F1 (Total FT), F2 (Por equipo), F3 (Primera), F4 (Roja)
# ============================================================

from ..core.devig import calculate_edge
from ..core.poisson import calculate_lambda_cards, poisson_probability
from ..config.constants import CALIBRATION_TAXES


TAXES = {
    "F1": CALIBRATION_TAXES["F1_total_cards"],   # -1.5
    "F2": CALIBRATION_TAXES["F2_team_cards"],    # -1.0
    "F3": CALIBRATION_TAXES["F3_first_card"],    # -2.0
    "F4": CALIBRATION_TAXES["F4_red_card"],      # -2.5
}


def _calculate_flags(match_data: dict) -> dict:
    """Evalúa todos los flags del módulo F."""
    ref_avg     = match_data.get("referee_cards_avg", 3.5)
    home_cards  = match_data.get("home_cards_last10", 2.0)
    away_cards  = match_data.get("away_cards_last10", 2.0)
    rivalry     = match_data.get("rivalry_flag", False)
    urgency     = match_data.get("urgency_flag", False)
    ci          = match_data.get("chaos_index", 0)
    exp_goals   = match_data.get("expected_goals_total", 2.5)
    tight_70    = match_data.get("projected_tight_70", False)

    flags = {
        "HighRef":     ref_avg >= 5.0,
        "LowRef":      ref_avg <= 2.5,
        "RivalryFlag": rivalry or urgency,
        "CleanTeam_H": home_cards <= 1.2,
        "CleanTeam_A": away_cards <= 1.2,
        "DirtyTeam_H": home_cards >= 2.8,
        "DirtyTeam_A": away_cards >= 2.8,
        "HT70":        tight_70 and ref_avg >= 3.5 and (home_cards >= 2.8 or away_cards >= 2.8),
        "OpenGame_ON": ci >= 3 or exp_goals >= 3.5,
    }
    return flags


def _kill_switch_check(match_data: dict, flags: dict,
                       direction: str, threshold: float) -> tuple:
    """
    Verifica kill-switches del módulo F.

    Returns:
        (paper_trigger: bool, reason: str)
    """
    if not match_data.get("referee_verified", True):
        return True, "Sin datos árbitro verificados → PAPER"

    if match_data.get("referee_changed_48h", False):
        return True, "Árbitro cambió < 48h → PAPER"

    if flags.get("RivalryFlag") and direction == "under" and threshold <= 3.5:
        return True, "RivalryFlag ON + Under fino <= 3.5 → PAPER"

    # T_esperadas en zona 50/50
    ref_avg   = match_data.get("referee_cards_avg", 3.5)
    home_c    = match_data.get("home_cards_last10", 2.0)
    away_c    = match_data.get("away_cards_last10", 2.0)
    t_expected = calculate_lambda_cards(home_c, away_c, ref_avg)
    if abs(t_expected - threshold) < 0.3:
        return True, f"T_esperadas ({t_expected:.1f}) en zona 50/50 alrededor de {threshold} → PAPER"

    return False, ""


def evaluate_module_f(match_data: dict, markets: dict, h2h: dict) -> list:
    """
    Evalúa el Módulo F — Tarjetas.

    Args:
        match_data: estadísticas del partido
        markets:    dict con mercados devigueados
        h2h:        datos de H2H

    Returns:
        lista de candidatos para el pipeline
    """
    candidates = []
    flags = _calculate_flags(match_data)

    ref_avg    = match_data.get("referee_cards_avg", 3.5)
    home_cards = match_data.get("home_cards_last10", 2.0)
    away_cards = match_data.get("away_cards_last10", 2.0)
    rivalry    = 1.15 if flags["RivalryFlag"] else 1.0

    t_expected = calculate_lambda_cards(home_cards, away_cards, ref_avg, rivalry)

    # ── F1: Total Tarjetas FT ─────────────────────────────
    for market_key in ("total_cards",):
        if market_key not in markets:
            continue

        mkt         = markets[market_key]
        odds_over   = mkt["odds_over"]
        odds_under  = mkt["odds_under"]
        p_over_mkt  = mkt["p_over"]
        p_under_mkt = mkt["p_under"]
        threshold   = mkt.get("threshold", 3.5)

        p_model_over  = poisson_probability(t_expected, threshold, "over")
        p_model_under = poisson_probability(t_expected, threshold, "under")

        for direction in ("over", "under"):
            p_model  = p_model_over if direction == "over" else p_model_under
            p_market = p_over_mkt  if direction == "over" else p_under_mkt
            odds     = odds_over   if direction == "over" else odds_under

            edge_pp  = calculate_edge(p_model, p_market) + TAXES["F1"]
            patches  = []
            paper_tr = False

            kill_ok, kill_reason = _kill_switch_check(match_data, flags, direction, threshold)
            if kill_ok:
                paper_tr = True
                patches.append(kill_reason)

            # Aplicar flags
            if direction == "over":
                if flags["HighRef"]:
                    edge_pp += 2.0
                    patches.append("HighRef: +2.0 pp (árbitro >= 5.0 amarillas/p)")
                if flags["HT70"]:
                    edge_pp += 1.5
                    patches.append("HT70: +1.5 pp (marcador ajustado hasta 70'+)")
                if flags["OpenGame_ON"]:
                    edge_pp -= 2.5
                    patches.append("OpenGame_ON (PATCH v1.2.6): -2.5 pp")
            else:  # under
                if flags["LowRef"]:
                    edge_pp += 2.0
                    patches.append("LowRef: +2.0 pp (árbitro <= 2.5 amarillas/p)")

            candidates.append({
                "module":         "F",
                "sub_market":     "F1",
                "team":           "total",
                "direction":      direction,
                "market":         f"over_cards" if direction == "over" else "under_cards",
                "market_label":   f"Total Tarjetas {direction.capitalize()} {threshold}",
                "threshold":      threshold,
                "odds":           odds,
                "p_implied":      p_market,
                "p_model":        p_model,
                "lambda":         t_expected,
                "edge_pp":        edge_pp,
                "patches_applied":patches,
                "paper_trigger":  paper_tr,
                "current_market": "over_cards" if direction == "over" else "under_cards",
                "projected_tight_70": match_data.get("projected_tight_70", False),
                "ref_cards_avg":  ref_avg,
                "dirty_team_on":  flags["DirtyTeam_H"] or flags["DirtyTeam_A"],
                "expected_goals": match_data.get("expected_goals_total", 2.5),
                "chaos_index":    match_data.get("chaos_index", 0),
            })

    return candidates
