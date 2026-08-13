# ============================================================
#  CG-0P — core/pipeline.py
#  Pipeline de 7 pasos obligatorio para evaluar un partido
# ============================================================

from ..config.patches import apply_all_patches
from ..config.constants import PROXY_MODE_PENALTY, MODULE_ORDER_LOW_CHAOS
from .devig import devig_2way, calculate_edge, calculate_ev, validate_line
from .chaos_index import calculate_chaos_index, get_module_order
from .stress_test import run_stress_test
from .decision import decide_pick, format_decision_output
from ..modules.module_b import evaluate_module_b
from ..modules.module_c import evaluate_module_c
from ..modules.module_d import evaluate_module_d
from ..modules.module_f import evaluate_module_f
from ..modules.module_g import evaluate_module_g
from ..modules.module_a import evaluate_module_a


MODULE_EVALUATORS = {
    "B": evaluate_module_b,
    "C": evaluate_module_c,
    "D": evaluate_module_d,
    "F": evaluate_module_f,
    "G": evaluate_module_g,
    "A": evaluate_module_a,
}


def run_pipeline(match_data: dict, odds_data: dict,
                 proxy_mode: bool = False) -> dict:
    """
    Pipeline completo de evaluación de un partido (7 pasos).

    Args:
        match_data: dict con estadísticas del partido (Sección 16 del spec)
        odds_data:  dict con mercados y cuotas disponibles
        proxy_mode: True si se usan cuotas no-Pinnacle (penalización -1 pp)

    Returns:
        {
            "match":       str,
            "chaos_index": int,
            "flags":       list,
            "picks":       list de resultados de decide_pick(),
            "paper_a":     list,
            "summary":     str,
        }
    """
    result = {
        "match":       f"{match_data.get('home_team','Local')} vs {match_data.get('away_team','Visitante')}",
        "date":        match_data.get("date", ""),
        "league":      match_data.get("league", ""),
        "chaos_index": 0,
        "flags":       [],
        "flag_reasons":{},
        "picks":       [],
        "paper_a":     [],
        "passes":      [],
        "summary":     "",
        "pipeline_log":[],
    }

    log = result["pipeline_log"]

    # ── PASO 1: Contexto del partido ──────────────────────
    log.append("PASO 1: Contexto del partido")
    context_ok = all([
        match_data.get("home_team"),
        match_data.get("away_team"),
        match_data.get("league"),
    ])
    if not context_ok:
        result["summary"] = "ERROR: Datos de contexto incompletos"
        return result

    # ── PASO 2: Alineaciones probables + confianza ────────
    log.append("PASO 2: Alineaciones y confianza")
    lineup_confidence = match_data.get("lineup_confidence", 3)
    match_data["lineup_confidence"] = lineup_confidence
    log.append(f"  Confianza alineaciones: {lineup_confidence}/5")

    # ── PASO 3: Flags + ChaosIndex ────────────────────────
    log.append("PASO 3: ChaosIndex y Flags")
    ci, active_flags, flag_reasons = calculate_chaos_index(match_data)
    result["chaos_index"]  = ci
    result["flags"]        = active_flags
    result["flag_reasons"] = flag_reasons
    match_data["chaos_index"]  = ci
    match_data["active_flags"] = active_flags
    log.append(f"  CI={ci} | Flags: {active_flags}")

    # ── PASO 4: Datos recientes (últimos 5-10) ────────────
    log.append("PASO 4: Datos recientes")
    recent_ok = _validate_recent_data(match_data)
    if not recent_ok:
        log.append("  AVISO: Datos recientes incompletos — confianza reducida")
        match_data["lineup_confidence"] = min(lineup_confidence, 2)

    # ── PASO 5: Head-to-Head ──────────────────────────────
    log.append("PASO 5: Head-to-Head")
    h2h = match_data.get("h2h", {})
    h2h_count = len(h2h.get("results", []))
    log.append(f"  H2H disponibles: {h2h_count} partidos")

    # ── PASO 6: Lectura de mercado + Devig ────────────────
    log.append("PASO 6: Lectura de mercado y Devig")
    markets_devigued = {}
    for market_key, market_odds in odds_data.items():
        over_key  = market_key + "_over"
        under_key = market_key + "_under"
        odds_over  = market_odds.get("over", 0)
        odds_under = market_odds.get("under", 0)

        if not validate_line(odds_over, odds_under):
            log.append(f"  {market_key}: línea inválida ({odds_over}/{odds_under}) → SKIP")
            continue

        try:
            p_over, p_under, vig = devig_2way(odds_over, odds_under)
            markets_devigued[market_key] = {
                "odds_over":  odds_over,
                "odds_under": odds_under,
                "p_over":     p_over,
                "p_under":    p_under,
                "vig_pct":    vig,
            }
            log.append(
                f"  {market_key}: O{odds_over}/U{odds_under} → "
                f"p_over={p_over:.1%}, p_under={p_under:.1%}, vig={vig:.1f}%"
            )
        except ValueError as e:
            log.append(f"  {market_key}: Error devig — {e}")

    if not markets_devigued:
        result["summary"] = "Sin mercados válidos para analizar"
        return result

    # ── PASO 7: Evaluación por módulo + Stress test ───────
    log.append("PASO 7: Evaluación por módulo")
    module_order = get_module_order(ci)
    log.append(f"  Orden de módulos (CI={ci}): {module_order}")

    for module_id in module_order:
        evaluator = MODULE_EVALUATORS.get(module_id)
        if not evaluator:
            continue

        log.append(f"\n  --- MÓDULO {module_id} ---")
        try:
            module_picks = evaluator(match_data, markets_devigued, h2h)
        except Exception as e:
            log.append(f"  ERROR en módulo {module_id}: {e}")
            continue

        for pick_candidate in module_picks:
            log.append(f"    Candidato: {pick_candidate.get('market_label','')}")

            # Aplicar ProxyMode
            edge_pp = pick_candidate.get("edge_pp", 0.0)
            if proxy_mode:
                edge_pp += PROXY_MODE_PENALTY
                pick_candidate["patches_applied"] = pick_candidate.get("patches_applied", [])
                pick_candidate["patches_applied"].append(
                    f"ProxyMode: {PROXY_MODE_PENALTY:+.1f} pp"
                )

            # Aplicar todos los patches
            context_for_patches = {**match_data, **pick_candidate}
            edge_pp, patches_applied, paper_trigger = apply_all_patches(
                edge_pp, module_id, context_for_patches
            )
            pick_candidate["edge_pp"] = edge_pp
            pick_candidate["patches_applied"] = (
                pick_candidate.get("patches_applied", []) + patches_applied
            )
            if paper_trigger:
                pick_candidate["paper_trigger"] = True

            # Stress test G1-G5
            stress_result = run_stress_test(pick_candidate, match_data)
            pick_candidate["stress_test"] = stress_result
            robustness = stress_result["robustness"]
            log.append(
                f"    Robustez: {robustness}/5 "
                f"({stress_result['survive_count']} escenarios superados)"
            )

            # Decisión final
            ev = calculate_ev(
                pick_candidate.get("p_model", 0.0),
                pick_candidate.get("odds", 1.0),
            )
            pick_candidate["ev"] = ev

            decision = decide_pick(
                edge_pp=edge_pp,
                ev=ev,
                robustness=robustness,
                odds=pick_candidate.get("odds", 1.0),
                p_final=pick_candidate.get("p_model", 0.0),
                chaos_index=ci,
                market_type=pick_candidate.get("market", ""),
                uncertainty=pick_candidate.get("uncertainty", 0),
                paper_trigger=pick_candidate.get("paper_trigger", False),
            )
            pick_candidate.update(decision)
            pick_candidate["module"] = module_id

            log.append(f"    Decisión: {decision['decision']}")

            # Clasificar resultado
            if decision["decision"] == "EJECUTAR":
                result["picks"].append(pick_candidate)
            elif decision["decision"] == "PAPER-A":
                result["paper_a"].append(pick_candidate)
            else:
                result["passes"].append(pick_candidate)

    # ── Resumen final ─────────────────────────────────────
    n_picks   = len(result["picks"])
    n_paper_a = len(result["paper_a"])
    n_pass    = len(result["passes"])

    result["summary"] = (
        f"{'='*60}\n"
        f"PARTIDO: {result['match']} | CI={ci} {active_flags}\n"
        f"RESULTADO: {n_picks} PICK(S) | {n_paper_a} PAPER-A | {n_pass} PASS\n"
        f"{'='*60}"
    )

    return result


def _validate_recent_data(match_data: dict) -> bool:
    """Verifica que los datos recientes están presentes."""
    required = [
        "home_corners_avg", "away_corners_avg",
        "home_corners_conceded", "away_corners_conceded",
    ]
    return all(match_data.get(k) is not None for k in required)
