"""
rocket_view.py
===============

Representación visual animada del cohete (Persona 3 - Kenneth).

Dibuja, en un Canvas de Tkinter, un cohete que se mueve verticalmente
según la altura reportada en cada SimulationState, junto con una señal
visual clara de la fase actual (color + texto + ícono):

    - PHASE_1_PROPULSION : cohete con llama de empuje, etiqueta naranja.
    - PHASE_2_FREE_FLIGHT: cohete sin llama, etiqueta azul.
    - PHASE_3_DESCENT    : cohete con paracaídas abierto, etiqueta verde.
    - PHASE_4_IMPACT / FINISHED: marca de impacto en el suelo, etiqueta roja.

Esta vista se actualiza desde el mismo callback que alimenta las 7
gráficas de Matplotlib (ver ui.py -> _update_ui_from_state), por lo
que ambas quedan sincronizadas al mismo loop de simulación.

Este módulo NO calcula física, solo interpreta y dibuja el
SimulationState que ya viene resuelto por Persona 1 y Persona 2.
"""

from __future__ import annotations

import tkinter as tk

from config import SimulationPhase, SimulationState

# Colores por fase: (color de fondo de la etiqueta, texto, ícono corto)
_PHASE_STYLE: dict[SimulationPhase, tuple[str, str, str]] = {
    SimulationPhase.IDLE: ("#9e9e9e", "En espera", "•"),
    SimulationPhase.PHASE_1_PROPULSION: ("#fb8c00", "Propulsión", "🔥"),
    SimulationPhase.PHASE_2_FREE_FLIGHT: ("#1e88e5", "Vuelo libre", "↑"),
    SimulationPhase.PHASE_3_DESCENT: ("#43a047", "Descenso", "🪂"),
    SimulationPhase.PHASE_4_IMPACT: ("#e53935", "Impacto", "💥"),
    SimulationPhase.FINISHED: ("#e53935", "Finalizado", "✔"),
}


