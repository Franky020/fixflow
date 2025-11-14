import os
import json
import firebase_admin
from firebase_admin import credentials

# Cargar JSON desde variable de entorno
firebase_config_json = os.environ.get("FIREBASE_CONFIG")

if firebase_config_json:
    firebase_config = json.loads(firebase_config_json)

    # Inicializar Firebase solo una vez
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
else:
    raise Exception("FIREBASE_CONFIG environment variable not found.")
