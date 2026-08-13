""" GEINER - simulador de cohete- fase 3 y 4
phase3_4.py
============

Implementación de los Subsistemas 3 y 4 del simulador de cohete:

    - Subsistema 3 (simulate_phase3): descenso con paracaídas.
      F_drag = -c * v * |v|  y detección de velocidad terminal.
    - Subsistema 4 (simulate_phase4): aterrizaje / impacto.
      Cálculo de fuerza de impacto y verificación de umbrales G_max / F_imp_max.

Responsable: Persona 2.
"""

from __future__ import annotations

from config import SimulationState, SimulationPhase

# ---------------------------------------------------------------------------
# Constantes físicas del paracaídas y umbrales de seguridad
# ---------------------------------------------------------------------------
GRAVITY = 9.81                     # m/s^2
AIR_DENSITY = 1.225                # kg/m^3
PARACHUTE_DRAG_COEFFICIENT = 1.5   # adimensional (paracaídas hemisférico típico: 1.3-1.5)
PARACHUTE_AREA = 8.0               # m^2 (área efectiva ya desplegado el paracaídas)

# c agrupa 0.5 * Cd * rho * A, de forma que F_drag = -c * v * |v|
DRAG_C = 0.5 * PARACHUTE_DRAG_COEFFICIENT * AIR_DENSITY * PARACHUTE_AREA

# Umbrales de seguridad (ajustar según lo que pida el enunciado/rúbrica)
G_MAX = 15.0        # g's máximas toleradas
F_IMP_MAX = 5000.0  # N, fuerza de impacto máxima tolerada


def _default_dt(state: SimulationState) -> float:
    """Obtiene Δt a partir de las dos últimas marcas de tiempo del historial."""
    times = state.history.time
    if len(times) >= 2:
        return times[-1] - times[-2]
    return 0.1


def _terminal_velocity(mass: float) -> float:
    """Velocidad terminal teórica: v_t = -sqrt(m * g / c)."""
    if DRAG_C <= 0:
        return float("-inf")
    return -((mass * GRAVITY / DRAG_C) ** 0.5)


def simulate_phase3(state: SimulationState) -> SimulationState:
    """
    Fase 3: Descenso con paracaídas.

    Física aplicada
    ----------------
    - Arrastre:     F_drag = -c * v * |v|
    - Neta:         F_neta = -m*g + F_drag
    - Aceleración:  a = F_neta / m
    - Euler:        v_new = v + a * dt
                    y_new = y + v * dt   (velocidad ANTERIOR)
    - Energías:     E_c = 1/2 * m * v^2 ; E_p = m*g*y ; E_total = E_c + E_p
    - Velocidad terminal: v_t = -sqrt(m*g/c)
    """
    dt = _default_dt(state)
    mass = state.current_mass if state.current_mass > 0 else 1.0
    v = state.velocity

    f_drag = -DRAG_C * v * abs(v)
    state.acceleration = -GRAVITY + f_drag / mass
    state.g_force = abs(state.acceleration) / GRAVITY

    new_height = state.height + v * dt
    new_velocity = v + state.acceleration * dt

    state.height = max(new_height, 0.0)
    state.velocity = new_velocity
    state.time += dt
    state.current_mass = mass

    state.terminal_velocity = _terminal_velocity(mass)

    state.kinetic_energy = 0.5 * mass * state.velocity ** 2
    state.potential_energy = mass * GRAVITY * state.height
    state.total_energy = state.kinetic_energy + state.potential_energy

    # NOTA (corrección Informe Final): se quitó el history.append() que
    # estaba aquí. El controlador (simulation_controller._emit_state) ya
    # registra el estado una vez por paso; duplicarlo aquí dejaba dos
    # marcas de tiempo idénticas seguidas, y como esta misma función lee
    # su Δt restando las dos últimas marcas del historial, esa resta daba
    # 0 y la simulación se congelaba en su primer paso de descenso.

    if state.height <= 0.0:
        state.height = 0.0
        # NOTA (corrección Informe Final): esto decía PHASE_3_DESCENT,
        # o sea que al tocar altura 0 la fase "transicionaba" a la fase
        # en la que ya estaba. Nunca se llegaba a PHASE_4_IMPACT, así que
        # el controlador jamás llamaba a simulate_phase4 ni terminaba la
        # simulación (quedaba repitiendo fase 3 con altura 0 hasta el
        # límite de pasos de seguridad).
        state.phase = SimulationPhase.PHASE_4_IMPACT

    return state


def simulate_phase4(state: SimulationState) -> SimulationState:
    """
    Fase 4: Impacto / aterrizaje.

    Calcula la fuerza de impacto asumiendo frenado de v_impact a 0 en Δt,
    calcula g's, verifica umbrales G_MAX y F_IMP_MAX, y deja el estado en
    y=0, v=0 (condición de fin automático de la simulación).
    """
    mass = state.current_mass if state.current_mass > 0 else 1.0
    dt = _default_dt(state)

    v_impact = state.velocity
    impact_acceleration = (0.0 - v_impact) / dt if dt > 0 else 0.0

    state.acceleration = impact_acceleration
    state.impact_force = mass * abs(impact_acceleration)
    state.g_force = abs(impact_acceleration) / GRAVITY

    state.velocity = 0.0
    state.height = 0.0
    state.time += dt

    state.kinetic_energy = 0.0
    state.potential_energy = 0.0
    state.total_energy = 0.0

    if state.g_force > G_MAX:
        print(f"[ALERTA] Fuerza G en el impacto ({state.g_force:.2f} g) "
              f"supera el umbral G_MAX={G_MAX} g.")
    if state.impact_force > F_IMP_MAX:
        print(f"[ALERTA] Fuerza de impacto ({state.impact_force:.2f} N) "
              f"supera el umbral F_IMP_MAX={F_IMP_MAX} N.")

    # NOTA (corrección Informe Final): se quitó el history.append()
    # duplicado (ver misma nota en simulate_phase3).
    state.phase = SimulationPhase.PHASE_4_IMPACT
    return state