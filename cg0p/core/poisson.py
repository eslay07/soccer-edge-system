# ============================================================
#  CG-0P — core/poisson.py
#  Modelo Poisson para corners, tarjetas y goles
# ============================================================

import math


def poisson_pmf(k: int, lam: float) -> float:
    """
    Función de masa de probabilidad Poisson: P(X = k).

    Args:
        k:   número de eventos
        lam: lambda (expectativa)

    Returns:
        probabilidad P(X = k)
    """
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def poisson_cdf(n: int, lam: float) -> float:
    """
    Función de distribución acumulada Poisson: P(X <= n).

    Args:
        n:   umbral superior
        lam: lambda (expectativa)

    Returns:
        probabilidad P(X <= n)
    """
    if lam <= 0:
        return 1.0
    return sum(poisson_pmf(k, lam) for k in range(n + 1))


def poisson_probability(lambda_param: float, threshold: float,
                        direction: str) -> float:
    """
    Calcula la probabilidad Poisson para Over/Under de corners/goles.

    Args:
        lambda_param: expectativa (lambda) de eventos
        threshold:    línea (ej: 4.5, 3.5)
        direction:    "over" o "under"

    Returns:
        probabilidad entre 0 y 1

    Examples:
        >>> poisson_probability(4.2, 4.5, "under")  # P(X <= 4)
        >>> poisson_probability(4.2, 4.5, "over")   # P(X >= 5)
    """
    if direction == "under":
        return poisson_cdf(int(threshold), lambda_param)
    else:
        return 1.0 - poisson_cdf(int(threshold), lambda_param)


def calculate_lambda(
    team_avg: float,
    opponent_conceded_avg: float,
    league_avg: float = None,
    h2h_avg: float = None,
    recent_form_avg: float = None,
) -> float:
    """
    Calcula lambda (expectativa de corners/goles) para un equipo.

    Pondera múltiples fuentes de datos para obtener una estimación
    más robusta que usar solo el promedio del equipo.

    Args:
        team_avg:              promedio del equipo en la temporada
        opponent_conceded_avg: promedio concedido por el rival
        league_avg:            promedio de la liga (opcional)
        h2h_avg:               promedio H2H (opcional)
        recent_form_avg:       promedio últimos 5 partidos (opcional)

    Returns:
        lambda ponderado
    """
    # Base: combinación equipo + rival
    matchup_lambda = (team_avg + opponent_conceded_avg) / 2.0

    # Pesos según disponibilidad de datos
    w_matchup = 0.40
    w_season  = 0.25
    w_form    = 0.20
    w_h2h     = 0.15

    weighted = matchup_lambda * w_matchup
    weighted += team_avg * w_season

    if recent_form_avg is not None:
        weighted += recent_form_avg * w_form
    else:
        weighted += team_avg * w_form

    if h2h_avg is not None:
        weighted += h2h_avg * w_h2h
    else:
        weighted += matchup_lambda * w_h2h

    return max(weighted, 0.1)  # Lambda mínimo para evitar división por cero


def calculate_lambda_cards(
    home_cards_avg: float,
    away_cards_avg: float,
    referee_cards_avg: float,
    rivalry_factor: float = 1.0,
) -> float:
    """
    Calcula lambda de tarjetas esperadas en el partido.

    Args:
        home_cards_avg:    tarjetas promedio del equipo local
        away_cards_avg:    tarjetas promedio del equipo visitante
        referee_cards_avg: tarjetas promedio del árbitro
        rivalry_factor:    factor de rivalidad (1.0 = normal, > 1.0 = derby)

    Returns:
        tarjetas esperadas totales
    """
    team_expected = home_cards_avg + away_cards_avg
    ref_adjustment = referee_cards_avg / max(team_expected, 0.1)

    # Ponderar: 60% perfil equipos, 40% árbitro
    raw = team_expected * 0.60 + (referee_cards_avg) * 0.40
    return raw * rivalry_factor


def expected_corners_match(
    home_team_avg: float,
    away_team_avg: float,
    home_conceded_avg: float,
    away_conceded_avg: float,
) -> tuple:
    """
    Calcula corners esperados para cada equipo en el partido.

    Args:
        home_team_avg:    corners promedio del equipo local
        away_team_avg:    corners promedio del equipo visitante
        home_conceded_avg: corners concedidos promedio por el local
        away_conceded_avg: corners concedidos promedio por el visitante

    Returns:
        (lambda_home, lambda_away, lambda_total)
    """
    lam_home = (home_team_avg + away_conceded_avg) / 2.0
    lam_away = (away_team_avg + home_conceded_avg) / 2.0
    return lam_home, lam_away, lam_home + lam_away
