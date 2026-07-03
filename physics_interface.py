"""
physics_interface.py
=====================

IMPORTANTE: Este archivo NO contiene física. Es únicamente el
"contrato" (interfaz) que Persona 1 y Persona 2 deben implementar.

Cómo integrar el trabajo de tus compañeros
-------------------------------------------
1. Persona 1 debe reemplazar el cuerpo de:
     - simulate_phase1(params)
     - simulate_phase2(state)

2. Persona 2 debe reemplazar el cuerpo de:
     - simulate_phase3(state)
     - simulate_phase4(state)
   y es responsable de calcular dentro de sus fases:
     energía cinética, energía potencial, energía total,
     fuerza de impacto, g's y velocidad terminal.

3. Lo más simple es que cada compañero pegue su código directamente
   en las funciones de este archivo (respetando la firma y el tipo
   de retorno). Alternativamente, pueden crear sus propios módulos
   (por ejemplo `phase1_2.py` y `phase3_4.py`) e importar sus
   funciones aquí, así:

       from phase1_2 import simulate_phase1 as _p1_impl
       def simulate_phase1(params):
           return _p1_impl(params)

Mientras la firma (parámetros de entrada / SimulationState de salida)
se mantenga igual, el resto del proyecto (UI, gráficas, controlador)
no requiere ningún cambio.

Autor: Persona 3 (UI / Gráficas / Integración) - Solo define el contrato.
"""

from __future__ import annotations

from config import SimulationParameters, SimulationState, SimulationPhase


def simulate_phase1(params: SimulationParameters) -> SimulationState:
    """
    Fase 1: Propulsión (motor encendido).

    Responsable: Persona 1.

    Debe calcular el estado inicial del cohete mientras el motor está
    activo (empuje, consumo de combustible, aceleración resultante, etc.)
    y devolver el primer SimulationState de la simulación (t=0 o t=Δt).

    Parameters
    ----------
    params : SimulationParameters
        Parámetros configurados por el usuario en la interfaz.

    Returns
    -------
    SimulationState
        Estado del cohete al finalizar el primer paso de la fase de
        propulsión, con phase=SimulationPhase.PHASE_1_PROPULSION.

    Nota: Esta función es un stub. Persona 1 debe reemplazar el
    cuerpo con la física real. NO debe ser implementada por Persona 3.
    """
    raise NotImplementedError(
        "simulate_phase1 debe ser implementada por Persona 1. "
        "Este es solo el contrato de la interfaz."
    )


def simulate_phase2(state: SimulationState) -> SimulationState:
    """
    Fase 2: Vuelo libre (motor apagado, ascenso/descenso balístico).

    Responsable: Persona 1.

    Recibe el estado actual y devuelve el siguiente estado (un paso
    de tiempo Δt más adelante), actualizando altura, velocidad y
    aceleración bajo los efectos de gravedad y arrastre.

    Parameters
    ----------
    state : SimulationState
        Estado actual del cohete.

    Returns
    -------
    SimulationState
        Siguiente estado, con phase=SimulationPhase.PHASE_2_FREE_FLIGHT.

    Nota: Esta función es un stub. Persona 1 debe reemplazar el
    cuerpo con la física real. NO debe ser implementada por Persona 3.
    """
    raise NotImplementedError(
        "simulate_phase2 debe ser implementada por Persona 1. "
        "Este es solo el contrato de la interfaz."
    )


def simulate_phase3(state: SimulationState) -> SimulationState:
    """
    Fase 3: Descenso.

    Responsable: Persona 2.

    Debe calcular, además de la cinemática de descenso:
        - energía cinética (state.kinetic_energy)
        - energía potencial (state.potential_energy)
        - energía total (state.total_energy)
        - velocidad terminal (state.terminal_velocity)

    Parameters
    ----------
    state : SimulationState
        Estado actual del cohete.

    Returns
    -------
    SimulationState
        Siguiente estado, con phase=SimulationPhase.PHASE_3_DESCENT.

    Nota: Esta función es un stub. Persona 2 debe reemplazar el
    cuerpo con la física real. NO debe ser implementada por Persona 3.
    """
    raise NotImplementedError(
        "simulate_phase3 debe ser implementada por Persona 2. "
        "Este es solo el contrato de la interfaz."
    )


def simulate_phase4(state: SimulationState) -> SimulationState:
    """
    Fase 4: Impacto.

    Responsable: Persona 2.

    Debe calcular, al momento del impacto contra el suelo:
        - fuerza de impacto (state.impact_force)
        - g's resultantes (state.g_force)
    y marcar phase=SimulationPhase.PHASE_4_IMPACT (o FINISHED si
    corresponde) para que el controlador detenga el bucle.

    Parameters
    ----------
    state : SimulationState
        Estado actual del cohete (justo antes o en el momento del impacto).

    Returns
    -------
    SimulationState
        Estado final del cohete.

    Nota: Esta función es un stub. Persona 2 debe reemplazar el
    cuerpo con la física real. NO debe ser implementada por Persona 3.
    """
    raise NotImplementedError(
        "simulate_phase4 debe ser implementada por Persona 2. "
        "Este es solo el contrato de la interfaz."
    )