"""
theme.py
========

Paleta de colores y constantes de estilo compartidas entre la interfaz
(ui.py) y las gráficas (plot_manager.py), para que ambas se vean como
parte de una misma aplicación "web-like" en vez de un Tkinter genérico.

Autor: Persona 3 (UI / Gráficas / Integración)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Paleta general
# ---------------------------------------------------------------------------
APP_BG = "#eef1f8"          # fondo general de la ventana
CARD_BG = "#ffffff"         # fondo de las "tarjetas"
CARD_BORDER = "#e2e8f0"     # borde sutil de las tarjetas
HEADER_BG = "#4338ca"       # franja superior (indigo oscuro)
HEADER_BG_LIGHT = "#4f46e5"  # variante para degradado simulado

TEXT_PRIMARY = "#0f172a"    # texto principal (casi negro azulado)
TEXT_SECONDARY = "#64748b"  # texto secundario / labels
TEXT_MUTED = "#94a3b8"      # texto apagado (placeholders, notas)

ACCENT = "#4f46e5"          # indigo — acción principal
ACCENT_HOVER = "#4338ca"
DANGER = "#ef4444"          # rojo — reiniciar
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"         # ámbar — pausar
WARNING_HOVER = "#d97706"
SUCCESS = "#16a34a"         # verde — continuar / finalizado

ENTRY_BG = "#f8fafc"
ENTRY_BORDER = "#cbd5e1"
ENTRY_BORDER_FOCUS = ACCENT

FONT_FAMILY = "Segoe UI"

# ---------------------------------------------------------------------------
# Colores por fase (usados en la "badge" de estado y podrían reusarse en
# la futura vista animada del cohete)
# ---------------------------------------------------------------------------
PHASE_COLORS = {
    "IDLE": TEXT_MUTED,
    "PHASE_1_PROPULSION": "#f97316",   # naranja — motor encendido
    "PHASE_2_FREE_FLIGHT": "#3b82f6",  # azul — vuelo balístico
    "PHASE_3_DESCENT": "#8b5cf6",      # violeta — paracaídas
    "PHASE_4_IMPACT": "#ef4444",       # rojo — impacto
    "FINISHED": "#16a34a",             # verde — terminado
}

PHASE_LABELS = {
    "IDLE": "En espera",
    "PHASE_1_PROPULSION": "Propulsión",
    "PHASE_2_FREE_FLIGHT": "Vuelo libre",
    "PHASE_3_DESCENT": "Descenso (paracaídas)",
    "PHASE_4_IMPACT": "Impacto",
    "FINISHED": "Finalizado",
}

# ---------------------------------------------------------------------------
# Paleta de curvas para las gráficas de Matplotlib (más moderna que los
# "tab:*" por defecto)
# ---------------------------------------------------------------------------
PLOT_COLORS = {
    "height": "#4f46e5",           # indigo
    "velocity": "#f97316",         # naranja
    "acceleration": "#16a34a",     # verde
    "kinetic_energy": "#ef4444",   # rojo
    "potential_energy": "#8b5cf6",  # violeta
    "total_energy": "#0891b2",     # cian
    "g_force": "#db2777",          # rosa
}

PLOT_GRID_COLOR = "#e2e8f0"
PLOT_AXIS_COLOR = "#94a3b8"
PLOT_BG = "#ffffff"