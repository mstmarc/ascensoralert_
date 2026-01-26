"""
HELPERS.PY - Funciones auxiliares para AscensorAlert
Optimiza y centraliza código repetitivo
"""

from functools import wraps
from flask import session, redirect, flash
from datetime import datetime
import requests

# ============================================
# CONFIGURACIÓN
# ============================================

SUPABASE_URL = None
HEADERS = None

def init_helpers(url, headers):
    """Inicializa los helpers con la configuración de Supabase"""
    global SUPABASE_URL, HEADERS
    SUPABASE_URL = url
    HEADERS = headers


# ============================================
# DECORADORES
# ============================================

def login_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# SISTEMA DE PERFILES Y PERMISOS
# ============================================

# Definición de módulos del sistema
MODULOS = {
    'inspecciones': 'Inspecciones (IPOs)',
    'clientes': 'Clientes/Comunidades',
    'equipos': 'Equipos/Ascensores',
    'oportunidades': 'Oportunidades Comerciales',
    'administradores': 'Administradores de Fincas',
    'visitas': 'Visitas',
    'home': 'Dashboard',
    'notificaciones_cliente': 'Notificaciones a Clientes'
}

# Definición de permisos por perfil
# 'read': puede ver | 'write': puede crear/editar | 'delete': puede eliminar
PERMISOS_POR_PERFIL = {
    'admin': {
        # Admin tiene acceso total a todo
        'inspecciones': {'read': True, 'write': True, 'delete': True},
        'clientes': {'read': True, 'write': True, 'delete': True},
        'equipos': {'read': True, 'write': True, 'delete': True},
        'oportunidades': {'read': True, 'write': True, 'delete': True},
        'administradores': {'read': True, 'write': True, 'delete': True},
        'visitas': {'read': True, 'write': True, 'delete': True},
        'home': {'read': True, 'write': True, 'delete': True},
        'notificaciones_cliente': {'read': True, 'write': True, 'delete': True}
    },
    'gestor': {
        # Gestor: todo EXCEPTO inspecciones
        'inspecciones': {'read': False, 'write': False, 'delete': False},
        'clientes': {'read': True, 'write': True, 'delete': True},
        'equipos': {'read': True, 'write': True, 'delete': True},
        'oportunidades': {'read': True, 'write': True, 'delete': True},
        'administradores': {'read': True, 'write': True, 'delete': True},
        'visitas': {'read': True, 'write': True, 'delete': True},
        'home': {'read': True, 'write': True, 'delete': True},
        'notificaciones_cliente': {'read': True, 'write': True, 'delete': True}
    },
    'visualizador': {
        # Visualizador: solo lectura, sin inspecciones
        'inspecciones': {'read': False, 'write': False, 'delete': False},
        'clientes': {'read': True, 'write': False, 'delete': False},
        'equipos': {'read': True, 'write': False, 'delete': False},
        'oportunidades': {'read': True, 'write': False, 'delete': False},
        'administradores': {'read': True, 'write': False, 'delete': False},
        'visitas': {'read': True, 'write': False, 'delete': False},
        'home': {'read': True, 'write': False, 'delete': False},
        'notificaciones_cliente': {'read': False, 'write': False, 'delete': False}
    },
    'tecnico': {
        # Técnico: solo acceso a notificaciones a clientes
        'inspecciones': {'read': False, 'write': False, 'delete': False},
        'clientes': {'read': False, 'write': False, 'delete': False},
        'equipos': {'read': False, 'write': False, 'delete': False},
        'oportunidades': {'read': False, 'write': False, 'delete': False},
        'administradores': {'read': False, 'write': False, 'delete': False},
        'visitas': {'read': False, 'write': False, 'delete': False},
        'home': {'read': True, 'write': False, 'delete': False},
        'notificaciones_cliente': {'read': True, 'write': True, 'delete': False}
    }
}


def obtener_perfil_usuario():
    """Obtiene el perfil del usuario actual desde la sesión"""
    return session.get("perfil", "visualizador")


