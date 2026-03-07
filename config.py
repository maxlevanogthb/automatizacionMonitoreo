import os
from dotenv import load_dotenv

# Cargamos el archivo .env aquí para que los diccionarios puedan acceder a las contraseñas
load_dotenv()

# --- CREDENCIALES DE SERVIDORES ---
SSH_SERVER = {
    "host": os.getenv("SSH_HOST"),
    "user": os.getenv("SSH_USER"),
    "password": os.getenv("SSH_PASSWORD"),
    "port": int(os.getenv("SSH_PORT", 22))
}

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 1521)),
    "sid": os.getenv("DB_SID")
}

DB_CONFIG_EURAFR = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_EURAFR_HOST"), 
    "port": int(os.getenv("DB_PORT", 1521)),
    "sid": os.getenv("DB_SID")
}

# --- CONFIGURACIONES DEL NEGOCIO ---
FOLDERS_BY_COUNTRY = {
    "CO": ["/u01/sftp/COL/out/ivy/tline/Entrada/"],
    "EC": ["/u01/sftp/ECU/out/ivy/tline/Entrada/"],
    "CR": ["/u01/sftp/CRI/out/ivy/tline/Entrada/"],
    "HN": ["/u01/sftp/HON/out/ivy/tline/Entrada/"],
    "GT": ["/u01/sftp/GUA/out/ivy/tline/Entrada/"],
    "PA": ["/u01/sftp/PAN/out/ivy/tline/Entrada/"],
    "NI": ["/u01/sftp/NIC/out/ivy/tline/Entrada/"],
    "VE": ["/u01/sftp/VEN/out/ivy/tline/Entrada/"],
    "MA": ["/u01/sftp/MAR/out/ivy/tline/Entrada/"]
}

SCHEDULES = {
    "CO": {"inicio": "23:00", "fin": "23:59"},
    "EC": {"inicio": "23:00", "fin": "23:59"},
    "CR": {"inicio": "00:30", "fin": "00:59"},
    "HN": {"inicio": "01:00", "fin": "01:59"},
    "GT": {"inicio": "01:00", "fin": "01:59"},
    "PA": {"inicio": "01:00", "fin": "01:59"},
    "NI": {"inicio": "01:00", "fin": "01:59"},
    "VE": {"inicio": "00:00", "fin": "00:59"},
    "MA": {"inicio": "18:00", "fin": "19:00"}
}

DATOS_PAISES = {
    "CO": {"nombre": "Colombia", "centros": 47},
    "EC": {"nombre": "Ecuador", "centros": 19},
    "CR": {"nombre": "Costa Rica", "centros": 15},
    "HN": {"nombre": "Honduras", "centros": 10},
    "GT": {"nombre": "Guatemala", "centros": 34},
    "PA": {"nombre": "Panamá", "centros": 5},
    "NI": {"nombre": "Nicaragua", "centros": 7},
    "VE": {"nombre": "Venezuela", "centros": 5},
    "MA": {"nombre": "Marruecos", "centros": 7}
}