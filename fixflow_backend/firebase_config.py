import os
import json
import firebase_admin
from firebase_admin import credentials


# Obtiene la ruta absoluta del directorio actual
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta correcta al JSON (usa el nombre con guion medio)
#cred_path = os.path.join(os.path.dirname(BASE_DIR), "firebase-credentials.json")

# Inicializa Firebase solo una vez
# if not firebase_admin._apps:
#     cred = credentials.Certificate(cred_path)
#     firebase_admin.initialize_app(cred)

firebase_config_json = os.environ.get("FIREBASE_CONFIG")
if firebase_config_json:
    firebase_config = json.loads(firebase_config_json)

    # Inicializar Firebase solo una vez
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
else:
    raise Exception("FIREBASE_CONFIG environment variable not found.")
