# ============================================================
#  CG-0P — core/decision.py
#  Lógica de decisión final: EJECUTAR / PAPER-A / PASS
# ============================================================

from ..config.constants import (
    MIN_EDGE_PP, MIN_ODDS, SMARTMODE_LOW, SMARTMODE_HIGH,
    MIN_EV, MIN_ROBUSTNESS,
    PAPER_A_EDGE_LOW, PAPER_A_EDGE_HIGH, PAPER_A_MIN_ROB,
    PAPER_A_MIN_PROB, PAPER_A_MIN_EV,
    DEFAULT_STAKE, REDUCED_STAKE,
    CI_ULTRA_COLCHON, CI_UNDERS_FINOS,
)


def decide_pick(
    edge_pp: float,
    ev: float,
    robustness: int,
    odds: float,
    p_final: float,
    chaos_index: int,
    market_type: str = "",
    uncertainty: int = 0,
    paper_trigger: bool = False,
) -> dict:
    """
    Decisión final sobre un pick candidato.

    Args:
        edge_pp:       edge neto en pp (después de impuestos y patches)
        ev:            Expected Value
        robustness:    robustez del stress test (0-5)
        odds:          cuota disponible
        p_final:       probabilidad final del sistema
        chaos_index:   índice de caos del partido
        market_type:   tipo de mercado (para kill-switches por CI)
        uncertainty:   nivel de incertidumbre (0-3)
        paper_trigger: True si algún patch forzó PAPER

    Returns:
        {
            "decision":     "EJECUTAR" | "PAPER-A" | "PASS" | "REJECT",
            "stake":        float,
            "reason":       str,
            "conditions":   dict,
        }
    """
    conditions = {
        "edge_pp":       edge_pp,
        "ev":            ev,
        "robustness":    robustness,
        "odds":          odds,
        "p_final":       p_final,
        "chaos_index":   chaos_index,
        "uncertainty":   uncertainty,
        "paper_trigger": paper_trigger,
    }

    # ── Kill-switch: patch forzó PAPER ────────────────────
    if paper_trigger:
        return _result("PAPER-A", 0, "Patch activo forzó PAPER automático", conditions)

    # ── Kill-switch: cuota mínima absoluta ────────────────
    if odds < MIN_ODDS:
        return _result(
            "REJECT", 0,
            f"Cuota {odds:.2f} < mínimo absoluto {MIN_ODDS}",
            conditions,
        )

    # ── Kill-switch: robustez insuficiente ────────────────
    if robustness <= 3:
        return _result(
            "PASS", 0,
            f"Robustez {robustness}/5 insuficiente (mínimo {MIN_ROBUSTNESS})",
            conditions,
        )

    # ── Kill-switch: CI y under fino ──────────────────────
    is_under_fino = "under" in market_type.lower() and any(
        t in market_type.lower() for t in ["3.5", "4.5", "2.5"]
    )
    if chaos_index >= CI_ULTRA_COLCHON:
        if is_under_fino or ("under_4.5" in market_type.lower()):
            return _result(
                "PASS", 0,
                f"CI={chaos_index} >= {CI_ULTRA_COLCHON}: NUNCA Under 4.5 con caos extremo",
                conditions,
            )

    if chaos_index >= CI_UNDERS_FINOS and is_under_fino:
        return _result(
            "PASS", 0,
            f"CI={chaos_index} >= {CI_UNDERS_FINOS}: No unders finos — usar solo colchón alto",
            conditions,
        )

    # ── Cuota fuera de SmartMode Low (< 1.55) ─────────────
    if odds < SMARTMODE_LOW:
        if not (p_final >= 0.77 or (edge_pp >= 9.0 and robustness == 5)):
            return _result(
                "PASS", 0,
                f"Cuota {odds:.2f} < {SMARTMODE_LOW}: Necesita p_final >= 77% o "
                f"(edge >= 9 pp Y rob = 5). "
                f"Actual: p={p_final:.0%}, edge={edge_pp:.1f} pp, rob={robustness}/5",
                conditions,
            )

    # ── Cuota fuera de SmartMode High (> 1.85) ────────────
    if odds > SMARTMODE_HIGH:
        if not (ev >= MIN_EV and robustness == 5):
            return _result(
                "PASS", 0,
                f"Cuota {odds:.2f} > {SMARTMODE_HIGH}: Necesita EV >= {MIN_EV} Y rob = 5. "
                f"Actual: EV={ev:.3f}, rob={robustness}/5",
                conditions,
            )

    # ── EJECUTAR ──────────────────────────────────────────
    if edge_pp >= MIN_EDGE_PP and ev >= MIN_EV and robustness >= MIN_ROBUSTNESS:
        stake = DEFAULT_STAKE if uncertainty <= 1 else REDUCED_STAKE
        return _result(
            "EJECUTAR", stake,
            (
                f"edge={edge_pp:.1f} pp >= {MIN_EDGE_PP} | "
                f"EV={ev:.3f} >= {MIN_EV} | "
                f"rob={robustness}/5 >= {MIN_ROBUSTNESS}"
            ),
            conditions,
        )

    # ── PAPER-A ───────────────────────────────────────────
    if (
        PAPER_A_EDGE_LOW <= edge_pp <= PAPER_A_EDGE_HIGH
        and robustness >= PAPER_A_MIN_ROB
        and p_final >= PAPER_A_MIN_PROB
        and ev >= PAPER_A_MIN_EV
    ):
        return _result(
            "PAPER-A", 0,
            (
                f"edge={edge_pp:.1f} pp (zona PAPER-A) | "
                f"EV={ev:.3f} >= {PAPER_A_MIN_EV} | "
                f"p={p_final:.0%} >= {PAPER_A_MIN_PROB:.0%} | "
                f"rob={robustness}/5"
            ),
            conditions,
        )

    # ── PASS ──────────────────────────────────────────────
    if edge_pp < PAPER_A_EDGE_LOW:
        reason = f"Edge {edge_pp:.1f} pp < {PAPER_A_EDGE_LOW} pp mínimo para PAPER-A"
    elif ev < PAPER_A_MIN_EV:
        reason = f"EV {ev:.3f} < {PAPER_A_MIN_EV} mínimo"
    elif p_final < PAPER_A_MIN_PROB:
        reason = f"Probabilidad {p_final:.0%} < {PAPER_A_MIN_PROB:.0%} mínimo"
    else:
        reason = "No cumple umbrales requeridos"

    return _result("PASS", 0, reason, conditions)


