from binance.client import Client
import time
import pandas as pd
from datetime import datetime

variacion = 5  # Variación en los últimos 30 minutos en porcentaje
# Variación en los últimos 30 minutos en porcentaje si tiene menos de 100k de volumen
variacion_100 = 7
variacionfast = 2  # Variación en los últimos 2 minutos en porcentaje

client = Client('', '', tld='com')

# Función para obtener el MACD y la Signal Line


def calcular_macd(klines):
    # Extraer los precios de cierre de las velas
    closes = [float(kline[4]) for kline in klines]
    df = pd.DataFrame(closes, columns=['Close'])

    # Calcular las EMAs
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

    # Calcular el MACD
    df['MACD'] = df['EMA12'] - df['EMA26']

    # Calcular la Signal Line (EMA de 9 días sobre el MACD)
    df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Retornar el último valor del MACD y la Signal Line
    macd = df['MACD'].iloc[-1]
    signal_line = df['Signal Line'].iloc[-1]
    return macd, signal_line


def buscarticks():
    ticks = []
    lista_ticks = client.futures_symbol_ticker()
    print('Numero de monedas encontradas #' + str(len(lista_ticks)))

    for tick in lista_ticks:
        if tick['symbol'][-4:] != 'USDT':  # seleccionar todas las monedas en el par USDT
            continue
        ticks.append(tick['symbol'])

    print('Numero de monedas encontradas en el par USDT: #' + str(len(ticks)))

    return ticks


def get_klines(tick):
    klines = client.futures_klines(
        symbol=tick, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30)
    return klines


def infoticks(tick):
    info = client.futures_ticker(symbol=tick)
    return info


def human_format(volumen):
    magnitude = 0
    while abs(volumen) >= 1000:
        magnitude += 1
        volumen /= 1000.0
    return '%.2f%s' % (volumen, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def porcentaje_klines(tick, klines, knumber):
    inicial = float(klines[0][4])
    final = float(klines[knumber][4])

    # Calcular el MACD y la Signal Line
    macd, signal_line = calcular_macd(klines)

    # Obtener la hora actual
    hora_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # LONG
    if inicial > final:
        result = round(((inicial - final) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                print('LONG: ' + tick)
                print('Current price: ' + info['lastPrice'])
                print('Variacion: ' + str(result) + '%')
                print('Volumen: ' + human_format(volumen))
                print('Precio max: ' + info['highPrice'])
                print('Precio min: ' + info['lowPrice'])
                print('MACD: ' + str(macd))
                print('Signal Line: ' + str(signal_line))
                print('Hora: ' + hora_actual)
                print('')

    # SHORT
    if final > inicial:
        result = round(((final - inicial) / inicial) * 100, 2)
        if result >= variacion:
            info = infoticks(tick)
            volumen = float(info['quoteVolume'])
            if volumen > 100000000 or result >= variacion_100:
                print('SHORT: ' + tick)
                print('Current price: ' + info['lastPrice'])
                print('Variacion: ' + str(result) + '%')
                print('Volumen: ' + human_format(volumen))
                print('Precio max: ' + info['highPrice'])
                print('Precio min: ' + info['lowPrice'])
                print('MACD: ' + str(macd))
                print('Signal Line: ' + str(signal_line))
                print('Hora: ' + hora_actual)
                print('')

    # FAST
    if knumber >= 3:
        inicial = float(klines[knumber-2][4])
        final = float(klines[knumber][4])
        if inicial < final:
            result = round(((final - inicial) / inicial) * 100, 2)
            if result >= variacionfast:
                info = infoticks(tick)
                volumen = float(info['quoteVolume'])
                print('FAST SHORT!: ' + tick)
                print('Current price: ' + info['lastPrice'])
                print('Variacion: ' + str(result) + '%')
                print('Volumen: ' + human_format(volumen))
                print('Precio max: ' + info['highPrice'])
                print('Precio min: ' + info['lowPrice'])
                print('MACD: ' + str(macd))
                print('Signal Line: ' + str(signal_line))
                print('Hora: ' + hora_actual)
                print('')


while True:
    ticks = buscarticks()
    print('Escaneando monedas...')
    print('')
    for tick in ticks:
        klines = get_klines(tick)
        knumber = len(klines)
        if knumber > 0:
            knumber = knumber - 1
            porcentaje_klines(tick, klines, knumber)
    print('Esperando 30 segundos...')
    print('')
    time.sleep(30)
