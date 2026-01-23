"""
Servicio centralizado de caché para optimizar consultas a Supabase
"""
from datetime import datetime, timedelta
import requests
from config import config, CACHE_TTL_ADMINISTRADORES, CACHE_TTL_METRICAS_HOME, CACHE_TTL_FILTROS, CACHE_TTL_INSTALACIONES, CACHE_TTL_OPORTUNIDADES

# ============================================
# ESTRUCTURAS DE CACHÉ
# ============================================

# Caché para administradores (5 min)
cache_administradores = {
    'data': [],
    'timestamp': None
}

# Caché para métricas del dashboard home (5 min)
cache_metricas_home = {
    'data': None,
    'timestamp': None
}

# Caché para filtros de localidades y empresas (30 min - cambian poco)
cache_filtros = {
    'localidades': [],
    'empresas': [],
    'timestamp': None
}

# Caché para últimas instalaciones (10 min)
cache_ultimas_instalaciones = {
    'data': [],
    'timestamp': None
}

# Caché para últimas oportunidades (10 min)
cache_ultimas_oportunidades = {
    'data': [],
    'timestamp': None
}


# ============================================
# FUNCIONES DE CACHÉ
# ============================================

def get_administradores_cached():
    """
    Obtiene la lista de administradores usando caché.
    Se renueva automáticamente cada 5 minutos.
    Esto reduce drásticamente las consultas a Supabase.
    """
    now = datetime.now()

    # Si no hay caché o pasaron 5 minutos, renovar
    if not cache_administradores['timestamp'] or \
       (now - cache_administradores['timestamp']) > timedelta(minutes=CACHE_TTL_ADMINISTRADORES):

        try:
            print(f"🔄 Consultando administradores desde Supabase...")
            response = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/administradores?select=id,nombre_empresa&order=nombre_empresa.asc",
                headers=config.HEADERS,
                timeout=10
            )

            print(f"📡 Respuesta de Supabase - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                cache_administradores['data'] = data
                cache_administradores['timestamp'] = now
                print(f"✅ Caché de administradores actualizado: {len(data)} registros")
            else:
                print(f"⚠️ Error al actualizar caché de administradores: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                # Si falla pero hay caché previo, usarlo
                if cache_administradores['data']:
                    print(f"ℹ️ Usando caché anterior: {len(cache_administradores['data'])} registros")

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout al consultar Supabase (>10s)")
        except Exception as e:
            print(f"❌ Excepción al actualizar caché de administradores: {type(e).__name__}: {str(e)}")
            # Si falla, devolver lo que haya en caché (aunque esté desactualizado)

    return cache_administradores['data']


def get_metricas_home_cached():
    """
    Obtiene las métricas del dashboard home usando caché.
    Se renueva cada 5 minutos.
    """
    now = datetime.now()

    if not cache_metricas_home['timestamp'] or \
       (now - cache_metricas_home['timestamp']) > timedelta(minutes=CACHE_TTL_METRICAS_HOME):

        try:
            print(f"🔄 Consultando métricas del home desde Supabase...")

            metricas = {}

            # Total clientes
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/clientes?select=id", headers=config.HEADERS, timeout=10)
            metricas['total_clientes'] = len(resp.json()) if resp.ok else 0

            # Total equipos
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/equipos?select=id", headers=config.HEADERS, timeout=10)
            metricas['total_equipos'] = len(resp.json()) if resp.ok else 0

            # Total oportunidades
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/oportunidades?select=id", headers=config.HEADERS, timeout=10)
            metricas['total_oportunidades'] = len(resp.json()) if resp.ok else 0

            # IPOs de hoy
            hoy = datetime.now().strftime("%Y-%m-%d")
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/equipos?select=id&ipo_proxima=eq.{hoy}", headers=config.HEADERS, timeout=10)
            metricas['ipos_hoy'] = len(resp.json()) if resp.ok else 0

            # Contratos por vencer (próximos 30 días)
            fecha_inicio = datetime.now().strftime("%Y-%m-%d")
            fecha_fin = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            resp = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/equipos?select=id&fecha_vencimiento_contrato=gte.{fecha_inicio}&fecha_vencimiento_contrato=lte.{fecha_fin}",
                headers=config.HEADERS, timeout=10
            )
            metricas['contratos_vencer'] = len(resp.json()) if resp.ok else 0

            # IPOs de esta semana
            fecha_fin_semana = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            resp = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/equipos?select=id&ipo_proxima=gte.{fecha_inicio}&ipo_proxima=lte.{fecha_fin_semana}",
                headers=config.HEADERS, timeout=10
            )
            metricas['ipos_semana'] = len(resp.json()) if resp.ok else 0

            # Oportunidades pendientes
            resp = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/oportunidades?select=id&estado=eq.activa",
                headers=config.HEADERS, timeout=10
            )
            metricas['oportunidades_pendientes'] = len(resp.json()) if resp.ok else 0

            cache_metricas_home['data'] = metricas
            cache_metricas_home['timestamp'] = now
            print(f"✅ Caché de métricas home actualizado")

        except Exception as e:
            print(f"❌ Error al actualizar caché de métricas: {type(e).__name__}: {str(e)}")
            # Si falla, devolver lo que haya en caché

    return cache_metricas_home['data']