class RocketView:
    """
    Widget de visualización animada del cohete, embebido en un frame
    de Tkinter. Expone `update(state)` y `reset()`, con la misma forma
    que PlotManager, para integrarse de manera simétrica en la UI.
    """

    _CANVAS_WIDTH = 340
    _CANVAS_HEIGHT = 460
    _MARGIN_TOP = 30
    _MARGIN_BOTTOM = 40
    _ROCKET_X = _CANVAS_WIDTH // 2
    _ROCKET_HALF_WIDTH = 12
    _ROCKET_HEIGHT = 34

    def __init__(self, parent: tk.Widget) -> None:
        self._parent = parent

        header = tk.Frame(parent)
        header.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        self._phase_badge = tk.Label(
            header,
            text="●  En espera",
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="#9e9e9e",
            padx=10,
            pady=4,
        )
        self._phase_badge.pack(side=tk.LEFT)

        self._height_label = tk.Label(
            header, text="Altura: 0.0 m", font=("Segoe UI", 10)
        )
        self._height_label.pack(side=tk.RIGHT)

        self._canvas = tk.Canvas(
            parent,
            width=self._CANVAS_WIDTH,
            height=self._CANVAS_HEIGHT,
            bg="#e8f0fb",
            highlightthickness=1,
            highlightbackground="#c0c0c0",
        )
        self._canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._max_height_seen = 50.0  # escala inicial (m), autoescala hacia arriba
        self._ground_y = self._CANVAS_HEIGHT - self._MARGIN_BOTTOM

        self._draw_static_scene()

    # ------------------------------------------------------------------
    # Escena estática (fondo, suelo) — se dibuja una sola vez / al resetear
    # ------------------------------------------------------------------

    def _draw_static_scene(self) -> None:
        self._canvas.delete("all")

        # Cielo con degradado simple (franjas horizontales).
        steps = 12
        for i in range(steps):
            y0 = i * (self._ground_y / steps)
            y1 = (i + 1) * (self._ground_y / steps)
            shade = 235 - int(40 * (i / steps))
            color = f"#{shade:02x}{shade:02x}ff"
            self._canvas.create_rectangle(
                0, y0, self._CANVAS_WIDTH, y1, fill=color, outline=""
            )

        # Suelo.
        self._canvas.create_rectangle(
            0,
            self._ground_y,
            self._CANVAS_WIDTH,
            self._CANVAS_HEIGHT,
            fill="#6d4c33",
            outline="",
        )
        self._canvas.create_line(
            0, self._ground_y, self._CANVAS_WIDTH, self._ground_y,
            fill="#4a3320", width=2,
        )
        self._canvas.create_text(
            self._CANVAS_WIDTH - 8,
            self._CANVAS_HEIGHT - 10,
            text="Suelo",
            fill="#f0e6d8",
            font=("Segoe UI", 8),
            anchor="e",
            )

        self._draw_rocket(height=0.0, phase=SimulationPhase.IDLE)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def update(self, state: SimulationState) -> None:
        """Redibuja el cohete en su nueva posición/fase para este estado."""
        if state.height > self._max_height_seen:
            self._max_height_seen = state.height * 1.15  # margen visual

        self._draw_rocket(state.height, state.phase)
        self._update_badge(state.phase)
        self._height_label.config(text=f"Altura: {state.height:.1f} m")

    def reset(self) -> None:
        """Reinicia la escena a su estado inicial (sin simulación)."""
        self._max_height_seen = 50.0
        self._draw_static_scene()
        self._update_badge(SimulationPhase.IDLE)
        self._height_label.config(text="Altura: 0.0 m")

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def _height_to_y(self, height: float) -> float:
        usable = self._ground_y - self._MARGIN_TOP
        height = max(0.0, min(height, self._max_height_seen))
        fraction = height / self._max_height_seen if self._max_height_seen > 0 else 0.0
        return self._ground_y - fraction * usable

    def _draw_rocket(self, height: float, phase: SimulationPhase) -> None:
        self._canvas.delete("rocket_group")

        center_y = self._height_to_y(height)
        top_y = center_y - self._ROCKET_HEIGHT / 2
        bottom_y = center_y + self._ROCKET_HEIGHT / 2
        x = self._ROCKET_X
        hw = self._ROCKET_HALF_WIDTH

        # Paracaídas (fase 3): se dibuja detrás/arriba del cuerpo.
        if phase == SimulationPhase.PHASE_3_DESCENT:
            canopy_y = top_y - 30
            self._canvas.create_arc(
                x - 3 * hw, canopy_y - 22, x + 3 * hw, canopy_y + 22,
                start=0, extent=180, fill="#e53935", outline="#8e1c1c",
                tags="rocket_group",
                )
            for dx in (-2 * hw, -hw, hw, 2 * hw):
                self._canvas.create_line(
                    x + dx, canopy_y, x, top_y,
                    fill="#8e1c1c", tags="rocket_group",
                    )

        # Cuerpo del cohete (triángulo + rectángulo simple).
        self._canvas.create_polygon(
            x, top_y,
            x - hw, top_y + 10,
            x - hw, bottom_y,
            x + hw, bottom_y,
            x + hw, top_y + 10,
            fill="#37474f", outline="#111111",
            tags="rocket_group",
            )
        # Aletas.
        self._canvas.create_polygon(
            x - hw, bottom_y - 4,
            x - hw - 8, bottom_y + 10,
            x - hw, bottom_y + 4,
            fill="#263238", outline="#111111",
            tags="rocket_group",
            )
        self._canvas.create_polygon(
            x + hw, bottom_y - 4,
            x + hw + 8, bottom_y + 10,
            x + hw, bottom_y + 4,
            fill="#263238", outline="#111111",
            tags="rocket_group",
            )

        # Llama de propulsión (fase 1).
        if phase == SimulationPhase.PHASE_1_PROPULSION:
            self._canvas.create_polygon(
                x - hw + 3, bottom_y,
                x, bottom_y + 22,
                x + hw - 3, bottom_y,
                fill="#ffb300", outline="#e65100",
                tags="rocket_group",
                )

        # Marca de impacto (fase 4 / finalizado, ya en el suelo).
        if phase in (SimulationPhase.PHASE_4_IMPACT, SimulationPhase.FINISHED) and height <= 0.5:
            self._canvas.create_oval(
                x - 24, self._ground_y - 6, x + 24, self._ground_y + 6,
                fill="#ffccbc", outline="#e64a19", width=2,
                tags="rocket_group",
                )
            self._canvas.create_text(
                x, self._ground_y - 20, text="💥", font=("Segoe UI", 16),
                tags="rocket_group",
                   )

    def _update_badge(self, phase: SimulationPhase) -> None:
        color, text, icon = _PHASE_STYLE.get(
            phase, _PHASE_STYLE[SimulationPhase.IDLE]
        )
        self._phase_badge.config(text=f"{icon}  {text}", bg=color)