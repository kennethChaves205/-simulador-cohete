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
from phase3_4 import simulate_phase3 as _p3_impl
from phase3_4 import simulate_phase4 as _p4_impl

def simulate_phase1(params: SimulationParameters) -> SimulationState:
    """
    Fase 1: Propulsión (motor encendido).

    Responsable: Persona 1.

    Integra numéricamente (Euler) el movimiento del cohete mientras el
    motor está activo. La masa disminuye conforme se consume el combustible.
    Recorre TODOS los pasos de la fase y devuelve el estado final listo
    para que el controlador entre al bucle de la fase 2.

    Física aplicada
    ---------------
    - Fuerza neta:  F_neta = thrust - current_mass * gravity
    - Aceleración:  a = F_neta / current_mass
    - Euler semi-implícito (Euler-Cromer): primero se actualiza la
      velocidad con la aceleración del paso, y LUEGO se actualiza la
      posición con la velocidad ya actualizada (v_new), no con la
      anterior. Este orden es el que hace estable el método frente al
      Euler explícito puro, sobre todo una vez que fase 3 (paracaídas)
      encadena su propia integración a partir de este estado.
        v_new = v + a * dt
        y_new = y + v_new * dt
    - G's:          g_force = |a| / gravity
    - Consumo de masa: se reparte el combustible uniformemente en el tiempo
                       de encendido → dm/dt = fuel_mass / engine_duration
    """
    dt = params.time_step
    g = params.gravity

    # Tasa de consumo de combustible (kg por segundo)
    mass_flow = params.fuel_mass / params.engine_duration if params.engine_duration > 0 else 0.0

    # Estado inicial
    state = SimulationState(
        time=0.0,
        phase=SimulationPhase.PHASE_1_PROPULSION,
        height=params.initial_height,
        velocity=0.0,
        acceleration=0.0,
        current_mass=params.mass,
    )

    # Número de pasos que dura el motor
    n_steps = max(1, int(round(params.engine_duration / dt)))

    for _ in range(n_steps):
        # Masa actual (nunca menor que la masa seca)
        dry_mass = params.mass - params.fuel_mass
        state.current_mass = max(state.current_mass - mass_flow * dt, dry_mass)

        # Aceleración neta: empuje hacia arriba, peso hacia abajo
        f_neta = params.thrust - state.current_mass * g
        state.acceleration = f_neta / state.current_mass

        # Euler semi-implícito: velocidad primero, posición con la
        # velocidad YA actualizada (no con la anterior).
        new_velocity = state.velocity + state.acceleration * dt
        new_height = state.height + new_velocity * dt

        state.velocity = new_velocity
        state.height = max(new_height, 0.0)  # el cohete no puede bajar del suelo
        state.time += dt
        state.g_force = abs(state.acceleration) / g

        # Energías (antes solo se calculaban en fase 3 -> las gráficas de
        # Energía Cinética/Potencial/Total quedaban en 0 durante toda la
        # propulsión y el vuelo libre, la mayor parte del vuelo).
        state.kinetic_energy = 0.5 * state.current_mass * state.velocity ** 2
        state.potential_energy = state.current_mass * g * state.height
        state.total_energy = state.kinetic_energy + state.potential_energy

        # Registrar este paso en el historial para las gráficas
        state.history.append(state)

    # Al terminar el motor, transición a vuelo libre
    state.phase = SimulationPhase.PHASE_2_FREE_FLIGHT
    return state


