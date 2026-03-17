# 🚀 Panel de Monitoreo IVY/TLine

Aplicación web robusta desarrollada en Python (Flask) para la supervisión automatizada, validación de cuadratura y emisión de reportes de los procesos de facturación y pólizas (Operación Bimbo / TLine). 

El sistema centraliza la lectura de bases de datos Oracle y servidores SFTP en 9 países, ofreciendo una interfaz de control en tiempo real, detección de incidencias y un motor de envío de correos programados.

## ✨ Características Principales

* 📊 **Dashboard Web Reactivo:** Interfaz moderna en Modo Oscuro (Bootstrap 5) con actualización de memoria asíncrona (AJAX) sin recarga de página.
* 🔍 **Cuadratura Inteligente:** Cruce de datos avanzado entre la base de datos Oracle (FAC_ENC/DET, PROCESADOS) y los archivos físicos (AR_FILE) alojados en el FTP.
* 🚨 **Alertas Preventivas Automáticas:** Detección en caliente de desfases numéricos, ejecución fuera de horarios SLA, y clasificación de archivos con Duplicidad (D) o Error (E).
* ⏰ **Motor de Tareas Programadas:** Integración con `APScheduler` y `pytz` para encolar y disparar correos automáticos en la zona horaria correcta, con interfaz visual de la cola en tiempo real.
* 💻 **Consola Web (Live Logs):** Redirección del `stdout` del sistema hacia el navegador web para auditar la actividad del servidor sin necesidad de acceder a la consola de Windows.
* 💾 **Persistencia de Estado:** Memoria local automatizada mediante archivos `.json` que conserva configuraciones de países apagados/encendidos y el borrador de las notas del operador.
* 🚀 **Listo para Producción:** Despliegue optimizado para redes locales (LAN/VPN) utilizando el servidor WSGI `waitress`.

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.8+
* **Framework Web:** Flask, Jinja2
* **Base de Datos:** Oracle DB (`oracledb`)
* **Red y Archivos:** SSH/SFTP (`paramiko`)
* **Automatización:** `apscheduler`, `pytz`
* **Servidor de Producción:** `waitress`
* **Notificaciones:** SMTP nativo (`smtplib`, `email.mime`)

## ⚙️ Estructura del Proyecto
monitoreo/
├── app.py                 # Orquestador principal, servidor web y motor de tareas.
├── config.py              # Diccionarios de configuración (Credenciales, horarios y servidores).
├── oracle_db.py           # Conexiones y consultas SQL a las bases de datos Oracle.
├── sftp_server.py         # Conexión SSH y escaneo de directorios físicos físicos.
├── notificador.py         # Ensamblaje y transmisión de correos (SMTP).
├── memoria.py             # Lógica de persistencia (Lectura/Escritura de JSONs).
├── INICIAR_PANEL.bat      # Script de arranque rápido para entorno de producción.
├── .env                   # Variables de entorno (No versionado).
├── estados.json           # (Autogenerado) Persistencia de interruptores UI.
├── notas.json             # (Autogenerado) Persistencia de textos del operador.
└── templates/             
    ├── index.html         # Dashboard interactivo.
    └── correo.html        # Plantilla renderizada para los reportes enviados.

🚀 Instalación y Despliegue
pip install flask python-dotenv oracledb paramiko apscheduler waitress pytz

Configurar variables de entorno:
Crear un archivo .env en la raíz basándose en el siguiente formato:
FLASK_SECRET_KEY=clave_segura_flask
DEFAULT_TO=lista_destinatarios@tline.com
DEFAULT_CC=lista_copias@tline.com
DB_USER=usuario_oracle
DB_PASSWORD=password_oracle
DB_HOST=ip_servidor_oracle
DB_PORT=1521
DB_SID=sid_oracle
DB_EURAFR_HOST=ip_servidor_marruecos
SSH_HOST=ip_sftp
SSH_USER=usuario_sftp
SSH_PASSWORD=password_sftp
EMAIL_SENDER=tu_correo_remitente
EMAIL_PASSWORD=tu_password_smtp
EMAIL_SMTP_SERVER=smtp.tudominio.com
EMAIL_SMTP_PORT=587


