# ============================================================
#  CG-0P — core/devig.py
#  Eliminación del margen de la casa (devig) y cálculos base
# ============================================================


def devig_2way(odds_over: float, odds_under: float) -> tuple:
    """
    Elimina el margen de la casa de una línea 2-way.

    Args:
        odds_over:  cuota del Over (ej: 1.80)
        odds_under: cuota del Under (ej: 2.10)

    Returns:
        (p_over_real, p_under_real): probabilidades reales sin vig

    Raises:
        ValueError: si alguna cuota es <= 1.0
    """
    if odds_over <= 1.0 or odds_under <= 1.0:
        raise ValueError(
            f"Cuotas inválidas: over={odds_over}, under={odds_under}. "
            "Deben ser > 1.0"
        )

    p_over_implied  = 1.0 / odds_over
    p_under_implied = 1.0 / odds_under
    total           = p_over_implied + p_under_implied  # > 1.0 por el margen

    p_over_real  = p_over_implied  / total
    p_under_real = p_under_implied / total

    vig_pct = (total - 1.0) * 100
    return p_over_real, p_under_real, vig_pct


def calculate_edge(p_model: float, p_implied: float) -> float:
    """
    Calcula el edge en puntos porcentuales (pp).

    Edge positivo → sistema cree que hay más probabilidad real
    que la que ofrece el mercado.

    Args:
        p_model:   probabilidad estimada por el sistema (0-1)
        p_implied: probabilidad implícita de la cuota tras devig (0-1)

    Returns:
        edge en puntos porcentuales (ej: 8.5 → 8.5 pp de ventaja)
    """
    return (p_model - p_implied) * 100.0


def calculate_ev(p_model: float, odds: float) -> float:
    """
    Calcula el Expected Value (EV) de una apuesta.

    EV > 0 → apuesta tiene valor positivo a largo plazo.
    EV = 0.030 → por cada unidad apostada se esperan 0.03u de ganancia.

    Args:
        p_model: probabilidad estimada por el sistema (0-1)
        odds:    cuota decimal disponible

    Returns:
        EV (positivo = valor positivo)
    """
    return (p_model * odds) - 1.0


def vig_percentage(odds_over: float, odds_under: float) -> float:
    """
    Calcula el porcentaje de margen (vig) de la línea.

    Args:
        odds_over:  cuota del Over
        odds_under: cuota del Under

    Returns:
        vig como porcentaje (ej: 4.5 → 4.5% de margen)
    """
    if odds_over <= 1.0 or odds_under <= 1.0:
        return 0.0
    p_over  = 1.0 / odds_over
    p_under = 1.0 / odds_under
    return (p_over + p_under - 1.0) * 100.0


def validate_line(odds_over: float, odds_under: float) -> bool:
    """
    Verifica que una línea 2-way es válida para análisis.

    Returns:
        True si ambas cuotas son > 1.0 y el vig es < 10%
    """
    if odds_over <= 1.0 or odds_under <= 1.0:
        return False
    v = vig_percentage(odds_over, odds_under)
    return v < 10.0
