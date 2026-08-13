# ============================================================
#  SOCCER EDGE SYSTEM — main.py
#  Punto de entrada principal del sistema
# ============================================================

from database  import inicializar_db, guardar_pick, obtener_estadisticas
from scraper   import obtener_partidos, normalizar_partido, analizar_partido, imprimir_analisis
from reportes  import generar_reporte_imagen
from config    import LIGAS


def correr_analisis(ligas: list = None, generar_imagen: bool = True, guardar_en_db: bool = True):
    """
    Analiza todas las ligas configuradas (o las indicadas).
    - Imprime análisis en consola
    - Guarda picks/passes en DB
    - Genera reporte imagen PNG
    """
    inicializar_db()
    ligas_a_analizar = ligas or list(LIGAS.keys())
    todos_los_analisis = []

    for nombre_liga in ligas_a_analizar:
        sport_key = LIGAS.get(nombre_liga)
        if not sport_key:
            print(f"⚠️  Liga no encontrada: {nombre_liga}")
            continue

        print(f"\n📡 Descargando odds: {nombre_liga}...")
        try:
            partidos_raw = obtener_partidos(sport_key)
        except Exception as e:
            print(f"❌ Error al obtener datos de {nombre_liga}: {e}")
            continue

        print(f"   → {len(partidos_raw)} partidos encontrados")

        for p_raw in partidos_raw:
            partido = normalizar_partido(p_raw)
            analisis = analizar_partido(partido)

            # Imprimir en consola
            imprimir_analisis(analisis)

            todos_los_analisis.extend(analisis)

            # Guardar en DB
            if guardar_en_db:
                for a in analisis:
                    guardar_pick(a)

    # Reporte imagen
    if generar_imagen and todos_los_analisis:
        generar_reporte_imagen(todos_los_analisis)

    # Stats globales
    print("\n" + "═" * 60)
    print("📈  ESTADÍSTICAS GLOBALES DEL SISTEMA")
    stats = obtener_estadisticas()
    if stats:
        print(f"   Total picks resueltos : {stats['total_picks']}")
        print(f"   W / L / P             : {stats['wins']} / {stats['losses']} / {stats['pushes']}")
        print(f"   Tasa de acierto        : {stats['tasa_acierto_pct']}%")
        print(f"   ROI                    : {stats['roi_pct']}%")
        print(f"   P&L total              : {stats['pl_total']:+.2f} u")
        print(f"   Edge promedio          : {stats['edge_promedio']}%")
    else:
        print("   Sin historial resuelto aún.")

    return todos_los_analisis


# ── MODO INTERACTIVO: RESOLVER PICKS ──────────────────────
def modo_resolver():
    """Permite resolver picks pendientes desde la consola."""
    from database import get_conn, resolver_pick
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, partido, seleccion, cuota_tomada, edge_pct
        FROM picks WHERE es_pick=1 AND resultado IS NULL
        ORDER BY fecha_analisis DESC
    """)
    pendientes = c.fetchall()
    conn.close()

    if not pendientes:
        print("✅ No hay picks pendientes de resolver.")
        return

    print(f"\n🕐 {len(pendientes)} picks pendientes:\n")
    for row in pendientes:
        pid, partido, sel, cuota, edge = row
        print(f"  [{pid}] {partido}  |  {sel}  @{cuota}  Edge:{edge}%")

    try:
        pid = int(input("\nID del pick a resolver: "))
        res = input("Resultado (W/L/P): ").upper()
        stake = float(input("Stake apostado (unidades): "))
        cuota_r = float(input("Cuota tomada: "))
        if res == "W":
            pl = round(stake * (cuota_r - 1), 3)
        elif res == "L":
            pl = -stake
        else:
            pl = 0
        resolver_pick(pid, res, pl)
    except (ValueError, KeyboardInterrupt):
        print("Cancelado.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "resolver":
        modo_resolver()
    else:
        correr_analisis()
