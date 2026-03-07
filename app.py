from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# Importamos nuestras configuraciones desde el archivo config.py
from config import SSH_SERVER, DB_CONFIG, DB_CONFIG_EURAFR, FOLDERS_BY_COUNTRY, SCHEDULES, DATOS_PAISES
# Importamos nuestras funciones de memoria
from memoria import cargar_estados, guardar_estados, cargar_notas_guardadas, guardar_notas
# Importamos nuestras funciones de consulta Oracle
from oracle_db import check_db_web, check_policies_web, check_ar_file_summary_web, check_files_log_web
# Importamos nuestras funciones de consulta SFTP
from sftp_server import check_server_web
# Importamos nuestras funciones de envios de correo
from notificador import enviar_email
import sys
from collections import deque
from flask import jsonify
import pytz

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave_monitoreo_123") # Flask necesita esto para los mensajes Flash

scheduler = BackgroundScheduler() 
scheduler.start()

# --- RUTAS LOGS ---
@app.route('/api/logs')
def api_logs():
    return jsonify(list(console_logs))

@app.route('/api/toggle_estado', methods=['POST'])
def api_toggle_estado():
    data = request.json
    estados = cargar_estados()
    estados[data['codigo']] = data['estado']
    guardar_estados(estados)
    return jsonify({"status": "ok"})

# --- NUEVA API: COLA DE TAREAS PROGRAMADAS ---
@app.route('/api/tareas')
def api_tareas():
    jobs = scheduler.get_jobs()
    tareas = []
    for job in jobs:
        # Extraemos a qué hora se va a ejecutar y qué tipo de reporte es
        tiempo = job.next_run_time.strftime('%H:%M:%S') if job.next_run_time else "Pendiente"
        tipo = job.args[4] if len(job.args) > 4 else "Desconocido"
        tareas.append({"id": job.id, "tiempo": tiempo, "tipo": tipo})
    return jsonify(tareas)


console_logs = deque(maxlen=50) # Guarda las últimas 50 líneas de logs

class ConsoleLogger:
    def __init__(self):
        self.terminal = sys.stdout
    def write(self, message):
        self.terminal.write(message)
        if message.strip():
            # Agregamos la hora a cada print automáticamente
            tiempo = datetime.now().strftime('%H:%M:%S')
            if not message.startswith("["):
                console_logs.append(f"[{tiempo}] {message.strip()}")
            else:
                console_logs.append(message.strip())
    def flush(self):
        self.terminal.flush()

# Redirigimos la salida del sistema a nuestra clase
sys.stdout = ConsoleLogger()
print("Sistema de monitoreo inicializado...")
# ---------------------------------


def obtener_datos_monitoreo():
    reporte = {}
    fecha_db = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    fecha_tabla = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%y")

    # Fechas de prueba
    #fecha_db = "20250407" 
    #fecha_tabla = "07/04/25"


    for country, info in DATOS_PAISES.items():
        reporte[country] = {
            "nombre": info["nombre"],
            "fecha": fecha_tabla,
            "centros": info["centros"],
            "sftp_archivos": [],  
            "ficha": 0, "efectivo": 0, "mov_det": 0, "fac": 0, "procesados": 0,
            "ftp": "0", "logs_state": "Sin datos", "polizas": 0, "horario": "✔️ OK"
        }
        
        check_server_web(country, FOLDERS_BY_COUNTRY[country], reporte[country])
        check_db_web(country, fecha_db, reporte[country])
        check_policies_web(country, fecha_db, reporte[country])
        check_ar_file_summary_web(country, fecha_db, reporte[country])
        check_files_log_web(country, fecha_db, reporte[country])

    return reporte

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    datos_completos = obtener_datos_monitoreo()
    
    # Revision de estados para saber que pais esta apagado
    estados_guardados = cargar_estados()
    
    # Se carga la memoria de las notas tal cual están en el JSON
    notas_guardadas = cargar_notas_guardadas()
    notas_monitoreo = notas_guardadas["monitoreo"]
    notas_polizas = notas_guardadas["polizas"]
    
    # Generamos las alertas
    notas_errores = []
    alertas_preventivas = []
    
    for country, datos in datos_completos.items():
        # A. Errores de SFTP/Logs (¡SE VALIDAN SIEMPRE, INCLUSO SI ESTÁ APAGADO!)
            if "archivos_error" in datos and datos["archivos_error"]:
                duplicados = [archivo.replace(" (D)", "") for archivo in datos["archivos_error"] if "(D)" in archivo]
                errores = [archivo.replace(" (E)", "") for archivo in datos["archivos_error"] if "(E)" in archivo]
                
                if duplicados:
                    notas_errores.append(f"En {datos['nombre']}, los siguientes archivos marcaron Duplicidad (D): {', '.join(duplicados)}.")
                if errores:
                    notas_errores.append(f"En {datos['nombre']}, los siguientes archivos marcaron Error (E): {', '.join(errores)}.")
            
            # ¡NUEVA POSICIÓN DEL CANDADO! 
            # Si el país está apagado, saltamos ÚNICAMENTE las validaciones de Cuadratura
            if estados_guardados.get(country) == 'apagado':
                continue 
                
            # B. Alerta Inteligente de Cuadratura (FAC vs PROCESADOS vs AR_FILE)
            try: fac_int = int(datos.get("fac", 0) or 0)
            except: fac_int = 0
                
            try: proc_int = int(datos.get("procesados", 0) or 0)
            except: proc_int = 0
                
            try: ftp_int = int(datos.get("ftp", 0) or 0)
            except: ftp_int = 0
                
            if fac_int > 0 and (proc_int == 0 or ftp_int == 0):
                alertas_preventivas.append(f"En {datos['nombre'].upper()}: Se detectaron {fac_int} FAC_ENC/DET, pero PROCESADOS o AR_FILE muestran 0.")
    
    # Encabezado temporal para las notas del correo
    alerta_hoy = ""
    if notas_errores:
        alerta_hoy = "SE DETECTARON INCIDENCIAS HOY:\n" + "\n".join(notas_errores) + "\n\n"

    return render_template('index.html', 
                           datos_tabla=datos_completos,
                           default_to=os.getenv("DEFAULT_TO", ""),
                           default_cc=os.getenv("DEFAULT_CC", ""),
                           alerta_hoy=alerta_hoy, 
                           alertas_preventivas=alertas_preventivas, 
                           notas_monitoreo=notas_monitoreo,
                           notas_polizas=notas_polizas,
                           estados=estados_guardados)


