from binance.client import Client
from colorama import init, Fore
import os
import pygame
import subprocess
import threading
import time
import importlib
import sys

PIN = (time.strftime('%H:%M:%S')).replace(':', '')
print('PIN:', PIN)

# import dinamically the correct module
module_name = 'constants.base'
log_path = f'log/base/{PIN}'
if len(sys.argv) > 1 and sys.argv[1] == 'dev':
    module_name = 'constants.dev'
    log_path = f'log/dev/{PIN}'
constants = importlib.import_module(module_name)

if constants.SOUND['ACTIVE']:
    pygame.mixer.init()
    pygame.mixer.music.load(constants.SOUND['PATH'])
client = Client('', '', tld='com')
init(autoreset=True)

possible_operations = {}


def get_usdt_ticks():
    """Gets all symbols with USDT pair from Binance futures."""
    tick_list = client.futures_symbol_ticker()
    usdt_ticks = [tick['symbol']
                  for tick in tick_list if tick['symbol'].endswith('USDT')]
    return usdt_ticks


def get_klines(tick, interval, limit):
    """Gets candlestick data for a specific symbol."""
    return client.futures_klines(symbol=tick, interval=interval, limit=limit)


def get_ticker_info(tick):
    """Gets general information for a symbol."""
    return client.futures_ticker(symbol=tick)


def evaluate_variation(tick, klines, knumber):
    """Evaluates price variations in LONG, SHORT and FAST."""
    initial_price = float(klines[0][4])
    final_price = float(klines[knumber][4])

    # Evaluate LONG
    if initial_price > final_price:
        variation = round(
            ((initial_price - final_price) / initial_price) * 100, 2)
        process_entry(tick, variation, constants.LONG, final_price)

    # Evaluate SHORT
    if final_price > initial_price:
        variation = round(
            ((final_price - initial_price) / initial_price) * 100, 2)
        process_entry(tick, variation, constants.SHORT, final_price)

    # Evaluate FAST
    if knumber >= 3:
        fast_initial_price = float(klines[knumber - 2][4])
        fast_final_price = float(klines[knumber][4])
        if fast_final_price > fast_initial_price:
            fast_variation = round(
                ((fast_final_price - fast_initial_price) / fast_initial_price) * 100, 2)
            if fast_variation >= constants.VARIATION_FAST_PERCENTAGE:
                print_target(tick, constants.FAST_SHORT, fast_final_price)


def process_entry(tick, variation, type, current_price):
    """Processes a ticker entry if it meets the variation and volume conditions."""
    if variation >= constants.VARIATION_PERCENTAGE:
        info = get_ticker_info(tick)
        volume = float(info['quoteVolume'])
        if volume > 100_000_000 or variation >= constants.VARIATION_100_PERCENTAGE:
            print_target(tick, type, current_price)


def show_notification(title, message):
    """Shows a system notification without blocking the program."""
    notification_thread = threading.Thread(
        target=_show_notification_thread,
        args=(title, message),
        daemon=True
    )
    notification_thread.start()


