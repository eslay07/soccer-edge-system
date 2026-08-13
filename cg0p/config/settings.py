import os

# ============================================================
#  CG-0P — config/settings.py
#  Configuración centralizada del sistema v1.2.7
#
#  EDITA ESTE ARCHIVO para ajustar claves de API, parámetros
#  de apuesta, rutas y otros valores configurables.
# ============================================================

# ─────────────────────────────────────────────────────────────
# SECCIÓN 1 — SHARP API  (sharpapi.io)
# Documentación: https://docs.sharpapi.io
# ─────────────────────────────────────────────────────────────

# Clave de autenticación — obtenerla en https://sharpapi.io/dashboard
SHARP_API_KEY = os.getenv("SHARP_API_KEY", "")
# Endpoint base (no cambiar salvo que SharpAPI actualice su versión)
SHARP_API_BASE = "https://api.sharpapi.io/api/v1"

# Claves de liga que acepta SharpAPI en el parámetro ?league=
# Si tu plan da error en alguna, consulta los valores exactos en:
#   GET /sports  o en el panel de SharpAPI
SHARP_LEAGUE_KEYS: dict[str, str] = {
    "Premier League":   "EPL",
    "La Liga":          "LA_LIGA",
    "Bundesliga":       "BUNDESLIGA",
    "Serie A":          "SERIE_A",
    "Ligue 1":          "LIGUE_1",
    "Champions League": "UEFA_CL",
    "Europa League":    "UEFA_EL",
    "MLS":              "MLS",
}

# Casas de apuestas a priorizar al extraer cuotas
# Las sharp books (Pinnacle, Circa) son la referencia para EV real
SHARP_BOOKMAKERS_PRIORITY = [
    "pinnacle", "circa", "bookmaker", "bet365",
    "draftkings", "fanduel", "betmgm",
]

# Ventana de días hacia adelante al buscar partidos próximos
SHARP_DAYS_AHEAD = 7

# ─────────────────────────────────────────────────────────────
# SECCIÓN 2 — PARÁMETROS DE ANÁLISIS Y APUESTA
# ─────────────────────────────────────────────────────────────

# Edge mínimo (en puntos porcentuales) para considerar un pick ejecutable
EDGE_MINIMO: float = 3.5

# Rango de cuotas aceptable para ejecutar picks
VALUE_BET_MINIMO: float = 1.05
VALUE_BET_MAXIMO: float = 4.0

# Kelly fraccionado — 0.25 = Kelly al 25% (más conservador, recomendado)
KELLY_FRACCION: float = 0.25

# Bankroll base en unidades monetarias
BANKROLL: float = 1000.0

# ─────────────────────────────────────────────────────────────
# SECCIÓN 3 — BASE DE DATOS Y RUTAS
# ─────────────────────────────────────────────────────────────

DB_PATH        = "cg0p_picks.db"
SCREENSHOTS_DIR = "screenshots"
REPORTES_DIR    = "reportes"

# ─────────────────────────────────────────────────────────────
# SECCIÓN 4 — CSV HISTÓRICOS (football-data.co.uk)
# Solo cambiar si cambian las URLs de la fuente
# ─────────────────────────────────────────────────────────────

# Temporada actual
CSV_TEMPORADA: str = "2425"

# URLs de la temporada actual por liga
CSV_URLS_ACTUALES: dict[str, str] = {
    "Premier League": f"https://www.football-data.co.uk/mmz4281/{CSV_TEMPORADA}/E0.csv",
    "La Liga":        f"https://www.football-data.co.uk/mmz4281/{CSV_TEMPORADA}/SP1.csv",
    "Bundesliga":     f"https://www.football-data.co.uk/mmz4281/{CSV_TEMPORADA}/D1.csv",
    "Serie A":        f"https://www.football-data.co.uk/mmz4281/{CSV_TEMPORADA}/I1.csv",
    "Ligue 1":        f"https://www.football-data.co.uk/mmz4281/{CSV_TEMPORADA}/F1.csv",
}
