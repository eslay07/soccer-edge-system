# ============================================================
#  SOCCER EDGE SYSTEM — scraper.py
#  Recolecta líneas de The Odds API + calcula edge
# ============================================================

import requests
from datetime import datetime
from config import API_KEY, BASE_URL, LIGAS, BOOKMAKERS, EDGE_MINIMO, VALUE_BET_MINIMO, VALUE_BET_MAXIMO, KELLY_FRACCION, BANKROLL


# ─────────────────────────────────────────────
#  1. OBTENER PARTIDOS DE UNA LIGA
# ─────────────────────────────────────────────
def obtener_partidos(sport_key: str) -> list:
    """Devuelve lista de partidos con sus odds de múltiples casas."""
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        "apiKey":   API_KEY,
        "regions":  "eu",
        "markets":  "h2h,spreads,totals",
        "oddsFormat": "decimal",
        "bookmakers": ",".join(BOOKMAKERS),
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────
#  2. EXTRAER Y NORMALIZAR LÍNEAS
# ─────────────────────────────────────────────
def normalizar_partido(partido: dict) -> dict:
    """Extrae las mejores cuotas y la cuota promedio sharp por resultado."""
    home = partido["home_team"]
    away = partido["away_team"]

    # Recopilamos cuotas por outcome de todas las casas
    cuotas = {"home": [], "away": [], "draw": []}

    for book in partido.get("bookmakers", []):
        for market in book.get("markets", []):
            if market["key"] == "h2h":
                for outcome in market["outcomes"]:
                    nombre = outcome["name"]
                    precio = outcome["price"]
                    if nombre == home:
                        cuotas["home"].append((book["key"], precio))
                    elif nombre == away:
                        cuotas["away"].append((book["key"], precio))
                    elif nombre == "Draw":
                        cuotas["draw"].append((book["key"], precio))

    # Cuota máxima disponible (best line) y promedio sharp (Pinnacle si existe)
    def best_and_sharp(lista):
        if not lista:
            return None, None
        precios = [p for _, p in lista]
        best = max(precios)
        sharp_price = next((p for k, p in lista if k == "pinnacle"), None)
        return best, sharp_price or (sum(precios) / len(precios))

    home_best, home_sharp = best_and_sharp(cuotas["home"])
    away_best, away_sharp = best_and_sharp(cuotas["away"])
    draw_best, draw_sharp = best_and_sharp(cuotas["draw"])

    return {
        "id":            partido["id"],
        "liga":          partido["sport_title"],
        "partido":       f"{home} vs {away}",
        "home":          home,
        "away":          away,
        "fecha_partido": partido["commence_time"],
        "cuotas": {
            "home": {"best": home_best, "sharp": home_sharp, "lineas": cuotas["home"]},
            "away": {"best": away_best, "sharp": away_sharp, "lineas": cuotas["away"]},
            "draw": {"best": draw_best, "sharp": draw_sharp, "lineas": cuotas["draw"]},
        }
    }


# ─────────────────────────────────────────────
#  3. CALCULAR EDGE
# ─────────────────────────────────────────────
def cuota_a_prob(cuota: float) -> float:
    return 1 / cuota if cuota and cuota > 0 else 0


def eliminar_vig(prob_h: float, prob_a: float, prob_d: float = 0) -> tuple:
    """Elimina el vig (overround) para obtener probabilidades reales."""
    total = prob_h + prob_a + prob_d
    if total == 0:
        return prob_h, prob_a, prob_d
    return prob_h / total, prob_a / total, prob_d / total


def calcular_edge(prob_real: float, cuota_tomada: float) -> float:
    """Edge = (prob_real × cuota_tomada) - 1  → en %"""
    return (prob_real * cuota_tomada - 1) * 100


def kelly_units(prob_real: float, cuota: float, fraccion: float = KELLY_FRACCION) -> float:
    """Kelly fraccionado en unidades."""
    b = cuota - 1
    q = 1 - prob_real
    kelly = (b * prob_real - q) / b
    return max(0, round(kelly * fraccion, 4))


# ─────────────────────────────────────────────
#  4. ANALIZAR PARTIDO COMPLETO
# ─────────────────────────────────────────────
def analizar_partido(p: dict) -> list:
    """
    Retorna lista de oportunidades evaluadas.
    Cada item indica si es PICK o PASS y por qué.
    """
    cuotas = p["cuotas"]
    resultados = []

    for lado in ["home", "away", "draw"]:
        data = cuotas[lado]
        if not data["best"] or not data["sharp"]:
            continue

        # Probabilidades sin vig usando las cuotas sharp
        ph = cuota_a_prob(cuotas["home"]["sharp"])
        pa = cuota_a_prob(cuotas["away"]["sharp"])
        pd = cuota_a_prob(cuotas["draw"]["sharp"]) if cuotas["draw"]["sharp"] else 0

        prob_h, prob_a, prob_d = eliminar_vig(ph, pa, pd)
        prob_map = {"home": prob_h, "away": prob_a, "draw": prob_d}

        prob_real  = prob_map[lado]
        cuota_best = data["best"]
        edge       = calcular_edge(prob_real, cuota_best)
        k_units    = kelly_units(prob_real, cuota_best)
        stake      = round(k_units * BANKROLL, 2)

        # ─── FILTRO PICK / PASS ───
        motivo_pass = None

        if cuota_best < VALUE_BET_MINIMO:
            motivo_pass = f"Cuota {cuota_best} menor al mínimo {VALUE_BET_MINIMO}"
        elif cuota_best > VALUE_BET_MAXIMO:
            motivo_pass = f"Cuota {cuota_best} supera máximo {VALUE_BET_MAXIMO} (longshot sin base)"
        elif edge < EDGE_MINIMO:
            motivo_pass = f"Edge {edge:.2f}% insuficiente (mínimo {EDGE_MINIMO}%)"
        elif prob_real < 0.20:
            motivo_pass = "Probabilidad real < 20%, muy incierto"

        es_pick = motivo_pass is None

        resultados.append({
            "liga":           p["liga"],
            "partido":        p["partido"],
            "fecha_partido":  p["fecha_partido"],
            "mercado":        "1X2",
            "seleccion":      lado.upper(),
            "cuota":          cuota_best,
            "prob_implicita": round(cuota_a_prob(cuota_best) * 100, 2),
            "prob_modelo":    round(prob_real * 100, 2),
            "edge_pct":       round(edge, 2),
            "kelly_units":    k_units,
            "stake":          stake,
            "es_pick":        es_pick,
            "motivo_pass":    motivo_pass,
        })

    return resultados


# ─────────────────────────────────────────────
#  5. IMPRIMIR RESULTADO EN CONSOLA
# ─────────────────────────────────────────────
def imprimir_analisis(analisis: list):
    for a in analisis:
        print("\n" + "═" * 60)
        print(f"  {a['partido']}  |  {a['liga']}")
        print(f"  Mercado: {a['mercado']}  |  Selección: {a['seleccion']}")
        print(f"  Cuota best: {a['cuota']}  |  Prob. modelo: {a['prob_modelo']}%")
        print(f"  Prob. implícita: {a['prob_implicita']}%  |  Edge: {a['edge_pct']}%")
        if a["es_pick"]:
            print(f"  🟢 PICK  →  Stake: {a['kelly_units']} u  (${a['stake']})")
        else:
            print(f"  🔴 PASS  →  {a['motivo_pass']}")