def tiene_permiso(modulo, accion='read'):
    """
    Verifica si el usuario actual tiene permiso para una acción en un módulo

    Args:
        modulo: nombre del módulo ('inspecciones', 'clientes', etc.)
        accion: tipo de acción ('read', 'write', 'delete')

    Returns:
        bool: True si tiene permiso, False en caso contrario
    """
    perfil = obtener_perfil_usuario()

    # Si el perfil no existe en la configuración, denegar acceso
    if perfil not in PERMISOS_POR_PERFIL:
        return False

    # Si el módulo no existe, denegar acceso
    if modulo not in PERMISOS_POR_PERFIL[perfil]:
        return False

    # Retornar el permiso específico
    return PERMISOS_POR_PERFIL[perfil][modulo].get(accion, False)


def requiere_permiso(modulo, accion='read'):
    """
    Decorador que verifica permisos antes de ejecutar una ruta

    Uso:
        @app.route('/inspecciones')
        @login_required
        @requiere_permiso('inspecciones', 'read')
        def listar_inspecciones():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not tiene_permiso(modulo, accion):
                flash(f"No tienes permiso para acceder a este módulo", "error")
                return redirect("/home")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def solo_admin(f):
    """Decorador que solo permite acceso a usuarios con perfil admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if obtener_perfil_usuario() != 'admin':
            flash("Esta funcionalidad solo está disponible para administradores", "error")
            return redirect("/home")
        return f(*args, **kwargs)
    return decorated_function


def puede_escribir(modulo):
    """
    Función auxiliar para templates: verifica si el usuario puede crear/editar en un módulo

    Uso en Jinja2:
        {% if puede_escribir('clientes') %}
            <button>Crear Cliente</button>
        {% endif %}
    """
    return tiene_permiso(modulo, 'write')


def puede_eliminar(modulo):
    """
    Función auxiliar para templates: verifica si el usuario puede eliminar en un módulo

    Uso en Jinja2:
        {% if puede_eliminar('clientes') %}
            <button>Eliminar</button>
        {% endif %}
    """
    return tiene_permiso(modulo, 'delete')


def obtener_modulos_permitidos():
    """
    Retorna lista de módulos a los que el usuario tiene acceso (al menos lectura)
    Útil para generar menús dinámicos
    """
    perfil = obtener_perfil_usuario()
    modulos_permitidos = []

    if perfil in PERMISOS_POR_PERFIL:
        for modulo, permisos in PERMISOS_POR_PERFIL[perfil].items():
            if permisos.get('read', False):
                modulos_permitidos.append(modulo)

    return modulos_permitidos


# ============================================
# CLIENTE SUPABASE SIMPLIFICADO
# ============================================

class SupabaseClient:
    """Cliente simplificado para operaciones con Supabase"""
    
    @staticmethod
    def get(table, filters=None, select="*", order=None, limit=None, offset=None):
        """GET request a Supabase"""
        url = f"{SUPABASE_URL}/rest/v1/{table}?select={select}"
        if filters:
            url += f"&{filters}"
        if order:
            url += f"&order={order}"
        if limit:
            url += f"&limit={limit}"
        if offset is not None:
            url += f"&offset={offset}"
        return requests.get(url, headers=HEADERS)
    
    @staticmethod
    def post(table, data, select="id"):
        """POST request a Supabase"""
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        if select:
            url += f"?select={select}"
        return requests.post(url, json=data, headers=HEADERS)
    
    @staticmethod
    def patch(table, filters, data):
        """PATCH request a Supabase"""
        url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
        return requests.patch(url, json=data, headers=HEADERS)
    
    @staticmethod
    def delete(table, filters):
        """DELETE request a Supabase"""
        url = f"{SUPABASE_URL}/rest/v1/{table}?{filters}"
        return requests.delete(url, headers=HEADERS)
    
    @staticmethod
    def count(table, filters=None):
        """Cuenta registros en una tabla"""
        url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
        if filters:
            url += f"&{filters}"
        headers_with_count = {**HEADERS, "Prefer": "count=exact"}
        response = requests.get(url, headers=headers_with_count)
        if response.status_code == 200:
            content_range = response.headers.get("Content-Range", "0")
            return int(content_range.split("/")[-1])
        return 0


# ============================================
# FORMATEO DE FECHAS
# ============================================

def formatear_fecha(fecha_str, formato_entrada='%Y-%m-%d', formato_salida='%d/%m/%Y'):
    """Formatea una fecha de un formato a otro"""
    if not fecha_str or fecha_str == "-":
        return "-"
    try:
        # Manejar timestamps ISO con T
        fecha_limpia = fecha_str.split('T')[0]
        fecha = datetime.strptime(fecha_limpia, formato_entrada)
        return fecha.strftime(formato_salida)
    except:
        return "-"


