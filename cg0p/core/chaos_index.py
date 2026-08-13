# ============================================================
#  CG-0P — core/chaos_index.py
#  Cálculo del ChaosIndex (CI) — Índice de Volatilidad del Partido
# ============================================================

from ..config.constants import CHAOS_FLAG_NAMES, CHAOS_FLAG_DESCRIPTIONS


def calculate_chaos_index(match_data: dict) -> tuple:
    """
    Calcula el ChaosIndex del partido (0-5).

    Cada flag activo suma 1 punto al CI.
    El CI determina qué módulos se priorizan y qué kill-switches se activan.

    Args:
        match_data: dict con estadísticas del partido

    Returns:
        (chaos_index: int, active_flags: list, flag_reasons: dict)
    """
    active_flags  = []
    flag_reasons  = {}

    # ── EG: Early Goal ────────────────────────────────────
    # Prob >= 25% de gol antes del minuto 20 (de cualquier equipo)
    eg_home = match_data.get("home_early_goal_prob", 0.0)
    eg_away = match_data.get("away_early_goal_prob", 0.0)
    eg_max  = max(eg_home, eg_away)
    if eg_max >= 0.25:
        active_flags.append("EG")
        flag_reasons["EG"] = (
            f"Prob. gol < 20': {eg_max:.0%} "
            f"(local {eg_home:.0%}, visitante {eg_away:.0%})"
        )

    # ── LS: Late Surge ────────────────────────────────────
    # Equipos con tendencia a goles en los últimos 20 minutos
    home_late_goals = match_data.get("home_late_goal_rate", 0.0)
    away_late_goals = match_data.get("away_late_goal_rate", 0.0)
    if home_late_goals >= 0.35 or away_late_goals >= 0.35:
        active_flags.append("LS")
        flag_reasons["LS"] = (
            f"Tendencia goles tardíos: local {home_late_goals:.0%}, "
            f"visitante {away_late_goals:.0%}"
        )

    # ── ABP: Set Pieces ───────────────────────────────────
    # Al menos un equipo con amenaza real de balón parado
    home_sp_threat = match_data.get("home_set_piece_threat", False)
    away_sp_threat = match_data.get("away_set_piece_threat", False)
    if home_sp_threat or away_sp_threat:
        active_flags.append("ABP")
        teams = []
        if home_sp_threat:
            teams.append("local")
        if away_sp_threat:
            teams.append("visitante")
        flag_reasons["ABP"] = f"Amenaza balón parado: {', '.join(teams)}"

    # ── REF_VAR: Árbitro/VAR ──────────────────────────────
    # Árbitro con alto ratio de penales o controversias
    ref_penalty_rate = match_data.get("referee_penalties_avg", 0.0)
    ref_red_rate     = match_data.get("referee_reds_avg", 0.0)
    if ref_penalty_rate >= 0.25 or ref_red_rate >= 0.20:
        active_flags.append("REF_VAR")
        flag_reasons["REF_VAR"] = (
            f"Árbitro volátil: {ref_penalty_rate:.2f} pen/partido, "
            f"{ref_red_rate:.2f} rojas/partido"
        )

    # ── OG: Open Game ─────────────────────────────────────
    # Perfil táctico de partido abierto con muchas transiciones
    expected_goals   = match_data.get("expected_goals_total", 0.0)
    home_open_style  = match_data.get("home_open_game_style", False)
    away_open_style  = match_data.get("away_open_game_style", False)
    if expected_goals >= 3.0 or (home_open_style and away_open_style):
        active_flags.append("OG")
        flag_reasons["OG"] = (
            f"Partido abierto: {expected_goals:.1f} goles esperados, "
            f"estilos: local={'abierto' if home_open_style else 'cerrado'}, "
            f"visitante={'abierto' if away_open_style else 'cerrado'}"
        )

    chaos_index = len(active_flags)
    return chaos_index, active_flags, flag_reasons


def get_module_order(chaos_index: int) -> list:
    """
    Determina el orden de evaluación de módulos según el CI.

    Args:
        chaos_index: valor del CI (0-5)

    Returns:
        lista de IDs de módulos en orden de prioridad
    """
    if chaos_index <= 1:
        return ["B", "C", "D", "F", "G", "A"]
    elif chaos_index <= 3:
        return ["A", "B", "C", "F", "D", "G"]
    else:
        return ["A"]  # CI 4-5: solo ultra-colchón


def chaos_index_label(ci: int) -> str:
    """Devuelve etiqueta descriptiva del nivel de caos."""
    labels = {
        0: "Muy bajo",
        1: "Bajo",
        2: "Moderado",
        3: "Alto",
        4: "Muy alto",
        5: "Extremo",
    }
    return labels.get(ci, "Desconocido")
