import websocket
import json
import threading
import time
from binance.client import Client
from collections import defaultdict, deque
from datetime import datetime
from pynput import keyboard
import os

# Configuración de variaciones
VARIACION = 5  # Variación en los últimos 30 minutos (en porcentaje)
# Variación para pares con volumen menor a 100k (en porcentaje)
VARIACION_100 = 7
VARIACION_FAST = 2  # Variación en los últimos 2 minutos (en porcentaje)

# API Binance (dejar vacío para acceso a datos públicos)
client = Client('', '', tld='com')

# Archivo que contiene la lista de activos
ASSETS_FILE = "crypto_assets.txt"

# Variables globales
CRYPTO_ASSETS = []
price_history = defaultdict(lambda: deque(maxlen=30))
posibles_operaciones = {}
ws = None
restart_required = False


def load_crypto_assets():
    """Carga la lista de activos desde un archivo de texto."""
    global CRYPTO_ASSETS

    # Crear el archivo si no existe
    if not os.path.exists(ASSETS_FILE):
        with open(ASSETS_FILE, "w") as f:
            default_assets = ['BTCUSDT']
            f.write('\n'.join(default_assets))

    # Leer los activos del archivo
    with open(ASSETS_FILE, "r") as f:
        CRYPTO_ASSETS = [line.strip()
                         for line in f.readlines() if line.strip()]

    print(f"Activos cargados: {', '.join(CRYPTO_ASSETS)}")
    return CRYPTO_ASSETS


def update_crypto_assets():
    """Actualiza la lista de activos y reinicia las conexiones."""
    global restart_required

    old_assets = set(CRYPTO_ASSETS)
    load_crypto_assets()
    new_assets = set(CRYPTO_ASSETS)

    if old_assets != new_assets:
        print("Lista de activos actualizada. Reiniciando conexiones...")
        restart_required = True
        if ws:
            ws.close()
    else:
        print("No hay cambios en la lista de activos.")


def formato_volumen(volumen):
    """Convierte un volumen numérico a formato legible (e.g., K, M, G)."""
    magnitudes = ['', 'K', 'M', 'G', 'T', 'P']
    magnitud = 0
    while abs(volumen) >= 1000:
        magnitud += 1
        volumen /= 1000.0
    return f'{volumen:.2f}{magnitudes[magnitud]}'