def parse_fecha(fecha_str, formato='%Y-%m-%d'):
    """Convierte string a objeto datetime, retorna None si falla"""
    if not fecha_str or fecha_str == "-":
        return None
    try:
        return datetime.strptime(fecha_str.split('T')[0], formato)
    except:
        return None


# ============================================
# CÁLCULO DE COLORES (ALERTAS)
# ============================================

def calcular_color_ipo(fecha_ipo_str):
    """Calcula el color de fondo para la celda de IPO según la urgencia"""
    if not fecha_ipo_str or fecha_ipo_str == "-":
        return ""
    
    fecha_ipo = parse_fecha(fecha_ipo_str, '%d/%m/%Y')
    if not fecha_ipo:
        return ""
    
    diferencia = (fecha_ipo - datetime.now()).days
    
    # 15 días DESPUÉS de IPO (amarillo)
    if -15 <= diferencia < 0:
        return "background-color: #FFF59D;"
    
    # Hasta 30 días antes de IPO (rojo)
    if 0 <= diferencia <= 30:
        return "background-color: #FFCDD2;"
    
    return ""


def calcular_color_contrato(fecha_contrato_str):
    """Calcula el color de fondo para la celda de contrato según vencimiento"""
    if not fecha_contrato_str or fecha_contrato_str == "-":
        return ""
    
    fecha_contrato = parse_fecha(fecha_contrato_str, '%d/%m/%Y')
    if not fecha_contrato:
        return ""
    
    diferencia = (fecha_contrato - datetime.now()).days
    
    # Menos de 30 días (rojo)
    if diferencia <= 30:
        return "background-color: #FFCDD2;"
    
    # Entre 30 y 90 días (amarillo)
    if 30 < diferencia <= 90:
        return "background-color: #FFF59D;"
    
    return ""


# ============================================
# MANEJO DE RESPUESTAS
# ============================================

def handle_response(response, success_redirect=None, success_message="Operación exitosa", 
                   error_message="Error en la operación"):
    """Maneja respuestas HTTP de forma uniforme"""
    if response.status_code in [200, 201, 204]:
        if success_redirect:
            flash(success_message, "success")
            return redirect(success_redirect)
        return response.json() if response.text else True
    else:
        flash(f"{error_message}", "error")
        return None


# ============================================
# HELPERS ESPECÍFICOS DE NEGOCIO
# ============================================

def obtener_cliente_con_info(cliente_id):
    """Obtiene un cliente con sus relaciones básicas"""
    response = SupabaseClient.get("clientes", filters=f"id=eq.{cliente_id}")
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None


def obtener_equipos_cliente(cliente_id):
    """Obtiene equipos de un cliente con fechas formateadas"""
    response = SupabaseClient.get("equipos", filters=f"cliente_id=eq.{cliente_id}")
    if response.status_code != 200:
        return []
    
    equipos = []
    for equipo in response.json():
        equipos.append({
            "id": equipo.get("id"),
            "tipo_equipo": equipo.get("tipo_equipo", "-"),
            "identificacion": equipo.get("identificacion", "-"),
            "rae": equipo.get("rae", "-"),
            "ipo_proxima": formatear_fecha(equipo.get("ipo_proxima")),
            "fecha_vencimiento_contrato": formatear_fecha(equipo.get("fecha_vencimiento_contrato")),
            "descripcion": equipo.get("descripcion", "-")
        })
    return equipos


def es_mobile(user_agent_string):
    """Detecta si el user agent es de un dispositivo móvil"""
    ua = user_agent_string.lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    return any(keyword in ua for keyword in mobile_keywords)


def formatear_importe(importe):
    """Formatea un importe numérico con separador de miles"""
    if not importe:
        return "-"
    try:
        return f"{float(importe):,.0f}".replace(',', '.')
    except:
        return str(importe)


def extraer_cliente_info(cliente_data):
    """Extrae info de cliente de respuesta con relación (puede ser lista o dict)"""
    if isinstance(cliente_data, list) and cliente_data:
        return cliente_data[0]
    return cliente_data if isinstance(cliente_data, dict) else {}
