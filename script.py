import threading
import time
from binance.client import Client
import pandas as pd
from datetime import datetime

# Configuración de variaciones y cliente
VARIACION = 5  # Variación en los últimos 30 minutos (en porcentaje)
# Variación para pares con volumen menor a 100k (en porcentaje)
VARIACION_100 = 7
VARIACION_FAST = 2  # Variación en los últimos 2 minutos (en porcentaje)
VOLUMEN_MINIMO = 100_000_000  # Volumen mínimo para evaluar operaciones
INTERVALO_EVALUACION = 120  # Intervalo de evaluación en segundos
INTERVALO_ESCANEO = 30  # Intervalo de escaneo en segundos

client = Client('', '', tld='com')

# Lista para almacenar posibles operaciones
posibles_operaciones = {}


def obtener_ticks_usdt():
    """Obtiene todos los símbolos con el par USDT de futuros en Binance."""
    try:
        lista_ticks = client.futures_symbol_ticker()
        return [tick['symbol'] for tick in lista_ticks if tick['symbol'].endswith('USDT')]
    except Exception as e:
        print(f"Error al obtener ticks: {e}")
        return []


def obtener_klines(tick, intervalo, limite):
    """Obtiene los datos de velas de un símbolo específico."""
    try:
        return client.futures_klines(symbol=tick, interval=intervalo, limit=limite)
    except Exception as e:
        print(f"Error al obtener klines para {tick}: {e}")
        return []


def obtener_info_ticker(tick):
    """Obtiene información general de un símbolo."""
    try:
        return client.futures_ticker(symbol=tick)
    except Exception as e:
        print(f"Error al obtener info para {tick}: {e}")
        return {}


def formato_volumen(volumen):
    """Convierte un volumen numérico a formato legible (e.g., K, M, G)."""
    magnitudes = ['', 'K', 'M', 'G', 'T', 'P']
    magnitud = 0
    while abs(volumen) >= 1000:
        magnitud += 1
        volumen /= 1000.0
    return f'{volumen:.2f}{magnitudes[magnitud]}'


def calcular_macd(klines, EMA1=6, EMA2=13, SIGNAL=5):
    """Calcula el MACD y la Signal Line."""
    closes = [float(kline[4]) for kline in klines]
    df = pd.DataFrame(closes, columns=['Close'])

    df['EMA1'] = df['Close'].ewm(span=EMA1, adjust=False).mean()
    df['EMA2'] = df['Close'].ewm(span=EMA2, adjust=False).mean()
    df['MACD'] = df['EMA1'] - df['EMA2']
    df['Signal Line'] = df['MACD'].ewm(span=SIGNAL, adjust=False).mean()

    return df['MACD'].iloc[-1], df['Signal Line'].iloc[-1]


def evaluar_variacion(tick, klines):
    """Evalúa las variaciones de precio en LONG, SHORT y FAST."""
    if len(klines) < 2:
        return  # Si no hay suficientes datos para calcular variaciones

    precio_inicial = float(klines[0][4])
    precio_final = float(klines[len(klines)-1][4])

    macd, signal_line = calcular_macd(klines)

    tipo = None
    if precio_inicial > precio_final:
        tipo = "LONG"
        variacion = round(
            ((precio_inicial - precio_final) / precio_inicial) * 100, 2)
    elif precio_final > precio_inicial:
        tipo = "SHORT"
        variacion = round(
            ((precio_final - precio_inicial) / precio_inicial) * 100, 2)

    if tipo:
        procesar_entrada(tick, variacion, macd,
                         signal_line, tipo, precio_final)


def procesar_entrada(tick, variacion, macd, signal_line, tipo, precio_actual):
    """Procesa la entrada de un ticker si cumple las condiciones de variación y volumen."""
    if variacion >= VARIACION:
        info = obtener_info_ticker(tick)
        volumen = float(info.get('quoteVolume', 0))
        if volumen > VOLUMEN_MINIMO or variacion >= VARIACION_100:
            if tick not in posibles_operaciones:
                posibles_operaciones[tick] = {
                    "tipo": tipo,
                    "precio_entrada": precio_actual
                }
            imprimir_resultado(tick, variacion, macd, signal_line, tipo, info)


def imprimir_resultado(tick, variacion, macd, signal_line, tipo, info=None):
    """Imprime el resultado de la evaluación."""
    hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    volumen = formato_volumen(float(info['quoteVolume']))
    print(f'Hora: {hora_actual}')
    print(f'{tipo}: {tick}')
    print(f'MACD: {macd}, Signal Line: {signal_line}')
    print(f'Variación: {variacion}%')
    print(f'Current price: {info['lastPrice']}')
    print(f'Volumen: {volumen}')
    print('\n')


def evaluar_evolucion_operaciones():
    """Evalúa la evolución de las posibles operaciones guardadas."""
    print("\nEvaluando evolución de operaciones...")
    for key, value in posibles_operaciones.items():
        tipo = value['tipo']
        entry_price = value['precio_entrada']

        info = obtener_info_ticker(key)
        precio_actual = float(info.get('lastPrice', 0))
        diferencia = round(
            ((precio_actual - entry_price) / entry_price) * 100, 2)

        if tipo == "SHORT":
            diferencia *= -1

        print(f"Ticker: {key}, Tipo: {tipo}")
        print(f"Precio entrada: {entry_price}, Precio actual: {precio_actual}")
        print(f"Diferencia: {diferencia}%\n")
    print(f"...ok\n")


def escanear_monedas():
    """Escanea las monedas en futuros y evalúa sus variaciones de precio."""
    ticks = obtener_ticks_usdt()
    if not ticks:
        return  # No continuar si no se encuentran símbolos con USDT

    print('Buscando...\n')
    for tick in ticks:
        klines = obtener_klines(tick, Client.KLINE_INTERVAL_1MINUTE, 30)
        if klines:
            evaluar_variacion(tick, klines)


def ciclo_escaner():
    """Ciclo que escanea monedas cada 30 segundos."""
    while True:
        escanear_monedas()
        time.sleep(INTERVALO_ESCANEO)


def ciclo_evaluacion():
    """Ciclo que evalúa operaciones cada 2 minutos."""
    while True:
        time.sleep(INTERVALO_EVALUACION)
        evaluar_evolucion_operaciones()


if __name__ == "__main__":
    thread_escaner = threading.Thread(target=ciclo_escaner, daemon=True)
    thread_evaluacion = threading.Thread(target=ciclo_evaluacion, daemon=True)

    thread_escaner.start()
    thread_evaluacion.start()

    thread_escaner.join()
    thread_evaluacion.join()
