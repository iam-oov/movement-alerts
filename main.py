from binance.client import Client
from colorama import init, Fore
import builtins
import os
import pygame
import subprocess
import threading
import time
import importlib
import sys

# Global Variables
PIN = (time.strftime('%H:%M:%S')).replace(':', '')
print('-----------------')
print('PIN:', PIN)
print('-----------------')

# Dynamic Module Import
module_name = 'constants.base'
log_path = f'log/base/{PIN}'
is_dev = False
if len(sys.argv) > 1 and sys.argv[1] == 'dev':
    module_name = 'constants.dev'
    log_path = f'log/dev/{PIN}'
    is_dev = True

constants = importlib.import_module(module_name)
_original_print = builtins.print

print(f'STOP_LOSS_PERCENTAGE: {constants.STOP_LOSS_PERCENTAGE}%')
print(f'TAKE_PROFIT_PERCENTAGE: {constants.TAKE_PROFIT_PERCENTAGE}%')
print(f'VARIATION_PERCENTAGE: {constants.VARIATION_PERCENTAGE}%')
print(f'VARIATION_100K_PERCENTAGE: {constants.VARIATION_100K_PERCENTAGE}%')
print(f'VARIATION_FAST_PERCENTAGE: {constants.VARIATION_FAST_PERCENTAGE}%')


def custom_print(*args, force=False, **kwargs):
    """
    if `is_dev` is True, prints the message
    If `is_dev` is False, only print if `force=True`.
    """
    if is_dev or force:
        _original_print(*args, **kwargs)


# Override built-in print function
builtins.print = custom_print

# Initialize Sound and Binance Client
if constants.SOUND['ACTIVE']:
    pygame.mixer.init()
    pygame.mixer.music.load(constants.SOUND['PATH'])
client = Client('', '', tld='com')
init(autoreset=True)

possible_operations = {}


def get_usdt_ticks():
    """Gets all symbols with USDT pair from Binance futures."""
    tick_list = client.futures_symbol_ticker()
    return [tick['symbol'] for tick in tick_list if tick['symbol'].endswith('USDT')]


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

    if initial_price > final_price:
        variation = calculate_variation(initial_price, final_price)
        process_entry(tick, variation, constants.LONG, final_price)
    elif final_price > initial_price:
        variation = calculate_variation(final_price, initial_price)
        process_entry(tick, variation, constants.SHORT, final_price)

    if knumber >= 3:
        evaluate_fast_variation(tick, klines, knumber)


def evaluate_fast_variation(tick, klines, knumber):
    """Evaluates fast price variations."""
    fast_initial_price = float(klines[knumber - 2][4])
    fast_final_price = float(klines[knumber][4])
    if fast_final_price > fast_initial_price:
        fast_variation = calculate_variation(
            fast_final_price, fast_initial_price)
        if fast_variation >= constants.VARIATION_FAST_PERCENTAGE:
            print_target(tick, constants.FAST_SHORT, fast_final_price)


def calculate_variation(price1, price2):
    """Calculates percentage variation between two prices."""
    return round(((price1 - price2) / price1) * 100, 2)


def process_entry(tick, variation, type, current_price):
    """Processes a ticker entry if it meets the variation and volume conditions."""
    if variation >= constants.VARIATION_PERCENTAGE:
        info = get_ticker_info(tick)
        volume = float(info['quoteVolume'])
        if volume > 100_000_000 or variation >= constants.VARIATION_100K_PERCENTAGE:
            print_target(tick, type, current_price)


def show_notification(title, message):
    """Shows a system notification without blocking the program."""
    threading.Thread(
        target=_show_notification_thread,
        args=(title, message),
        daemon=True
    ).start()


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
    tp, sl = calculate_tp_sl(type, current_price)

    if tick not in possible_operations or not possible_operations[tick]['is_active']:
        save_operation(tick, type, current_price, tp, sl)
        notify_operation(tick, type, current_price, tp, sl)


def calculate_tp_sl(type, current_price):
    """Calculates Take Profit and Stop Loss values."""
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
    return tp, sl


