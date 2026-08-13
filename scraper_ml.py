# ============================================================
#  SOCCER EDGE SYSTEM — scraper_ml.py
#  Versión actualizada del scraper que usa el modelo XGBoost
#  para calcular probabilidades propias en lugar del mercado
# ============================================================

from scraper  import obtener_partidos, normalizar_partido, imprimir_analisis
from features import construir_feature_vector, calcular_forma, calcular_h2h
from modelo   import predecir_partido
from config   import LIGAS, EDGE_MINIMO, VALUE_BET_MINIMO, VALUE_BET_MAXIMO, KELLY_FRACCION, BANKROLL


def cuota_a_prob(cuota):
    return 1 / cuota if cuota and cuota > 0 else 0


def kelly_units(prob_real, cuota, fraccion=KELLY_FRACCION):
    b = cuota - 1
    q = 1 - prob_real
    k = (b * prob_real - q) / b
    return max(0, round(k * fraccion, 4))


def analizar_partido_ml(partido: dict, forma_db: dict = None) -> list:
    """
    Analiza un partido usando probabilidades del modelo XGBoost.

    forma_db: dict con historial de cada equipo. Si es None,
              se usan las probabilidades del mercado como fallback
              hasta que el modelo tenga suficientes datos propios.

    Estructura esperada de forma_db:
    {
        "home_team": {
            "partidos": [...],   # lista de dicts con resultados históricos
            "h2h":      [...]    # partidos H2H específicos
        },
        "away_team": { ... }
    }
    """
    cuotas    = partido["cuotas"]
    home_team = partido["home"]
    away_team = partido["away"]

    # ── Probabilidades implícitas del mercado (sharp, sin vig) ──
    ph = cuota_a_prob(cuotas["home"]["sharp"])
    pa = cuota_a_prob(cuotas["away"]["sharp"])
    pd = cuota_a_prob(cuotas["draw"]["sharp"]) if cuotas["draw"]["sharp"] else 0
    total = ph + pa + pd or 1
    mkt_home = ph / total
    mkt_away = pa / total
    mkt_draw = pd / total

    # ── Construir vector de features ──
    if forma_db:
        fh = calcular_forma(forma_db.get("home_partidos", []), home_team)
        fa = calcular_forma(forma_db.get("away_partidos", []), away_team)
        h2h = calcular_h2h(forma_db.get("h2h", []), home_team)
        dias_home = forma_db.get("dias_descanso_home", 7)
        dias_away = forma_db.get("dias_descanso_away", 7)
        mov_linea = forma_db.get("mov_linea_home", 0.0)
    else:
        # Fallback: forma neutral cuando no hay historial
        forma_neutra = {"wins": 0.4, "draws": 0.25, "losses": 0.35,
                        "gf_avg": 1.4, "gc_avg": 1.2, "puntos": 0.45}
        fh = fa = forma_neutra
        h2h = {"h2h_win_rate": 0.33, "h2h_goles_avg": 2.5, "h2h_partidos": 0}
        dias_home = dias_away = 7
        mov_linea = 0.0

    features = construir_feature_vector(
        home=home_team, away=away_team,
        forma_home=fh, forma_away=fa, h2h=h2h,
        prob_implicita_home=mkt_home,
        prob_implicita_away=mkt_away,
        prob_implicita_draw=mkt_draw,
        mov_linea_home=mov_linea,
        dias_descanso_home=dias_home,
        dias_descanso_away=dias_away,
    )

    # ── Obtener probabilidades del modelo ──
    probs_ml = predecir_partido(features)

    if probs_ml:
        prob_home = probs_ml["HOME"]
        prob_draw = probs_ml["DRAW"]
        prob_away = probs_ml["AWAY"]
        fuente_prob = "XGBoost"
    else:
        # Sin modelo entrenado aún → usa mercado como proxy
        prob_home = mkt_home
        prob_draw = mkt_draw
        prob_away = mkt_away
        fuente_prob = "Mercado (fallback)"

    # ── Calcular edge para cada resultado ──
    analisis = []
    for lado, prob_real, cuota_key in [
        ("home", prob_home, "home"),
        ("draw", prob_draw, "draw"),
        ("away", prob_away, "away"),
    ]:
        data = cuotas[cuota_key]
        if not data or not data.get("best"):
            continue

        cuota_best = data["best"]
        edge       = (prob_real * cuota_best - 1) * 100
        k_units    = kelly_units(prob_real, cuota_best)
        stake      = round(k_units * BANKROLL, 2)

        # ── Filtro PICK / PASS ──
        motivo_pass = None

        if cuota_best < VALUE_BET_MINIMO:
            motivo_pass = f"Cuota {cuota_best} < mínimo {VALUE_BET_MINIMO}"
        elif cuota_best > VALUE_BET_MAXIMO:
            motivo_pass = f"Cuota {cuota_best} > máximo {VALUE_BET_MAXIMO}"
        elif edge < EDGE_MINIMO:
            motivo_pass = f"Edge {edge:.2f}% insuficiente (mín. {EDGE_MINIMO}%)"
        elif prob_real < 0.18:
            motivo_pass = "Prob. modelo < 18%, demasiada incertidumbre"

        # Doble filtro: si el mercado y el modelo apuntan en direcciones opuestas
        # con diferencia grande, es señal de riesgo → reducir confianza
        desacuerdo = abs(prob_real - (mkt_home if lado == "home" else
                                      mkt_away if lado == "away" else mkt_draw))
        if desacuerdo > 0.20 and not motivo_pass:
            motivo_pass = f"Desacuerdo modelo/mercado {desacuerdo*100:.1f}% — señal ambigua"

        es_pick = motivo_pass is None

        analisis.append({
            "liga":              partido["liga"],
            "partido":           partido["partido"],
            "fecha_partido":     partido["fecha_partido"],
            "mercado":           "1X2",
            "seleccion":         lado.upper(),
            "cuota":             cuota_best,
            "prob_implicita":    round(cuota_a_prob(cuota_best) * 100, 2),
            "prob_modelo":       round(prob_real * 100, 2),
            "prob_mkt":          round((mkt_home if lado == "home" else
                                        mkt_away if lado == "away" else mkt_draw) * 100, 2),
            "fuente_prob":       fuente_prob,
            "edge_pct":          round(edge, 2),
            "kelly_units":       k_units,
            "stake":             stake,
            "es_pick":           es_pick,
            "motivo_pass":       motivo_pass,
            "features":          features,   # guardamos para re-entrenamiento
        })

    return analisis


