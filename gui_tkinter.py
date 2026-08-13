# ============================================================
#  CG-0P — gui_tkinter.py
#  Interfaz Gráfica con Tkinter
#  Sistema de Análisis de Apuestas Deportivas v1.2.7
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


# ── Colores y estilos ─────────────────────────────────────
BG_DARK     = "#1a1a2e"
BG_MEDIUM   = "#16213e"
BG_LIGHT    = "#0f3460"
ACCENT      = "#e94560"
ACCENT2     = "#0f9b8e"
TEXT_WHITE  = "#eaeaea"
TEXT_GRAY   = "#a0a0b0"
GREEN       = "#00c853"
YELLOW      = "#ffd600"
RED_COLOR   = "#ff1744"
BLUE        = "#40c4ff"

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_MONO   = ("Courier New", 9)
FONT_SMALL  = ("Segoe UI", 9)


class CG0PApp(tk.Tk):
    """Ventana principal de la aplicación CG-0P."""

    def __init__(self):
        super().__init__()
        self.title("CG-0P v1.2.7 — Sistema de Análisis de Apuestas Deportivas")
        self.geometry("1200x800")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Intentar importar módulos CG-0P
        self._cg0p_available = self._try_import_cg0p()

        self._build_ui()

    def _try_import_cg0p(self) -> bool:
        """Intenta importar el módulo CG-0P. Retorna True si tiene éxito."""
        try:
            from cg0p.core.pipeline import run_pipeline
            from cg0p.tracking.history import PickHistory
            from cg0p.tracking.metrics import SystemMetrics
            from cg0p.output.formatter import format_full_analysis, format_post_match
            self._run_pipeline      = run_pipeline
            self._PickHistory       = PickHistory
            self._SystemMetrics     = SystemMetrics
            self._format_analysis   = format_full_analysis
            self._format_post       = format_post_match
            return True
        except Exception as e:
            self._import_error = str(e)
            return False

    # ── Construcción de la UI ─────────────────────────────

    def _build_ui(self):
        """Construye la interfaz principal con pestañas."""
        # Barra de título personalizada
        self._build_header()

        # Notebook (pestañas)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TNotebook",        background=BG_DARK,  borderwidth=0)
        style.configure("Custom.TNotebook.Tab",    background=BG_MEDIUM, foreground=TEXT_GRAY,
                         padding=[15, 8], font=FONT_BODY)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", BG_LIGHT)],
                  foreground=[("selected", TEXT_WHITE)])

        self.notebook = ttk.Notebook(self, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Pestañas
        self._tab_analisis   = self._build_tab_analisis()
        self._tab_historial  = self._build_tab_historial()
        self._tab_metricas   = self._build_tab_metricas()
        self._tab_patches    = self._build_tab_patches()
        self._tab_actualizar = self._build_tab_actualizar()

        self.notebook.add(self._tab_analisis,   text="  Análisis PRE  ")
        self.notebook.add(self._tab_historial,  text="  Historial  ")
        self.notebook.add(self._tab_metricas,   text="  Métricas  ")
        self.notebook.add(self._tab_patches,    text="  Patches  ")
        self.notebook.add(self._tab_actualizar, text="  📥 Actualizar  ")

        # Barra de estado
        self._build_statusbar()

    def _build_header(self):
        """Construye la cabecera de la aplicación."""
        header = tk.Frame(self, bg=BG_LIGHT, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="CG-0P — Sistema Predictivo de Apuestas Deportivas",
            font=FONT_TITLE, bg=BG_LIGHT, fg=TEXT_WHITE,
        ).pack(side="left", padx=20, pady=10)

        version_label = tk.Label(
            header,
            text="v1.2.7",
            font=FONT_SMALL, bg=BG_LIGHT, fg=ACCENT,
        )
        version_label.pack(side="right", padx=20)

        status_icon = "✅ Módulos OK" if self._cg0p_available else "⚠️ Error de importación"
        status_color = GREEN if self._cg0p_available else YELLOW

        tk.Label(
            header,
            text=status_icon,
            font=FONT_SMALL, bg=BG_LIGHT, fg=status_color,
        ).pack(side="right", padx=10)

    # ─────────────────────────────────────────────────────
    # PESTAÑA 1: ANÁLISIS PRE-PARTIDO
    # ─────────────────────────────────────────────────────

    def _bind_scroll(self, canvas: tk.Canvas, handler):
        """Registra el scroll del ratón en el canvas (Windows + Linux)."""
        canvas.bind_all("<MouseWheel>", handler)   # Windows / macOS
        canvas.bind_all("<Button-4>",   handler)   # Linux scroll up
        canvas.bind_all("<Button-5>",   handler)   # Linux scroll down

    def _unbind_scroll(self, canvas: tk.Canvas):
        """Desregistra el scroll del ratón."""
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    def _build_tab_analisis(self) -> tk.Frame:
        """Pestaña de análisis PRE-partido."""
        frame = tk.Frame(self.notebook, bg=BG_DARK)

        # ── Panel izquierdo: formulario con scroll ─────────
        left_container = tk.Frame(frame, bg=BG_MEDIUM, width=445)
        left_container.pack(side="left", fill="y", padx=(5, 2), pady=5)
        left_container.pack_propagate(False)

        # Canvas + Scrollbar vertical
        _canvas  = tk.Canvas(left_container, bg=BG_MEDIUM, highlightthickness=0)
        _vscroll = ttk.Scrollbar(left_container, orient="vertical",
                                  command=_canvas.yview)
        left = tk.Frame(_canvas, bg=BG_MEDIUM)
        _cw  = _canvas.create_window((0, 0), window=left, anchor="nw")
        _canvas.configure(yscrollcommand=_vscroll.set)

        # Ajustar scrollregion cuando el contenido cambia de tamaño
        left.bind("<Configure>",
                  lambda e: _canvas.configure(scrollregion=_canvas.bbox("all")))
        # Ajustar ancho del frame interior al canvas
        _canvas.bind("<Configure>",
                     lambda e: _canvas.itemconfig(_cw, width=e.width))

        # Handler de scroll compatible con Windows y Linux
        def _scroll_handler(event):
            if event.num == 4:          # Linux scroll up
                _canvas.yview_scroll(-1, "units")
            elif event.num == 5:        # Linux scroll down
                _canvas.yview_scroll(1, "units")
            else:                       # Windows / macOS
                _canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        _canvas.bind("<Enter>", lambda e: self._bind_scroll(_canvas, _scroll_handler))
        _canvas.bind("<Leave>", lambda e: self._unbind_scroll(_canvas))

        _vscroll.pack(side="right", fill="y")
        _canvas.pack(side="left", fill="both", expand=True)

        tk.Label(
            left, text="DATOS DEL PARTIDO",
            font=FONT_HEADER, bg=BG_MEDIUM, fg=ACCENT,
        ).pack(pady=(15, 5), padx=15, anchor="w")

        # ── Información básica ─────────────────────────
        self._entry_vars = {}
        fields_basic = [
            ("Liga",               "liga",         "Premier League"),
            ("Equipo Local",       "home_team",    "Arsenal"),
            ("Equipo Visitante",   "away_team",    "Chelsea"),
            ("Fecha partido",      "date",         "22/02/2026"),
            ("Árbitro (opcional)", "referee_name", ""),
        ]
        self._build_form_section(left, "INFORMACIÓN BÁSICA", fields_basic)

        # ── Botón autocompletar ────────────────────────
        autofill_frame = tk.Frame(left, bg=BG_MEDIUM)
        autofill_frame.pack(fill="x", padx=15, pady=(8, 2))

        tk.Button(
            autofill_frame,
            text="🔍  AUTOCOMPLETAR DATOS",
            command=self._autofill_form,
            font=FONT_BODY,
            bg=ACCENT2, fg="white",
            activebackground="#0a7a6e",
            relief="flat", bd=0,
            cursor="hand2",
            pady=8,
        ).pack(fill="x")

        self._autofill_status = tk.Label(
            left,
            text="↑  Ingresa Liga + Equipos y presiona Autocompletar",
            font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY,
            wraplength=390, justify="left",
        )
        self._autofill_status.pack(padx=15, pady=(3, 5), anchor="w")

        # ── Corners ───────────────────────────────────
        fields_corners = [
            ("CK Avg Local (temporada)",   "home_corners_avg",        "5.2"),
            ("CK Avg Visitante (temporada)","away_corners_avg",        "4.8"),
            ("CK Concedidos Local/p",      "home_corners_conceded",   "4.5"),
            ("CK Concedidos Visitante/p",  "away_corners_conceded",   "5.0"),
            ("CK Local últimos 5",         "home_corners_last5",      "5.8"),
            ("CK Visitante últimos 5",     "away_corners_last5",      "4.2"),
        ]
        self._build_form_section(left, "DATOS DE CORNERS", fields_corners)

        # ── xG y BTTS ────────────────────────────────
        fields_xg = [
            ("xG Local",         "home_xg",             "1.35"),
            ("xG Visitante",     "away_xg",             "1.10"),
            ("xGA Local",        "home_xga",            "1.20"),
            ("xGA Visitante",    "away_xga",             "0.95"),
            ("BTTS% Local (10p)","home_btts_pct_last10", "0.55"),
            ("BTTS% Visit.(10p)","away_btts_pct_last10", "0.60"),
            ("CS% Local",        "home_clean_sheet_pct", "0.30"),
            ("CS% Visitante",    "away_clean_sheet_pct", "0.25"),
        ]
        self._build_form_section(left, "xG / BTTS", fields_xg)

        # ── Árbitro ───────────────────────────────────
        fields_ref = [
            ("Árbitro: amarillas/p",  "referee_cards_avg",     "3.5"),
            ("Árbitro: rojas/p",      "referee_reds_avg",       "0.10"),
            ("Árbitro: penales/p",    "referee_penalties_avg",  "0.15"),
        ]
        self._build_form_section(left, "ÁRBITRO", fields_ref)

        # ── Flags del partido ──────────────────────────
        fields_flags = [
            ("Prob. Gol < 20' Local",     "home_early_goal_prob",    "0.20"),
            ("Prob. Gol < 20' Visitante", "away_early_goal_prob",    "0.15"),
            ("Racha perd. Visitante",      "away_losing_streak",      "0"),
            ("% Calidad plantilla Visit.", "away_squad_quality_percentile","50"),
        ]
        self._build_form_section(left, "FLAGS Y CONTEXTO", fields_flags)

        # Checkboxes
        self._check_vars = {}
        checks = [
            ("Árbitro verificado",         "referee_verified"),
            ("DT Visit. bajo presión",     "away_manager_under_pressure"),
            ("H2H competitivo en casa",    "h2h_competitive"),
            ("xG verificado",              "xg_verified"),
            ("Rivalidad/Urgencia",         "rivalry_flag"),
            ("ProxyMode (no Pinnacle)",    "proxy_mode"),
            ("Partido ajustado hasta 70'", "projected_tight_70"),
        ]
        self._build_checkboxes(left, checks)

        # ── Cuotas del partido ─────────────────────────
        tk.Label(
            left, text="CUOTAS DEL PARTIDO", font=FONT_HEADER,
            bg=BG_MEDIUM, fg=ACCENT,
        ).pack(pady=(10, 3), padx=15, anchor="w")

        tk.Label(
            left,
            text="Ingresa las cuotas de tu casa de apuestas. Deja en 0 las que no apliquen.",
            font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY, wraplength=390,
        ).pack(padx=15, anchor="w")

        self._odds_vars = {}

        # ── Definición de todos los mercados con líneas ──
        # Formato: (label, market_key, threshold, default_over, default_under)
        # market_key debe coincidir con lo que espera el pipeline/módulos

        markets_config = [
            ("Total de Goles", [
                ("Over/Under 1.5", "goals_under_15", 1.5, "0", "0"),
                ("Over/Under 2.5", "goals_under_25", 2.5, "0", "0"),
                ("Over/Under 3.5", "goals_under_35", 3.5, "0", "0"),
                ("Over/Under 4.5", "goals_under_45", 4.5, "0", "0"),
                ("Over/Under 5.5", "goals_under_55", 5.5, "0", "0"),
            ]),
            ("Ambos Marcan (BTTS)", [
                ("Ambos Marcan", "btts", 0, "0", "0"),
            ]),
            ("Total de Corners", [
                ("Over/Under 8.5",  "total_corners_85",  8.5,  "0", "0"),
                ("Over/Under 9.5",  "total_corners_95",  9.5,  "0", "0"),
                ("Over/Under 10.5", "total_corners_105", 10.5, "0", "0"),
                ("Over/Under 11.5", "total_corners_115", 11.5, "0", "0"),
            ]),
            ("Corners Equipo Local", [
                ("Over/Under 3.5", "team_corners_home_35", 3.5, "0", "0"),
                ("Over/Under 4.5", "team_corners_home",    4.5, "0", "0"),
                ("Over/Under 5.5", "team_corners_home_55", 5.5, "0", "0"),
                ("Over/Under 6.5", "team_corners_home_65", 6.5, "0", "0"),
            ]),
            ("Corners Equipo Visitante", [
                ("Over/Under 3.5", "team_corners_away_35", 3.5, "0", "0"),
                ("Over/Under 4.5", "team_corners_away",    4.5, "0", "0"),
                ("Over/Under 5.5", "team_corners_away_55", 5.5, "0", "0"),
                ("Over/Under 6.5", "team_corners_away_65", 6.5, "0", "0"),
            ]),
            ("Corners 1era Mitad", [
                ("Local Over/Under 2.5",      "1h_corners_home",    2.5, "0", "0"),
                ("Local Over/Under 3.5",      "1h_corners_home_35", 3.5, "0", "0"),
                ("Visitante Over/Under 2.5",  "1h_corners_away",    2.5, "0", "0"),
                ("Visitante Over/Under 3.5",  "1h_corners_away_35", 3.5, "0", "0"),
            ]),
            ("Handicap de Corners (Local)", [
                ("Handicap -2.5", "corner_handicap_m25", -2.5, "0", "0"),
                ("Handicap -1.5", "corner_handicap_m15", -1.5, "0", "0"),
                ("Handicap -0.5", "corner_handicap",     -0.5, "0", "0"),
                ("Handicap +0.5", "corner_handicap_p05",  0.5, "0", "0"),
                ("Handicap +1.5", "corner_handicap_p15",  1.5, "0", "0"),
            ]),
            ("Total de Tarjetas", [
                ("Over/Under 2.5", "total_cards_25", 2.5, "0", "0"),
                ("Over/Under 3.5", "total_cards",    3.5, "0", "0"),
                ("Over/Under 4.5", "total_cards_45", 4.5, "0", "0"),
                ("Over/Under 5.5", "total_cards_55", 5.5, "0", "0"),
            ]),
            ("Tarjetas Equipo Local", [
                ("Over/Under 0.5", "cards_home_05", 0.5, "0", "0"),
                ("Over/Under 1.5", "cards_home_15", 1.5, "0", "0"),
                ("Over/Under 2.5", "cards_home_25", 2.5, "0", "0"),
            ]),
            ("Tarjetas Equipo Visitante", [
                ("Over/Under 0.5", "cards_away_05", 0.5, "0", "0"),
                ("Over/Under 1.5", "cards_away_15", 1.5, "0", "0"),
                ("Over/Under 2.5", "cards_away_25", 2.5, "0", "0"),
            ]),
        ]

        for group_title, lines in markets_config:
            self._build_market_block(left, group_title, lines)

        # Botón analizar
        btn_frame = tk.Frame(left, bg=BG_MEDIUM)
        btn_frame.pack(fill="x", padx=15, pady=10)

        tk.Button(
            btn_frame,
            text="▶  ANALIZAR PARTIDO",
            command=self._run_analysis,
            font=FONT_HEADER,
            bg=ACCENT, fg="white",
            activebackground="#c73652",
            relief="flat", bd=0,
            cursor="hand2",
            pady=10,
        ).pack(fill="x")

        tk.Button(
            btn_frame,
            text="  Limpiar formulario",
            command=self._clear_form,
            font=FONT_SMALL,
            bg=BG_LIGHT, fg=TEXT_GRAY,
            relief="flat", bd=0,
            cursor="hand2",
            pady=5,
        ).pack(fill="x", pady=(5, 0))

        # Panel derecho: resultado del análisis
        right = tk.Frame(frame, bg=BG_DARK)
        right.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)

        tk.Label(
            right, text="RESULTADO DEL ANÁLISIS",
            font=FONT_HEADER, bg=BG_DARK, fg=ACCENT2,
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Panel de picks rápidos
        self._picks_summary_frame = tk.Frame(right, bg=BG_DARK)
        self._picks_summary_frame.pack(fill="x", padx=10, pady=5)

        # Área de texto del análisis completo
        self._analysis_text = scrolledtext.ScrolledText(
            right,
            font=FONT_MONO,
            bg="#0d0d1a",
            fg=TEXT_WHITE,
            insertbackground=TEXT_WHITE,
            selectbackground=BG_LIGHT,
            wrap="word",
            relief="flat",
            bd=1,
        )
        self._analysis_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._analysis_text.configure(state="disabled")

        # Mensaje inicial
        self._set_analysis_text(
            "Completa el formulario de la izquierda y presiona '▶ ANALIZAR PARTIDO'.\n\n"
            "El sistema evaluará todos los módulos activos (B, C, D, F, G, A) y "
            "te indicará si hay picks ejecutables, PAPER-A o PASS.\n\n"
            "Consulta el archivo INSTRUCCIONES.txt para una guía detallada paso a paso."
        )

        return frame

    def _build_form_section(self, parent: tk.Frame, title: str, fields: list):
        """Construye una sección de campos del formulario."""
        tk.Label(
            parent, text=title, font=FONT_HEADER,
            bg=BG_MEDIUM, fg=ACCENT,
        ).pack(pady=(10, 3), padx=15, anchor="w")

        for label, key, default in fields:
            row = tk.Frame(parent, bg=BG_MEDIUM)
            row.pack(fill="x", padx=15, pady=1)

            tk.Label(
                row, text=label, font=FONT_SMALL,
                bg=BG_MEDIUM, fg=TEXT_GRAY, width=26, anchor="w",
            ).pack(side="left")

            var = tk.StringVar(value=default)
            entry = tk.Entry(
                row, textvariable=var, font=FONT_SMALL,
                bg=BG_DARK, fg=TEXT_WHITE,
                insertbackground=TEXT_WHITE,
                relief="flat", bd=1, width=10,
            )
            entry.pack(side="right", fill="x", expand=True)
            self._entry_vars[key] = var

    def _build_checkboxes(self, parent: tk.Frame, checks: list):
        """Construye la sección de checkboxes."""
        tk.Label(
            parent, text="OPCIONES", font=FONT_HEADER,
            bg=BG_MEDIUM, fg=ACCENT,
        ).pack(pady=(10, 3), padx=15, anchor="w")

        for label, key in checks:
            var = tk.BooleanVar(value=(key == "referee_verified" or key == "xg_verified"))
            cb = tk.Checkbutton(
                parent, text=label, variable=var,
                font=FONT_SMALL,
                bg=BG_MEDIUM, fg=TEXT_WHITE,
                selectcolor=BG_DARK,
                activebackground=BG_MEDIUM,
                activeforeground=TEXT_WHITE,
                anchor="w",
            )
            cb.pack(fill="x", padx=20, pady=1)
            self._check_vars[key] = var

    def _build_market_block(self, parent: tk.Frame, title: str, lines: list):
        """
        Construye un bloque de mercado con múltiples líneas Over/Under.

        Args:
            parent: frame contenedor
            title:  nombre del mercado (ej. "Total de Goles")
            lines:  lista de (label, market_key, threshold, default_over, default_under)
        """
        is_btts = (title.startswith("Ambos"))

        # Cabecera del mercado
        hdr = tk.Frame(parent, bg="#1a2a45")
        hdr.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(
            hdr, text=title, font=("Segoe UI", 9, "bold"),
            bg="#1a2a45", fg=BLUE, anchor="w",
        ).pack(side="left", padx=5, pady=2)

        # Columnas
        col = tk.Frame(parent, bg=BG_MEDIUM)
        col.pack(fill="x", padx=10)
        tk.Label(col, text="", font=FONT_SMALL,
                 bg=BG_MEDIUM, fg=TEXT_GRAY, width=20, anchor="w").pack(side="left", padx=(5, 0))
        tk.Label(col, text="Sí" if is_btts else "Over", font=FONT_SMALL,
                 bg=BG_MEDIUM, fg=TEXT_GRAY, width=7).pack(side="left")
        tk.Label(col, text="No" if is_btts else "Under", font=FONT_SMALL,
                 bg=BG_MEDIUM, fg=TEXT_GRAY, width=7).pack(side="left")

        for label, key, threshold, def_over, def_under in lines:
            row = tk.Frame(parent, bg=BG_MEDIUM)
            row.pack(fill="x", padx=10, pady=0)

            tk.Label(
                row, text=label, font=FONT_SMALL,
                bg=BG_MEDIUM, fg=TEXT_WHITE, width=20, anchor="w",
            ).pack(side="left", padx=(5, 0))

            over_var  = tk.StringVar(value=def_over)
            under_var = tk.StringVar(value=def_under)

            tk.Entry(
                row, textvariable=over_var, font=FONT_SMALL,
                bg=BG_DARK, fg=YELLOW, insertbackground=YELLOW,
                relief="flat", bd=1, width=7,
            ).pack(side="left", padx=2)

            tk.Entry(
                row, textvariable=under_var, font=FONT_SMALL,
                bg=BG_DARK, fg=YELLOW, insertbackground=YELLOW,
                relief="flat", bd=1, width=7,
            ).pack(side="left", padx=2)

            self._odds_vars[key] = {
                "over":      over_var,
                "under":     under_var,
                "threshold": tk.StringVar(
                    value=str(threshold) if threshold is not None else "0"
                ),
            }

    # ─────────────────────────────────────────────────────
    # PESTAÑA 2: HISTORIAL DE PICKS
    # ─────────────────────────────────────────────────────

    def _build_tab_historial(self) -> tk.Frame:
        """Pestaña de historial de picks y resolución."""
        frame = tk.Frame(self.notebook, bg=BG_DARK)

        # Título
        header = tk.Frame(frame, bg=BG_MEDIUM)
        header.pack(fill="x", padx=5, pady=5)

        tk.Label(
            header, text="HISTORIAL DE PICKS CG-0P",
            font=FONT_HEADER, bg=BG_MEDIUM, fg=ACCENT2,
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            header, text="↻ Actualizar",
            command=self._refresh_history,
            font=FONT_SMALL, bg=BG_LIGHT, fg=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=10, pady=5,
        ).pack(side="right", padx=10, pady=10)

        # Tabla de picks pendientes
        tk.Label(
            frame, text="PICKS PENDIENTES DE RESOLVER",
            font=FONT_HEADER, bg=BG_DARK, fg=YELLOW,
        ).pack(anchor="w", padx=15, pady=(10, 3))

        # Treeview para pendientes
        pending_frame = tk.Frame(frame, bg=BG_DARK)
        pending_frame.pack(fill="x", padx=10, pady=5)

        cols_pending = ("ID", "Partido", "Módulo", "Mercado", "Cuota", "Edge", "Stake")
        self._tree_pending = ttk.Treeview(
            pending_frame, columns=cols_pending, show="headings", height=6,
        )
        self._style_treeview()
        for col in cols_pending:
            self._tree_pending.heading(col, text=col)
            self._tree_pending.column(col, width=120, anchor="center")
        self._tree_pending.column("Partido", width=200)
        self._tree_pending.column("Mercado", width=180)

        scroll_p = ttk.Scrollbar(pending_frame, orient="vertical",
                                 command=self._tree_pending.yview)
        self._tree_pending.configure(yscrollcommand=scroll_p.set)
        self._tree_pending.pack(side="left", fill="x", expand=True)
        scroll_p.pack(side="right", fill="y")

        # Panel de resolución
        resolve_frame = tk.Frame(frame, bg=BG_MEDIUM)
        resolve_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            resolve_frame, text="RESOLVER PICK SELECCIONADO",
            font=FONT_HEADER, bg=BG_MEDIUM, fg=ACCENT,
        ).pack(anchor="w", padx=15, pady=(10, 5))

        row_res = tk.Frame(resolve_frame, bg=BG_MEDIUM)
        row_res.pack(fill="x", padx=15, pady=5)

        fields_res = [
            ("Resultado (W/L/V):", "res_resultado", "W"),
            ("Stake apostado (u):", "res_stake",    "1.0"),
            ("Cuota tomada:",       "res_cuota",    "0"),
            ("Corners local:",      "res_ck_home",  "0"),
            ("Corners visitante:",  "res_ck_away",  "0"),
            ("Tarjetas total:",     "res_cards",    "0"),
        ]
        self._resolve_vars = {}
        for label, key, default in fields_res:
            r = tk.Frame(row_res, bg=BG_MEDIUM)
            r.pack(side="left", padx=10)
            tk.Label(r, text=label, font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY).pack()
            var = tk.StringVar(value=default)
            tk.Entry(r, textvariable=var, font=FONT_BODY, bg=BG_DARK, fg=TEXT_WHITE,
                     relief="flat", width=8).pack()
            self._resolve_vars[key] = var

        notes_frame = tk.Frame(resolve_frame, bg=BG_MEDIUM)
        notes_frame.pack(fill="x", padx=15, pady=3)
        tk.Label(notes_frame, text="Notas post-match:", font=FONT_SMALL,
                 bg=BG_MEDIUM, fg=TEXT_GRAY).pack(anchor="w")
        self._resolve_notes = tk.Entry(notes_frame, font=FONT_BODY, bg=BG_DARK,
                                        fg=TEXT_WHITE, relief="flat")
        self._resolve_notes.pack(fill="x", pady=2)

        tk.Button(
            resolve_frame, text="✓  Guardar Resultado",
            command=self._resolve_selected_pick,
            font=FONT_BODY, bg=GREEN, fg="black",
            relief="flat", cursor="hand2", pady=8,
        ).pack(padx=15, pady=10, fill="x")

        # Historial resuelto
        tk.Label(
            frame, text="HISTORIAL RESUELTO (últimos 30)",
            font=FONT_HEADER, bg=BG_DARK, fg=TEXT_WHITE,
        ).pack(anchor="w", padx=15, pady=(10, 3))

        hist_frame = tk.Frame(frame, bg=BG_DARK)
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols_hist = ("Fecha", "Partido", "Mod.", "Mercado", "Cuota", "Edge", "Res.", "P&L")
        self._tree_history = ttk.Treeview(
            hist_frame, columns=cols_hist, show="headings", height=10,
        )
        for col in cols_hist:
            self._tree_history.heading(col, text=col)
            self._tree_history.column(col, width=110, anchor="center")
        self._tree_history.column("Partido", width=200)
        self._tree_history.column("Mercado", width=180)

        scroll_h = ttk.Scrollbar(hist_frame, orient="vertical",
                                  command=self._tree_history.yview)
        self._tree_history.configure(yscrollcommand=scroll_h.set)
        self._tree_history.pack(side="left", fill="both", expand=True)
        scroll_h.pack(side="right", fill="y")

        # Cargar datos
        self._refresh_history()
        return frame

    # ─────────────────────────────────────────────────────
    # PESTAÑA 3: MÉTRICAS
    # ─────────────────────────────────────────────────────

    def _build_tab_metricas(self) -> tk.Frame:
        """Pestaña de métricas y dashboard."""
        frame = tk.Frame(self.notebook, bg=BG_DARK)

        header = tk.Frame(frame, bg=BG_MEDIUM)
        header.pack(fill="x", padx=5, pady=5)

        tk.Label(
            header, text="DASHBOARD DE MÉTRICAS",
            font=FONT_HEADER, bg=BG_MEDIUM, fg=ACCENT2,
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            header, text="↻ Actualizar métricas",
            command=self._refresh_metrics,
            font=FONT_SMALL, bg=BG_LIGHT, fg=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=10, pady=5,
        ).pack(side="right", padx=10, pady=10)

        # Cards de métricas globales
        cards_frame = tk.Frame(frame, bg=BG_DARK)
        cards_frame.pack(fill="x", padx=10, pady=5)

        self._metric_labels = {}
        metric_cards = [
            ("Total Picks",    "total_picks",    "0",    BLUE),
            ("Win Rate",       "win_rate",        "0%",   GREEN),
            ("ROI",            "roi",             "0%",   GREEN),
            ("P&L Total",      "pl_total",        "0u",   GREEN),
            ("Edge Promedio",  "edge_avg",        "0 pp", YELLOW),
        ]
        for title, key, default, color in metric_cards:
            card = tk.Frame(cards_frame, bg=BG_MEDIUM, padx=15, pady=10)
            card.pack(side="left", fill="y", expand=True, padx=5, pady=5)

            tk.Label(card, text=title, font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY).pack()
            lbl = tk.Label(card, text=default, font=("Segoe UI", 18, "bold"),
                           bg=BG_MEDIUM, fg=color)
            lbl.pack()
            self._metric_labels[key] = lbl

        # Tabla de rendimiento por módulo
        tk.Label(
            frame, text="RENDIMIENTO POR MÓDULO",
            font=FONT_HEADER, bg=BG_DARK, fg=ACCENT,
        ).pack(anchor="w", padx=15, pady=(15, 3))

        mod_frame = tk.Frame(frame, bg=BG_DARK)
        mod_frame.pack(fill="x", padx=10, pady=5)

        cols_mod = ("Módulo", "Nombre", "Picks", "Hits", "Win Rate", "P&L", "Brier")
        self._tree_modules = ttk.Treeview(
            mod_frame, columns=cols_mod, show="headings", height=7,
        )
        self._style_treeview()
        for col in cols_mod:
            self._tree_modules.heading(col, text=col)
            self._tree_modules.column(col, width=110, anchor="center")
        self._tree_modules.column("Nombre", width=200, anchor="w")
        self._tree_modules.pack(fill="x", padx=0)

        # Curva de bankroll (texto)
        tk.Label(
            frame, text="CURVA DE BANKROLL",
            font=FONT_HEADER, bg=BG_DARK, fg=ACCENT,
        ).pack(anchor="w", padx=15, pady=(15, 3))

        self._bankroll_canvas = tk.Canvas(
            frame, bg="#0d0d1a", height=180, relief="flat",
        )
        self._bankroll_canvas.pack(fill="x", padx=10, pady=5)

        # Anti-recency alert
        self._anti_recency_label = tk.Label(
            frame, text="",
            font=FONT_BODY, bg=BG_DARK, fg=YELLOW,
        )
        self._anti_recency_label.pack(padx=15, pady=5, anchor="w")

        self._refresh_metrics()
        return frame

    # ─────────────────────────────────────────────────────
    # PESTAÑA 4: PATCHES
    # ─────────────────────────────────────────────────────

    def _build_tab_patches(self) -> tk.Frame:
        """Pestaña de patches activos del sistema."""
        frame = tk.Frame(self.notebook, bg=BG_DARK)

        tk.Label(
            frame, text="PATCHES ACTIVOS — v1.2.7",
            font=FONT_HEADER, bg=BG_DARK, fg=ACCENT,
        ).pack(padx=15, pady=(15, 5), anchor="w")

        tk.Label(
            frame,
            text="Los patches son correcciones incrementales derivadas de análisis post-match.\n"
                 "Principio: los patches NUNCA se eliminan — se acumulan permanentemente.",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY, justify="left",
        ).pack(padx=15, pady=3, anchor="w")

        # Lista de patches
        patches_frame = tk.Frame(frame, bg=BG_DARK)
        patches_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._patches_text = scrolledtext.ScrolledText(
            patches_frame,
            font=FONT_MONO, bg="#0d0d1a", fg=TEXT_WHITE,
            wrap="word", relief="flat",
        )
        self._patches_text.pack(fill="both", expand=True)
        self._load_patches_info()

        return frame

    def _load_patches_info(self):
        """Carga la información de patches en el área de texto."""
        try:
            from cg0p.config.patches import PATCHES
            text = ""
            for patch_id, patch in PATCHES.items():
                text += f"{'─'*60}\n"
                text += f"🔧 {patch_id}\n"
                text += f"   Versión:  {patch.get('version','?')}\n"
                text += f"   Módulo:   {patch.get('module_affected','?')}\n"
                if patch.get("origin_match"):
                    text += f"   Origen:   {patch.get('origin_match')}\n"
                if patch.get("origin_result"):
                    text += f"   Resultado:{patch.get('origin_result')}\n"
                text += f"   Regla:    {patch.get('rule','')[:200]}\n\n"
        except Exception as e:
            text = f"Error al cargar patches: {e}\n\nAsegúrate de que el módulo cg0p esté instalado correctamente."

        self._patches_text.configure(state="normal")
        self._patches_text.delete("1.0", "end")
        self._patches_text.insert("1.0", text)
        self._patches_text.configure(state="disabled")

    # ─────────────────────────────────────────────────────
    # PESTAÑA 5: ACTUALIZAR DATOS
    # ─────────────────────────────────────────────────────

    def _build_tab_actualizar(self) -> tk.Frame:
        """Pestaña para actualizar CSVs y buscar partidos próximos en SharpAPI."""
        import threading

        frame = tk.Frame(self.notebook, bg=BG_DARK)

        # ── Título ─────────────────────────────────────────
        tk.Label(
            frame, text="ACTUALIZAR DATOS",
            font=FONT_HEADER, bg=BG_DARK, fg=ACCENT,
        ).pack(padx=15, pady=(12, 2), anchor="w")

        tk.Label(
            frame,
            text="Descarga datos históricos de football-data.co.uk y consulta cuotas de partidos próximos con SharpAPI.",
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY,
        ).pack(padx=15, pady=(0, 8), anchor="w")

        # ── Contenedor horizontal ───────────────────────────
        body = tk.Frame(frame, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        # ── Panel izquierdo: CSVs ───────────────────────────
        left = tk.LabelFrame(
            body, text=" 📂 Datos Históricos (CSV) ",
            font=FONT_SMALL, bg=BG_DARK, fg=BLUE, labelanchor="nw",
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Botones por liga
        ligas = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]

        btns_frame = tk.Frame(left, bg=BG_DARK)
        btns_frame.pack(fill="x", padx=8, pady=8)

        for liga in ligas:
            row = tk.Frame(btns_frame, bg=BG_DARK)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=liga, font=FONT_SMALL,
                     bg=BG_DARK, fg=TEXT_WHITE, width=18, anchor="w").pack(side="left")
            tk.Button(
                row, text="Temporada actual",
                font=FONT_SMALL, bg=BG_LIGHT, fg=TEXT_WHITE,
                relief="flat", cursor="hand2", pady=2,
                command=lambda l=liga: threading.Thread(
                    target=self._update_csv_season, args=(l,), daemon=True
                ).start(),
            ).pack(side="left", padx=4)
            tk.Button(
                row, text="Todas las temporadas",
                font=FONT_SMALL, bg="#1a3a5c", fg=TEXT_GRAY,
                relief="flat", cursor="hand2", pady=2,
                command=lambda l=liga: threading.Thread(
                    target=self._update_csv_all, args=(l,), daemon=True
                ).start(),
            ).pack(side="left", padx=2)

        # Botón "Actualizar todo"
        tk.Button(
            left, text="⬇️  ACTUALIZAR TODO (temporada actual)",
            font=FONT_BODY, bg=ACCENT2, fg="white",
            relief="flat", cursor="hand2", pady=6,
            command=lambda: threading.Thread(
                target=self._update_all_leagues, daemon=True
            ).start(),
        ).pack(fill="x", padx=8, pady=(4, 8))

        # Estado de actualización
        self._update_status_var = tk.StringVar(value="Listo.")
        tk.Label(
            left, textvariable=self._update_status_var,
            font=FONT_SMALL, bg=BG_DARK, fg=YELLOW, wraplength=380, justify="left",
        ).pack(padx=8, pady=2, anchor="w")

        # Tabla de estado de CSVs
        tk.Label(left, text="Estado de archivos locales:",
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY).pack(padx=8, pady=(8, 2), anchor="w")

        csv_table_frame = tk.Frame(left, bg=BG_DARK)
        csv_table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        cols = ("Liga", "Archivo", "Partidos", "Actualizado")
        self._csv_tree = ttk.Treeview(
            csv_table_frame, columns=cols, show="headings",
            height=8, style="Treeview",
        )
        for col in cols:
            self._csv_tree.heading(col, text=col)
            self._csv_tree.column(col, width=100 if col != "Liga" else 130, anchor="w")

        csv_scroll = ttk.Scrollbar(csv_table_frame, orient="vertical", command=self._csv_tree.yview)
        self._csv_tree.configure(yscrollcommand=csv_scroll.set)
        csv_scroll.pack(side="right", fill="y")
        self._csv_tree.pack(side="left", fill="both", expand=True)

        tk.Button(
            left, text="↻ Refrescar tabla",
            font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY,
            relief="flat", cursor="hand2",
            command=self._refresh_csv_table,
        ).pack(padx=8, pady=(0, 8))

        self._refresh_csv_table()

        # ── Panel derecho: Odds API ─────────────────────────
        right = tk.LabelFrame(
            body, text=" 🎯 🎯 Cuotas Próximos Partidos (SharpAPI) ",
            font=FONT_SMALL, bg=BG_DARK, fg=YELLOW, labelanchor="nw",
        )
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # Liga selector
        top_row = tk.Frame(right, bg=BG_DARK)
        top_row.pack(fill="x", padx=8, pady=8)

        tk.Label(top_row, text="Liga:", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_WHITE).pack(side="left")

        self._odds_liga_var = tk.StringVar(value="Premier League")
        liga_combo = ttk.Combobox(
            top_row, textvariable=self._odds_liga_var,
            values=ligas + ["Champions League", "Europa League"],
            state="readonly", width=22, font=FONT_SMALL,
        )
        liga_combo.pack(side="left", padx=6)

        tk.Button(
            top_row, text="🔍 Buscar Partidos",
            font=FONT_SMALL, bg=ACCENT2, fg="white",
            relief="flat", cursor="hand2", pady=4, padx=8,
            command=lambda: threading.Thread(
                target=self._fetch_odds_matches, daemon=True
            ).start(),
        ).pack(side="left", padx=4)

        # Estado de la API
        self._odds_status_var = tk.StringVar(value="Selecciona una liga y pulsa Buscar Partidos.")
        tk.Label(
            right, textvariable=self._odds_status_var,
            font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY, wraplength=360, justify="left",
        ).pack(padx=8, pady=2, anchor="w")

        # Lista de partidos
        tk.Label(right, text="Partidos encontrados:",
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY).pack(padx=8, pady=(6, 2), anchor="w")

        matches_frame = tk.Frame(right, bg=BG_DARK)
        matches_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        match_scroll = ttk.Scrollbar(matches_frame, orient="vertical")
        self._matches_listbox = tk.Listbox(
            matches_frame, font=FONT_SMALL,
            bg=BG_MEDIUM, fg=TEXT_WHITE, selectbackground=BG_LIGHT,
            relief="flat", activestyle="dotbox",
            yscrollcommand=match_scroll.set,
        )
        match_scroll.config(command=self._matches_listbox.yview)
        match_scroll.pack(side="right", fill="y")
        self._matches_listbox.pack(side="left", fill="both", expand=True)

        # Almacena los datos completos de los partidos
        self._odds_matches_data = []

        # Detalle de cuotas del partido seleccionado
        tk.Label(right, text="Cuotas del partido seleccionado:",
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_GRAY).pack(padx=8, pady=(4, 2), anchor="w")

        self._odds_detail_var = tk.StringVar(value="—")
        tk.Label(
            right, textvariable=self._odds_detail_var,
            font=FONT_MONO, bg=BG_MEDIUM, fg=GREEN,
            justify="left", wraplength=400, relief="flat",
        ).pack(padx=8, fill="x")

        self._matches_listbox.bind("<<ListboxSelect>>", self._on_match_selected)

        # Botón cargar en análisis
        tk.Button(
            right, text="→ Cargar Partido en Análisis PRE",
            font=FONT_BODY, bg=ACCENT, fg="white",
            relief="flat", cursor="hand2", pady=6,
            command=self._load_match_to_analisis,
        ).pack(fill="x", padx=8, pady=(6, 10))

        return frame

    # ── Callbacks del tab Actualizar ───────────────────────

    def _update_csv_season(self, league: str):
        """Descarga el CSV de la temporada actual para una liga (en hilo)."""
        try:
            from cg0p.data.updater import update_current_season
        except ImportError:
            self._update_status_var.set("❌ No se encontró cg0p/data/updater.py")
            return

        self._update_status_var.set(f"⏳ Actualizando {league}...")
        result = update_current_season(
            league,
            progress_cb=lambda msg: self._update_status_var.set(msg),
        )
        self._update_status_var.set(result.get("msg", ""))
        self._refresh_csv_table()

    def _update_csv_all(self, league: str):
        """Descarga todas las temporadas de una liga (en hilo)."""
        try:
            from cg0p.data.updater import update_all_seasons
        except ImportError:
            self._update_status_var.set("❌ No se encontró cg0p/data/updater.py")
            return

        self._update_status_var.set(f"⏳ Descargando todas las temporadas de {league}...")
        results = update_all_seasons(
            league,
            progress_cb=lambda msg: self._update_status_var.set(msg),
        )
        ok  = sum(1 for r in results if r.get("ok"))
        total = len(results)
        self._update_status_var.set(f"✅ {league}: {ok}/{total} archivos descargados")
        self._refresh_csv_table()

    def _update_all_leagues(self):
        """Actualiza la temporada actual de todas las ligas (en hilo)."""
        try:
            from cg0p.data.updater import update_all_leagues_current
        except ImportError:
            self._update_status_var.set("❌ No se encontró cg0p/data/updater.py")
            return

        self._update_status_var.set("⏳ Actualizando todas las ligas...")
        results = update_all_leagues_current(
            progress_cb=lambda msg: self._update_status_var.set(msg),
        )
        ok = sum(1 for r in results if r.get("ok"))
        self._update_status_var.set(f"✅ Actualización completa: {ok}/{len(results)} ligas OK")
        self._refresh_csv_table()

    def _refresh_csv_table(self):
        """Recarga la tabla de estado de CSVs locales."""
        try:
            from cg0p.data.updater import get_csv_status
        except ImportError:
            return

        status_list = get_csv_status()

        self._csv_tree.delete(*self._csv_tree.get_children())
        for s in status_list:
            icon = "✅" if s["exists"] else "❌"
            rows = str(s["rows"]) if s["rows"] > 0 else "—"
            self._csv_tree.insert(
                "", "end",
                values=(s["league"], f"{icon} {s['file']}", rows, s["mtime"]),
            )

    def _fetch_odds_matches(self):
        """Llama a SharpAPI y puebla la lista de partidos (en hilo)."""
        try:
            from cg0p.data.updater import fetch_upcoming_matches
        except ImportError:
            self._odds_status_var.set("❌ No se encontró cg0p/data/updater.py")
            return

        # Leer API key desde settings centralizado
        try:
            from cg0p.config.settings import SHARP_API_KEY as API_KEY
        except ImportError:
            API_KEY = ""

        if not API_KEY:
            self._odds_status_var.set("❌ API Key no configurada en config.py")
            return

        liga = self._odds_liga_var.get()
        self._odds_status_var.set(f"⏳ Buscando partidos de {liga}...")

        result = fetch_upcoming_matches(liga, API_KEY)

        self._odds_matches_data = result.get("matches", [])
        self._matches_listbox.delete(0, "end")

        if not result.get("ok"):
            self._odds_status_var.set(result.get("msg", "Error"))
            return

        for match in self._odds_matches_data:
            self._matches_listbox.insert("end", match.get("label", ""))

        self._odds_status_var.set(result.get("msg", ""))

    def _on_match_selected(self, event=None):
        """Muestra las cuotas del partido seleccionado."""
        sel = self._matches_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._odds_matches_data):
            return

        match = self._odds_matches_data[idx]
        odds  = match.get("odds", {})

        lines = []

        # 1X2
        if odds.get("h2h_home"):
            lines.append(
                f"1X2     {match['home']} {odds['h2h_home']:.2f}  "
                f"X {odds.get('h2h_draw', 0):.2f}  "
                f"{match['away']} {odds.get('h2h_away', 0):.2f}"
            )

        # Total de goles — mostrar todas las líneas disponibles
        for line in (1.5, 2.5, 3.5, 4.5, 5.5):
            o = odds.get(f"total_goals_over_{line}", 0)
            u = odds.get(f"total_goals_under_{line}", 0)
            if o and u:
                lines.append(f"Goles   O/U {line}   Over {o:.2f}  Under {u:.2f}")

        # BTTS
        if odds.get("btts_yes"):
            lines.append(
                f"BTTS    Sí {odds['btts_yes']:.2f}  "
                f"No {odds.get('btts_no', 0):.2f}"
            )

        # Total corners
        for line in (8.5, 9.5, 10.5, 11.5):
            o = odds.get(f"total_corners_over_{line}", 0)
            u = odds.get(f"total_corners_under_{line}", 0)
            if o and u:
                lines.append(f"Corners O/U {line}  Over {o:.2f}  Under {u:.2f}")

        # Total tarjetas
        for line in (2.5, 3.5, 4.5, 5.5):
            o = odds.get(f"total_cards_over_{line}", 0)
            u = odds.get(f"total_cards_under_{line}", 0)
            if o and u:
                lines.append(f"Tarjetas O/U {line}  Over {o:.2f}  Under {u:.2f}")

        if not lines:
            lines.append("Sin cuotas — la API no devolvió mercados para este partido")
            lines.append(f"Mercados recibidos: {list(odds.keys())[:8]}")

        self._odds_detail_var.set("\n".join(lines))

    def _load_match_to_analisis(self):
        """Carga el partido seleccionado en la pestaña de Análisis PRE."""
        sel = self._matches_listbox.curselection()
        if not sel:
            self._odds_status_var.set("⚠️ Selecciona un partido primero.")
            return

        idx = sel[0]
        if idx >= len(self._odds_matches_data):
            return

        match = self._odds_matches_data[idx]
        odds  = match.get("odds", {})
        liga  = self._odds_liga_var.get()

        # Rellenar campos básicos del partido
        if "liga" in self._entry_vars:
            self._entry_vars["liga"].set(liga)
        if "home_team" in self._entry_vars:
            self._entry_vars["home_team"].set(match.get("home", ""))
        if "away_team" in self._entry_vars:
            self._entry_vars["away_team"].set(match.get("away", ""))
        if "date" in self._entry_vars:
            self._entry_vars["date"].set(match.get("date", ""))

        # Rellenar cuotas en _odds_vars
        def set_odds(market_key: str, direction: str, value):
            v = float(value) if value else 0
            if v > 1.0 and market_key in self._odds_vars:
                if direction in self._odds_vars[market_key]:
                    self._odds_vars[market_key][direction].set(f"{v:.2f}")

        # Total Goles — mapear líneas de la API a los keys del panel
        for line_val in ("1.5", "2.5", "3.5", "4.5", "5.5"):
            k_suffix = line_val.replace(".", "")
            set_odds(f"goals_under_{k_suffix}", "over",
                     odds.get(f"total_goals_over_{line_val}", 0))
            set_odds(f"goals_under_{k_suffix}", "under",
                     odds.get(f"total_goals_under_{line_val}", 0))
        # Fallback: si la API solo devolvió una línea (2.5)
        if odds.get("total_goals_over") and not odds.get("total_goals_over_2.5"):
            set_odds("goals_under_25", "over",  odds.get("total_goals_over", 0))
            set_odds("goals_under_25", "under", odds.get("total_goals_under", 0))

        # BTTS
        set_odds("btts", "over",  odds.get("btts_yes", 0))
        set_odds("btts", "under", odds.get("btts_no", 0))

        # Total Corners
        for line_val in ("8.5", "9.5", "10.5", "11.5"):
            k_suffix = line_val.replace(".", "")
            set_odds(f"total_corners_{k_suffix}", "over",
                     odds.get(f"total_corners_over_{line_val}", 0))
            set_odds(f"total_corners_{k_suffix}", "under",
                     odds.get(f"total_corners_under_{line_val}", 0))

        # Corners por equipo
        for side in ("home", "away"):
            for line_val in ("3.5", "4.5", "5.5", "6.5"):
                k_suffix = line_val.replace(".", "")
                base = f"team_corners_{side}"
                gui_key = base if line_val == "4.5" else f"{base}_{k_suffix}"
                set_odds(gui_key, "over",
                         odds.get(f"{base}_over_{line_val}", 0))
                set_odds(gui_key, "under",
                         odds.get(f"{base}_under_{line_val}", 0))

        # Total Tarjetas
        for line_val in ("2.5", "3.5", "4.5", "5.5"):
            k_suffix = line_val.replace(".", "")
            base = "total_cards" if line_val == "3.5" else f"total_cards_{k_suffix}"
            set_odds(base, "over",  odds.get(f"total_cards_over_{line_val}", 0))
            set_odds(base, "under", odds.get(f"total_cards_under_{line_val}", 0))

        # Cambiar a pestaña Análisis PRE
        self.notebook.select(self._tab_analisis)

        # Lanzar autocompletado
        self._autofill_form()

        self._set_status(
            f"Partido cargado: {match.get('home')} vs {match.get('away')} ({liga})"
        )

    # ─────────────────────────────────────────────────────
    # BARRA DE ESTADO
    # ─────────────────────────────────────────────────────

    def _build_statusbar(self):
        """Construye la barra de estado inferior."""
        status_frame = tk.Frame(self, bg=BG_MEDIUM, height=25)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self._status_var = tk.StringVar(value="Sistema listo — CG-0P v1.2.7")
        tk.Label(
            status_frame,
            textvariable=self._status_var,
            font=FONT_SMALL, bg=BG_MEDIUM, fg=TEXT_GRAY,
        ).pack(side="left", padx=15)

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    # ─────────────────────────────────────────────────────
    # LÓGICA DE ANÁLISIS
    # ─────────────────────────────────────────────────────

    def _run_analysis(self):
        """Ejecuta el análisis del partido con los datos del formulario."""
        if not self._cg0p_available:
            messagebox.showerror(
                "Error de importación",
                f"No se pudieron cargar los módulos CG-0P:\n{self._import_error}\n\n"
                "Asegúrate de que todas las dependencias estén instaladas.\n"
                "Ejecuta: pip install -r requirements.txt",
            )
            return

        self._set_status("Analizando partido...")

        try:
            match_data, odds_data, proxy_mode = self._collect_form_data()
            result = self._run_pipeline(match_data, odds_data, proxy_mode=proxy_mode)
            analysis_text = self._format_analysis(result)

            self._set_analysis_text(analysis_text)
            self._update_picks_summary(result)

            # Guardar en DB si hay picks
            if result.get("picks") or result.get("paper_a"):
                self._save_result_to_db(result)

            n_picks = len(result.get("picks", []))
            n_paper = len(result.get("paper_a", []))
            self._set_status(f"Análisis completado — {n_picks} PICK(S) | {n_paper} PAPER-A")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self._set_analysis_text(f"ERROR durante el análisis:\n\n{error_msg}")
            self._set_status(f"Error: {str(e)[:60]}")
            messagebox.showerror("Error en análisis", str(e))

    def _autofill_form(self):
        """
        Auto-rellena el formulario con datos históricos de los CSV locales.
        El usuario solo necesita haber ingresado: Liga, Equipo Local, Equipo Visitante.
        """
        liga      = self._entry_vars.get("liga",      tk.StringVar()).get().strip()
        home      = self._entry_vars.get("home_team", tk.StringVar()).get().strip()
        away      = self._entry_vars.get("away_team", tk.StringVar()).get().strip()
        referee   = self._entry_vars.get("referee_name", tk.StringVar()).get().strip()

        if not liga or not home or not away:
            self._autofill_status.config(
                text="⚠️  Ingresa Liga, Equipo Local y Equipo Visitante antes de autocompletar.",
                fg=YELLOW,
            )
            return

        self._autofill_status.config(
            text="⏳  Buscando datos en CSVs históricos...", fg=YELLOW
        )
        self.update_idletasks()

        try:
            from cg0p.data.fetcher import fetch_match_data
        except ImportError as e:
            self._autofill_status.config(
                text=f"❌ Error importando fetcher: {e}", fg=RED_COLOR
            )
            return

        data = fetch_match_data(home, away, liga, referee)

        if "error" in data:
            self._autofill_status.config(text=f"❌ {data['error']}", fg=RED_COLOR)
            return

        # ── Rellenar campos numéricos ──────────────────────
        field_map = {
            "home_corners_avg":          "home_corners_avg",
            "away_corners_avg":          "away_corners_avg",
            "home_corners_conceded":     "home_corners_conceded",
            "away_corners_conceded":     "away_corners_conceded",
            "home_corners_last5":        "home_corners_last5",
            "away_corners_last5":        "away_corners_last5",
            "home_xg":                   "home_xg",
            "away_xg":                   "away_xg",
            "home_xga":                  "home_xga",
            "away_xga":                  "away_xga",
            "home_btts_pct_last10":      "home_btts_pct_last10",
            "away_btts_pct_last10":      "away_btts_pct_last10",
            "home_clean_sheet_pct":      "home_clean_sheet_pct",
            "away_clean_sheet_pct":      "away_clean_sheet_pct",
            "referee_cards_avg":         "referee_cards_avg",
            "referee_reds_avg":          "referee_reds_avg",
            "referee_penalties_avg":     "referee_penalties_avg",
            "away_losing_streak":        "away_losing_streak",
            "away_squad_quality_percentile": "away_squad_quality_percentile",
        }
        for data_key, form_key in field_map.items():
            val = data.get(data_key)
            if val is not None and form_key in self._entry_vars:
                self._entry_vars[form_key].set(str(val))

        # Corregir nombres de equipos si hubo fuzzy match
        if data.get("home_team_matched") and "home_team" in self._entry_vars:
            self._entry_vars["home_team"].set(data["home_team_matched"])
        if data.get("away_team_matched") and "away_team" in self._entry_vars:
            self._entry_vars["away_team"].set(data["away_team_matched"])

        # Mostrar nota de resultado
        note = data.get("_note", "")
        warning = data.get("_warning", "")
        status_text = note.split("\n")[0] if note else "✅ Datos completados."
        if warning:
            status_text += f"\n⚠️ {warning}"
        self._autofill_status.config(text=status_text, fg=GREEN)
        self._set_status(f"Autocompletado: {home} vs {away} ({liga})")

    def _collect_form_data(self) -> tuple:
        """Recopila los datos del formulario y construye los dicts."""
        def get_float(key, default=0.0):
            try:
                return float(self._entry_vars[key].get())
            except (ValueError, KeyError):
                return default

        def get_int(key, default=0):
            try:
                return int(self._entry_vars[key].get())
            except (ValueError, KeyError):
                return default

        def get_bool(key, default=False):
            try:
                return self._check_vars[key].get()
            except KeyError:
                return default

        match_data = {
            "liga":          self._entry_vars.get("liga", tk.StringVar()).get(),
            "league":        self._entry_vars.get("liga", tk.StringVar()).get(),
            "home_team":     self._entry_vars.get("home_team", tk.StringVar()).get(),
            "away_team":     self._entry_vars.get("away_team", tk.StringVar()).get(),
            "date":          self._entry_vars.get("date", tk.StringVar()).get(),

            # Corners
            "home_corners_avg":        get_float("home_corners_avg",     5.0),
            "away_corners_avg":        get_float("away_corners_avg",     4.5),
            "home_corners_conceded":   get_float("home_corners_conceded", 4.5),
            "away_corners_conceded":   get_float("away_corners_conceded", 5.0),
            "home_corners_last5":      get_float("home_corners_last5",   5.0),
            "away_corners_last5":      get_float("away_corners_last5",   4.5),

            # xG y BTTS
            "home_xg":                 get_float("home_xg",              1.3),
            "away_xg":                 get_float("away_xg",              1.1),
            "home_xga":                get_float("home_xga",             1.2),
            "away_xga":                get_float("away_xga",             1.0),
            "home_btts_pct_last10":    get_float("home_btts_pct_last10", 0.55),
            "away_btts_pct_last10":    get_float("away_btts_pct_last10", 0.55),
            "home_clean_sheet_pct":    get_float("home_clean_sheet_pct", 0.30),
            "away_clean_sheet_pct":    get_float("away_clean_sheet_pct", 0.25),

            # Árbitro
            "referee_cards_avg":       get_float("referee_cards_avg",    3.5),
            "referee_reds_avg":        get_float("referee_reds_avg",     0.10),
            "referee_penalties_avg":   get_float("referee_penalties_avg",0.15),

            # Flags
            "home_early_goal_prob":    get_float("home_early_goal_prob", 0.20),
            "away_early_goal_prob":    get_float("away_early_goal_prob", 0.15),
            "away_losing_streak":      get_int("away_losing_streak",      0),
            "away_squad_quality_percentile": get_int("away_squad_quality_percentile", 50),

            # Checks
            "referee_verified":             get_bool("referee_verified",             True),
            "away_manager_under_pressure":  get_bool("away_manager_under_pressure",  False),
            "h2h_competitive":              get_bool("h2h_competitive",              False),
            "xg_verified":                  get_bool("xg_verified",                 True),
            "rivalry_flag":                 get_bool("rivalry_flag",                 False),
            "projected_tight_70":           get_bool("projected_tight_70",           False),

            # Defaults para campos que el pipeline necesita
            "lineup_confidence":       3,
            "expected_goals_total":    get_float("home_xg", 1.3) + get_float("away_xg", 1.1),
            "h2h": {},
        }

        proxy_mode = get_bool("proxy_mode", False)

        # Construir odds_data
        odds_data = {}
        for market_key, vars_dict in self._odds_vars.items():
            try:
                o_over  = float(vars_dict["over"].get())
                o_under = float(vars_dict["under"].get())
                thresh  = float(vars_dict["threshold"].get()) if vars_dict.get("threshold") else 0

                if o_over > 1.0 and o_under > 1.0:
                    odds_data[market_key] = {
                        "over":      o_over,
                        "under":     o_under,
                        "threshold": thresh,
                    }
            except (ValueError, TypeError):
                continue

        return match_data, odds_data, proxy_mode

    def _save_result_to_db(self, result: dict):
        """Guarda los picks del análisis en la base de datos."""
        try:
            history = self._PickHistory()
            for pick in result.get("picks", []):
                history.save_pick(result, pick)
            for pa in result.get("paper_a", []):
                history.save_pick(result, pa)
        except Exception as e:
            self._set_status(f"Aviso: no se pudo guardar en DB — {str(e)[:40]}")

    def _update_picks_summary(self, result: dict):
        """Actualiza el panel de resumen de picks."""
        for widget in self._picks_summary_frame.winfo_children():
            widget.destroy()

        picks   = result.get("picks", [])
        paper_a = result.get("paper_a", [])
        ci      = result.get("chaos_index", 0)

        # CI badge
        ci_colors = {0: BLUE, 1: BLUE, 2: YELLOW, 3: YELLOW, 4: RED_COLOR, 5: RED_COLOR}
        ci_frame = tk.Frame(self._picks_summary_frame, bg=ci_colors.get(ci, BLUE), padx=8, pady=4)
        ci_frame.pack(side="left", padx=5)
        tk.Label(ci_frame, text=f"CI = {ci}", font=FONT_BODY, bg=ci_colors.get(ci, BLUE),
                 fg="white").pack()

        if picks:
            for pick in picks:
                pf = tk.Frame(self._picks_summary_frame, bg=GREEN, padx=10, pady=5)
                pf.pack(side="left", padx=5)
                tk.Label(
                    pf,
                    text=f"✅ [{pick.get('module','?')}] {pick.get('market_label','?')[:25]}\n"
                         f"@{pick.get('odds',0):.2f} | Edge:{pick.get('edge_pp',0):.1f}pp | Stake:{pick.get('stake',0):.1f}u",
                    font=FONT_SMALL, bg=GREEN, fg="black",
                ).pack()
        else:
            ef = tk.Frame(self._picks_summary_frame, bg="#333", padx=10, pady=5)
            ef.pack(side="left", padx=5)
            tk.Label(ef, text="❌ Sin picks ejecutar", font=FONT_SMALL, bg="#333",
                     fg=TEXT_GRAY).pack()

        if paper_a:
            for pa in paper_a:
                pf = tk.Frame(self._picks_summary_frame, bg=BG_LIGHT, padx=10, pady=5)
                pf.pack(side="left", padx=5)
                tk.Label(
                    pf,
                    text=f"📋 PAPER-A [{pa.get('module','?')}]\n"
                         f"{pa.get('market_label','')[:25]}",
                    font=FONT_SMALL, bg=BG_LIGHT, fg=YELLOW,
                ).pack()

    def _set_analysis_text(self, text: str):
        """Actualiza el área de texto del análisis."""
        self._analysis_text.configure(state="normal")
        self._analysis_text.delete("1.0", "end")
        self._analysis_text.insert("1.0", text)
        self._analysis_text.configure(state="disabled")

    def _clear_form(self):
        """Limpia el formulario."""
        for key, var in self._entry_vars.items():
            var.set("")
        for key, var in self._check_vars.items():
            var.set(False)
        self._set_analysis_text("Formulario limpiado. Ingresa nuevos datos.")
        self._set_status("Formulario limpiado.")

    # ─────────────────────────────────────────────────────
    # LÓGICA DE HISTORIAL
    # ─────────────────────────────────────────────────────

    def _refresh_history(self):
        """Actualiza las tablas de historial."""
        if not self._cg0p_available:
            return
        try:
            history = self._PickHistory()

            # Pendientes
            for row in self._tree_pending.get_children():
                self._tree_pending.delete(row)

            for pick in history.get_pending_picks():
                self._tree_pending.insert("", "end", values=(
                    pick.get("id"),
                    pick.get("partido", "")[:30],
                    pick.get("modulo", ""),
                    pick.get("mercado_label", "")[:25],
                    f"{pick.get('cuota', 0):.2f}",
                    f"{pick.get('edge_pp', 0):.1f} pp",
                    f"{pick.get('stake', 0):.1f}u",
                ))

            # Resueltos
            for row in self._tree_history.get_children():
                self._tree_history.delete(row)

            for pick in history.get_resolved_picks(limit=30):
                result = pick.get("resultado", "?")
                pl     = pick.get("pl_unidades", 0) or 0
                tag    = "hit" if result == "W" else "miss" if result == "L" else ""

                self._tree_history.insert("", "end", values=(
                    pick.get("fecha_analisis", "")[:10],
                    pick.get("partido", "")[:25],
                    pick.get("modulo", ""),
                    pick.get("mercado_label", "")[:20],
                    f"{pick.get('cuota', 0):.2f}",
                    f"{pick.get('edge_pp', 0):.1f} pp",
                    result,
                    f"{pl:+.2f}u",
                ), tags=(tag,))

            self._tree_history.tag_configure("hit",  foreground=GREEN)
            self._tree_history.tag_configure("miss", foreground=RED_COLOR)

        except Exception as e:
            self._set_status(f"Error cargando historial: {str(e)[:50]}")

    def _resolve_selected_pick(self):
        """Resuelve el pick seleccionado en la tabla."""
        selection = self._tree_pending.selection()
        if not selection:
            messagebox.showwarning("Selección", "Selecciona un pick de la tabla primero.")
            return

        item = self._tree_pending.item(selection[0])
        pick_id = item["values"][0]

        try:
            resultado = self._resolve_vars["res_resultado"].get().upper()
            stake     = float(self._resolve_vars["res_stake"].get())
            cuota     = float(self._resolve_vars["res_cuota"].get())
            notas     = self._resolve_notes.get()

            if resultado == "W":
                pl = round(stake * (cuota - 1), 3)
            elif resultado == "L":
                pl = -stake
            else:
                pl = 0.0

            history = self._PickHistory()
            history.resolve_pick(int(pick_id), resultado, pl, notas)

            self._refresh_history()
            self._refresh_metrics()
            self._set_status(f"Pick #{pick_id} resuelto: {resultado} ({pl:+.2f}u)")
            messagebox.showinfo("Resuelto", f"Pick #{pick_id} guardado como {resultado} ({pl:+.2f}u)")

        except ValueError as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ─────────────────────────────────────────────────────
    # LÓGICA DE MÉTRICAS
    # ─────────────────────────────────────────────────────

    def _refresh_metrics(self):
        """Actualiza el dashboard de métricas."""
        if not self._cg0p_available:
            return
        try:
            metrics = self._SystemMetrics()
            dashboard = metrics.get_full_dashboard()
            stats = dashboard.get("global_stats", {})

            # Actualizar cards
            total = stats.get("total_picks", 0)
            wr    = stats.get("win_rate_pct", 0)
            roi   = stats.get("roi_pct", 0)
            pl    = stats.get("pl_total", 0)
            edge  = stats.get("edge_promedio_pp", 0)

            self._metric_labels["total_picks"].config(text=str(total))
            self._metric_labels["win_rate"].config(
                text=f"{wr:.1f}%", fg=GREEN if wr >= 55 else YELLOW if wr >= 45 else RED_COLOR
            )
            self._metric_labels["roi"].config(
                text=f"{roi:+.1f}%", fg=GREEN if roi > 0 else RED_COLOR
            )
            self._metric_labels["pl_total"].config(
                text=f"{pl:+.2f}u", fg=GREEN if pl > 0 else RED_COLOR
            )
            self._metric_labels["edge_avg"].config(text=f"{edge:.1f} pp")

            # Tabla de módulos
            for row in self._tree_modules.get_children():
                self._tree_modules.delete(row)

            module_names = {
                "B": "Team Corners FT",
                "C": "Corners 1T",
                "D": "Hándicap Corners",
                "F": "Tarjetas",
                "G": "BTTS",
                "A": "Goles Alt Totals",
            }
            brier_data = dashboard.get("brier_by_module", {})
            by_module  = stats.get("by_module", {})

            for mod_id in ["B", "C", "D", "F", "G", "A"]:
                mod_stats = by_module.get(mod_id, {})
                n     = mod_stats.get("total", 0)
                hits  = mod_stats.get("hits", 0)
                pl_m  = mod_stats.get("pl", 0) or 0
                wr_m  = f"{hits/n*100:.0f}%" if n > 0 else "—"
                brier = brier_data.get(mod_id, {}).get("brier_avg", "—")
                brier_str = f"{brier:.3f}" if isinstance(brier, float) else "—"

                self._tree_modules.insert("", "end", values=(
                    mod_id,
                    module_names.get(mod_id, ""),
                    n,
                    hits,
                    wr_m,
                    f"{pl_m:+.2f}u" if n > 0 else "—",
                    brier_str,
                ))

            # Anti-recency
            anti = dashboard.get("anti_recency", {})
            if anti.get("alert"):
                self._anti_recency_label.config(
                    text=f"⚠️  ALERTA ANTI-RECENCY: {anti.get('consecutive_misses', 0)} MISS consecutivos — {anti.get('recommendation','')}",
                    fg=RED_COLOR,
                )
            else:
                consecutive = anti.get("consecutive_misses", 0)
                self._anti_recency_label.config(
                    text=f"✅ Sistema normal — {consecutive} MISS consecutivos recientes",
                    fg=GREEN,
                )

            # Curva de bankroll (simplificada)
            self._draw_bankroll_curve(dashboard.get("bankroll_curve", []))

        except Exception as e:
            self._set_status(f"Error en métricas: {str(e)[:50]}")

    def _draw_bankroll_curve(self, curve: list):
        """Dibuja la curva de bankroll en el canvas."""
        canvas = self._bankroll_canvas
        canvas.delete("all")

        w = canvas.winfo_width() or 800
        h = canvas.winfo_height() or 180

        if len(curve) < 2:
            canvas.create_text(w//2, h//2, text="Sin datos suficientes para graficar",
                                fill=TEXT_GRAY, font=FONT_SMALL)
            return

        values = [v for _, v in curve]
        min_v  = min(values)
        max_v  = max(values)
        rng    = max_v - min_v or 1

        # Línea cero
        zero_y = h - int((0 - min_v) / rng * (h - 30)) - 15
        canvas.create_line(0, zero_y, w, zero_y, fill=TEXT_GRAY, dash=(4, 4))
        canvas.create_text(w - 40, zero_y - 8, text="0u", fill=TEXT_GRAY, font=FONT_SMALL)

        # Curva
        points = []
        for i, (_, v) in enumerate(curve):
            x = int(i / (len(curve) - 1) * (w - 20)) + 10
            y = h - int((v - min_v) / rng * (h - 30)) - 15
            points.extend([x, y])

        if len(points) >= 4:
            canvas.create_line(
                points,
                fill=GREEN if values[-1] >= 0 else RED_COLOR,
                width=2, smooth=True,
            )

        # Etiqueta final
        last_val = values[-1]
        canvas.create_text(
            w - 60, 20,
            text=f"Actual: {last_val:+.2f}u",
            fill=GREEN if last_val >= 0 else RED_COLOR,
            font=FONT_BODY,
        )

    # ─────────────────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────────────────

    def _style_treeview(self):
        """Aplica estilos al Treeview."""
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=BG_MEDIUM, fieldbackground=BG_MEDIUM,
            foreground=TEXT_WHITE, rowheight=25, font=FONT_SMALL,
        )
        style.configure(
            "Treeview.Heading",
            background=BG_LIGHT, foreground=TEXT_WHITE, font=FONT_SMALL,
        )
        style.map("Treeview", background=[("selected", BG_LIGHT)])


def main():
    """Punto de entrada de la GUI."""
    app = CG0PApp()
    app.mainloop()


if __name__ == "__main__":
    main()
