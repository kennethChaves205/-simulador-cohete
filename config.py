"""
config.py
=========

Define las estructuras de datos compartidas entre todos los subsistemas
del proyecto: parámetros de entrada de la simulación y el estado que
viaja entre las fases (Persona 1 -> Persona 2 -> UI/Gráficas).

Este módulo NO contiene ninguna ecuación física. Solo define los
"contratos" de datos (dataclasses) que Persona 1 y Persona 2 deben
respetar al implementar simulate_phase1..4.

Autor: Persona 3 (UI / Gráficas / Integración)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class SimulationPhase(Enum):
    """Fases del vuelo del cohete."""

    IDLE = auto()
    PHASE_1_PROPULSION = auto()     # Persona 1
    PHASE_2_FREE_FLIGHT = auto()    # Persona 1
    PHASE_3_DESCENT = auto()        # Persona 2
    PHASE_4_IMPACT = auto()         # Persona 2
    FINISHED = auto()


@dataclass
class SimulationParameters:
    """
    Parámetros de entrada configurables desde la interfaz gráfica.

    Todos los campos aquí definidos deben quedar disponibles para
    Persona 1 y Persona 2 al momento de invocar sus funciones físicas.
    """

    initial_height: float = 0.0        # m
    mass: float = 50.0                 # kg (masa total inicial, incluyendo combustible)
    fuel_mass: float = 20.0            # kg
    time_step: float = 0.01            # s (Δt) — bajado de 0.1 a 0.01:
                                        # con 0.1 el Euler diverge en fase 3
                                        # (arrastre cuadrático del paracaídas)
    gravity: float = 9.81              # m/s^2
    thrust: float = 2000.0             # N (empuje del motor)
    engine_duration: float = 5.0       # s (duración del motor encendido)
    # NOTA: fase 1 y 2 no usan arrastre, así que estos tres campos solo
    # tienen efecto en fase 3 (paracaídas). Los valores por defecto
    # corresponden a un paracaídas hemisférico real (no al cuerpo del
    # cohete); con un Cd/área pequeños (p. ej. 0.5 / 0.3 m², típicos del
    # fuselaje) la velocidad terminal sale absurdamente alta y la fuerza
    # de impacto se dispara a cientos de g's.
    drag_coefficient: float = 1.5      # adimensional (Cd del paracaídas ya desplegado)
    cross_sectional_area: float = 8.0  # m^2 (área efectiva del paracaídas ya desplegado)
    air_density: float = 1.225         # kg/m^3
    t_deploy: float = 1.5              # s (tiempo desde que inicia la fase 3 hasta
                                        # que el paracaídas está completamente desplegado;
                                        # antes de eso el cohete cae libre)

    def as_dict(self) -> dict:
        """Devuelve los parámetros como diccionario (útil para logging/debug)."""
        return {
            "initial_height": self.initial_height,
            "mass": self.mass,
            "fuel_mass": self.fuel_mass,
            "time_step": self.time_step,
            "gravity": self.gravity,
            "thrust": self.thrust,
            "engine_duration": self.engine_duration,
            "drag_coefficient": self.drag_coefficient,
            "cross_sectional_area": self.cross_sectional_area,
            "air_density": self.air_density,
            "t_deploy": self.t_deploy,
        }


@dataclass
class SimulationState:
    """
    Estado instantáneo del cohete en un instante t.

    Este objeto es el que se pasa entre fases:
        state = simulate_phase1(params)
        state = simulate_phase2(state)
        state = simulate_phase3(state)
        state = simulate_phase4(state)

    Persona 1 y Persona 2 deben leer/actualizar estos campos.
    Persona 3 (UI) solo LEE estos campos para graficar, nunca los calcula.
    """

    time: float = 0.0
    phase: SimulationPhase = SimulationPhase.IDLE

    # Cinemática (Persona 1 / Persona 2)
    height: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0

    # Energía (Persona 2)
    kinetic_energy: float = 0.0
    potential_energy: float = 0.0
    total_energy: float = 0.0

    # Impacto / esfuerzos (Persona 2)
    impact_force: float = 0.0
    g_force: float = 0.0
    terminal_velocity: float = 0.0

    # Masa restante (puede variar si hay consumo de combustible)
    current_mass: float = 0.0

    # Despliegue del paracaídas (Persona 2 / fase 3)
    descent_start_time: float = -1.0   # marca de tiempo al entrar a fase 3 (-1 = aún no entra)
    parachute_deployed: bool = False   # True una vez transcurrido t_deploy

    # Historial acumulado para graficar (listas paralelas por índice de tiempo)
    history: "SimulationHistory" = field(default_factory=lambda: SimulationHistory())


@dataclass
class SimulationHistory:
    """
    Acumula las series de tiempo necesarias para las 7 gráficas.
    Persona 3 (plot_manager.py) consume estas listas directamente.
    """

    time: list = field(default_factory=list)
    height: list = field(default_factory=list)
    velocity: list = field(default_factory=list)
    acceleration: list = field(default_factory=list)
    kinetic_energy: list = field(default_factory=list)
    potential_energy: list = field(default_factory=list)
    total_energy: list = field(default_factory=list)
    g_force: list = field(default_factory=list)

    def append(self, state: SimulationState) -> None:
        """Agrega el estado actual a las series históricas."""
        self.time.append(state.time)
        self.height.append(state.height)
        self.velocity.append(state.velocity)
        self.acceleration.append(state.acceleration)
        self.kinetic_energy.append(state.kinetic_energy)
        self.potential_energy.append(state.potential_energy)
        self.total_energy.append(state.total_energy)
        self.g_force.append(state.g_force)

    def clear(self) -> None:
        """Limpia todas las series (usado al reiniciar la simulación)."""
        self.time.clear()
        self.height.clear()
        self.velocity.clear()
        self.acceleration.clear()
        self.kinetic_energy.clear()
        self.potential_energy.clear()
        self.total_energy.clear()
        self.g_force.clear()