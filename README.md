# Simulador de Lanzamiento de Cohete

Proyecto universitario que simula el lanzamiento de un cohete a través de
cuatro fases (propulsión, vuelo libre, descenso e impacto), con una interfaz
gráfica en Tkinter y visualización en tiempo real con Matplotlib.

Este repositorio corresponde al trabajo de **Persona 3**: interfaz gráfica,
gráficas en tiempo real y la integración/controlador del sistema. La física
del cohete (fases 1–4) es responsabilidad de Persona 1 y Persona 2, y se
conecta mediante el archivo `physics_interface.py`.

## Descripción del proyecto

El sistema se divide en cuatro subsistemas físicos:

| Fase | Descripción | Responsable |
|------|-------------|-------------|
| 1. Propulsión | Motor encendido, ascenso inicial | Persona 1 |
| 2. Vuelo libre | Motor apagado, ascenso/descenso balístico | Persona 1 |
| 3. Descenso | Caída, cálculo de energías y velocidad terminal | Persona 2 |
| 4. Impacto | Fuerza de impacto y g's | Persona 2 |

Persona 3 (este código) provee:

- Interfaz gráfica en Tkinter con controles para todos los parámetros.
- 7 gráficas en tiempo real (Matplotlib embebido): altura, velocidad,
  aceleración, energía cinética, energía potencial, energía total y g's.
- Un `SimulationController` que ejecuta el bucle de simulación llamando a
  las funciones físicas (`simulate_phase1`..`simulate_phase4`) sin
  implementar ninguna ecuación.

## Estructura de carpetas

```
project/
├── main.py                   # Punto de entrada de la aplicación
├── ui.py                     # Interfaz gráfica (Tkinter)
├── plot_manager.py           # Gráficas en tiempo real (Matplotlib)
├── simulation_controller.py  # Bucle de simulación / integración
├── config.py                 # Dataclasses: parámetros y estado
├── physics_interface.py      # Contrato para Persona 1 y Persona 2
├── README.md
└── requirements.txt
```

## Cómo instalar Python

1. Descargar Python 3.10 o superior desde https://www.python.org/downloads/
2. Durante la instalación en Windows, marcar la casilla **"Add Python to PATH"**.
3. Verificar la instalación:

   ```bash
   python --version
   ```

## Crear entorno virtual

Desde la carpeta `project/`:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

## Instalar dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

### Dependencias

| Paquete | Versión |
|---------|---------|
| matplotlib | 3.9.2 |
| numpy | 1.26.4 |

`tkinter` no aparece en `requirements.txt` porque viene incluido con la
instalación estándar de Python (en algunas distribuciones de Linux debe
instalarse aparte, por ejemplo `sudo apt install python3-tk`).

## Cómo ejecutar

```bash
python main.py
```

Se abrirá la ventana principal del simulador.

## Explicación rápida de la interfaz

- **Panel izquierdo (Controles):**
    - Campos numéricos para todos los parámetros del modelo (altura inicial,
      masa, Δt, gravedad, empuje, duración del motor, coeficiente de
      arrastre, área, densidad del aire, masa de combustible).
    - Botones: **Iniciar simulación**, **Pausar**, **Continuar**, **Reiniciar**.
    - Panel de estado en vivo: fase actual, tiempo, altura, velocidad y
      aceleración.
    - Mensajes de estado/errores en la parte inferior.

- **Panel derecho (Gráficas):** 7 gráficas que se actualizan en tiempo real
  a medida que avanza la simulación.

## Problemas comunes

- **`NotImplementedError: simulate_phaseX debe ser implementada por...`**
  Este error es esperado hasta que Persona 1 y Persona 2 completen sus
  funciones en `physics_interface.py`. No es un bug de la interfaz.

- **La ventana no responde mientras corre la simulación.**
  El bucle de simulación corre en un hilo aparte (`threading`), por lo que
  esto no debería ocurrir. Si sucede, revisar que las funciones físicas no
  contengan bucles bloqueantes de larga duración sin ceder el control.

- **Error `_tkinter.TclError: no display name`** (Linux sin entorno gráfico)
  Tkinter requiere un entorno gráfico (X11/Wayland). Ejecutar en una
  máquina con interfaz gráfica o usar un servidor X virtual (`xvfb`).

- **`ModuleNotFoundError: No module named 'tkinter'`** (Linux)
  Instalar el paquete del sistema: `sudo apt install python3-tk` (Debian/Ubuntu).

## Cómo integrar los archivos de Persona 1 y Persona 2

1. Abrir `physics_interface.py`.
2. Reemplazar el cuerpo de `simulate_phase1` y `simulate_phase2` con la
   implementación de Persona 1, y el de `simulate_phase3` y
   `simulate_phase4` con la de Persona 2.
3. **Respetar la firma de cada función**:
    - Debe recibir `SimulationParameters` (solo `simulate_phase1`) o
      `SimulationState` (las demás).
    - Debe devolver siempre un `SimulationState` (ver `config.py`).
    - Cada función debe actualizar `state.phase` cuando corresponda avanzar
      a la siguiente etapa (usando los valores del enum `SimulationPhase`).
4. Persona 2 debe llenar, dentro de sus fases, los campos:
   `kinetic_energy`, `potential_energy`, `total_energy`, `impact_force`,
   `g_force` y `terminal_velocity` del `SimulationState`.
5. No es necesario modificar `ui.py`, `plot_manager.py` ni
   `simulation_controller.py`: estos archivos ya están preparados para
   consumir cualquier implementación que respete el contrato de
   `physics_interface.py`.
6. Alternativa: si Persona 1 y Persona 2 prefieren trabajar en sus propios
   archivos (por ejemplo `phase1_2.py`, `phase3_4.py`), pueden hacerlo y
   simplemente importar/reexportar sus funciones desde
   `physics_interface.py` para no romper el resto del proyecto.

## Buenas prácticas aplicadas

- Type hints en todas las funciones y dataclasses.
- Docstrings en todos los módulos, clases y funciones públicas.
- Separación de responsabilidades (UI, gráficas, controlador, configuración,
  contrato de física) siguiendo un enfoque similar a MVC:
    - **Modelo:** `config.py`, `physics_interface.py`
    - **Vista:** `ui.py`, `plot_manager.py`
    - **Controlador:** `simulation_controller.py`
- Sin ecuaciones físicas implementadas por Persona 3, tal como lo exige el
  alcance del proyecto.
