# ============================================================
#  CG-0P — config/patterns.py
#  Patrones tácticos identificados (learnings post-match)
# ============================================================

TACTICAL_PATTERNS = {

    "Favorito_Clinico": {
        "description": (
            "Equipo claramente superior que gana eficientemente sin generar "
            "muchos corners. Marca 1-0 y administra. No empuja, no arriesga."
        ),
        "effect_on_system": [
            "Corners FT del favorito clínico son MENORES que su promedio",
            "Cuidado con Over corners del favorito",
            "BTTS No se fortalece",
        ],
        "detection_signals": {
            "xg_over_goals_ratio": "> 1.2",
            "possession":          "> 55%",
            "corners_vs_avg":      "< media de liga",
            "win_rate":            "> 60%",
        },
        "abbreviation": "FC",
    },

    "Posesion_Esteril": {
        "description": (
            "Equipo con mucha posesión pero que no genera situaciones de "
            "peligro real. Pasa el balón lateralmente, no llega a línea "
            "de fondo → no genera corners."
        ),
        "effect_on_system": [
            "Señal FUERTE para Under 1T corners del equipo con PE",
            "H2H con PE histórico → refuerza Under",
        ],
        "detection_signals": {
            "possession":  "> 55%",
            "corners_avg": "< 4.5 por partido",
            "xg":          "< 1.2 a pesar de alta posesión",
        },
        "abbreviation": "PE",
    },

    "Visitor_Comfort_Zone": {
        "description": (
            "Visitante que va 2+ goles arriba al descanso se repliega "
            "completamente en 2H. Su producción de corners en 2H colapsa a ~0. "
            "El local empuja pero sin generar corners excesivos."
        ),
        "effect_on_system": [
            "Under FT del visitante se fortalece enormemente",
            "Separar SIEMPRE análisis 1H vs FT para visitantes",
        ],
        "origin":       "Brentford 0-2 Brighton (Brighton 4 CK en 1H, 0 en 2H)",
        "abbreviation": "VCZ",
    },

    "Form_Trap": {
        "description": (
            "Equipo en mala racha con DT bajo presión que produce su MEJOR "
            "fútbol al inicio del siguiente partido. La desesperación genera "
            "intensidad, no pasividad."
        ),
        "effect_on_system": [
            "NO asumir que mala forma = baja actividad",
            "Equipos con talento + desesperación = VisitorSurge1H",
            "1H Unders extremadamente vulnerables",
        ],
        "origin":       "Brighton racha 3 derrotas → dominaron 1H vs Brentford",
        "abbreviation": "FT",
    },

    "OpenGame_Cards_Trap": {
        "description": (
            "Partidos con alto CI y muchos goles esperados parecen buenos "
            "para Over tarjetas, pero en realidad la fluidez del juego "
            "REDUCE las faltas tácticas."
        ),
        "effect_on_system": [
            "Partidos abiertos → MENOS tarjetas, no más",
            "-2.5 pp a Over tarjetas cuando OpenGame ON",
        ],
        "origin":       "Lens vs Monaco 21/02/2026",
        "abbreviation": "OGC",
    },

    "Mourinho_Playoff_Trap": {
        "description": (
            "En eliminatorias europeas, equipos con DT defensivo/pragmático "
            "juegan ultra-cerrado. Corners totales bajan, tarjetas suben "
            "por faltas tácticas. Los H2H de liga NO son predictivos."
        ),
        "effect_on_system": [
            "Descuento H2H en eliminatorias vs liga",
            "Under corners se fortalece en eliminatorias cerradas",
        ],
        "origin":       "Benfica vs Real Madrid UCL playoff",
        "abbreviation": "MPT",
    },
}