def _show_notification_thread(title, message):
    """Thread function to display notification."""
    try:
        subprocess.run(
            ["zenity", "--info", f"--title={title}",
                f"--text={message}", f'--timeout={constants.CLOSE_NOTIFICATION_TIMEOUT}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print("Could not display notification")


def print_target(tick, type, current_price):
    """Prints the result of the evaluation."""

    if type['name'] == constants.LONG['name']:
        tp = round(current_price + (current_price *
                                    constants.TAKE_PROFIT_PERCENTAGE / 100), 5)
        sl = round(current_price - (current_price *
                                    constants.STOP_LOSS_PERCENTAGE / 100), 5)
    else:
        tp = round(current_price - (current_price *
                                    constants.TAKE_PROFIT_PERCENTAGE / 100), 5)
        sl = round(current_price + (current_price *
                                    constants.STOP_LOSS_PERCENTAGE / 100), 5)

    if (tick not in possible_operations.keys() or not possible_operations[tick]['is_active']) and len(possible_operations) < 4:
        possible_operations[tick] = {
            'type': type,
            'entry_price': current_price,
            'tp': tp,
            'sl': sl,
            'start_time': time.time(),
            'is_active': True
        }

        if constants.ACTIVE_LOG:
            os.makedirs(log_path, exist_ok=True)
            sufix = str(current_price)[-3:]
            with open(f'{log_path}/{type["name"]}-{tick}-{sufix}.txt', 'w') as file:
                file.write(f'PIN: {PIN}\n')
                file.write(
                    f'VariationPercentage: {constants.VARIATION_PERCENTAGE}%\n')
                file.write(
                    f'TakeProfitPercentage: {constants.TAKE_PROFIT_PERCENTAGE}%\n')
                file.write(
                    f'stopLossPercentage: {constants.STOP_LOSS_PERCENTAGE}%\n')
                file.write(f'-----------------\n')
                file.write(f'{type["emoji"]}{type["name"]}: {tick}\n')
                file.write(f'Hour: {time.strftime("%H:%M")}\n')
                file.write(f'EntryPrice: {current_price}\n')
                file.write(f'TakeProfit: {tp}\n')
                file.write(f'StopLoss: {sl}\n')
                file.write(f'-----------------\n')

        title = f'{type['emoji']}{type['name']}\n{tick}'
        message = f'Current price: {current_price}\nTake profit: {tp}\nStop loss: {sl}'
        show_notification(title, message)

        if constants.SOUND['ACTIVE']:
            pygame.mixer.music.play()

        print(f'Random number: {PIN}')
        print(f'{type['emoji']}{type['name']}: {tick}')
        print(f'Current price: {current_price}')
        print(f'Take profit: {tp}')
        print(f'Stop loss: {sl}', '\n')


def evaluate_operation_evolution():
    """Evaluates the evolution of saved possible operations."""
    print('[EVAL]PIN:', PIN)
    for tick, value in possible_operations.items():
        if not value['is_active']:
            continue

        operation_type = value['type']
        entry_price = value['entry_price']
        info = get_ticker_info(tick)
        sufix = str(entry_price)[-3:]
        current_price = float(info['lastPrice'])
        difference = round(((current_price * 100) / entry_price) - 100, 2)
        file_path = f'{log_path}/{operation_type["name"]}-{tick}-{sufix}.txt'

        if operation_type['name'] == constants.LONG['name']:
            deactivate = current_price >= value['tp'] or current_price <= value['sl']
            win_or_loss = 'WIN' if current_price >= value['tp'] else 'LOSS'
        else:
            deactivate = current_price <= value['tp'] or current_price >= value['sl']
            win_or_loss = 'WIN' if current_price <= value['tp'] else 'LOSS'

        if operation_type['name'] == constants.LONG['name']:
            if difference < 0:
                color = Fore.RED
                color_difference = constants.SHORT['emoji']
            else:
                color = Fore.GREEN
                color_difference = constants.LONG['emoji']
        else:
            if difference < 0:
                color = Fore.GREEN
                color_difference = constants.LONG['emoji']
            else:
                color = Fore.RED
                color_difference = constants.SHORT['emoji']
            difference *= -1

        if constants.ACTIVE_LOG:
            with open(file_path, 'a') as file:
                file.write(
                    f'{time.strftime("%H:%M:%S")};{entry_price};{current_price};{difference};{color_difference}\n')

            if deactivate:
                os.rename(
                    file_path, f'{log_path}/{win_or_loss}-{operation_type["name"]}-{tick}-{sufix}.txt')

        if deactivate:
            value['is_active'] = False

        print(color + f"Ticker: {tick}, Type: {operation_type}")
        print(
            color + f"Entry price: {entry_price}, Current price: {current_price}")
        print(color + f"TP: {value['tp']}, SL: {value['sl']}")
        print(color + f"Difference: {difference}%")
        print('\n')


def scan_coins():
    """Scans futures coins and evaluates their price variations."""
    ticks = get_usdt_ticks()

    for tick in ticks:
        klines = get_klines(tick, Client.KLINE_INTERVAL_1MINUTE, 30)
        if klines:
            evaluate_variation(tick, klines, len(klines) - 1)


def scanner_cycle():
    """Cycle that scans coins every X seconds."""
    while True:
        scan_coins()
        time.sleep(constants.SCAN_TICKER_CYCLE_TIME)


def evaluation_cycle():
    """Cycle that evaluates operations every X seconds."""
    while True:
        time.sleep(constants.EVALUATION_CYCLE_TIME)
        evaluate_operation_evolution()


if __name__ == "__main__":
    scanner_thread = threading.Thread(target=scanner_cycle, daemon=True)
    evaluation_thread = threading.Thread(target=evaluation_cycle, daemon=True)

    scanner_thread.start()
    evaluation_thread.start()

    scanner_thread.join()
    evaluation_thread.join()