def _result(decision: str, stake: float, reason: str, conditions: dict) -> dict:
    """Construye el diccionario de resultado de decisión."""
    return {
        "decision":   decision,
        "stake":      stake,
        "reason":     reason,
        "conditions": conditions,
    }


def format_decision_output(pick_result: dict) -> str:
    """
    Formatea la decisión para mostrar en consola/GUI.

    Args:
        pick_result: resultado de decide_pick() enriquecido con datos del pick

    Returns:
        string formateado
    """
    d         = pick_result.get("decision", "PASS")
    stake     = pick_result.get("stake", 0)
    reason    = pick_result.get("reason", "")
    cond      = pick_result.get("conditions", {})
    market    = pick_result.get("market_label", "")
    odds      = pick_result.get("odds", 0)
    module_id = pick_result.get("module", "")
    patches   = pick_result.get("patches_applied", [])

    lines = []

    if d == "EJECUTAR":
        lines.append(f"✅ PICK EJECUTAR [{module_id}]")
        lines.append(f"   {market} @{odds:.2f}")
        lines.append(f"   Stake: {stake}u")
        lines.append(
            f"   Edge: {cond.get('edge_pp',0):.1f} pp | "
            f"EV: +{cond.get('ev',0):.3f} | "
            f"Robustez: {cond.get('robustness',0)}/5"
        )
        if patches:
            lines.append(f"   Patches: {' | '.join(patches)}")

    elif d == "PAPER-A":
        lines.append(f"📋 PAPER-A [{module_id}]")
        lines.append(f"   {market} @{odds:.2f}")
        lines.append(f"   {reason}")

    elif d == "REJECT":
        lines.append(f"⛔ REJECT [{module_id}]: {reason}")

    else:  # PASS
        lines.append(f"   PASS — {reason}")

    return "\n".join(lines)
