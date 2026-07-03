"""
simulation_controller.py
=========================

Controlador que orquesta la simulación: llama a las funciones de fase
(simulate_phase1..4, implementadas por Persona 1 y Persona 2), avanza
el tiempo en pasos de Δt, y notifica a la interfaz/gráficas mediante
callbacks para que se actualicen en tiempo real.

Este módulo NO implementa física. Solo decide CUÁNDO llamar a cada
función de fase y gestiona el ciclo de vida de la simulación
(iniciar, pausar, continuar, reiniciar).

Autor: Persona 3 (UI / Gráficas / Integración)
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from config import SimulationParameters, SimulationState, SimulationPhase
from physics_interface import (
    simulate_phase1,
    simulate_phase2,
    simulate_phase3,
    simulate_phase4,
)


# Callback que recibe el estado actualizado tras cada paso de simulación.
StateCallback = Callable[[SimulationState], None]

# Callback que se invoca cuando la simulación termina o hay un error.
StatusCallback = Callable[[str], None]


class SimulationController:
    """
    Orquesta el bucle de simulación en un hilo independiente para no
    congelar la interfaz gráfica de Tkinter.

    Flujo general (pseudocódigo del enunciado):

        while running:
            state = simulate_phaseX(...)
            actualizar interfaz
            actualizar gráficas
            esperar Δt
    """

    def __init__(
            self,
            on_state_update: StateCallback,
            on_status_message: Optional[StatusCallback] = None,
    ) -> None:
        """
        Parameters
        ----------
        on_state_update : StateCallback
            Función invocada con el nuevo SimulationState en cada paso.
            Normalmente actualiza la UI (etiquetas) y las gráficas.
        on_status_message : Optional[StatusCallback]
            Función invocada con mensajes de estado/errores (opcional).
        """
        self._on_state_update = on_state_update
        self._on_status_message = on_status_message or (lambda msg: None)

        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._stop_requested = threading.Event()

        self._state: SimulationState = SimulationState()
        self._params: SimulationParameters = SimulationParameters()

        # Límite de seguridad para evitar bucles infinitos si las fases
        # de Persona 1/2 aún no están implementadas o no marcan FINISHED.
        self._max_steps = 100_000

    # ------------------------------------------------------------------
    # API pública: controles de la simulación
    # ------------------------------------------------------------------

    def start(self, params: SimulationParameters) -> None:
        """Inicia una nueva simulación con los parámetros dados."""
        if self._thread is not None and self._thread.is_alive():
            self._on_status_message("La simulación ya está en ejecución.")
            return

        self._params = params
        self._state = SimulationState()
        self._stop_requested.clear()
        self._paused.clear()
        self._running.set()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._on_status_message("Simulación iniciada.")

    def pause(self) -> None:
        """Pausa la simulación en curso (el hilo sigue vivo, en espera)."""
        if self._running.is_set():
            self._paused.set()
            self._on_status_message("Simulación pausada.")

    def resume(self) -> None:
        """Reanuda una simulación previamente pausada."""
        if self._running.is_set() and self._paused.is_set():
            self._paused.clear()
            self._on_status_message("Simulación reanudada.")

    def reset(self) -> None:
        """Detiene la simulación actual y limpia el estado."""
        self._stop_requested.set()
        self._paused.clear()
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._thread = None
        self._state = SimulationState()
        self._on_status_message("Simulación reiniciada.")

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @property
    def is_paused(self) -> bool:
        return self._paused.is_set()

    # ------------------------------------------------------------------
    # Bucle interno de simulación
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """
        Bucle principal ejecutado en un hilo aparte.

        Llama a simulate_phase1 una sola vez para obtener el estado
        inicial, y luego avanza por las fases 2, 3 y 4 según el valor
        de state.phase, hasta llegar a FINISHED o alcanzar el límite
        de seguridad de pasos.
        """
        try:
            self._state = simulate_phase1(self._params)
            self._emit_state()

            steps = 0
            while (
                    self._running.is_set()
                    and not self._stop_requested.is_set()
                    and self._state.phase != SimulationPhase.FINISHED
                    and steps < self._max_steps
            ):
                # Respeta pausa sin consumir CPU en un busy-wait agresivo.
                while self._paused.is_set() and not self._stop_requested.is_set():
                    time.sleep(0.05)

                if self._stop_requested.is_set():
                    break

                self._state = self._advance_phase(self._state)
                self._emit_state()

                steps += 1
                time.sleep(max(self._params.time_step, 0.001))

            if not self._stop_requested.is_set():
                self._on_status_message("Simulación finalizada.")

        except NotImplementedError as exc:
            # Ocurre mientras Persona 1 / Persona 2 no hayan implementado
            # sus funciones. Se informa de forma clara en vez de fallar
            # silenciosamente.
            self._on_status_message(f"Función física pendiente de implementar: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._on_status_message(f"Error durante la simulación: {exc}")
        finally:
            self._running.clear()

    def _advance_phase(self, state: SimulationState) -> SimulationState:
        """
        Decide qué función de fase invocar según state.phase actual.

        Persona 1 y Persona 2 son responsables de, dentro de sus
        funciones, actualizar `state.phase` al valor correspondiente
        cuando corresponda avanzar a la siguiente etapa.
        """
        if state.phase in (
                SimulationPhase.IDLE,
                SimulationPhase.PHASE_1_PROPULSION,
        ):
            return simulate_phase2(state)
        if state.phase == SimulationPhase.PHASE_2_FREE_FLIGHT:
            return simulate_phase3(state)
        if state.phase == SimulationPhase.PHASE_3_DESCENT:
            return simulate_phase4(state)
        if state.phase == SimulationPhase.PHASE_4_IMPACT:
            state.phase = SimulationPhase.FINISHED
            return state

        # Fallback defensivo: si la fase no es reconocida, se detiene.
        state.phase = SimulationPhase.FINISHED
        return state

    def _emit_state(self) -> None:
        """Registra el estado en el historial y notifica a la UI/gráficas."""
        self._state.history.append(self._state)
        self._on_state_update(self._state)