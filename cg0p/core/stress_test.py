# ============================================================
#  CG-0P — core/stress_test.py
#  Stress Test G1-G5: 5 escenarios obligatorios
# ============================================================


def _evaluate_g1_early_goal(pick: dict, match_data: dict) -> tuple:
    """
    G1: Early Goal — Gol antes del minuto 20.
    Bidireccional (PATCH_G1_Simetrico activo).

    Returns (survives: bool, reason: str)
    """
    team_bet  = pick.get("team", "home")
    direction = pick.get("direction", "over")   # "over" o "under"
    market    = pick.get("market", "corners")

    # Probabilidades de gol temprano
    if team_bet == "home":
        team_eg_prob = match_data.get("home_early_goal_prob", 0.0)
        rival_eg_prob = match_data.get("away_early_goal_prob", 0.0)
        team_admin    = match_data.get("home_admin_pattern", False)
    else:
        team_eg_prob = match_data.get("away_early_goal_prob", 0.0)
        rival_eg_prob = match_data.get("home_early_goal_prob", 0.0)
        team_admin    = match_data.get("away_admin_pattern", False)

    # Dirección 1: el equipo apostado marca temprano
    dir1_fail = False
    if team_eg_prob >= 0.25:
        if "corners" in market and direction == "over":
            if team_admin:  # administra → menos corners
                dir1_fail = True

    # Dirección 2: el rival marca temprano
    dir2_fail = False
    if rival_eg_prob >= 0.25:
        if "corners" in market and direction == "under":
            # Equipo apostado en under reacciona empujando → más corners
            dir2_fail = True

    if dir1_fail or dir2_fail:
        reason = []
        if dir1_fail:
            reason.append(f"Equipo apostado marca temprano y administra (EG={team_eg_prob:.0%})")
        if dir2_fail:
            reason.append(f"Rival marca temprano → equipo apostado empuja (EG={rival_eg_prob:.0%})")
        return False, " | ".join(reason)

    return True, f"G1 OK — EG equipo:{team_eg_prob:.0%} rival:{rival_eg_prob:.0%}"


def _evaluate_g2_late_surge(pick: dict, match_data: dict) -> tuple:
    """
    G2: Late Surge — Partido trabado hasta 70'+, equipo necesitado empuja.

    Returns (survives: bool, reason: str)
    """
    direction = pick.get("direction", "over")
    market    = pick.get("market", "corners")

    home_late = match_data.get("home_late_goal_rate", 0.0)
    away_late = match_data.get("away_late_goal_rate", 0.0)
    late_surge_risk = max(home_late, away_late)

    if direction == "under" and "corners" in market and late_surge_risk >= 0.40:
        return (
            False,
            f"Late surge genera spike de corners tardíos (riesgo {late_surge_risk:.0%})",
        )

    if direction == "under" and "cards" in market and late_surge_risk >= 0.35:
        return (
            False,
            f"Late surge genera tarjetas por frustración (riesgo {late_surge_risk:.0%})",
        )

    return True, f"G2 OK — Late surge riesgo: {late_surge_risk:.0%}"


def _evaluate_g3_red_card(pick: dict, match_data: dict) -> tuple:
    """
    G3: Red Card / Mid-match disruption — Expulsión al min 50-60.

    Returns (survives: bool, reason: str)
    """
    direction      = pick.get("direction", "over")
    market         = pick.get("market", "corners")
    team_bet       = pick.get("team", "home")

    ref_red_rate   = match_data.get("referee_reds_avg", 0.0)
    red_card_risk  = ref_red_rate >= 0.15  # >= 1 roja cada 6-7 partidos

    if red_card_risk:
        if "corners" in market and direction == "under":
            # Con 10 jugadores: rival domina → más corners para rival
            # Si apostamos under del equipo con tarjeta, puede sobrevivir
            # Si apostamos under del equipo que domina → peligro
            rival_dominant = match_data.get("rival_likely_dominant", False)
            if rival_dominant and team_bet == "away":
                return (
                    False,
                    f"Tarjeta roja → rival domina corners (árb. {ref_red_rate:.2f} rojas/p)",
                )

        if "cards" in market and direction == "under":
            return (
                False,
                f"Riesgo de tarjeta roja adicional (árb. {ref_red_rate:.2f} rojas/p)",
            )

    return True, f"G3 OK — Red card risk: {'alto' if red_card_risk else 'bajo'}"


