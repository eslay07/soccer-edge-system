# ============================================================
#  CG-0P — tracking/brier.py
#  Cálculo del Brier Score para calibración post-match
# ============================================================


def brier_score(p_predicted: float, outcome: int) -> float:
    """
    Calcula el Brier Score de una predicción.

    Mide la calidad de la predicción probabilística:
    - Brier < 0.15  → Excelente
    - Brier 0.15-0.25 → Aceptable
    - Brier > 0.25  → Malo, necesita recalibración

    Args:
        p_predicted: probabilidad asignada al resultado (0-1)
        outcome:     1 si el resultado ocurrió, 0 si no

    Returns:
        Brier Score (0 = perfecto, 1 = peor posible)
    """
    p_clamped = max(0.0, min(1.0, p_predicted))
    return (p_clamped - outcome) ** 2


def brier_summary(predictions: list) -> dict:
    """
    Calcula el resumen de Brier Scores para una lista de predicciones.

    Args:
        predictions: lista de dicts con 'p_predicted' y 'outcome'

    Returns:
        dict con estadísticas de calibración
    """
    if not predictions:
        return {"n": 0, "avg_brier": None, "quality": "sin_datos"}

    scores = [
        brier_score(p.get("p_predicted", 0.5), p.get("outcome", 0))
        for p in predictions
    ]

    avg_bs = sum(scores) / len(scores)

    quality = (
        "excelente"  if avg_bs < 0.15  else
        "aceptable"  if avg_bs < 0.25  else
        "RECALIBRAR"
    )

    return {
        "n":           len(scores),
        "avg_brier":   round(avg_bs, 4),
        "min_brier":   round(min(scores), 4),
        "max_brier":   round(max(scores), 4),
        "quality":     quality,
        "scores":      scores,
    }


def interpret_brier(brier: float) -> str:
    """
    Devuelve interpretación textual del Brier Score.

    Args:
        brier: valor del Brier Score

    Returns:
        string descriptivo
    """
    if brier < 0.05:
        return "Excelente — calibración casi perfecta"
    elif brier < 0.10:
        return "Muy buena calibración"
    elif brier < 0.15:
        return "Buena calibración"
    elif brier < 0.20:
        return "Calibración aceptable"
    elif brier < 0.25:
        return "Calibración marginal — monitorear"
    else:
        return "Mala calibración — recalibrar urgente"
