import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def enviar_email(destinatarios, copias, tipo_reporte, html_correo):
    """
    Ensambla y transmite correos electrónicos en formato HTML utilizando el servidor SMTP configurado.
    
    Este módulo funciona de forma agnóstica; no sabe de dónde vienen los datos, 
    solo se encarga de empaquetar el HTML provisto y negociar la conexión segura.
    Depende directamente de las variables de entorno (.env) para credenciales y host.
    
    Args:
        destinatarios (str): Cadena con los correos de destino separados por comas.
        copias (str): Cadena con los correos en copia (CC) separados por comas. Puede estar vacía.
        tipo_reporte (str): Identificador del tipo de reporte ('polizas' o 'monitoreo') para el Asunto.
        html_correo (str): Código HTML pre-renderizado (Jinja2) que formará el cuerpo del correo.
    """
    try:
        # MIMEMultipart permite estructurar un correo complejo (necesario para inyectar HTML puro)
        msg = MIMEMultipart()
        msg['From'] = os.getenv("EMAIL_SENDER")
        msg['To'] = destinatarios
        
        # Solo agregamos el header CC visual si existen copias definidas en la web
        if copias: msg['Cc'] = copias
        
        # Generación dinámica del Asunto (Subject) basada en el botón presionado en la UI
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        if tipo_reporte == 'polizas':
            msg['Subject'] = f"ESTATUS {fecha_hoy}"
        else:
            msg['Subject'] = f"ESTATUS {fecha_hoy}"
        
        # Adjuntamos el HTML que ya viene armado desde el template de app.py
        msg.attach(MIMEText(html_correo, 'html'))
        
        # Conexión al servidor SMTP corporativo (usualmente Office365 o similar)
        # Se hace un cast a int() para el puerto, con 587 como puerto TLS por defecto
        server = smtplib.SMTP(os.getenv("EMAIL_SMTP_SERVER"), int(os.getenv("EMAIL_SMTP_PORT", 587)))
        
        # starttls() es obligatorio en servidores modernos para encriptar el canal de comunicación
        server.starttls()
        server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
        
        # PREPARACIÓN DEL ENRUTAMIENTO (SMTP Envelope):
        # NOTA CRÍTICA: smtplib.sendmail requiere que TODOS los destinatarios (To y Cc) 
        # estén en una sola lista plana de Python. Los headers de arriba (msg['To'], msg['Cc']) 
        # son solo visuales para Outlook/Gmail, no enrutan el correo.
        todos_los_destinatarios = [e.strip() for e in destinatarios.split(',')]
        if copias: 
            todos_los_destinatarios += [e.strip() for e in copias.split(',')]
            
        # Disparo final del correo al servidor
        server.sendmail(os.getenv("EMAIL_SENDER"), todos_los_destinatarios, msg.as_string())
        server.quit()
        
        # Este log alimenta directamente la "Consola Web" de la UI mediante la intercepción en app.py
        print(f"¡[{datetime.now().strftime('%H:%M:%S')}] Correo ({tipo_reporte}) enviado con éxito al servidor SMTP!")
        
    except Exception as e:
        # Captura errores de red, credenciales inválidas o bloqueos de firewall corporativo
        print(f"¡Error crítico en el módulo notificador!: {e}")