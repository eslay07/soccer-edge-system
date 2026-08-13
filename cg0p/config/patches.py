# ============================================================
#  CG-0P — config/patches.py
#  Registro de todos los patches activos del sistema
#  Principio: los patches NUNCA se eliminan, se acumulan.
# ============================================================

PATCHES = {

    # ── PATCHPACK FUNDACIONAL ──────────────────────────────
    "PatchPack_2026-01-12_to_22": {
        "version":     "fundacional",
        "description": "Conjunto inicial de calibraciones del sistema",
        "includes": [
            "PatchPack 2026-01-12",
            "PatchPack 2026-01-13",
            "PatchPack 2026-01-14",
            "PatchPack 2026-01-17(v2)",
            "PatchPack 2026-01-22",
        ],
        "effect":          "Calibraciones base de todos los módulos",
        "module_affected": "ALL",
    },

    "Integration_2026-01-22": {
        "version":         "fundacional",
        "description":     "Integración de módulos 1T + Handicap Corners",
        "effect":          "Activación de módulos C y D con sus impuestos",
        "module_affected": "C, D",
    },

    # ── PATCH 2026-02-20: FC Bidireccional ────────────────
    "PATCH_FC_Bidireccional": {
        "version":         "2026-02-20",
        "origin_match":    "Brest vs Marseille 20/02/2026",
        "origin_result":   "MISS — Brest anotó temprano y administró",
        "module_affected": "B",
        "rule": (
            "FC (Favorito Clínico) aplica también al equipo local underdog. "
            "Si local marca <= 30' y su perfil muestra <= 4 corners cuando "
            "gana cómodamente → FC Home ON → PAPER en Team Over CK. "
            "Antes: FC solo aplicaba al favorito claro. "
            "Ahora: FC aplica a CUALQUIER equipo que marque y administre."
        ),
        "condition":       "goal_before_30_prob >= 0.30 AND corners_when_winning <= 4.0",
        "action":          "PAPER",
    },

    # ── PATCH 2026-02-20: G1 Simétrico ────────────────────
    "PATCH_G1_Simetrico": {
        "version":         "2026-02-20",
        "origin_match":    "Brest vs Marseille 20/02/2026",
        "module_affected": "Stress Test G1",
        "rule": (
            "Evaluar G1 (Early Goal) en AMBAS direcciones: "
            "Dir1: Si equipo apostado marca < 15' y administraría → G1 = FAIL. "
            "Dir2: Si rival marca < 15' y equipo apostado reacciona → G1 = PASS. "
            "Si cualquier dirección = FAIL, el escenario no sobrevive."
        ),
        "bidirectional":   True,
    },

    # ── PATCH 2026-02-20: EG Home Penalización ────────────
    "PATCH_EG_Home_Penalizacion": {
        "version":         "2026-02-20",
        "origin_match":    "Brest vs Marseille 20/02/2026",
        "module_affected": "B",
        "rule": (
            "Si probabilidad >= 25% de que el equipo apostado anote antes "
            "del minuto 20 → -4 pp adicionales al edge calculado. "
            "Lógica: equipo que anota temprano cambia su comportamiento táctico "
            "(administra), reduciendo generación de corners."
        ),
        "condition":    "team_early_goal_prob >= 0.25",
        "penalty_pp":   -4.0,
        "target":       "team_corners_over",
    },

    # ── PATCH v1.2.4: P-G1-1T ─────────────────────────────
    "PATCH_v1.2.4_P-G1-1T": {
        "version":         "v1.2.4",
        "module_affected": "C",
        "rule": (
            "Si probabilidad >= 30% de gol antes del minuto 35 de CUALQUIER equipo "
            "→ Under 1T CK del equipo que quedaría PERDIENDO = PAPER automático. "
            "Lógica: equipo que va perdiendo en 1T tiende a empujar, "
            "generando más corners de los esperados."
        ),
        "condition":    "early_goal_any_team_prob >= 0.30",
        "bet_role":     "likely_losing",
        "action":       "PAPER",
    },

    # ── PATCH v1.2.5: P-HT70-F ────────────────────────────
    "PATCH_v1.2.5_P-HT70-F": {
        "version":         "v1.2.5",
        "module_affected": "F",
        "rule": (
            "Si el partido proyecta marcador ajustado hasta el minuto 70+ "
            "→ +1.5 pp al p_model en Over tarjetas. "
            "Condiciones: árbitro avg >= 3.5 amarillas/partido + DirtyTeam ON. "
            "Lógica: partidos cerrados generan frustración y faltas tácticas al final."
        ),
        "condition":   "projected_tight_70 AND ref_cards_avg >= 3.5 AND dirty_team_on",
        "bonus_pp":    +1.5,
        "target":      "over_cards",
    },

    # ── PATCH v1.2.6: P-OPENCARD-F ────────────────────────
    "PATCH_v1.2.6_P-OPENCARD-F": {
        "version":         "v1.2.6",
        "origin_match":    "Lens vs Monaco 21/02/2026",
        "origin_result":   "MISS — Total Tarjetas O3.5 @1.66",
        "module_affected": "F",
        "rule": (
            "Si OpenGame ON (CI >= 3 o proyección >= 3.5 goles esperados) "
            "→ -2.5 pp adicionales a p_model en Over tarjetas. "
            "Lógica: en partidos abiertos los equipos atacan fluidamente y hay "
            "MENOS faltas tácticas. Los partidos de ida y vuelta producen goles "
            "pero no necesariamente tarjetas."
        ),
        "condition":    "chaos_index >= 3 OR expected_goals >= 3.5",
        "penalty_pp":   -2.5,
        "target":       "over_cards",
    },

    # ── PATCH v1.2.7: P-VSURGE1H-C ───────────────────────
    "PATCH_v1.2.7_P-VSURGE1H-C": {
        "version":         "v1.2.7",
        "origin_match":    "Brentford vs Brighton 21/02/2026",
        "origin_result":   "MISS — 1H Under 4.5 CK @1.95 (real: 7 corners en 1H)",
        "module_affected": "C",
        "rule": (
            "Cuando se evalúa 1H Under Corners y el VISITANTE cumple 2+ de: "
            "(1) Racha perdedora >= 3 partidos, "
            "(2) DT bajo presión pública, "
            "(3) Calidad plantilla top 50%, "
            "(4) H2H competitivo en ese campo. "
            "→ Activar VisitorSurge1H: -4 pp al edge del Under 1H. "
            "Si edge < 7.0 después → PAPER automático. "
            "IMPORTANTE: NO aplica al Under FT del visitante."
        ),
        "conditions": [
            "visitor_losing_streak >= 3",
            "visitor_manager_under_pressure",
            "visitor_squad_quality_percentile >= 50",
            "h2h_competitive",
        ],
        "min_conditions_met": 2,
        "penalty_pp":          -4.0,
        "target":              "1h_corners_under",
        "exception":           "Under FT del visitante NO afectado",
    },
}


