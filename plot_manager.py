"""
plot_manager.py
================

Encapsula toda la lógica de gráficas en tiempo real usando Matplotlib
embebido en Tkinter (FigureCanvasTkAgg).

Responsabilidad única: recibir un SimulationState (o su historial) y
dibujar/actualizar las 7 gráficas requeridas:

    1. Altura vs tiempo
    2. Velocidad vs tiempo
    3. Aceleración vs tiempo
    4. Energía cinética vs tiempo
    5. Energía potencial vs tiempo
    6. Energía total vs tiempo
    7. G's vs tiempo

Este módulo NO calcula física, solo grafica los valores que ya vienen
en config.SimulationHistory.

Autor: Persona 3 (UI / Gráficas / Integración)
"""

from __future__ import annotations

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import SimulationHistory


class PlotManager:
    """
    Administra una figura de Matplotlib con 7 subplots embebida en un
    frame de Tkinter, y expone un método `update()` para refrescarla
    en tiempo real conforme avanza la simulación.
    """

    _PLOT_SPECS: list[tuple[str, str, str]] = [
        # (título, atributo de SimulationHistory, color)
        ("Altura vs Tiempo", "height", "tab:blue"),
        ("Velocidad vs Tiempo", "velocity", "tab:orange"),
        ("Aceleración vs Tiempo", "acceleration", "tab:green"),
        ("Energía Cinética vs Tiempo", "kinetic_energy", "tab:red"),
        ("Energía Potencial vs Tiempo", "potential_energy", "tab:purple"),
        ("Energía Total vs Tiempo", "total_energy", "tab:brown"),
        ("G's vs Tiempo", "g_force", "tab:pink"),
    ]

    def __init__(self, parent: tk.Widget) -> None:
        """
        Parameters
        ----------
        parent : tk.Widget
            Frame de Tkinter donde se embebe el canvas de Matplotlib.
        """
        self._parent = parent

        # 7 gráficas en una grilla de 4 filas x 2 columnas (una celda vacía)
        self._figure = Figure(figsize=(9, 11), dpi=90)
        self._axes = self._figure.subplots(nrows=4, ncols=2)
        self._axes_flat = self._axes.flatten()

        self._lines: dict[str, "matplotlib.lines.Line2D"] = {}
        self._init_axes()

        self._canvas = FigureCanvasTkAgg(self._figure, master=self._parent)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _init_axes(self) -> None:
        """Configura título, etiquetas y una línea vacía por cada subplot."""
        for ax, (title, attr, color) in zip(self._axes_flat, self._PLOT_SPECS):
            ax.set_title(title, fontsize=9)
            ax.set_xlabel("Tiempo (s)", fontsize=7)
            ax.tick_params(labelsize=7)
            ax.grid(True, linestyle="--", alpha=0.4)
            (line,) = ax.plot([], [], color=color, linewidth=1.5)
            self._lines[attr] = line

        # La octava celda (4x2 = 8, solo usamos 7) se oculta.
        if len(self._axes_flat) > len(self._PLOT_SPECS):
            self._axes_flat[-1].axis("off")

        self._figure.tight_layout()

    def update(self, history: SimulationHistory) -> None:
        """
        Redibuja todas las curvas con los datos actuales del historial.

        Parameters
        ----------
        history : SimulationHistory
            Series de tiempo acumuladas (llenadas por el controlador a
            partir de los SimulationState producidos por Persona 1/2).
        """
        time_values = history.time

        for ax, (_, attr, _) in zip(self._axes_flat, self._PLOT_SPECS):
            y_values = getattr(history, attr)
            line = self._lines[attr]
            line.set_data(time_values, y_values)

            ax.relim()
            ax.autoscale_view()

        self._canvas.draw_idle()

    def reset(self) -> None:
        """Limpia todas las curvas (usado al reiniciar la simulación)."""
        for line in self._lines.values():
            line.set_data([], [])
        for ax in self._axes_flat[: len(self._PLOT_SPECS)]:
            ax.relim()
            ax.autoscale_view()
        self._canvas.draw_idle()