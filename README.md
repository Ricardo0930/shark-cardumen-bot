# SHARK CARDUMEN

Bot de investigación de mercado para observar el comportamiento de BTC, DOGE, PEPE y SHIB en Binance Spot. El proyecto está orientado a análisis de flujo de trades en tiempo real, sin órdenes ni fondos reales.

## Objetivo

- Capturar trades públicos del WebSocket de Binance Spot.
- Detectar señales de BTC en tiempo real usando una ventana móvil de 60 segundos y volumen relativo.
- Medir la reacción de DOGE, PEPE y SHIB durante 300 segundos desde la activación de la señal BTC.
- Guardar eventos auditables en CSV.
- Mantener un diseño seguro: sin API de trading ni fondos reales.

## Requisitos

- Python 3.10+
- pip
- acceso a Internet para consultar Binance public WebSocket

## Instalación en Windows

```powershell
cd C:\ruta\al\proyecto
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Si PowerShell bloquea la activación del entorno:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Configuración

Archivo `config.json`:

- `btc_threshold_percent`: valor inicial 0.5
- `btc_volume_ratio`: valor inicial 1.5
- `btc_window_seconds`: 60
- `observation_seconds`: 300
- `min_reaction_percent`: 0.05
- `btc_reversion_percent`: 0.10

## Modo demo

Este proyecto solo consume datos públicos de mercado y no envía órdenes. La sección `demo_mode` existe solo como referencia conceptual y nunca habilita operaciones reales ni creadas en el entorno de Binance.

## Ejecución

```powershell
python main.py
```

Se conectará a Binance public stream y registrará eventos en `data/events.csv`.

## Pruebas

```powershell
python -m pytest -q
```

## Estructura

- `binance_stream.py`: conexión WebSocket y reconexión automática.
- `market_data.py`: normalización de trades y timestamps.
- `btc_detector.py`: cálculo de umbral y volumen para BTC.
- `reaction_engine.py`: evaluación de DOGE/PEPE/SHIB.
- `event_manager.py`: lifecycle de eventos y cierre a 300s.
- `storage.py`: guardado de eventos en CSV.
- `metrics.py`: estadísticas y resumen de resultados.
- `main.py`: punto de entrada.

## Nota de seguridad

Este proyecto no conecta con Binance Spot API privada ni con fondos reales. No se usa Binance Demo Trading ni se generan órdenes. El acceso es solo a datos públicos de mercado.
