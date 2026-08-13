# ============================================================
#  SOCCER EDGE SYSTEM — descargar_datos.py
#  Descarga datos históricos GRATUITOS de football-data.co.uk
#  y los convierte al formato del modelo
# ============================================================

import os
import requests
import pandas as pd
import numpy as np
from features import construir_feature_vector

DATOS_PATH   = "datos_entrenamiento.csv"
CACHE_DIR    = "datos_raw"
os.makedirs(CACHE_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────
#  FUENTES DE DATOS GRATUITAS
#  football-data.co.uk tiene CSVs históricos de ~25 ligas
# ──────────────────────────────────────────────────────────
FUENTES = {
    "Premier League":  [
        "https://www.football-data.co.uk/mmz4281/2425/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2223/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2122/E0.csv",
    ],
    "La Liga": [
        "https://www.football-data.co.uk/mmz4281/2425/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/SP1.csv",
    ],
    "Bundesliga": [
        "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/D1.csv",
    ],
    "Serie A": [
        "https://www.football-data.co.uk/mmz4281/2425/I1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/I1.csv",
    ],
    "Ligue 1": [
        "https://www.football-data.co.uk/mmz4281/2425/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
        "https://www.football-data.co.uk/mmz4281/2223/F1.csv",
    ],
}


def descargar_csv(url: str) -> pd.DataFrame | None:
    nombre = url.split("/")[-2] + "_" + url.split("/")[-1]
    ruta_cache = os.path.join(CACHE_DIR, nombre)

    if os.path.exists(ruta_cache):
        print(f"   📁 Cache: {nombre}")
        return pd.read_csv(ruta_cache, on_bad_lines="skip")

    try:
        print(f"   ⬇️  Descargando: {url}")
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        with open(ruta_cache, "wb") as f:
            f.write(r.content)
        return pd.read_csv(ruta_cache, on_bad_lines="skip")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def calcular_forma_rolling(df: pd.DataFrame, equipo: str, fecha_idx: int, n: int = 5) -> dict:
    """Calcula forma del equipo en los N partidos anteriores al índice dado."""
    partidos_ant = df.iloc[:fecha_idx]
    juegos_home  = partidos_ant[partidos_ant["HomeTeam"] == equipo].tail(n)
    juegos_away  = partidos_ant[partidos_ant["AwayTeam"] == equipo].tail(n)

    resultados = []
    for _, r in juegos_home.iterrows():
        resultados.append({
            "gf": r.get("FTHG", 0), "gc": r.get("FTAG", 0),
            "pts": 3 if r.get("FTR") == "H" else (1 if r.get("FTR") == "D" else 0)
        })
    for _, r in juegos_away.iterrows():
        resultados.append({
            "gf": r.get("FTAG", 0), "gc": r.get("FTHG", 0),
            "pts": 3 if r.get("FTR") == "A" else (1 if r.get("FTR") == "D" else 0)
        })

    resultados = sorted(resultados, key=lambda x: x.get("pts", 0))[-n:]  # últimos N

    if not resultados:
        return {"wins": 0.33, "draws": 0.25, "losses": 0.33, "gf_avg": 1.3, "gc_avg": 1.3, "puntos": 0.4}

    wins   = sum(1 for j in resultados if j["pts"] == 3) / n
    draws  = sum(1 for j in resultados if j["pts"] == 1) / n
    losses = sum(1 for j in resultados if j["pts"] == 0) / n
    gf_avg = np.mean([j["gf"] for j in resultados])
    gc_avg = np.mean([j["gc"] for j in resultados])
    puntos = np.mean([j["pts"] for j in resultados]) / 3

    return {"wins": wins, "draws": draws, "losses": losses,
            "gf_avg": round(gf_avg, 3), "gc_avg": round(gc_avg, 3), "puntos": round(puntos, 3)}


def procesar_liga(df: pd.DataFrame, liga: str) -> list:
    """Convierte los partidos del CSV al formato de features del modelo."""
    filas = []
    df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"]).reset_index(drop=True)

    # Columnas de odds Pinnacle o B365 como fallback
    col_h = next((c for c in ["PSH", "B365H"] if c in df.columns), None)
    col_a = next((c for c in ["PSA", "B365A"] if c in df.columns), None)
    col_d = next((c for c in ["PSD", "B365D"] if c in df.columns), None)

    for i, row in df.iterrows():
        if i < 10:  # necesitamos historial mínimo
            continue

        home = row["HomeTeam"]
        away = row["AwayTeam"]
        resultado_raw = row["FTR"]  # H, D, A
        resultado_mapeado = {"H": "HOME", "D": "DRAW", "A": "AWAY"}.get(resultado_raw)
        if not resultado_mapeado:
            continue

        fh  = calcular_forma_rolling(df, home, i)
        fa  = calcular_forma_rolling(df, away, i)

        # H2H simplificado
        h2h_df = df.iloc[:i]
        h2h_df = h2h_df[((h2h_df["HomeTeam"] == home) & (h2h_df["AwayTeam"] == away)) |
                         ((h2h_df["HomeTeam"] == away) & (h2h_df["AwayTeam"] == home))].tail(6)
        h2h_home_wins = sum(
            1 for _, r in h2h_df.iterrows()
            if (r["HomeTeam"] == home and r["FTR"] == "H") or
               (r["AwayTeam"] == home and r["FTR"] == "A")
        )
        h2h_n = len(h2h_df)
        h2h = {
            "h2h_win_rate":  h2h_home_wins / h2h_n if h2h_n else 0.33,
            "h2h_goles_avg": h2h_df.apply(lambda r: r.get("FTHG", 0) + r.get("FTAG", 0), axis=1).mean() if h2h_n else 2.5,
            "h2h_partidos":  h2h_n,
        }

        # Probabilidades implícitas
        def safe_prob(col):
            try:
                v = float(row[col])
                return 1/v if v > 0 else 0.33
            except:
                return 0.33

        mkt_h = safe_prob(col_h) if col_h else 0.45
        mkt_a = safe_prob(col_a) if col_a else 0.30
        mkt_d = safe_prob(col_d) if col_d else 0.25
        total = mkt_h + mkt_a + mkt_d or 1
        mkt_h /= total; mkt_a /= total; mkt_d /= total

        fv = construir_feature_vector(
            home=home, away=away,
            forma_home=fh, forma_away=fa, h2h=h2h,
            prob_implicita_home=mkt_h,
            prob_implicita_away=mkt_a,
            prob_implicita_draw=mkt_d,
        )
        fv["resultado"] = resultado_mapeado
        filas.append(fv)

    print(f"   ✅ {len(filas)} partidos procesados de {liga}")
    return filas


def descargar_y_preparar_datos(ligas: list = None) -> pd.DataFrame:
    """
    Descarga datos históricos y genera el CSV de entrenamiento.
    """
    ligas = ligas or list(FUENTES.keys())
    todos = []

    for liga in ligas:
        if liga not in FUENTES:
            continue
        print(f"\n📥 Liga: {liga}")
        frames = []
        for url in FUENTES[liga]:
            df_raw = descargar_csv(url)
            if df_raw is not None and len(df_raw) > 0:
                frames.append(df_raw)

        if frames:
            df_liga = pd.concat(frames, ignore_index=True)
            filas = procesar_liga(df_liga, liga)
            todos.extend(filas)

    if not todos:
        print("❌ No se pudieron descargar datos. Verifica tu conexión.")
        return pd.DataFrame()

    df_final = pd.DataFrame(todos)
    df_final.to_csv(DATOS_PATH, index=False)
    print(f"\n✅ Dataset guardado: {len(df_final)} partidos → {DATOS_PATH}")
    print(f"   Distribución: {df_final['resultado'].value_counts().to_dict()}")
    return df_final


if __name__ == "__main__":
    print("🔄 Descargando datos históricos para entrenar el modelo...")
    df = descargar_y_preparar_datos()
    if len(df) > 0:
        print("\n🤖 Iniciando entrenamiento del modelo...")
        from modelo import entrenar_modelo
        entrenar_modelo(forzar=True)
