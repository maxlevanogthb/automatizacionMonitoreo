import oracledb
from datetime import datetime
from config import DB_CONFIG, DB_CONFIG_EURAFR, SCHEDULES

def get_db_connection(country_code):
    """
    Establece la conexión con la base de datos Oracle correspondiente.
    Maneja la lógica de enrutamiento: Marruecos (MA) usa un servidor dedicado, 
    mientras que LATAM usa el servidor principal.
    
    Args:
        country_code (str): Código ISO del país (ej. 'MX', 'MA').
    Returns:
        oracledb.Connection | None: Objeto de conexión si es exitosa, None si falla.
    """
    config = DB_CONFIG_EURAFR if country_code == "MA" else DB_CONFIG
    dsn = oracledb.makedsn(config["host"], config["port"], sid=config["sid"])
    try:
        conn = oracledb.connect(user=config["user"], password=config["password"], dsn=dsn)
        return conn
    except Exception as e:
        print(f"[{country_code}] Error connecting to Oracle: {e}")
        return None

def check_db_web(country_code, date, datos_pais):
    """
    Consulta la tabla 'logs_table' para obtener el conteo general de archivos 
    procesados por tipo (Ficha_de, Efectivo, Mov_Det, Fac_enc/det).
    También extrae la hora mínima y máxima de procesamiento para cruzarla 
    contra los horarios permitidos en config.py.
    
    Muta el diccionario 'datos_pais' inyectando los resultados.
    """
    conn = get_db_connection(country_code)
    if not conn: return
    
    cursor = conn.cursor()
    query = f"""
        SELECT country_code, substr(TABLE_NAME,1,12) AS web_service, 
               trunc(creation_date)-1 AS fecha,  
               count(*) AS archivos,
               MIN(creation_date) AS started,  
               MAX(creation_date) AS ended
        FROM logs_table
        WHERE trunc(creation_date) >= '01-01-2025' AND trunc(creation_date) <= '31-12-2026'
          AND logs_state = 'C'
          AND table_name LIKE '%{date}%'
          AND country_code = '{country_code}'
        GROUP BY country_code, substr(TABLE_NAME,1,12), trunc(creation_date)-1
        ORDER BY 1,4,5
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        tipo = row[1]
        cantidad = row[3]
        started = row[4]
        ended = row[5]

        # Validación de SLA (Acuerdo de Nivel de Servicio) de horarios
        if started and ended:
            started_ok = datetime.strptime(SCHEDULES[country_code]["inicio"], "%H:%M").time()
            ended_ok = datetime.strptime(SCHEDULES[country_code]["fin"], "%H:%M").time()
            started_time = started.time() if isinstance(started, datetime) else started
            ended_time = ended.time() if isinstance(ended, datetime) else ended
            
            # Si el inicio o el fin caen fuera de la ventana permitida, marcamos error
            if not (started_ok <= started_time <= ended_ok and started_ok <= ended_time <= ended_ok):
                datos_pais["horario"] = "❌ Fuera de horario"

        # Clasificación de archivos basada en el prefijo del nombre
        if "Ivy_Fac_enc" in tipo: datos_pais["fac"] = cantidad
        elif "Ivy_Fac_det" in tipo: datos_pais["procesados"] = cantidad
        elif "Ivy_Ficha_de" in tipo: datos_pais["ficha"] = cantidad
        elif "Ivy_Efectivo" in tipo: datos_pais["efectivo"] = cantidad
        elif "Ivy_Mov_Det" in tipo: datos_pais["mov_det"] = cantidad

    conn.close()

def check_policies_web(country_code, date, datos_pais):
    """
    Consulta 'tline_policy_header' para obtener el volumen total de pólizas emitidas.
    Contiene un mapeo duro (hardcoded) para cruzar ID_STRUCTURE con el código ISO del país.
    """
    conn = get_db_connection(country_code)
    if not conn: return
    
    formatted_date = datetime.strptime(date, "%Y%m%d").strftime("%d-%m-%Y")
    
    # Excepción de base de datos: Honduras se registra como 'HO' en lugar de 'HN'
    country_code_query = "HO" if country_code == "HN" else country_code
    
    cursor = conn.cursor()
    query = f"""
        select policy_date,  
            case 
            when ID_STRUCTURE = 2      then 'MX'  
            when ID_STRUCTURE = 221    then 'PE' 
            when ID_STRUCTURE = 141    then 'EC' 
            when ID_STRUCTURE = 181    then 'BR' 
            when ID_STRUCTURE = 222    then 'CO' 
            when ID_STRUCTURE = 223    then 'PY' 
            when ID_STRUCTURE = 224    then 'UY' 
            when ID_STRUCTURE = 240    then 'AR' 
            when ID_STRUCTURE = 241    then 'CR' 
            when ID_STRUCTURE = 242    then 'CL' 
            when ID_STRUCTURE = 247    then 'ES' 
            when ID_STRUCTURE = 246    then 'VE' 
            when ID_STRUCTURE = 260    then 'GT' 
            when ID_STRUCTURE = 245   then 'PA'
            when ID_STRUCTURE = 250    then 'HO'
            when ID_STRUCTURE = 277    then 'NI'
            when ID_STRUCTURE = 248    then 'MA'
            end Country,
            case 
            when id_attribute2 = 1      then 'OBM'  
            when id_attribute2 = 2      then 'OBL' 
            when id_attribute2 = 101    then 'RIC' 
            when id_attribute2 = 4      then 'BPE' 
            when id_attribute2 = 81     then 'BBR' 
            when id_attribute2 = 3    then 'BCL' 
            when id_attribute2 = 5    then 'BCO' 
            when id_attribute2 = 6     then 'BPY' 
            when id_attribute2 = 7     then 'BUY' 
            when id_attribute2 = 8     then 'BCR' 
            when id_attribute2 = 9     then 'BAR' 
            when id_attribute2 = 11     then 'BDI' 
            when id_attribute2 = 65    then 'BEC' 
            when id_attribute2 = 15    then 'BVE' 
            when id_attribute2 = 17    then 'BCA' 
            when id_attribute2 = 14    then 'NUT'
            when id_attribute2 = 16    then 'BHO'
            when id_attribute2 = 19    then 'BNI'
            when id_attribute2 = 22    then 'MAD'
            end legal_entity,  
            policty_status, 
            count(*) Policy_count
        from tline_policy_header 
        where policy_date = '{formatted_date}' 
        and case 
            when ID_STRUCTURE = 2      then 'MX'  
            when ID_STRUCTURE = 221    then 'PE' 
            when ID_STRUCTURE = 141    then 'EC' 
            when ID_STRUCTURE = 181    then 'BR' 
            when ID_STRUCTURE = 222    then 'CO' 
            when ID_STRUCTURE = 223    then 'PY' 
            when ID_STRUCTURE = 224    then 'UY' 
            when ID_STRUCTURE = 240    then 'AR' 
            when ID_STRUCTURE = 241    then 'CR' 
            when ID_STRUCTURE = 242    then 'CL' 
            when ID_STRUCTURE = 247    then 'ES' 
            when ID_STRUCTURE = 246    then 'VE' 
            when ID_STRUCTURE = 260    then 'GT' 
            when ID_STRUCTURE = 245   then 'PA'
            when ID_STRUCTURE = 250    then 'HO'
            when ID_STRUCTURE = 277    then 'NI'
            when ID_STRUCTURE = 248    then 'MA'
            end = '{country_code_query}'
        group by policy_date, policty_status, id_attribute2, id_structure
        order by policty_status
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    total_polizas = 0
    if rows:
        for row in rows:
            total_polizas += row[4] # Suma la columna 'Policy_count'
            
    datos_pais["polizas"] = total_polizas
    conn.close()

