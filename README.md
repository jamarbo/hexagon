# Pelota rebotando dentro de un hexágono (Python + Pygame)

Simulación simple de una pelota que rebota dentro de un hexágono regular, con rebote lento (coeficiente de restitución bajo) y manejo robusto de detección y resolución de colisiones contra lados y vértices.

## Características
- Hexágono centrado y escalado a la ventana.
- Colisiones exactas contra segmentos y vértices con normales hacia el interior.
- Rebote lento: restitución < 1 y fricción tangencial para disipar energía.
- Corrección posicional y "snap inside" para garantizar que la pelota no salga por errores numéricos.

## Requisitos
- Python 3.9+
- Windows, macOS o Linux

## Instalación

```pwsh
# Crear y activar entorno virtual (recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```pwsh
python .\main.py
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
- La normal de cada arista está orientada hacia adentro asumiendo vértices generados CCW.
- La pelota rebotará también en vértices, no solo en lados.