def save_operation(tick, type, current_price, tp, sl):
    """Saves operation details to a log file."""
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
                f'StopLossPercentage: {constants.STOP_LOSS_PERCENTAGE}%\n')
            file.write(f'-----------------\n')
            file.write(f'{type["emoji"]}{type["name"]}: {tick}\n')
            file.write(f'Hour: {time.strftime("%H:%M")}\n')
            file.write(f'EntryPrice: {current_price}\n')
            file.write(f'TakeProfit: {tp}\n')
            file.write(f'StopLoss: {sl}\n')
            file.write(f'-----------------\n')


def notify_operation(tick, type, current_price, tp, sl):
    """Sends a notification for the operation."""
    title = f'{type["emoji"]}{type["name"]}\n{tick}'
    message = f'Current price: {current_price}\nTake profit: {tp}\nStop loss: {sl}'
    show_notification(title, message)

    if constants.SOUND['ACTIVE']:
        pygame.mixer.music.play()

    print('-----------------', force=True)
    print(f'PIN: {PIN}', force=True)
    print(f'{type["emoji"]}{type["name"]}: {tick}', force=True)
    print(f'Current price: {current_price}', force=True)
    print(f'Take profit: {tp}', force=True)
    print(f'Stop loss: {sl}', '\n', force=True)


def evaluate_operation_evolution():
    """Evaluates the evolution of saved possible operations."""
    print('[EVAL]PIN:', PIN)
    for tick, value in possible_operations.items():
        if not value['is_active']:
            continue
        evaluate_single_operation(tick, value)


def evaluate_single_operation(tick, value):
    """Evaluates a single operation."""
    operation_type = value['type']
    entry_price = value['entry_price']
    info = get_ticker_info(tick)
    current_price = float(info['lastPrice'])
    difference = calculate_difference(
        entry_price, current_price, operation_type)
    file_path = f'{log_path}/{operation_type["name"]}-{tick}-{str(entry_price)[-3:]}.txt'

    deactivate, win_or_loss = check_deactivation(
        operation_type, current_price, value)
    log_operation(file_path, entry_price, current_price,
                  difference, operation_type, deactivate, win_or_loss)

    if deactivate:
        value['is_active'] = False

    print_operation_status(tick, operation_type, entry_price,
                           current_price, value, difference)


def calculate_difference(entry_price, current_price, operation_type):
    """Calculates the price difference."""
    difference = round(((current_price * 100) / entry_price) - 100, 2)
    if operation_type['name'] == constants.SHORT['name']:
        difference *= -1
    return difference


def check_deactivation(operation_type, current_price, value):
    """Checks if an operation should be deactivated."""
    if operation_type['name'] == constants.LONG['name']:
        deactivate = current_price >= value['tp'] or current_price <= value['sl']
        win_or_loss = 'WIN' if current_price >= value['tp'] else 'LOSS'
    else:
        deactivate = current_price <= value['tp'] or current_price >= value['sl']
        win_or_loss = 'WIN' if current_price <= value['tp'] else 'LOSS'
    return deactivate, win_or_loss


def log_operation(file_path, entry_price, current_price, difference, operation_type, deactivate, win_or_loss):
    """Logs operation details to a file."""
    if constants.ACTIVE_LOG:
        with open(file_path, 'a') as file:
            file.write(
                f'{time.strftime("%H:%M:%S")};{entry_price};{current_price};{difference};\n')
        if deactivate:
            os.rename(
                file_path, f'{log_path}/{win_or_loss}-{operation_type["name"]}-{str(entry_price)[-3:]}.txt')


def print_operation_status(tick, operation_type, entry_price, current_price, value, difference):
    """Prints the status of an operation."""
    color = Fore.GREEN if difference >= 0 else Fore.RED
    print(color + f"Ticker: {tick}, Type: {operation_type}")
    print(
        color + f"Entry price: {entry_price}, Current price: {current_price}")
    print(color + f"TP: {value['tp']}, SL: {value['sl']}")
    print(color + f"Difference: {difference}%\n")


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
