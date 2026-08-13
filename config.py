# ============================================================
#  SOCCER EDGE SYSTEM — config.py
#  NOTA: La configuración principal se movió a cg0p/config/settings.py
#  Este archivo se mantiene por compatibilidad con código existente.
# ============================================================

# Re-exportar desde settings centralizado
try:
    from cg0p.config.settings import (
        SHARP_API_KEY as API_KEY,
        SHARP_API_BASE as BASE_URL,
        SHARP_LEAGUE_KEYS as LIGAS,
        SHARP_BOOKMAKERS_PRIORITY as BOOKMAKERS,
        EDGE_MINIMO,
        VALUE_BET_MINIMO,
        VALUE_BET_MAXIMO,
        KELLY_FRACCION,
        BANKROLL,
        DB_PATH,
        SCREENSHOTS_DIR,
        REPORTES_DIR,
    )
except ImportError:
    # Fallback si el paquete cg0p no está disponible
    API_KEY          = ""
    BASE_URL         = "https://api.sharpapi.io/api/v1"
    LIGAS            = {}
    BOOKMAKERS       = ["pinnacle", "bet365", "draftkings"]
    EDGE_MINIMO      = 3.5
    VALUE_BET_MINIMO = 1.05
    VALUE_BET_MAXIMO = 4.0
    KELLY_FRACCION   = 0.25
    BANKROLL         = 1000
    DB_PATH          = "cg0p_picks.db"
    SCREENSHOTS_DIR  = "screenshots"
    REPORTES_DIR     = "reportes"
