import threading
from binance.client import Client
import os
import time

# Configuración de variaciones y cliente
VARIACION = 5  # Variación en los últimos 30 minutos (en porcentaje)
# Variación para pares con volumen menor a 100k (en porcentaje)
VARIACION_100 = 7
VARIACION_FAST = 2  # Variación en los últimos 2 minutos (en porcentaje)

client = Client('', '', tld='com')

# Lista para almacenar posibles operaciones
posibles_operaciones = {}


def obtener_ticks_usdt():
    """Obtiene todos los símbolos con el par USDT de futuros en Binance."""
    lista_ticks = client.futures_symbol_ticker()
    ticks_usdt = [tick['symbol']
                  for tick in lista_ticks if tick['symbol'].endswith('USDT')]
    return ticks_usdt


def obtener_klines(tick, intervalo, limite):
    """Obtiene los datos de velas de un símbolo específico."""
    return client.futures_klines(symbol=tick, interval=intervalo, limit=limite)


def obtener_info_ticker(tick):
    """Obtiene información general de un símbolo."""
    return client.futures_ticker(symbol=tick)


def formato_volumen(volumen):
    """Convierte un volumen numérico a formato legible (e.g., K, M, G)."""
    magnitudes = ['', 'K', 'M', 'G', 'T', 'P']
    magnitud = 0
    while abs(volumen) >= 1000:
        magnitud += 1
        volumen /= 1000.0
    return f'{volumen:.2f}{magnitudes[magnitud]}'


def evaluar_variacion(tick, klines, knumber):
    """Evalúa las variaciones de precio en LONG, SHORT y FAST."""
    precio_inicial = float(klines[0][4])
    precio_final = float(klines[knumber][4])

    # Evaluar LONG
    if precio_inicial > precio_final:
        variacion = round(
            ((precio_inicial - precio_final) / precio_inicial) * 100, 2)
        procesar_entrada(tick, variacion, "LONG", precio_final)

    # Evaluar SHORT
    if precio_final > precio_inicial:
        variacion = round(
            ((precio_final - precio_inicial) / precio_inicial) * 100, 2)
        procesar_entrada(tick, variacion, "SHORT", precio_final)

    # Evaluar FAST
    if knumber >= 3:
        precio_rapido_inicial = float(klines[knumber - 2][4])
        precio_rapido_final = float(klines[knumber][4])
        if precio_rapido_final > precio_rapido_inicial:
            variacion_fast = round(
                ((precio_rapido_final - precio_rapido_inicial) / precio_rapido_inicial) * 100, 2)
            if variacion_fast >= VARIACION_FAST:
                imprimir_resultado(tick, variacion_fast, "FAST SHORT")


def procesar_entrada(tick, variacion, tipo, precio_actual):
    """Procesa la entrada de un ticker si cumple las condiciones de variación y volumen."""
    if variacion >= VARIACION:
        info = obtener_info_ticker(tick)
        volumen = float(info['quoteVolume'])

        if volumen > 100_000_000 or variacion >= VARIACION_100:
            if tick not in posibles_operaciones.keys():
                posibles_operaciones[tick] = {
                    "tipo": tipo,
                    "precio_entrada": precio_actual
                }
            imprimir_resultado(tick, variacion, tipo, info)


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


def evaluar_evolucion_operaciones():
    """Evalúa la evolución de las posibles operaciones guardadas."""
    print("\nEvaluando evolución de operaciones...")
    for key, value in posibles_operaciones.items():
        type_operation = value['tipo']
        entry_price = value['precio_entrada']

        info = obtener_info_ticker(key)
        precio_actual = float(info['lastPrice'])
        diferencia = round(
            ((precio_actual - entry_price) / entry_price) * 100, 2)

        if type_operation == "SHORT":
            diferencia = diferencia * -1

        print(f"Ticker: {key}, Tipo: {type_operation}")
        print(f"Precio entrada: {
            entry_price}, Precio actual: {precio_actual}")
        print(f"Diferencia: {diferencia}%\n")
    print(f"...ok\n")


def escanear_monedas():
    """Escanea las monedas en futuros y evalúa sus variaciones de precio."""
    ticks = obtener_ticks_usdt()
    print('Escaneando monedas...\n')

    for tick in ticks:
        klines = obtener_klines(tick, Client.KLINE_INTERVAL_1MINUTE, 30)
        if klines:
            evaluar_variacion(tick, klines, len(klines) - 1)


def ciclo_escaner():
    """Ciclo que escanea monedas cada 30 segundos."""
    while True:
        escanear_monedas()
        time.sleep(30)


def ciclo_evaluacion():
    """Ciclo que evalúa operaciones cada 2 minutos."""
    while True:
        time.sleep(120)
        evaluar_evolucion_operaciones()


if __name__ == "__main__":
    thread_escaner = threading.Thread(target=ciclo_escaner, daemon=True)
    thread_evaluacion = threading.Thread(target=ciclo_evaluacion, daemon=True)

    thread_escaner.start()
    thread_evaluacion.start()

    thread_escaner.join()
    thread_evaluacion.join()
