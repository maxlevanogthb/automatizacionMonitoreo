import json
import os

def cargar_estados():
    """
    Lee el archivo de persistencia 'estados.json' para recuperar la configuración 
    de los interruptores (países encendidos/apagados) del panel de Cuadratura.
    
    Returns:
        dict: Diccionario con los códigos de país y su estado (ej. {"MX": "encendido", "MA": "apagado"}).
              Si el archivo no existe o está corrupto, retorna un diccionario vacío {}.
    """
    if os.path.exists('estados.json'):
        try:
            with open('estados.json', 'r') as f:
                return json.load(f)
        except:
            # Captura silenciosa: Si el JSON fue modificado manualmente y tiene errores de sintaxis, 
            # evitamos que la aplicación crashee (se detenga) y lo tratamos como "sin estados previos".
            return {}
    return {}

def guardar_estados(estados):
    """
    Sobrescribe el archivo 'estados.json' con el diccionario de estados actual.
    Esta función es llamada vía AJAX cada vez que el usuario mueve un interruptor en la UI.
    
    Args:
        estados (dict): Diccionario actualizado con los estados de los procesos por país.
    """
    with open('estados.json', 'w') as f:
        json.dump(estados, f)

def cargar_notas_guardadas():
    """
    Lee el archivo 'notas.json' para recuperar el último texto redactado por el operador.
    Mantiene la persistencia del área de texto (textarea) en el "Centro de Emisión".
    
    Returns:
        dict: Diccionario con las notas guardadas por tipo de reporte ('monitoreo' y 'polizas').
              Si el archivo no existe, inyecta y devuelve plantillas de texto oficiales por defecto.
    """
    if os.path.exists('notas.json'):
        try:
            with open('notas.json', 'r') as f:
                return json.load(f)
        except:
            pass
            
    # Fallback: Textos "boilerplate" (por defecto) si es la primera vez que se abre el sistema 
    # o si el archivo 'notas.json' fue eliminado intencionalmente para resetear el panel.
    return {
        "monitoreo": "Todo se encuentra validado y cargado correctamente en todos los países.\nLas secuencias coinciden y están dentro de los horarios permitidos.\nSin incidencias reportadas en el monitoreo de hoy.",
        "polizas": "Para este ciclo, se registra la correcta ejecución de los procesos activos de generación de pólizas autorizados que fueron oportunamente confirmados y comunicados a este nivel al momento del registro."
    }

def guardar_notas(notas_guardadas):
    """
    Sobrescribe 'notas.json' con los textos limpios (sin alertas dinámicas) 
    inmediatamente antes de disparar un correo.
    
    Args:
        notas_guardadas (dict): Diccionario con el texto final que escribió el operador.
    """
    with open('notas.json', 'w') as f:
        json.dump(notas_guardadas, f)