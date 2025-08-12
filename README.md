# Pelotas con gravedad rebotando dentro de un hexágono (Python + Pygame)

Simulación de múltiples pelotas de diferentes colores que rebotan dentro de un hexágono regular, con gravedad, colisiones entre pelotas y manejo robusto de colisiones contra lados y vértices.

## Características
- Hexágono centrado y escalado a la ventana.
- Varias pelotas de colores aleatorios con tamaños variados.
- Gravedad (aceleración hacia abajo) y rebotes contra las paredes.
- Colisiones elásticas entre pelotas con corrección posicional.
- Colisiones exactas contra segmentos y vértices con normales hacia el interior.
- Corrección posicional y "snap inside" para garantizar que ninguna pelota salga por errores numéricos.

## Requisitos
- Python 3.9+
- Windows, macOS o Linux

## Instalación

```powershell
# Crear y activar entorno virtual (recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```powershell
# Desde la carpeta del proyecto (esta misma):
python .\main.py

# O desde la raíz del repositorio:
python .\hexagon\main.py
```

## Controles
- ESC: salir

## Ajustes útiles
- Cambia el tamaño de la ventana en `run()` (variables `W`, `H`).
- Ajusta la "lentitud" del rebote en `World.__init__` modificando:
  - `self.restitucion` (0.3–0.6 típicamente)
  - `self.friccion_tangencial` (0.0–0.05)
  - `self.damping_global` (0.0–0.01)
- Para timestep fijo, establece `fixed_dt = 1/120.0` en `run()`.

## Notas
- Ajusta parámetros en `World.__init__`:
  - `self.gravity` para la gravedad (px/s^2).
  - `self.restitucion_pared` y `self.friccion_tangencial` para rebotes con paredes.
  - `self.restitucion_bolas` para rebotes entre pelotas.
  - Cambia `self._spawn_balls(n=10)` para variar la cantidad de pelotas.
- Las normales de las aristas apuntan hacia adentro asumiendo vértices CCW.
- Las pelotas rebotan también en los vértices del hexágono, no solo en los lados.
