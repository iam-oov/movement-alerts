# Trading parameters
TRADING = {
    'STOP_LOSS_PERCENTAGE': 3.5,  # Stop loss percentage per operation
    'TAKE_PROFIT_PERCENTAGE': 3.5,  # Take profit percentage per operation
    'VARIATION_PERCENTAGE': 5,  # variation to activate the operation of possible pairs
    'VARIATION_100K_PERCENTAGE': 6,  # variation for pairs with volume less than 100k
    'VARIATION_FAST_PERCENTAGE': 2,  # variation for rapid upward movements
}

# Program config
ACTIVE_LOG = True
CLOSE_NOTIFICATION_TIMEOUT = 15  # seconds
EVALUATION_CYCLE_TIME = 120  # seconds
SCAN_TICKER_CYCLE_TIME = 30  # seconds
SOUND = {
    'ACTIVE': True,
    'PATH': 'media/piano.wav',
}
NOTIFICATIONS = {
    'ACTIVE': True,
}
WIN = {
    'name': 'WIN',
    'emoji': '🟢'
}
LOSE = {
    'name': 'LOSE',
    'emoji': '🔴'
}
IN_PROGRESS = {
    'name': 'IN_PROGRESS',
    'emoji': '🟡'
}

# Operation types
FAST_SHORT = {
    'name': 'FAST_SHORT',
    'emoji': '🔴🔥'
}
LONG = {
    'name': 'LONG',
    'emoji': '🟢'
}
SHORT = {
    'name': 'SHORT',
    'emoji': '🔴'
}
