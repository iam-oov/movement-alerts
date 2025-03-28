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


folder_name = "script_test_a"
configs = [
    ["1.5", "1.7", "2", "4", "1.5"],
    ["2.0", "1.7", "2", "4", "1.5"],
    ["2.3", "1.7", "2", "4", "1.5"],
    ["2.5", "1.7", "2", "4", "1.5"],
    ["3.0", "1.7", "2", "4", "1.5"],
]

configs = [config + [f"log/dev/{folder_name}{i + 1}/"]
           for i, config in enumerate(configs)]

threads = []

for config in configs:
    t = threading.Thread(target=run_instance, args=(config,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
