# ============================================================
#  SOCCER EDGE SYSTEM — reportes.py
#  Genera imagen PNG del análisis (para exportar/compartir)
# ============================================================

import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import REPORTES_DIR, EDGE_MINIMO

os.makedirs(REPORTES_DIR, exist_ok=True)


def _color_edge(edge: float):
    if edge >= EDGE_MINIMO * 2:
        return (0, 200, 100)    # verde brillante
    elif edge >= EDGE_MINIMO:
        return (100, 220, 120)  # verde
    elif edge >= 0:
        return (200, 180, 0)    # amarillo
    else:
        return (220, 60, 60)    # rojo


def generar_reporte_imagen(analisis: list, nombre_archivo: str = None) -> str:
    """
    Genera una imagen PNG con el reporte completo del análisis.
    Retorna la ruta del archivo generado.
    """
    picks  = [a for a in analisis if a["es_pick"]]
    passes = [a for a in analisis if not a["es_pick"]]

    ANCHO   = 900
    PADDING = 30
    FILA_H  = 28
    H_HEADER = 140
    H_PICK   = max(1, len(picks))  * (FILA_H * 7 + 20)
    H_PASS   = max(1, len(passes)) * (FILA_H * 3 + 10)
    ALTO    = H_HEADER + H_PICK + H_PASS + 120

    img  = Image.new("RGB", (ANCHO, ALTO), (18, 18, 30))
    draw = ImageDraw.Draw(img)

    try:
        font_title  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_head   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_small  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        font_title = font_head = font_normal = font_small = ImageFont.load_default()

    # ── HEADER ──
    draw.rectangle([(0, 0), (ANCHO, 80)], fill=(30, 30, 50))
    draw.text((PADDING, 20), "⚽  SOCCER EDGE SYSTEM", font=font_title, fill=(255, 255, 255))
    draw.text((PADDING, 52), f"Análisis generado: {datetime.now().strftime('%d/%m/%Y  %H:%M')}",
              font=font_normal, fill=(180, 180, 200))
    draw.text((ANCHO - 200, 52),
              f"Picks: {len(picks)}  |  Passes: {len(passes)}",
              font=font_head, fill=(100, 220, 140))

    y = 95

    # ── SECCIÓN PICKS ──
    draw.text((PADDING, y), "🟢  PICKS CON EDGE", font=font_head, fill=(100, 220, 140))
    y += 30

    if not picks:
        draw.text((PADDING + 20, y), "No hay picks con edge suficiente en este análisis.", font=font_normal, fill=(160, 160, 180))
        y += 40
    else:
        for p in picks:
            # Fondo de tarjeta
            draw.rectangle([(PADDING, y), (ANCHO - PADDING, y + FILA_H * 6 + 10)],
                           fill=(28, 36, 54), outline=(60, 80, 120))
            # Partido
            draw.text((PADDING + 10, y + 6),
                      f"  {p['partido']}  —  {p['liga']}",
                      font=font_head, fill=(220, 220, 255))
            # Línea de datos
            draw.text((PADDING + 10, y + 30),
                      f"  Selección: {p['seleccion']}   Cuota: {p['cuota']}   "
                      f"Prob. Modelo: {p['prob_modelo']}%   Prob. Implícita: {p['prob_implicita']}%",
                      font=font_normal, fill=(200, 200, 220))
            # Edge destacado
            edge_color = _color_edge(p["edge_pct"])
            draw.text((PADDING + 10, y + 54),
                      f"  Edge: {p['edge_pct']:+.2f}%",
                      font=font_head, fill=edge_color)
            # Stake
            draw.text((PADDING + 10, y + 78),
                      f"  Stake: {p['kelly_units']} u  (Kelly {p['kelly_units']*4:.4f} completo)",
                      font=font_normal, fill=(255, 220, 100))
            # Fecha
            draw.text((PADDING + 10, y + 102),
                      f"  Partido: {p['fecha_partido'][:16].replace('T', '  ')}",
                      font=font_small, fill=(140, 140, 160))
            y += FILA_H * 6 + 20

    # ── SECCIÓN PASSES ──
    y += 10
    draw.line([(PADDING, y), (ANCHO - PADDING, y)], fill=(60, 60, 80), width=1)
    y += 10
    draw.text((PADDING, y), "🔴  EVALUADOS — PASS", font=font_head, fill=(220, 80, 80))
    y += 28

    if not passes:
        draw.text((PADDING + 20, y), "Sin passes en este análisis.", font=font_normal, fill=(160, 160, 180))
        y += 40
    else:
        for p in passes:
            draw.rectangle([(PADDING, y), (ANCHO - PADDING, y + FILA_H * 2 + 8)],
                           fill=(36, 24, 28), outline=(90, 50, 55))
            draw.text((PADDING + 10, y + 5),
                      f"  {p['partido']}  |  {p['seleccion']}  |  Edge: {p['edge_pct']:+.2f}%",
                      font=font_normal, fill=(200, 160, 160))
            draw.text((PADDING + 10, y + 27),
                      f"  Motivo: {p['motivo_pass']}",
                      font=font_small, fill=(160, 120, 120))
            y += FILA_H * 2 + 14

    # Footer
    draw.text((PADDING, ALTO - 30),
              "Sistema privado — no compartir sin autorización",
              font=font_small, fill=(80, 80, 100))

    # Guardar
    nombre_archivo = nombre_archivo or f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    ruta = os.path.join(REPORTES_DIR, nombre_archivo)
    img.save(ruta, "PNG")
    print(f"📊 Reporte guardado: {ruta}")
    return ruta