def procesar_entrada(tick, variacion, tipo, precio_actual):
    """Procesa la entrada de un ticker si cumple las condiciones de variación y volumen."""
    if variacion >= VARIACION:
        # Obtener información del ticker
        try:
            info = client.futures_ticker(symbol=tick)
            volumen = float(info['quoteVolume'])

            if volumen > 100_000_000 or variacion >= VARIACION_100:
                if tick not in posibles_operaciones.keys():
                    posibles_operaciones[tick] = {
                        "tipo": tipo,
                        "precio_entrada": precio_actual,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                imprimir_resultado(tick, variacion, tipo, info)
        except Exception as e:
            print(f"Error al obtener información para {tick}: {e}")


def imprimir_resultado(tick, variacion, tipo, info=None):
    """Imprime el resultado de la evaluación."""
    print(f'{tipo}: {tick}')
    print(f'Variación: {variacion}%')

    if info:
        volumen = formato_volumen(float(info['quoteVolume']))
        print(f'Volumen: {volumen}')
        print(f'Precio máx: {info["highPrice"]}')
        print(f'Precio mín: {info["lowPrice"]}')
    print('')


def evaluar_variacion(symbol, current_price):
    """Evalúa las variaciones de precio en LONG, SHORT y FAST."""
    if len(price_history[symbol]) < 3:
        return  # No hay suficientes datos para evaluar

    # Obtener precios para evaluación
    precio_inicial = price_history[symbol][0]
    precio_final = current_price

    # Para evaluación rápida (últimos 2 min)
    if len(price_history[symbol]) >= 3:
        precio_rapido_inicial = price_history[symbol][-3]
        precio_rapido_final = price_history[symbol][-1]

    # Evaluar LONG (bajada de precio)
    if precio_inicial > precio_final:
        variacion = round(
            ((precio_inicial - precio_final) / precio_inicial) * 100, 2)
        procesar_entrada(symbol, variacion, "LONG", precio_final)

    # Evaluar SHORT (subida de precio)
    if precio_final > precio_inicial:
        variacion = round(
            ((precio_final - precio_inicial) / precio_inicial) * 100, 2)
        procesar_entrada(symbol, variacion, "SHORT", precio_final)

    # Evaluar FAST (movimiento rápido en 2 minutos)
    if len(price_history[symbol]) >= 3 and precio_rapido_final > precio_rapido_inicial:
        variacion_fast = round(
            ((precio_rapido_final - precio_rapido_inicial) / precio_rapido_inicial) * 100, 2)
        if variacion_fast >= VARIACION_FAST:
            imprimir_resultado(symbol, variacion_fast, "FAST SHORT")


def evaluar_evolucion_operaciones():
    """Evalúa la evolución de las posibles operaciones guardadas."""
    print("\nEvaluando evolución de operaciones...")
    for key, value in list(posibles_operaciones.items()):
        type_operation = value['tipo']
        entry_price = value['precio_entrada']
        entry_time = value['timestamp']

        try:
            info = client.futures_ticker(symbol=key)
            precio_actual = float(info['lastPrice'])
            diferencia = round(
                ((precio_actual - entry_price) / entry_price) * 100, 2)

            if type_operation == "SHORT":
                diferencia = diferencia * -1

            print(
                f"Ticker: {key}, Tipo: {type_operation}, Hora entrada: {entry_time}")
            print(
                f"Precio entrada: {entry_price}, Precio actual: {precio_actual}")
            print(f"Diferencia: {diferencia}%\n")
        except Exception as e:
            print(f"Error al evaluar {key}: {e}")

    print("...ok\n")


def on_message(ws, message):
    """
    Función que se ejecuta al recibir un mensaje del servidor WebSocket.
    Procesa el precio y evalúa variaciones.
    """
    data = json.loads(message)

    # Verificar si es un mensaje de suscripción exitosa
    if 'result' in data:
        print(f"Suscripción exitosa: {data}")
        return

    # Verificar si es un mensaje de trade
    if 'e' in data and data['e'] == 'trade':
        symbol = data['s']
        price = float(data['p'])
        if price > 0:
            # Almacenar el precio
            price_history[symbol].append(price)

            # Evaluar variación cuando tengamos suficientes datos
            if len(price_history[symbol]) >= 30:  # 30 minutos de datos
                evaluar_variacion(symbol, price)


def on_error(ws, error):
    """
    Función que se ejecuta al ocurrir un error en la conexión WebSocket.
    """
    print(f"Error en WebSocket: {error}")
    ws.close()


def on_close(ws, close_status_code, close_msg):
    """
    Función que se ejecuta al cerrar la conexión WebSocket.
    """
    print(f"Conexión cerrada: {close_status_code} - {close_msg}")


def on_open(ws):
    """
    Función que se ejecuta al abrir la conexión WebSocket.
    """
    print("Conexión WebSocket abierta")

    # Suscribirse a múltiples streams de trade
    params = [f"{symbol.lower()}@trade" for symbol in CRYPTO_ASSETS]
    subscription_message = {
        "method": "SUBSCRIBE",
        "params": params,
        "id": 1
    }
    ws.send(json.dumps(subscription_message))
    print(f"Suscrito a: {params}")


def on_ping(ws, message):
    """
    Función que se ejecuta al recibir un mensaje de ping del servidor.
    """
    print("Ping recibido, enviando pong")


def keep_alive(ws):
    """
    Función que envía un ping al servidor cada 9 minutos para mantener la conexión activa.
    """
    while ws.sock and ws.sock.connected:
        time.sleep(540)  # 9 minutos
        try:
            ws.ping("keepalive")
            print("Enviando ping de keepalive")
        except:
            print("Error al enviar ping de keepalive")
            break


def inicializar_historicos():
    """
    Inicializa los datos históricos para cada activo usando la API REST
    """
    for symbol in CRYPTO_ASSETS:
        try:
            klines = client.futures_klines(
                symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30)
            for kline in klines:
                close_price = float(kline[4])
                price_history[symbol].append(close_price)
        except Exception as e:
            print(f"Error al cargar datos históricos para {symbol}: {e}")
    # imprimir la hora de inicialización en format 23:59
    print(
        f"Datos históricos inicializados a las {datetime.now().strftime('%H:%M')}")


def ciclo_evaluacion():
    """
    Ciclo que evalúa operaciones cada 2 minutos.
    """
    while True:
        time.sleep(120)  # 2 minutos
        if not restart_required:
            evaluar_evolucion_operaciones()


def actualizar_historicos_periodicamente():
    """
    Función que se ejecuta en un hilo separado para actualizar los datos históricos cada 60 segundos
    """
    while True:
        if not restart_required:
            inicializar_historicos()
        time.sleep(60)  # 1 minuto


def key_press_monitor():
    """
    Monitorea las teclas presionadas para actualizar la lista de activos.
    """
    def on_press(key):
        try:
            if key.char == 'u':
                print("\nTecla 'u' presionada. Actualizando lista de activos...")
                update_crypto_assets()
        except AttributeError:
            # Ignorar teclas especiales
            pass

    def on_release(key):
        # Si presionas Esc, detener el listener (aunque en este caso no lo usamos)
        if key == keyboard.Key.esc:
            return False

    # Iniciar el listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    print("Monitoreo de teclas iniciado. Presiona 'u' para actualizar la lista de activos.")


def iniciar_websocket():
    """
    Inicia la conexión WebSocket con Binance.
    """
    global ws, restart_required

    # URL del WebSocket para futuros de Binance
    websocket_url = "wss://fstream.binance.com/ws"

    # Configuración del WebSocket
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        on_ping=on_ping
    )

    # Iniciar WebSocket
    print(f"Iniciando monitoreo para: {', '.join(CRYPTO_ASSETS)}")
    restart_required = False
    ws.run_forever(ping_interval=60, ping_timeout=10)