def get_filtros_cached():
    """
    Obtiene los filtros (localidades y empresas) usando caché.
    Se renueva cada 30 minutos (cambian poco).
    """
    now = datetime.now()

    if not cache_filtros['timestamp'] or \
       (now - cache_filtros['timestamp']) > timedelta(minutes=CACHE_TTL_FILTROS):

        try:
            print(f"🔄 Consultando filtros desde Supabase...")

            localidades = set()
            empresas = set()

            # Localidades
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/clientes?select=localidad", headers=config.HEADERS, timeout=10)
            if resp.ok:
                for item in resp.json():
                    if item.get("localidad"):
                        localidades.add(item["localidad"])

            # Empresas
            resp = requests.get(f"{config.SUPABASE_URL}/rest/v1/clientes?select=empresa_mantenedora", headers=config.HEADERS, timeout=10)
            if resp.ok:
                for item in resp.json():
                    if item.get("empresa_mantenedora"):
                        empresas.add(item["empresa_mantenedora"])

            cache_filtros['localidades'] = sorted(list(localidades))
            cache_filtros['empresas'] = sorted(list(empresas))
            cache_filtros['timestamp'] = now
            print(f"✅ Caché de filtros actualizado: {len(localidades)} localidades, {len(empresas)} empresas")

        except Exception as e:
            print(f"❌ Error al actualizar caché de filtros: {type(e).__name__}: {str(e)}")

    return cache_filtros['localidades'], cache_filtros['empresas']


def get_ultimas_instalaciones_cached():
    """
    Obtiene las últimas instalaciones usando caché.
    Se renueva cada 10 minutos.
    """
    now = datetime.now()

    if not cache_ultimas_instalaciones['timestamp'] or \
       (now - cache_ultimas_instalaciones['timestamp']) > timedelta(minutes=CACHE_TTL_INSTALACIONES):

        try:
            print(f"🔄 Consultando últimas instalaciones desde Supabase...")

            # OPTIMIZACIÓN: Seleccionar solo campos necesarios en lugar de *
            response = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/clientes?select=id,direccion,nombre_cliente,localidad,empresa_mantenedora,numero_ascensores,equipos(id)&order=fecha_visita.desc&limit=5",
                headers=config.HEADERS,
                timeout=10
            )

            if response.ok:
                leads_data = response.json()
                instalaciones = []

                for lead in leads_data:
                    equipos_data = lead.get('equipos', [])
                    num_equipos = len(equipos_data) if equipos_data else lead.get('numero_ascensores', 0)
                    empresa_mantenedora = lead.get('empresa_mantenedora', '-')

                    instalaciones.append({
                        'id': lead['id'],
                        'direccion': lead.get('direccion', 'Sin dirección'),
                        'nombre_cliente': lead.get('nombre_cliente', ''),
                        'localidad': lead.get('localidad', '-'),
                        'num_equipos': num_equipos,
                        'empresa_mantenedora': empresa_mantenedora
                    })

                cache_ultimas_instalaciones['data'] = instalaciones
                cache_ultimas_instalaciones['timestamp'] = now
                print(f"✅ Caché de últimas instalaciones actualizado: {len(instalaciones)} registros")

        except Exception as e:
            print(f"❌ Error al actualizar caché de instalaciones: {type(e).__name__}: {str(e)}")

    return cache_ultimas_instalaciones['data']


def get_ultimas_oportunidades_cached():
    """
    Obtiene las últimas oportunidades usando caché.
    Se renueva cada 10 minutos.
    """
    now = datetime.now()

    if not cache_ultimas_oportunidades['timestamp'] or \
       (now - cache_ultimas_oportunidades['timestamp']) > timedelta(minutes=CACHE_TTL_OPORTUNIDADES):

        try:
            print(f"🔄 Consultando últimas oportunidades desde Supabase...")

            # OPTIMIZACIÓN: Seleccionar solo campos necesarios en lugar de *
            response = requests.get(
                f"{config.SUPABASE_URL}/rest/v1/oportunidades?select=id,tipo,estado,clientes(nombre_cliente,direccion)&order=fecha_creacion.desc&limit=5",
                headers=config.HEADERS,
                timeout=10
            )

            if response.ok:
                cache_ultimas_oportunidades['data'] = response.json()
                cache_ultimas_oportunidades['timestamp'] = now
                print(f"✅ Caché de últimas oportunidades actualizado: {len(cache_ultimas_oportunidades['data'])} registros")

        except Exception as e:
            print(f"❌ Error al actualizar caché de oportunidades: {type(e).__name__}: {str(e)}")

    return cache_ultimas_oportunidades['data']


def clear_all_caches():
    """Limpia todas las cachés"""
    global cache_administradores, cache_metricas_home, cache_filtros, cache_ultimas_instalaciones, cache_ultimas_oportunidades

    cache_administradores = {'data': [], 'timestamp': None}
    cache_metricas_home = {'data': None, 'timestamp': None}
    cache_filtros = {'localidades': [], 'empresas': [], 'timestamp': None}
    cache_ultimas_instalaciones = {'data': [], 'timestamp': None}
    cache_ultimas_oportunidades = {'data': [], 'timestamp': None}

    return "Todas las cachés han sido limpiadas"