def _evaluate_g4_late_penalty(pick: dict, match_data: dict) -> tuple:
    """
    G4: Late Penalty — Penalti después del 75'.

    Returns (survives: bool, reason: str)
    """
    direction       = pick.get("direction", "over")
    market          = pick.get("market", "corners")

    ref_pen_rate    = match_data.get("referee_penalties_avg", 0.0)
    penalty_risk    = ref_pen_rate >= 0.20  # >= 1 penal cada 5 partidos

    if penalty_risk:
        if direction == "under" and "corners" in market:
            # Penal tardío cambia dinámica: equipo atrás empuja → más corners
            return (
                False,
                f"Penal tardío cambia dinámica, corners se disparan (árb. {ref_pen_rate:.2f} pen/p)",
            )

        if direction == "under" and "cards" in market:
            return (
                False,
                f"Penal tardío genera protestas y tarjetas (árb. {ref_pen_rate:.2f} pen/p)",
            )

    return True, f"G4 OK — Penalty risk: {'alto' if penalty_risk else 'bajo'}"


def _evaluate_g5_goal_burst(pick: dict, match_data: dict) -> tuple:
    """
    G5: Goal Burst — 2+ goles en ventana de 10 minutos.

    Returns (survives: bool, reason: str)
    """
    direction      = pick.get("direction", "over")
    market         = pick.get("market", "corners")

    expected_goals = match_data.get("expected_goals_total", 2.0)
    chaos_index    = match_data.get("chaos_index", 0)

    # Goal burst más probable con alto xG y CI elevado
    burst_prob = min(0.10 + (expected_goals - 2.0) * 0.08 + chaos_index * 0.05, 0.60)

    if burst_prob >= 0.30:
        if direction == "under" and "goals" in market:
            return (
                False,
                f"Goal burst con {burst_prob:.0%} prob. — Under goles en riesgo",
            )
        if direction == "under" and "corners" in market and chaos_index >= 3:
            return (
                False,
                f"Goal burst + CI alto ({chaos_index}) → caos total, under corners vulnerable",
            )

    return True, f"G5 OK — Burst prob: {burst_prob:.0%}"


def run_stress_test(pick: dict, match_data: dict) -> dict:
    """
    Ejecuta los 5 escenarios de stress test para un pick candidato.

    Args:
        pick:       dict con info del pick
            {
                "market":    "corners" | "cards" | "goals" | "btts",
                "direction": "over" | "under" | "si" | "no",
                "team":      "home" | "away" | "total",
                "threshold": float,
            }
        match_data: dict con estadísticas del partido

    Returns:
        {
            "robustness":    int (0-5),
            "scenarios":     dict con resultado de cada escenario,
            "survive_count": int,
            "fail_reasons":  list,
        }
    """
    evaluators = {
        "G1": _evaluate_g1_early_goal,
        "G2": _evaluate_g2_late_surge,
        "G3": _evaluate_g3_red_card,
        "G4": _evaluate_g4_late_penalty,
        "G5": _evaluate_g5_goal_burst,
    }

    scenarios     = {}
    fail_reasons  = []
    survive_count = 0

    for scenario_id, evaluator in evaluators.items():
        try:
            survives, reason = evaluator(pick, match_data)
        except Exception as e:
            survives = True  # Si hay error, no penalizar
            reason   = f"Error en evaluación: {e}"

        scenarios[scenario_id] = {
            "survives": survives,
            "reason":   reason,
        }

        if survives:
            survive_count += 1
        else:
            fail_reasons.append(f"{scenario_id}: {reason}")

    return {
        "robustness":    survive_count,
        "scenarios":     scenarios,
        "survive_count": survive_count,
        "fail_reasons":  fail_reasons,
    }