# Le agregamos el parámetro "incluir_incidencias"
def procesar_y_enviar_correo(destinatarios, copias, notas_usuario, estados_guardados, tipo_reporte, incluir_incidencias):
    with app.app_context(): 
        datos_completos = obtener_datos_monitoreo()
        
        for codigo, estado in estados_guardados.items():
            if estado == 'apagado':
                datos_completos[codigo]['ftp'] = 'apagado'
                
        notas_finales = notas_usuario
        
        # SOLO inyectamos los errores si el usuario dejó marcado el Checkbox
        if incluir_incidencias:
            notas_errores = []
            for country, datos in datos_completos.items():
                
                # ¡AQUÍ ESTÁ LA MAGIA! Borramos el "continue"
                # Ahora siempre revisará los archivos físicos (D/E), incluso si el país está apagado
                if "archivos_error" in datos and datos["archivos_error"]:
                    duplicados = [archivo.replace(" (D)", "") for archivo in datos["archivos_error"] if "(D)" in archivo]
                    errores = [archivo.replace(" (E)", "") for archivo in datos["archivos_error"] if "(E)" in archivo]
                    
                    if duplicados: 
                        notas_errores.append(f"En {datos['nombre']}, los siguientes archivos marcaron Duplicidad (D): {', '.join(duplicados)}.")
                    if errores: 
                        notas_errores.append(f"En {datos['nombre']}, los siguientes archivos marcaron Error (E): {', '.join(errores)}.")

            if notas_errores:
                alerta_fresca = "SE DETECTARON INCIDENCIAS HOY:\n" + "\n".join(notas_errores) + "\n\n"
                notas_finales = alerta_fresca + notas_usuario

        html_correo = render_template('correo.html', datos_tabla=datos_completos, notas=notas_finales, tipo_reporte=tipo_reporte)
        enviar_email(destinatarios, copias, tipo_reporte, html_correo)

@app.route('/enviar_correo', methods=['POST'])
def enviar_correo():
    destinatarios = request.form.get('destinatarios')
    copias = request.form.get('copias')
    notas = request.form.get('notas')
    hora_programada = request.form.get('hora_programada')
    tipo_reporte = request.form.get('tipo_reporte')
    
    # Leemos si el usuario dejó prendido el switch de incidencias
    incluir_incidencias = request.form.get('incluir_incidencias') == 'on'
    
    nuevos_estados = {}
    for codigo in DATOS_PAISES.keys():
        valor_checkbox = request.form.get(f'estado_{codigo}')
        nuevos_estados[codigo] = 'encendido' if valor_checkbox else 'apagado'
    guardar_estados(nuevos_estados)
    
    notas_limpias = notas.strip()
    notas_guardadas = cargar_notas_guardadas()
    notas_guardadas[tipo_reporte] = notas_limpias
    guardar_notas(notas_guardadas)
    
    if hora_programada: 
        hora, minuto = hora_programada.split(':')
        scheduler.add_job(
            func=procesar_y_enviar_correo, 
            trigger='cron', 
            hour=int(hora), 
            minute=int(minuto), 
            args=[destinatarios, copias, notas_limpias, nuevos_estados, tipo_reporte, incluir_incidencias], 
            id=f'envio_{datetime.now().timestamp()}'
        )
        flash(f"🕒 ¡El reporte {tipo_reporte} quedó programado! Se enviará automáticamente hoy a las {hora_programada}.", "success")
    else: 
        procesar_y_enviar_correo(destinatarios, copias, notas_limpias, nuevos_estados, tipo_reporte, incluir_incidencias) 
        flash(f"✅ ¡El reporte de {tipo_reporte} ha sido enviado por correo en este momento con éxito!", "success")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)