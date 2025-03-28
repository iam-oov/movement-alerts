import threading
import subprocess


def run_instance(config):
    cmd = ["python", "main.py"] + config
    subprocess.run(cmd)

# ------------------------------------
# (1)'STOP_LOSS_PERCENTAGE': 3.50,  # Stop loss percentage per operation
# (2)'TAKE_PROFIT_PERCENTAGE': 3.50,  # Take profit percentage per operation
# (3)'VARIATION_PERCENTAGE': 5,  # variation to activate the operation of possible pairs
# (4)'VARIATION_100K_PERCENTAGE': 7,  # variation for pairs with volume less than 100k
# (5)'VARIATION_FAST_PERCENTAGE': 2,  # variation for rapid upward movements
# Example of config:
# configs = [
#     ["(1)", "(2)", "(3)", "(4)", "(5)"],
#     ...
# ]
# ------------------------------------


name_block = "bloque/sl"
config_block = [
    ["1.5", "1.7", "2", "4", "1.5"],
    ["2.0", "1.7", "2", "4", "1.5"],
    ["2.3", "1.7", "2", "4", "1.5"],
    ["2.5", "1.7", "2", "4", "1.5"],
    ["3.0", "1.7", "2", "4", "1.5"],
]
config_sl = [config + [f"log/dev/{name_block}/"]
             for config in config_block]

name_block = "bloque/rr_1"
config_block = [
    ["1.2", "1.2", "2", "4", "1.5"],
    ["1.5", "1.5", "2", "4", "1.5"],
    ["1.7", "1.7", "2", "4", "1.5"],
    ["2.1", "2.1", "2", "4", "1.5"],
    ["2.5", "2.5", "2", "4", "1.5"],
    ["2.7", "2.7", "2", "4", "1.5"],
]
config_rr_1 = [config + [f"log/dev/{name_block}/"]
               for config in config_block]


configs = config_sl  # + config_rr_1

threads = []

for config in configs:
    t = threading.Thread(target=run_instance, args=(config,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