def main():
    """
    Función principal que inicializa y ejecuta el programa.
    """
    global restart_required

    # Cargar activos desde el archivo
    load_crypto_assets()

    # Inicializar datos históricos
    inicializar_historicos()

    # Iniciar el monitoreo de teclas (no necesita un hilo separado con pynput)
    key_press_monitor()

    # Crear y iniciar hilo para actualizar datos históricos periódicamente
    historicos_thread = threading.Thread(
        target=actualizar_historicos_periodicamente, daemon=True)
    historicos_thread.start()

    # Hilo para evaluar operaciones
    evaluacion_thread = threading.Thread(target=ciclo_evaluacion, daemon=True)
    evaluacion_thread.start()

    # Bucle principal que reinicia la conexión WebSocket cuando sea necesario
    while True:
        iniciar_websocket()

        # Si cerramos por actualización, esperar un poco y reiniciar
        if restart_required:
            print("Reiniciando conexiones después de actualizar la lista de activos...")
            time.sleep(2)

            # Limpiar historiales para activos que ya no estamos monitoreando
            for symbol in list(price_history.keys()):
                if symbol not in CRYPTO_ASSETS:
                    del price_history[symbol]

            # Reinicializar los históricos
            inicializar_historicos()
        else:
            # Si cerramos por un error, esperar más tiempo antes de reintentar
            print("Conexión cerrada inesperadamente. Reintentando en 5 segundos...")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")
    except Exception as e:
        print(f"Error inesperado: {e}")
