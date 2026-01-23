"""
Utilidades para formateo y transformación de datos
"""
from datetime import datetime


def limpiar_none(data):
    """Convierte valores None a strings vacíos para evitar mostrar 'none' en formularios"""
    if isinstance(data, dict):
        return {k: (v if v is not None else '') for k, v in data.items()}
    return data


def format_fecha_filter(fecha_str):
    """Formatea fechas al formato dd/mm/yyyy para mostrar en templates"""
    if not fecha_str or fecha_str == "-":
        return "-"
    try:
        # Manejar timestamps ISO con T y timezone
        fecha_limpia = fecha_str.split('T')[0] if 'T' in str(fecha_str) else str(fecha_str)
        # Intentar parsear en formato ISO (YYYY-MM-DD)
        fecha = datetime.strptime(fecha_limpia, '%Y-%m-%d')
        return fecha.strftime('%d/%m/%Y')
    except:
        # Si ya está en formato dd/mm/yyyy o no se puede parsear, retornar como está
        return str(fecha_str) if fecha_str else "-"


def calcular_color_ipo(fecha_ipo_str):
    """Calcula el color de fondo para la celda de IPO según la urgencia"""
    if not fecha_ipo_str or fecha_ipo_str == "-":
        return ""

    try:
        fecha_ipo = datetime.strptime(fecha_ipo_str, "%d/%m/%Y")
        hoy = datetime.now()
        diferencia = (fecha_ipo - hoy).days

        if -15 <= diferencia < 0:
            return "background-color: #FFF59D;"

        if diferencia >= 0 and diferencia <= 30:
            return "background-color: #FFCDD2;"

        return ""
    except:
        return ""


def calcular_color_contrato(fecha_contrato_str):
    """Calcula el color de fondo para la celda de contrato según vencimiento"""
    if not fecha_contrato_str or fecha_contrato_str == "-":
        return ""

    try:
        fecha_contrato = datetime.strptime(fecha_contrato_str, "%d/%m/%Y")
        hoy = datetime.now()
        diferencia = (fecha_contrato - hoy).days

        if diferencia <= 30:
            return "background-color: #FFCDD2;"

        if 30 < diferencia <= 90:
            return "background-color: #FFF59D;"

        return ""
    except:
        return ""
