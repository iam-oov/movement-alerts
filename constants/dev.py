# Trading parameters
STOP_LOSS_PERCENTAGE = 1  # Stop loss percentage per operation
TAKE_PROFIT_PERCENTAGE = 2  # Take profit percentage per operation
VARIATION_PERCENTAGE = 2  # variation to activate the operation of possible pairs
VARIATION_100_PERCENTAGE = 7  # variation for pairs with volume less than 100k
VARIATION_FAST_PERCENTAGE = 2  # variation for rapid upward movements

# Program config
ACTIVE_LOG = True
CLOSE_NOTIFICATION_TIMEOUT = 2  # seconds
EVALUATION_CYCLE_TIME = 15  # seconds
SCAN_TICKER_CYCLE_TIME = 120  # seconds
SOUND = {
    'ACTIVE': False,
    'PATH': 'media/piano.wav',
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
