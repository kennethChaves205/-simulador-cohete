"""
ui.py
=====

Interfaz gráfica principal (Tkinter). Contiene:

    - Franja superior: encabezado con badge de fase.
    - Panel izquierdo: controles, en tarjetas (parámetros, botones, estado).
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

El estilo visual (colores, tipografía) vive en theme.py para que la UI,
la vista del cohete y las gráficas compartan la misma paleta.

Autor: Persona 3 (UI / Gráficas / Vista animada / Integración)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import theme
from config import SimulationParameters, SimulationState
from plot_manager import PlotManager
from rocket_view import RocketView
from simulation_controller import SimulationController


class Card(tk.Frame):
    """
    Contenedor con fondo blanco, borde sutil y un título opcional,
    para agrupar visualmente secciones del panel de control (imita el
    look de una "card" de una interfaz web moderna).
    """

    def __init__(self, parent: tk.Widget, title: str | None = None, **kwargs) -> None:
        super().__init__(
            parent,
            bg=theme.CARD_BG,
            highlightbackground=theme.CARD_BORDER,
            highlightthickness=1,
            bd=0,
            **kwargs,
        )
        self.body = tk.Frame(self, bg=theme.CARD_BG)
        if title:
            header = tk.Label(
                self,
                text=title,
                bg=theme.CARD_BG,
                fg=theme.TEXT_PRIMARY,
                font=(theme.FONT_FAMILY, 11, "bold"),
                anchor="w",
            )
            header.pack(fill=tk.X, padx=16, pady=(14, 6))
        self.body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))


class FlatButton(tk.Button):
    """Botón plano con color sólido y hover, al estilo de un botón web."""

    def __init__(
            self,
            parent: tk.Widget,
            text: str,
            command: Callable[[], None],
            bg: str,
            hover_bg: str,
            fg: str = "#ffffff",
            **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            font=(theme.FONT_FAMILY, 10, "bold"),
            cursor="hand2",
            padx=10,
            pady=8,
            **kwargs,
        )
        self._bg = bg
        self._hover_bg = hover_bg
        self.bind("<Enter>", lambda _e: self.configure(bg=self._hover_bg))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._bg))


class RocketSimulatorApp:
    """Ventana principal de la aplicación de simulación de cohetes."""

    # (etiqueta visible, atributo en SimulationParameters, valor por defecto, unidad)
    _PARAM_FIELDS: list[tuple[str, str, float, str]] = [
        ("Altura inicial", "initial_height", 0.0, "m"),
        ("Masa total", "mass", 50.0, "kg"),
        ("Masa de combustible", "fuel_mass", 20.0, "kg"),
        ("Paso de tiempo (Δt)", "time_step", 0.01, "s"),
        ("Gravedad", "gravity", 9.81, "m/s²"),
        ("Empuje", "thrust", 2000.0, "N"),
        ("Duración del motor", "engine_duration", 5.0, "s"),
        ("Coeficiente de arrastre (paracaídas)", "drag_coefficient", 1.5, ""),
        ("Área del paracaídas", "cross_sectional_area", 8.0, "m²"),
        ("Densidad del aire", "air_density", 1.225, "kg/m³"),
        ("Tiempo de despliegue del paracaídas", "t_deploy", 1.5, "s"),
    ]

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title("Simulador de Lanzamiento de Cohete")
        self._root.geometry("1360x900")
        self._root.minsize(1120, 760)
        self._root.configure(bg=theme.APP_BG)

        self._entries: dict[str, tk.StringVar] = {}
        self._status_var = tk.StringVar(value="Listo para iniciar.")
        self._time_var = tk.StringVar(value="0.00 s")
        self._height_var = tk.StringVar(value="0.00 m")
        self._velocity_var = tk.StringVar(value="0.00 m/s")
        self._acceleration_var = tk.StringVar(value="0.00 m/s²")

        self._controller = SimulationController(
            on_state_update=self._handle_state_update,
            on_status_message=self._handle_status_message,
        )

        self._build_layout()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Franja superior + panel izquierdo (controles) y derecho (cohete + gráficas)."""
        self._build_header(self._root)

        body = tk.Frame(self._root, bg=theme.APP_BG)
        body.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo con scroll (por si la ventana se achica)
        left_container = tk.Frame(body, bg=theme.APP_BG, width=330)
        left_container.pack(side=tk.LEFT, fill=tk.Y)
        left_container.pack_propagate(False)

        canvas = tk.Canvas(left_container, bg=theme.APP_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        left_frame = tk.Frame(canvas, bg=theme.APP_BG)

        left_frame.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=left_frame, anchor="nw", width=314)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=12)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=12)

        right_frame = tk.Frame(body, bg=theme.APP_BG)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        self._build_control_panel(left_frame)
        self._build_visual_panel(right_frame)

    def _build_header(self, parent: tk.Widget) -> None:
        header = tk.Frame(parent, bg=theme.HEADER_BG, height=64)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="🚀  Simulador de Lanzamiento de Cohete",
            bg=theme.HEADER_BG,
            fg="#ffffff",
            font=(theme.FONT_FAMILY, 15, "bold"),
        )
        title.pack(side=tk.LEFT, padx=20)

        subtitle = tk.Label(
            header,
            text="Física I · Proyecto de Simulación",
            bg=theme.HEADER_BG,
            fg="#c7d2fe",
            font=(theme.FONT_FAMILY, 10),
        )
        subtitle.pack(side=tk.LEFT, pady=(4, 0))

        # "Badge" de fase actual, a la derecha del encabezado
        self._phase_badge = tk.Label(
            header,
            text=theme.PHASE_LABELS["IDLE"],
            bg=theme.PHASE_COLORS["IDLE"],
            fg="#ffffff",
            font=(theme.FONT_FAMILY, 10, "bold"),
            padx=14,
            pady=6,
        )
        self._phase_badge.pack(side=tk.RIGHT, padx=20)

    def _build_control_panel(self, parent: tk.Widget) -> None:
        """Panel izquierdo: tarjetas de parámetros, controles y estado."""

        # --- Tarjeta: parámetros ---------------------------------------
        params_card = Card(parent, title="⚙️  Parámetros de simulación")
        params_card.pack(fill=tk.X, pady=(0, 12))

        fields_frame = params_card.body
        for row, (label_text, attr, default, unit) in enumerate(self._PARAM_FIELDS):
            label_text_full = f"{label_text} ({unit})" if unit else label_text
            tk.Label(
                fields_frame,
                text=label_text_full,
                bg=theme.CARD_BG,
                fg=theme.TEXT_SECONDARY,
                font=(theme.FONT_FAMILY, 9),
                anchor="w",
            ).grid(row=row, column=0, sticky="w", pady=4)

            var = tk.StringVar(value=str(default))
            entry = tk.Entry(
                fields_frame,
                textvariable=var,
                width=10,
                relief="flat",
                bg=theme.ENTRY_BG,
                fg=theme.TEXT_PRIMARY,
                font=(theme.FONT_FAMILY, 9),
                highlightthickness=1,
                highlightbackground=theme.ENTRY_BORDER,
                highlightcolor=theme.ENTRY_BORDER_FOCUS,
                justify="right",
            )
            entry.grid(row=row, column=1, sticky="e", pady=4, padx=(8, 0), ipady=3)
            self._entries[attr] = var

        fields_frame.columnconfigure(0, weight=1)

        # --- Tarjeta: controles ------------------------------------------
        controls_card = Card(parent, title="🎮  Controles")
        controls_card.pack(fill=tk.X, pady=(0, 12))

        buttons_frame = controls_card.body
        buttons_frame.columnconfigure((0, 1), weight=1)

        self._start_btn = FlatButton(
            buttons_frame, "▶  Iniciar", self._on_start_clicked,
            bg=theme.ACCENT, hover_bg=theme.ACCENT_HOVER,
        )
        self._pause_btn = FlatButton(
            buttons_frame, "⏸  Pausar", self._on_pause_clicked,
            bg=theme.WARNING, hover_bg=theme.WARNING_HOVER,
        )
        self._resume_btn = FlatButton(
            buttons_frame, "⏵  Continuar", self._on_resume_clicked,
            bg=theme.SUCCESS, hover_bg="#15803d",
        )
        self._reset_btn = FlatButton(
            buttons_frame, "⟲  Reiniciar", self._on_reset_clicked,
            bg=theme.DANGER, hover_bg=theme.DANGER_HOVER,
        )

        self._start_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._pause_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=4)
        self._resume_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=4)
        self._reset_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        # --- Tarjeta: estado actual ---------------------------------------
        status_card = Card(parent, title="📊  Estado actual")
        status_card.pack(fill=tk.X, pady=(0, 12))

        state_rows = [
            ("Tiempo", self._time_var),
            ("Altura", self._height_var),
            ("Velocidad", self._velocity_var),
            ("Aceleración", self._acceleration_var),
        ]
        for label_text, var in state_rows:
            row = tk.Frame(status_card.body, bg=theme.CARD_BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(
                row, text=label_text, bg=theme.CARD_BG, fg=theme.TEXT_SECONDARY,
                font=(theme.FONT_FAMILY, 9), width=12, anchor="w",
            ).pack(side=tk.LEFT)
            tk.Label(
                row, textvariable=var, bg=theme.CARD_BG, fg=theme.TEXT_PRIMARY,
                font=(theme.FONT_FAMILY, 10, "bold"), anchor="e",
            ).pack(side=tk.RIGHT)

        # --- Mensaje de estado / errores -----------------------------------
        status_label = tk.Label(
            parent,
            textvariable=self._status_var,
            bg=theme.APP_BG,
            fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 9, "italic"),
            wraplength=290,
            justify="left",
            anchor="w",
        )
        status_label.pack(fill=tk.X, padx=4, pady=(0, 12))

    def _build_visual_panel(self, parent: tk.Widget) -> None:
        """
        Panel derecho, dividido verticalmente:
            - Arriba: vista animada del cohete (vista principal), en tarjeta.
            - Abajo: 7 gráficas de Matplotlib (apoyo secundario), en tarjeta.
        """
        vertical_split = ttk.Panedwindow(parent, orient=tk.VERTICAL)
        vertical_split.pack(fill=tk.BOTH, expand=True)

        rocket_card = Card(vertical_split, title="🚀  Vista del cohete")
        plots_card = Card(vertical_split, title="📈  Gráficas (apoyo secundario)")

        vertical_split.add(rocket_card, weight=2)
        vertical_split.add(plots_card, weight=3)

        self._rocket_view = RocketView(rocket_card.body)
        self._plot_manager = PlotManager(plots_card.body)

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
        self._set_phase_badge("IDLE")
        self._time_var.set("0.00 s")
        self._height_var.set("0.00 m")
        self._velocity_var.set("0.00 m/s")
        self._acceleration_var.set("0.00 m/s²")

    # ------------------------------------------------------------------
    # Callbacks invocados por SimulationController (desde otro hilo)
    # ------------------------------------------------------------------

    def _handle_state_update(self, state: SimulationState) -> None:
        """
        Se ejecuta en el hilo de simulación. Reenvía el trabajo pesado
        (actualizar UI, vista del cohete y gráficas) al hilo principal
        de Tkinter usando `after(0, ...)`, la forma segura de hacerlo.

        El controlador ya limita cuántas veces por segundo llega a
        llamar esto (ver simulation_controller._emit_state), así que
        aquí no hace falta throttling adicional.
        """
        self._root.after(0, self._update_ui_from_state, state)

    def _update_ui_from_state(self, state: SimulationState) -> None:
        self._set_phase_badge(state.phase.name)
        self._time_var.set(f"{state.time:.2f} s")
        self._height_var.set(f"{state.height:.2f} m")
        self._velocity_var.set(f"{state.velocity:.2f} m/s")
        self._acceleration_var.set(f"{state.acceleration:.2f} m/s²")

        # Ambas vistas se alimentan del mismo estado, en el mismo tick.
        self._rocket_view.update(state)
        self._plot_manager.update(state.history)

    def _handle_status_message(self, message: str) -> None:
        self._root.after(0, self._status_var.set, message)

    def _set_phase_badge(self, phase_key: str) -> None:
        """Actualiza el texto y color de la 'badge' de fase en el encabezado."""
        color = theme.PHASE_COLORS.get(phase_key, theme.TEXT_MUTED)
        label = theme.PHASE_LABELS.get(phase_key, phase_key)
        self._phase_badge.configure(text=label, bg=color)

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