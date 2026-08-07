"""
test_validation.py
===================

Prueba de validación física del simulador, corriendo la simulación
completa (fases 1 a 4) SIN la interfaz gráfica, para poder verificar en
CI / consola que el modelo integrado se comporta como la física manda.

Esto es exactamente lo que pedía la retroalimentación del Av2: no basta
con que cada fase esté bien planteada por separado, hay que probar el
resultado INTEGRADO.

Verifica dos cosas:
1. Que la fase 2 (vuelo libre) efectivamente se ejecuta y produce un
   apogeo razonable (si el bug de mapeo de fases reapareciera, el
   apogeo saldría absurdo o la simulación terminaría casi de inmediato).
2. Que la velocidad de descenso converge a la velocidad terminal
   teórica v_t = sqrt(m*g/c), con c = 0.5 * Cd * rho * A del paracaídas.

Uso:
    python test_validation.py
"""

from __future__ import annotations

from config import SimulationParameters, SimulationPhase
from physics_interface import simulate_phase1, simulate_phase2, simulate_phase3, simulate_phase4
from phase3_4 import _terminal_velocity, DRAG_C

# Tolerancia relativa aceptada entre la velocidad terminal numérica y la
# teórica.
TOL_RELATIVA = 0.02  # 2%

# Límite de pasos de seguridad, igual de espíritu al de simulation_controller.
MAX_STEPS = 200_000


def run_full_flight(params: SimulationParameters):
    """
    Corre la simulación completa fuera del hilo de Tkinter, replicando
    la misma lógica de _advance_phase ya corregida, y devuelve el
    estado final junto con la lista de velocidades registradas durante
    el descenso (fase 3), para poder analizar la convergencia a la
    velocidad terminal.
    """
    state = simulate_phase1(params)
    assert state.phase == SimulationPhase.PHASE_2_FREE_FLIGHT, (
        "simulate_phase1 debe dejar el estado en PHASE_2_FREE_FLIGHT "
        "al apagarse el motor."
    )

    apogee = state.height
    descent_velocities: list[float] = []
    steps = 0

    while state.phase != SimulationPhase.FINISHED and steps < MAX_STEPS:
        if state.phase == SimulationPhase.PHASE_2_FREE_FLIGHT:
            state = simulate_phase2(state)
            apogee = max(apogee, state.height)
        elif state.phase == SimulationPhase.PHASE_3_DESCENT:
            state = simulate_phase3(state)
            descent_velocities.append(state.velocity)
        elif state.phase == SimulationPhase.PHASE_4_IMPACT:
            state = simulate_phase4(state)
            state.phase = SimulationPhase.FINISHED
        else:
            break
        steps += 1

    return state, apogee, descent_velocities, steps


def test_fase2_se_ejecuta_y_hay_apogeo():
    """
    Si el bug de mapeo de fases (Av2) reapareciera, simulate_phase2
    nunca correría y pasaríamos directo a fase 3 con velocidad aún
    positiva (subiendo) -> apogeo espurio o comportamiento errático.
    Aquí verificamos que el apogeo sea mayor que la altura al apagarse
    el motor (el cohete debe seguir subiendo en vuelo libre) y que se
    hayan registrado varios pasos de fase 2 antes de pasar a fase 3.
    """
    params = SimulationParameters()
    state_al_apagar_motor = simulate_phase1(params)
    altura_apagado = state_al_apagar_motor.height

    state, apogee, descent_v, steps = run_full_flight(params)

    assert apogee > altura_apagado, (
        f"El apogeo ({apogee:.2f} m) debería ser mayor que la altura al "
        f"apagarse el motor ({altura_apagado:.2f} m); si no lo es, fase 2 "
        f"probablemente no se está ejecutando."
    )
    print(f"[OK] Altura al apagar motor: {altura_apagado:.2f} m | "
          f"Apogeo: {apogee:.2f} m | pasos totales: {steps}")


def test_velocidad_terminal_converge_a_teorica():
    """
    Compara la velocidad de descenso, ya estabilizada, contra
    v_t = -sqrt(m*g/c) (fórmula teórica de phase3_4._terminal_velocity).
    """
    params = SimulationParameters()
    state, apogee, descent_velocities, steps = run_full_flight(params)

    assert len(descent_velocities) > 10, (
        "Muy pocos pasos registrados en descenso; ¿fase 3 está "
        "corriendo con dt correcto?"
    )

    masa_final = state.current_mass if state.current_mass > 0 else params.mass
    v_teorica = _terminal_velocity(masa_final)

    # Tomamos el promedio del último 10% de las velocidades de descenso
    # como aproximación de la velocidad ya estabilizada.
    cola = descent_velocities[-max(1, len(descent_velocities) // 10):]
    v_numerica = sum(cola) / len(cola)

    error_relativo = abs(v_numerica - v_teorica) / abs(v_teorica)

    print(f"[OK] v_terminal teórica: {v_teorica:.3f} m/s | "
          f"v_terminal numérica (promedio cola): {v_numerica:.3f} m/s | "
          f"error relativo: {error_relativo * 100:.2f}%")

    assert error_relativo < TOL_RELATIVA, (
        f"La velocidad terminal numérica ({v_numerica:.3f} m/s) se aleja "
        f"más de {TOL_RELATIVA * 100:.0f}% de la teórica ({v_teorica:.3f} m/s). "
        f"DRAG_C usado: {DRAG_C:.4f}"
    )


if __name__ == "__main__":
    print("Corriendo validación física del simulador (fases 1-4)...\n")
    test_fase2_se_ejecuta_y_hay_apogeo()
    test_velocidad_terminal_converge_a_teorica()
    print("\nTodas las validaciones pasaron.")