def apply_all_patches(edge_pp: float, module_id: str, context: dict) -> tuple:
    """
    Aplica todos los patches activos para el módulo indicado.

    Args:
        edge_pp:   edge inicial en pp
        module_id: identificador del módulo ("B", "C", "F", etc.)
        context:   dict con todas las variables del partido

    Returns:
        (edge_pp_ajustado, patches_aplicados: list, paper_trigger: bool)
    """
    patches_aplicados = []
    paper_trigger = False

    for patch_id, patch in PATCHES.items():
        if module_id not in str(patch.get("module_affected", "")):
            continue

        # ── Patch FC Bidireccional ────────────────────────
        if patch_id == "PATCH_FC_Bidireccional":
            goal_prob = context.get("goal_before_30_prob", 0.0)
            corners_win = context.get("corners_when_winning", 999)
            if goal_prob >= 0.30 and corners_win <= 4.0:
                paper_trigger = True
                patches_aplicados.append(f"{patch_id} → PAPER (FC Bidireccional)")

        # ── Patch EG Home Penalización ────────────────────
        elif patch_id == "PATCH_EG_Home_Penalizacion":
            eg_prob = context.get("team_early_goal_prob", 0.0)
            if eg_prob >= 0.25:
                edge_pp += patch["penalty_pp"]
                patches_aplicados.append(
                    f"{patch_id} → {patch['penalty_pp']:+.1f} pp (EG Home)"
                )

        # ── Patch P-G1-1T ─────────────────────────────────
        elif patch_id == "PATCH_v1.2.4_P-G1-1T":
            eg_any = context.get("early_goal_any_team_prob", 0.0)
            role   = context.get("bet_team_role", "neutral")
            if eg_any >= 0.30 and role == "likely_losing":
                paper_trigger = True
                patches_aplicados.append(f"{patch_id} → PAPER (P-G1-1T)")

        # ── Patch P-HT70-F ────────────────────────────────
        elif patch_id == "PATCH_v1.2.5_P-HT70-F":
            tight_70   = context.get("projected_tight_70", False)
            ref_avg    = context.get("ref_cards_avg", 0.0)
            dirty      = context.get("dirty_team_on", False)
            market     = context.get("current_market", "")
            if tight_70 and ref_avg >= 3.5 and dirty and "over_cards" in market:
                edge_pp += patch["bonus_pp"]
                patches_aplicados.append(
                    f"{patch_id} → +{patch['bonus_pp']:.1f} pp (HT70)"
                )

        # ── Patch P-OPENCARD-F ────────────────────────────
        elif patch_id == "PATCH_v1.2.6_P-OPENCARD-F":
            ci      = context.get("chaos_index", 0)
            exp_gls = context.get("expected_goals", 0.0)
            market  = context.get("current_market", "")
            if (ci >= 3 or exp_gls >= 3.5) and "over_cards" in market:
                edge_pp += patch["penalty_pp"]
                patches_aplicados.append(
                    f"{patch_id} → {patch['penalty_pp']:+.1f} pp (OpenCard)"
                )

        # ── Patch P-VSURGE1H-C ────────────────────────────
        elif patch_id == "PATCH_v1.2.7_P-VSURGE1H-C":
            if module_id != "C":
                continue
            market = context.get("current_market", "")
            if "1h_corners_under" not in market:
                continue
            conditions_met = sum([
                context.get("visitor_losing_streak", 0) >= 3,
                context.get("visitor_manager_under_pressure", False),
                context.get("visitor_squad_quality_percentile", 0) >= 50,
                context.get("h2h_competitive", False),
            ])
            if conditions_met >= 2:
                edge_pp += patch["penalty_pp"]
                patches_aplicados.append(
                    f"{patch_id} → {patch['penalty_pp']:+.1f} pp (VisitorSurge1H, {conditions_met}/4 cond.)"
                )
                if edge_pp < 7.0:
                    paper_trigger = True
                    patches_aplicados.append(f"{patch_id} → PAPER (edge insuficiente post-penalización)")

    return edge_pp, patches_aplicados, paper_trigger
