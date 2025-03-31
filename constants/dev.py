# Trading parameters
TRADING = {
    'STOP_LOSS_PERCENTAGE': 2,  # Stop loss percentage per operation
    'TAKE_PROFIT_PERCENTAGE': 2,  # Take profit percentage per operation
    'VARIATION_PERCENTAGE': 1.2,  # variation to activate the operation of possible pairs
    'VARIATION_100K_PERCENTAGE': 2,  # variation for pairs with volume less than 100k
    'VARIATION_FAST_PERCENTAGE': 1,  # variation for rapid upward movements
    'LOG_PATH': 'log/',  # Path to the log file
}

# Program config
ACTIVE_LOG = True
CLOSE_NOTIFICATION_TIMEOUT = 2  # seconds
EVALUATION_CYCLE_TIME = 15  # seconds
SCAN_TICKER_CYCLE_TIME = 27  # seconds
SOUND = {
    'ACTIVE': False,
    'PATH': 'media/piano.wav',
}
NOTIFICATIONS = {
    'ACTIVE': False,
}

# Operation types
FAST_SHORT = {
    'name': 'FAST SHORT',
    'emoji': '🟣🔴🔥'
}
LONG = {
    'name': 'LONG',
    'emoji': '🟣🟢'
}
SHORT = {
    'name': 'SHORT',
    'emoji': '🟣🔴'
}
