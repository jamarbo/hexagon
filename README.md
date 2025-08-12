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

## Preparación (si no tienes Python)

1.  **Instalar Python**:
    - Ve a [python.org](https://www.python.org/downloads/) y descarga la última versión de Python para tu sistema operativo.
    - **Importante (en Windows)**: Durante la instalación, asegúrate de marcar la casilla que dice **"Add Python to PATH"**.

2.  **Verificar la instalación**:
    - Abre una nueva terminal o `PowerShell` y escribe `python --version`. Si funciona, estás listo para el siguiente paso.

## Instalación y Ejecución

Una vez que tienes Python, sigue estos pasos en la terminal dentro de la carpeta del proyecto:

1.  **Crear y activar un entorno virtual**:
    ```pwsh
    # Este comando crea una carpeta .venv con un entorno de Python aislado
    python -m venv .venv

    # Activa el entorno. Debes hacer esto cada vez que abras una nueva terminal.
    .\.venv\Scripts\Activate.ps1
    ```

2.  **Instalar las dependencias**:
    ```pwsh
    # Instala pygame usando el archivo de requisitos
    pip install -r requirements.txt
    ```

3.  **Ejecutar el programa**:
    ```pwsh
    python .\main.py
    ```

## Controles
- **ESPACIO**: Agitar el contenedor.
- **ESC**: Salir.

## Notas
- La simulación ahora incluye múltiples pelotas, gravedad y la capacidad de "agitar" el contenedor.
- El código de colisiones ha sido actualizado para manejar interacciones entre múltiples pelotas.
- Si tienes problemas, asegúrate de que el entorno virtual esté activado (deberías ver `(.venv)` al principio de la línea de tu terminal).
