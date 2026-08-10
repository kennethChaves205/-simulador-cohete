"""
ui.py
=====

Interfaz gráfica principal (Tkinter). Contiene:

    - Panel izquierdo: controles (campos de parámetros + botones).
    - Panel derecho, dividido verticalmente:
        - Arriba: vista animada del cohete (RocketView) — vista principal.
        - Abajo: las 7 gráficas en tiempo real (PlotManager) — apoyo secundario.

Este módulo NO implementa física ni el bucle de simulación; delega
esa responsabilidad a SimulationController, y solo se encarga de:

    1. Recolectar los parámetros ingresados por el usuario.
    2. Iniciar/pausar/reanudar/reiniciar la simulación.
    3. Mostrar el estado actual (altura, velocidad, fase, etc.)
    4. Reenviar cada nuevo estado a RocketView y PlotManager, ambos
       sincronizados al mismo callback del controlador.

Autor: Persona 3 (UI / Gráficas / Vista animada / Integración)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from config import SimulationParameters, SimulationState
from plot_manager import PlotManager
from rocket_view import RocketView
from simulation_controller import SimulationController


class RocketSimulatorApp:
    """Ventana principal de la aplicación de simulación de cohetes."""

    _PARAM_FIELDS: list[tuple[str, str, float, str]] = [
        ("Altura inicial", "initial_height", 0.0, "m"),
        ("Masa total", "mass", 50.0, "kg"),
        ("Masa de combustible", "fuel_mass", 20.0, "kg"),
        ("Paso de tiempo (Δt)", "time_step", 0.1, "s"),
        ("Gravedad", "gravity", 9.81, "m/s²"),
        ("Empuje", "thrust", 2000.0, "N"),
        ("Duración del motor", "engine_duration", 5.0, "s"),
        ("Coeficiente de arrastre", "drag_coefficient", 0.5, ""),
        ("Área transversal", "cross_sectional_area", 0.3, "m²"),
        ("Densidad del aire", "air_density", 1.225, "kg/m³"),
    ]

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title("Simulador de Lanzamiento de Cohete")
        self._root.geometry("1360x860")
        self._root.minsize(1100, 720)

        self._entries: dict[str, tk.StringVar] = {}
        self._status_var = tk.StringVar(value="Listo para iniciar.")
        self._phase_var = tk.StringVar(value="Fase: -")
        self._time_var = tk.StringVar(value="t = 0.00 s")
        self._height_var = tk.StringVar(value="Altura = 0.00 m")
        self._velocity_var = tk.StringVar(value="Velocidad = 0.00 m/s")
        self._acceleration_var = tk.StringVar(value="Aceleración = 0.00 m/s²")

        self._controller = SimulationController(
            on_state_update=self._handle_state_update,
            on_status_message=self._handle_status_message,
        )

        self._build_layout()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Panel izquierdo (controles) + panel derecho (cohete + gráficas)."""
        container = ttk.Panedwindow(self._root, orient=tk.HORIZONTAL)
        container.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(container, padding=12)
        right_frame = ttk.Frame(container, padding=6)

        container.add(left_frame, weight=1)
        container.add(right_frame, weight=3)

        self._build_control_panel(left_frame)
        self._build_visual_panel(right_frame)

    def _build_control_panel(self, parent: ttk.Frame) -> None:
        """Panel izquierdo: título, campos de parámetros, botones y estado."""
        title = ttk.Label(
            parent, text="Parámetros de Simulación", font=("Segoe UI", 13, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        fields_frame = ttk.Frame(parent)
        fields_frame.pack(fill=tk.X)

        for row, (label_text, attr, default, unit) in enumerate(self._PARAM_FIELDS):
            ttk.Label(fields_frame, text=f"{label_text} ({unit})" if unit else label_text).grid(
                row=row, column=0, sticky="w", pady=3
            )
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(fields_frame, textvariable=var, width=14)
            entry.grid(row=row, column=1, sticky="e", pady=3, padx=(8, 0))
            self._entries[attr] = var

        fields_frame.columnconfigure(0, weight=1)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=12)

        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(0, 12))

        self._start_btn = ttk.Button(
            buttons_frame, text="Iniciar simulación", command=self._on_start_clicked
        )
        self._pause_btn = ttk.Button(
            buttons_frame, text="Pausar", command=self._on_pause_clicked
        )
        self._resume_btn = ttk.Button(
            buttons_frame, text="Continuar", command=self._on_resume_clicked
        )
        self._reset_btn = ttk.Button(
            buttons_frame, text="Reiniciar", command=self._on_reset_clicked
        )

        self._start_btn.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        self._pause_btn.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        self._resume_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self._reset_btn.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        buttons_frame.columnconfigure((0, 1), weight=1)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=12)

        status_title = ttk.Label(parent, text="Estado actual", font=("Segoe UI", 11, "bold"))
        status_title.pack(anchor="w")

        for var in (
                self._phase_var,
                self._time_var,
                self._height_var,
                self._velocity_var,
                self._acceleration_var,
        ):
            ttk.Label(parent, textvariable=var, font=("Segoe UI", 10)).pack(anchor="w", pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=12)

        status_label = ttk.Label(
            parent, textvariable=self._status_var, foreground="#333333", wraplength=280
        )
        status_label.pack(anchor="w")

    def _build_visual_panel(self, parent: ttk.Frame) -> None:
        """
        Panel derecho, dividido verticalmente:
            - Arriba: vista animada del cohete (vista principal).
            - Abajo: 7 gráficas de Matplotlib (apoyo secundario).
        """
        vertical_split = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        vertical_split.pack(fill=tk.BOTH, expand=True)

        rocket_frame = ttk.Frame(vertical_split, padding=4)
        plots_frame = ttk.Frame(vertical_split, padding=4)

        vertical_split.add(rocket_frame, weight=2)
        vertical_split.add(plots_frame, weight=3)

        rocket_title = ttk.Label(
            rocket_frame, text="Vista del cohete", font=("Segoe UI", 11, "bold")
        )
        rocket_title.pack(anchor="w", pady=(0, 4))
        self._rocket_view = RocketView(rocket_frame)

        plots_title = ttk.Label(
            plots_frame, text="Gráficas (apoyo secundario)", font=("Segoe UI", 10, "bold")
        )
        plots_title.pack(anchor="w", pady=(0, 4))
        self._plot_manager = PlotManager(plots_frame)

    # ------------------------------------------------------------------
    # Callbacks de botones
    # ------------------------------------------------------------------

    def _on_start_clicked(self) -> None:
        try:
            params = self._collect_parameters()
        except ValueError as exc:
            messagebox.showerror("Parámetros inválidos", str(exc))
            return

        self._plot_manager.reset()
        self._rocket_view.reset()
        self._controller.start(params)

    def _on_pause_clicked(self) -> None:
        self._controller.pause()

    def _on_resume_clicked(self) -> None:
        self._controller.resume()

    def _on_reset_clicked(self) -> None:
        self._controller.reset()
        self._plot_manager.reset()
        self._rocket_view.reset()
        self._phase_var.set("Fase: -")
        self._time_var.set("t = 0.00 s")
        self._height_var.set("Altura = 0.00 m")
        self._velocity_var.set("Velocidad = 0.00 m/s")
        self._acceleration_var.set("Aceleración = 0.00 m/s²")

    # ------------------------------------------------------------------
    # Callbacks invocados por SimulationController (desde otro hilo)
    # ------------------------------------------------------------------

    def _handle_state_update(self, state: SimulationState) -> None:
        """
        Se ejecuta en el hilo de simulación. Reenvía el trabajo pesado
        (actualizar UI, vista del cohete y gráficas) al hilo principal
        de Tkinter usando `after(0, ...)`, la forma segura de hacerlo.
        """
        self._root.after(0, self._update_ui_from_state, state)

    def _update_ui_from_state(self, state: SimulationState) -> None:
        self._phase_var.set(f"Fase: {state.phase.name}")
        self._time_var.set(f"t = {state.time:.2f} s")
        self._height_var.set(f"Altura = {state.height:.2f} m")
        self._velocity_var.set(f"Velocidad = {state.velocity:.2f} m/s")
        self._acceleration_var.set(f"Aceleración = {state.acceleration:.2f} m/s²")

        # Ambas vistas se alimentan del mismo estado, en el mismo tick.
        self._rocket_view.update(state)
        self._plot_manager.update(state.history)

    def _handle_status_message(self, message: str) -> None:
        self._root.after(0, self._status_var.set, message)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _collect_parameters(self) -> SimulationParameters:
        """Lee y valida los campos de entrada, devolviendo SimulationParameters."""
        values: dict[str, float] = {}
        for _, attr, _, _ in self._PARAM_FIELDS:
            raw_value = self._entries[attr].get().strip()
            try:
                values[attr] = float(raw_value)
            except ValueError:
                raise ValueError(
                    f"El campo '{attr}' debe ser un número válido (valor recibido: '{raw_value}')."
                )
        return SimulationParameters(**values)


def launch_app() -> None:
    """Punto de entrada para crear y ejecutar la ventana principal."""
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    RocketSimulatorApp(root)
    root.mainloop()