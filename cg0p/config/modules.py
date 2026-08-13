# ============================================================
#  CG-0P — config/modules.py
#  Definición completa de los 6 módulos activos
# ============================================================

MODULES_CONFIG = {

    # ----------------------------------------------------------
    # MÓDULO B — Team Corners FT (Prioridad 1)
    # ----------------------------------------------------------
    "B": {
        "name":          "Team Corners FT",
        "priority":      1,
        "tax_base_pp":   -1.0,
        "status":        "active",
        "markets":       ["team_corners_over", "team_corners_under"],
        "devig_required": True,
        "two_key_rule":   True,          # Necesita 2+ indicadores convergentes
        "flags": {
            "EG_Home": {
                "condition":  "goal_before_20_prob >= 0.25",
                "penalty_pp": -4.0,
                "target":     "team_corners_over",
            },
            "FC_Home": {
                "condition": "fc_bidireccional_on",
                "action":    "PAPER",
                "note":      "Favorito Clínico: equipo que marca y administra",
            },
        },
        "kill_switches": [
            "FC_Home ON → PAPER automático",
            "Sin devig verificado → PAPER",
            "Menos de 2 indicadores convergentes → PAPER",
        ],
        "data_required": [
            "season_corners_avg", "home_away_corners_avg",
            "corners_conceded_avg", "last_5_corners_avg",
            "last_5_corners_conceded_avg", "h2h_corners",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO C — Corners 1T Team (Prioridad 2)
    # ----------------------------------------------------------
    "C": {
        "name":          "Corners 1T Team",
        "priority":      2,
        "tax_base_pp":   -1.0,
        "status":        "active",
        "markets":       ["1h_corners_over", "1h_corners_under"],
        "devig_required": True,
        "needs_numerical_key": True,
        "flags": {
            "PE": {
                "condition": "posesion_esteril_on",
                "action":    "PAPER_or_degrade",
            },
            "EG_High": {
                "condition":  "goal_before_15_prob >= 0.30",
                "penalty_pp": -1.0,
            },
            "VisitorSurge1H": {
                "condition": "visitor_surge_conditions >= 2",
                "penalty_pp": -4.0,
                "target":    "1h_corners_under",
                "note":      "NO aplica al Under FT del visitante",
            },
        },
        "patches": ["PATCH_v1.2.4_P-G1-1T", "PATCH_v1.2.7_P-VSURGE1H-C"],
        "kill_switches": [
            "P-G1-1T: gol antes del 35' de cualquier equipo → Under 1T del perdedor = PAPER",
            "PE ON → degradar o PAPER",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO F — Tarjetas (Prioridad 3)
    # ----------------------------------------------------------
    "F": {
        "name":     "Tarjetas",
        "priority": 3,
        "status":   "active",
        "sub_markets": {
            "F1": {"name": "Total tarjetas Over/Under FT",    "tax_pp": -1.5},
            "F2": {"name": "Tarjetas por equipo Over/Under",   "tax_pp": -1.0},
            "F3": {"name": "Primera tarjeta (equipo)",         "tax_pp": -2.0, "min_odds": 1.55},
            "F4": {
                "name":      "Tarjeta roja Sí/No",
                "tax_pp":    -2.5,
                "min_odds":  1.65,
                "condition": "solo si árbitro >= 0.35 rojas/partido",
            },
        },
        "flags": {
            "HighRef":     {"condition": "ref_cards_avg >= 5.0",  "effect": "+2 pp Over tarjetas"},
            "LowRef":      {"condition": "ref_cards_avg <= 2.5",  "effect": "+2 pp Under tarjetas"},
            "RivalryFlag": {"condition": "rivalry or urgency",    "effect": "+0.5 T_esperadas / cap 0.5u Unders"},
            "CleanTeam":   {"condition": "team_cards_avg <= 1.2", "effect": "-0.3 T_esperadas"},
            "DirtyTeam":   {"condition": "team_cards_avg >= 2.8", "effect": "+0.4 T_esperadas"},
            "HT70":        {
                "condition":      "marcador_ajustado_hasta_70",
                "effect":         "+1.5 pp Over tarjetas",
                "extra_condition": "ref_cards_avg >= 3.5 AND DirtyTeam ON",
            },
            "OpenGame_ON": {
                "condition":  "chaos_index >= 3 or expected_goals >= 3.5",
                "penalty_pp": -2.5,
                "target":     "over_cards",
                "patch":      "PATCH_v1.2.6_P-OPENCARD-F",
            },
        },
        "kill_switches": [
            "Árbitro cambia < 48h antes → PAPER",
            "RivalryFlag ON + Under fino <= 3.5 → PAPER",
            "Sin datos árbitro verificados → PAPER",
            "T_esperadas en zona 50/50 → PAPER",
        ],
        "data_required": [
            "referee_cards_avg", "referee_reds_avg",
            "referee_fouls_avg", "referee_penalties_avg",
            "home_cards_last_10", "away_cards_last_10",
            "h2h_cards",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO D — Hándicap Corners (Prioridad 4)
    # ----------------------------------------------------------
    "D": {
        "name":          "Hándicap Corners",
        "priority":      4,
        "tax_base_pp":   -1.5,
        "status":        "active",
        "markets":       ["corner_handicap"],
        "devig_required": True,
        "rules": [
            "Solo con dominancia unilateral clara",
            "SpikeRisk no alto bilateral",
            "FC=ON → PAPER",
            "Ref/VAR alto → -1 pp + cap 0.5u",
            "Devig 2-way obligatorio",
        ],
        "kill_switches": [
            "FC ON → PAPER",
            "Dominancia no unilateral clara → PAPER",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO G — BTTS (Prioridad 5)
    # ----------------------------------------------------------
    "G": {
        "name":     "BTTS (Both Teams To Score)",
        "priority": 5,
        "status":   "active",
        "sub_markets": {
            "G1": {"name": "BTTS Sí/No FT", "tax_si": -1.5, "tax_no": -2.0},
            "G3": {"name": "BTTS 1T",       "tax": -3.0, "note": "casi siempre PAPER"},
        },
        "thresholds": {
            "btts_si": 0.65,
            "btts_no": 0.70,
        },
        "flags": {
            "xGDominance":    {"condition": "xg_home >= 1.50 AND xg_away >= 1.20", "bonus_pp": +3.0},
            "CleanSheetRisk": {"condition": "clean_sheet_pct >= 0.45",             "penalty_pp": -3.0},
            "LowBlock":       {"condition": "lowblock_confirmed",                   "penalty_pp": -2.0},
            "NoMotivation":   {"condition": "team_no_motivation",                   "penalty_xg": -2.0},
        },
        "kill_switches": [
            "Sin xG verificado ambos equipos → PAPER",
            "H2H últimos 3: BTTS <= 1 vez Y pick es BTTS Sí → -4 pp",
            "CleanSheetRisk ON en ambos → PAPER",
            "NUNCA inferir BTTS desde corners ni tarjetas",
        ],
        "data_required": [
            "xg_home", "xg_away", "xga_home", "xga_away",
            "btts_pct_last_10_home", "btts_pct_last_10_away",
            "clean_sheet_pct_home", "clean_sheet_pct_away",
            "h2h_btts",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO A — Goles Alt Totals (Prioridad 6, Limitado)
    # ----------------------------------------------------------
    "A": {
        "name":          "Goles Alt Totals",
        "priority":      6,
        "tax_base_pp":   -0.5,
        "status":        "active",
        "restriction":   "Solo elegible U5.5+ con CI <= 2",
        "markets":       ["goals_alt_under"],
        "ladder":        ["U6.5", "U5.5", "U4.5", "U3.5"],
        "min_prob_under": 0.72,
        "rules": [
            "Escalera: U6.5 → U5.5 → U4.5 → U3.5",
            "p_final mínimo Unders: >= 72%",
            "CI >= 4: NUNCA Under 4.5 goles",
            "CI >= 3: no unders finos, solo colchón alto (U5.5+)",
        ],
        "kill_switches": [
            "CI >= 4 → NUNCA Under 4.5",
            "CI >= 3 → solo U5.5 o más",
        ],
    },

    # ----------------------------------------------------------
    # MÓDULO E — ELIMINADO
    # ----------------------------------------------------------
    "E": {
        "name":   "Total Corners FT",
        "status": "ELIMINADO",
        "reason": "Mercado demasiado eficiente, edge insuficiente consistentemente",
    },
}