def correr_analisis_ml(ligas: list = None) -> list:
    """Corre el análisis completo usando el modelo ML."""
    from database import inicializar_db, guardar_pick
    from reportes import generar_reporte_imagen

    inicializar_db()
    ligas_a_analizar = ligas or list(LIGAS.keys())
    todos = []

    for nombre_liga in ligas_a_analizar:
        sport_key = LIGAS.get(nombre_liga)
        if not sport_key:
            continue
        print(f"\n📡 {nombre_liga}...")
        try:
            partidos_raw = obtener_partidos(sport_key)
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

        for p_raw in partidos_raw:
            partido  = normalizar_partido(p_raw)
            analisis = analizar_partido_ml(partido)
            imprimir_analisis_ml(analisis)
            todos.extend(analisis)
            for a in analisis:
                guardar_pick(a)

    if todos:
        generar_reporte_imagen(todos)

    return todos


def imprimir_analisis_ml(analisis: list):
    for a in analisis:
        print("\n" + "═" * 65)
        print(f"  {a['partido']}  |  {a['liga']}")
        print(f"  Cuota: {a['cuota']}  |  Fuente: {a['fuente_prob']}")
        print(f"  Prob. Modelo: {a['prob_modelo']}%  |  Prob. Mercado: {a['prob_mkt']}%  |  Impl.: {a['prob_implicita']}%")
        print(f"  Edge: {a['edge_pct']:+.2f}%")
        if a["es_pick"]:
            print(f"  🟢 PICK [{a['seleccion']}]  →  {a['kelly_units']} u  (${a['stake']})")
        else:
            print(f"  🔴 PASS  →  {a['motivo_pass']}")