def check_ar_file_summary_web(country_code, date, datos_pais):
    """
    Verifica la tabla 'AR_FILE_SUMMARY' para cuadrar los archivos transferidos al FTP.
    Aplica regla de negocio: Los registros de AR se cuentan doble en DB, por lo que 
    el resultado se divide entre 2 (// 2) para obtener la cantidad real física.
    """
    # Panamá no aplica para esta validación, se salta por regla de negocio
    if country_code == "PA": return 
    
    conn = get_db_connection(country_code)
    if not conn: return
    
    country_code_query = "HO" if country_code == "HN" else country_code
    cursor = conn.cursor()
    query = f"select country_code, count(1), min(file_hour), max(file_hour) from AR_FILE_SUMMARY where FILE_NAME like '%{date}%' and country_code = '{country_code_query}' GROUP BY country_code"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if rows:
        for row in rows: 
            # División entera requerida por duplicidad de registros en BD
            cantidad_real = int(row[1]) // 2
            datos_pais["ftp"] = str(cantidad_real) 
            datos_pais["procesados"] = cantidad_real 
    conn.close()

def check_files_log_web(country_code, date, datos_pais):
    """
    Escanea la tabla 'logs_table' a nivel archivo para detectar fallos (D, E).
    Calcula el estado general del lote y construye la lista de archivos con error 
    para las alertas web y de correo.
    """
    conn = get_db_connection(country_code)
    if not conn: return
    
    country_code_query = "HO" if country_code == "HN" else country_code
    cursor = conn.cursor()
    query = f"select logs_state, table_name from logs_table where table_name like '%{date}%' and country_code = '{country_code_query}'"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    all_c = True
    archivos_error = [] 
    
    if rows:
        for row in rows:
            estado = row[0]
            archivo = row[1]
            if estado != "C": 
                all_c = False
                # Filtramos solo los estados D (Desconocido/Denegado) y E (Error)
                if estado in ['D', 'E']:
                    archivos_error.append(f"{archivo} ({estado})")
    
    # Si todos son 'C' (Completado) el lote está OK.
    datos_pais["logs_state"] = "C" if (all_c and rows) else "Pendiente/Error"
    datos_pais["archivos_error"] = archivos_error 
    conn.close()