import paramiko
from config import SSH_SERVER

def check_server_web(country, folders, datos_pais):
    """
    Establece una conexión SSH con el servidor de transferencia para listar 
    los archivos físicos pendientes en los directorios especificados.
    
    Muta el diccionario 'datos_pais' inyectando la lista de archivos encontrados 
    bajo la llave 'sftp_archivos', o un mensaje de error si falla la red/credenciales.
    
    Args:
        country (str): Código ISO del país (usado para contexto/trazabilidad).
        folders (list): Lista de rutas absolutas (strings) a escanear en el servidor.
        datos_pais (dict): Diccionario principal con el estado actual del país.
    """
    ssh_client = None
    try:
        # Inicializamos el cliente principal de SSH
        ssh_client = paramiko.SSHClient()
        
        # Política de llaves: Auto-aceptamos el host si es la primera vez que nos conectamos
        # (Evita que el script se cuelgue esperando confirmación manual [Y/n])
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conexión por contraseña. 
        # look_for_keys=False y allow_agent=False previenen que Paramiko intente 
        # usar llaves SSH locales de Windows, lo cual podría bloquear la cuenta por reintentos.
        ssh_client.connect(
            hostname=SSH_SERVER["host"], 
            username=SSH_SERVER["user"],
            password=SSH_SERVER["password"], 
            look_for_keys=False, 
            allow_agent=False, 
            timeout=10  # Timeout preventivo para evitar que la interfaz web se congele si el server cae
        )
        
        archivos = []
        for folder in folders:
            # Ejecutamos el comando de listado (ls).
            # El truco '2>/dev/null' envía los errores (ej. "carpeta no existe") a un agujero negro,
            # manteniendo el 'stdout' limpio solo con los nombres reales de los archivos.
            stdin, stdout, stderr = ssh_client.exec_command(f'ls "{folder}" 2>/dev/null')
            
            # Leemos la salida cruda, la decodificamos a texto y le quitamos espacios extra
            output_files = stdout.read().decode().strip()
            
            if output_files:
                # Si hay texto, dividimos por saltos de línea para aislar cada archivo
                archivos.extend([a.strip() for a in output_files.split('\n') if a.strip()])
        
        # Asignamos la lista limpia de archivos al diccionario
        datos_pais["sftp_archivos"] = archivos 
        
    except Exception as e:
        # Si la conexión falla, inyectamos el error en la tabla para no romper la app principal
        datos_pais["sftp_archivos"] = [f"Error de conexión: {e}"]
        
    finally:
        # Bloque crítico: Siempre cerramos la sesión SSH, incluso si hubo un crash.
        # Esto previene el agotamiento de sockets (Too many open files) en el servidor origen.
        if ssh_client:
            ssh_client.close()