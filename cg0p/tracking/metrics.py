# ============================================================
#  CG-0P — tracking/metrics.py
#  Métricas de seguimiento del sistema
# ============================================================

from .history import PickHistory


class SystemMetrics:
    """Calcula y gestiona las métricas de rendimiento del sistema."""

    ANTI_RECENCY_TRIGGER = 3   # Revisar si 3 MISS consecutivos
    PAPER_A_REVIEW_TARGET = 20 # Revisar PAPER-A cuando haya 20 registros

    def __init__(self):
        self.history = PickHistory()

    def get_full_dashboard(self) -> dict:
        """
        Devuelve el dashboard completo de métricas.

        Returns:
            dict con todas las métricas del sistema
        """
        stats = self.history.get_statistics()
        resolved = self.history.get_resolved_picks(limit=200)

        # Racha actual
        streak = self._calculate_streak(resolved)

        # Brier scores estimados por módulo
        brier_by_module = self._calculate_brier_by_module(resolved)

        # Curva de bankroll
        bankroll_curve = self._calculate_bankroll_curve(resolved)

        # Anti-recency check
        anti_recency = self._check_anti_recency(resolved)

        return {
            "global_stats":     stats,
            "streak":           streak,
            "brier_by_module":  brier_by_module,
            "bankroll_curve":   bankroll_curve,
            "anti_recency":     anti_recency,
            "paper_a_count":    len(self.history.get_paper_a_history(limit=100)),
        }

    def _calculate_streak(self, resolved: list) -> dict:
        """Calcula la racha actual de HITs/MISSes."""
        if not resolved:
            return {"current": 0, "type": "none", "alert": False}

        streak = 0
        streak_type = resolved[0].get("resultado", "")
        for pick in resolved:
            if pick.get("resultado") == streak_type:
                streak += 1
            else:
                break

        alert = streak_type == "L" and streak >= self.ANTI_RECENCY_TRIGGER

        return {
            "current":    streak,
            "type":       "HIT" if streak_type == "W" else "MISS",
            "alert":      alert,
            "message":    f"ALERTA: {streak} MISS consecutivos — revisar sistema" if alert else "",
        }

    def _calculate_brier_by_module(self, resolved: list) -> dict:
        """
        Calcula el Brier Score promedio por módulo.

        Brier Score = (p_pred - outcome)^2
        < 0.15 = excelente | 0.15-0.25 = aceptable | > 0.25 = recalibrar
        """
        from .brier import brier_score

        by_module = {}
        for pick in resolved:
            mod = pick.get("modulo", "?")
            if mod not in by_module:
                by_module[mod] = []

            p_pred  = pick.get("prob_modelo") or 0.5
            outcome = 1 if pick.get("resultado") == "W" else 0
            bs      = brier_score(p_pred, outcome)
            by_module[mod].append(bs)

        result = {}
        for mod, scores in by_module.items():
            avg_bs = sum(scores) / len(scores)
            result[mod] = {
                "brier_avg": round(avg_bs, 3),
                "n_samples": len(scores),
                "quality":   "excelente" if avg_bs < 0.15
                             else "aceptable" if avg_bs < 0.25
                             else "RECALIBRAR",
            }
        return result

    def _calculate_bankroll_curve(self, resolved: list) -> list:
        """
        Calcula la curva de bankroll a lo largo del tiempo.

        Returns:
            lista de (fecha, bankroll_acumulado)
        """
        bankroll = 0.0
        curve    = [(None, 0.0)]
        for pick in reversed(resolved):   # cronológico
            pl = pick.get("pl_unidades") or 0.0
            bankroll += pl
            curve.append((pick.get("fecha_analisis", ""), round(bankroll, 2)))
        return curve

    def _check_anti_recency(self, resolved: list) -> dict:
        """
        Verifica el mecanismo anti-recency bias.
        Si hay 3+ MISS consecutivos, emite alerta.
        """
        consecutive_misses = 0
        for pick in resolved:
            if pick.get("resultado") == "L":
                consecutive_misses += 1
            else:
                break

        return {
            "consecutive_misses": consecutive_misses,
            "alert": consecutive_misses >= self.ANTI_RECENCY_TRIGGER,
            "recommendation": (
                "Revisar umbrales del sistema — posible deriva"
                if consecutive_misses >= self.ANTI_RECENCY_TRIGGER
                else "Sistema operando normalmente"
            ),
        }

    def get_module_yield(self, module_id: str) -> dict:
        """
        Devuelve el yield (ROI) de un módulo específico.
        Se activa cuando hay >= 15 picks.
        """
        resolved = self.history.get_resolved_picks(limit=200)
        mod_picks = [p for p in resolved if p.get("modulo") == module_id]

        if len(mod_picks) < 15:
            return {
                "module":    module_id,
                "n_picks":   len(mod_picks),
                "status":    "Muestra insuficiente (< 15 picks)",
                "yield_pct": None,
            }

        hits  = sum(1 for p in mod_picks if p.get("resultado") == "W")
        pl    = sum((p.get("pl_unidades") or 0) for p in mod_picks)
        stake = sum((p.get("stake") or 1) for p in mod_picks)

        return {
            "module":    module_id,
            "n_picks":   len(mod_picks),
            "win_rate":  round(hits / len(mod_picks) * 100, 1),
            "pl_total":  round(pl, 2),
            "yield_pct": round(pl / stake * 100, 1) if stake > 0 else 0,
            "status":    "activo",
        }
