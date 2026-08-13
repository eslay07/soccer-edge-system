# ============================================================
#  CG-0P — config/constants.py
#  Parámetros globales del sistema v1.2.7
# ============================================================

# === UMBRALES PRINCIPALES ===
MIN_EDGE_PP       = 7.0    # Edge mínimo en pp para EJECUTAR
MIN_ODDS          = 1.40   # Cuota mínima absoluta
SMARTMODE_LOW     = 1.55   # Cuota objetivo inferior
SMARTMODE_HIGH    = 1.85   # Cuota objetivo superior
MIN_EV            = 0.030  # Expected Value mínimo
MIN_ROBUSTNESS    = 4      # Robustez mínima (sobre 5 escenarios)

# === UMBRALES PAPER-A ===
PAPER_A_EDGE_LOW  = 4.0    # Edge mínimo para PAPER-A
PAPER_A_EDGE_HIGH = 6.9    # Edge máximo para PAPER-A
PAPER_A_MIN_ROB   = 4      # Robustez mínima PAPER-A
PAPER_A_MIN_PROB  = 0.65   # Probabilidad mínima PAPER-A
PAPER_A_MIN_EV    = 0.015  # EV mínimo PAPER-A

# === STAKES ===
DEFAULT_STAKE     = 1.0    # Unidad estándar
REDUCED_STAKE     = 0.5    # Cuando Incertidumbre >= 2

# === PROXY MODE ===
PROXY_MODE_PENALTY = -1.0  # Penalización cuando NO se usa Pinnacle

# === CAOS ===
CI_ULTRA_COLCHON  = 4      # CI >= 4 → solo ultra-colchón o PAPER
CI_UNDERS_FINOS   = 3      # CI >= 3 → no unders finos

# === FLAGS DE CAOS ===
CHAOS_FLAG_NAMES = ["EG", "LS", "ABP", "REF_VAR", "OG"]

CHAOS_FLAG_DESCRIPTIONS = {
    "EG":      "Early Goal — prob >= 25% de gol antes del 20'",
    "LS":      "Late Surge — equipos con tendencia a goles tardíos",
    "ABP":     "Set Pieces — equipo con amenaza real de balón parado",
    "REF_VAR": "Árbitro/VAR — árbitro con alto ratio de penales o controversias",
    "OG":      "Open Game — perfil táctico de partido abierto con muchas transiciones",
}

# === IMPUESTOS DE CALIBRACIÓN ===
CALIBRATION_TAXES = {
    "B_team_corners_ft":  -1.0,
    "C_corners_1t_team":  -1.0,
    "D_handicap_corners": -1.5,
    "A_goals_alt_totals": -0.5,
    "F1_total_cards":     -1.5,
    "F2_team_cards":      -1.0,
    "F3_first_card":      -2.0,
    "F4_red_card":        -2.5,
    "G1_btts_si":         -1.5,
    "G1_btts_no":         -2.0,
    "G3_btts_1t":         -3.0,
    "proxy_mode":         -1.0,
    "pcr_anti_chaos":     -2.0,
}

# === ORDEN DE MÓDULOS POR CAOS ===
MODULE_ORDER_LOW_CHAOS  = ["B", "C", "D", "F", "G", "A"]   # CI 0-1
MODULE_ORDER_MID_CHAOS  = ["A", "B", "C", "F", "D", "G"]   # CI 2-3
MODULE_ORDER_HIGH_CHAOS = ["A"]                             # CI 4-5
