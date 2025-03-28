import sys
import json

# Configuración por defecto (podría venir de un archivo JSON, YAML, etc.)
config = {
    "STOP_LOSS_PERCENTAGE": 10,
    "TAKE_PROFIT_PERCENTAGE": 20,
    "VARIATION_PERCENTAGE": 30,
    "VARIATION_100K_PERCENTAGE": 40,
    "VARIATION_FAST_PERCENTAGE": 50
}

# Cargar argumentos de línea de comandos
args = sys.argv[1:]  # Ignorar el nombre del script

# Si hay argumentos, sobrescribir valores en orden
for i, key in enumerate(config.keys()):
    if i < len(args):
        try:
            config[key] = int(args[i])  # Convertir a int si es posible
        except ValueError:
            pass  # Si no se puede convertir, dejar el valor original

print("Configuración final:", config)
