import sys
import importlib

# Definir el módulo base
module_name = "constants.base"

# Verificar si hay un argumento y si es "dev"
if len(sys.argv) > 1 and sys.argv[1] == "dev":
    module_name = "constants.dev"

# Importar dinámicamente el módulo correcto
constants = importlib.import_module(module_name)

# Acceder a las constantes
print(f"Usando {module_name}: {constants.SOUND}")