def simulate_phase2(state: SimulationState) -> SimulationState:
    """
    Fase 2: Vuelo libre (motor apagado, ascenso balístico hasta apogeo).

    Responsable: Persona 1.

    El controlador llama esta función UNA VEZ por paso de tiempo (Δt).
    Solo actúa la gravedad: a = -g (constante).

    La fase termina cuando la velocidad cruza cero (apogeo) o cuando
    la altura cae a cero (caso borde: cohete muy lento al apagar motor).
    En ambos casos se transiciona a PHASE_3_DESCENT para que Persona 2
    tome el control del descenso con paracaídas.

    Física aplicada
    ---------------
    - Aceleración:  a = -g   (solo gravedad, sin empuje ni arrastre)
    - Euler semi-implícito: v_new = v + a * dt ; y_new = y + v_new * dt
      (velocidad NUEVA, mismo criterio de estabilidad usado en fase 1).
    - G's:          g_force = |a| / g = 1.0  (en vuelo libre siempre es 1 g)
    """
    # Leer Δt del historial: diferencia entre los dos últimos tiempos registrados.
    # Si el historial tiene al menos 2 puntos usamos esa diferencia; si no,
    # usamos 0.1 s como valor por defecto (no debería ocurrir en uso normal).
    history_times = state.history.time
    if len(history_times) >= 2:
        dt = history_times[-1] - history_times[-2]
    else:
        dt = 0.1

    g = 9.81  # m/s² — constante estándar

    # Aceleración en vuelo libre: solo gravedad
    state.acceleration = -g
    state.g_force = abs(state.acceleration) / g  # = 1.0 siempre en fase 2

    # Euler semi-implícito: velocidad primero, posición con la
    # velocidad YA actualizada.
    new_velocity = state.velocity + state.acceleration * dt
    new_height = state.height + new_velocity * dt

    state.velocity = new_velocity
    state.height = max(new_height, 0.0)
    state.time += dt

    # Energías (mismo motivo que en simulate_phase1: si no se calculan
    # aquí, las gráficas de energía quedan planas durante todo el vuelo
    # libre, que suele ser la fase más larga del ascenso).
    state.kinetic_energy = 0.5 * state.current_mass * state.velocity ** 2
    state.potential_energy = state.current_mass * g * state.height
    state.total_energy = state.kinetic_energy + state.potential_energy

    # NOTA (corrección Informe Final): NO se registra aquí en el historial.
    # El controlador (simulation_controller._emit_state) es el único
    # responsable de hacer state.history.append(state) para los pasos de
    # fase 2, 3 y 4. Si esta función también lo hiciera, cada paso quedaría
    # duplicado dos veces con el MISMO timestamp, y como simulate_phase2
    # calcula su propio dt restando las dos últimas marcas de tiempo del
    # historial (history_times[-1] - history_times[-2]), esa resta daría
    # 0 desde el segundo paso en adelante: el tiempo, la altura y la
    # velocidad quedarían congelados para siempre (justo el "no funciona,
    # solo aparece el cohete y no hace nada" que se ve al iniciar).

    # Condición de transición a fase 3:
    #   - Apogeo: velocidad cruza de positiva a negativa (o llega a cero)
    #   - Toca suelo (caso borde)
    if state.velocity <= 0.0 or state.height <= 0.0:
        state.phase = SimulationPhase.PHASE_3_DESCENT

    return state


def simulate_phase3(
    state: SimulationState, params: SimulationParameters | None = None
) -> SimulationState:
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
    params : Optional[SimulationParameters]
        Parámetros configurados desde la interfaz (drag_coefficient,
        cross_sectional_area, air_density, t_deploy). Si no se pasan
        (p. ej. código legado que aún llama simulate_phase3(state)),
        se usan los valores por defecto del paracaídas.

    Returns
    -------
    SimulationState
        Siguiente estado, con phase=SimulationPhase.PHASE_3_DESCENT.
    """
    return _p3_impl(state, params)


def simulate_phase4(
    state: SimulationState, params: SimulationParameters | None = None
) -> SimulationState:
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
    params : Optional[SimulationParameters]
        Parámetros de la interfaz (no se usan directamente en el cálculo
        de impacto hoy, pero se aceptan para mantener la misma firma que
        simulate_phase3).

    Returns
    -------
    SimulationState
        Estado final del cohete.
    """
    return _p4_impl(state, params)