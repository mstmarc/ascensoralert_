#!/usr/bin/env python3
"""
Detectores Automáticos de Alertas - AscensorAlert V2
Sistema de detección de patrones y generación de alertas prioritarias

Ejecutar manualmente:
    python detectores_alertas.py

O programar con cron:
    0 6 * * * cd /path/to/ascensoralert && python detectores_alertas.py >> logs/alertas.log 2>&1
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración Supabase
SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    logger.error("❌ ERROR: Variable de entorno SUPABASE_KEY no configurada")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================
# DETECTOR 1: FALLAS REPETIDAS
# ============================================

def detectar_fallas_repetidas():
    """
    Detecta componentes que fallan 2+ veces en 30 días o 3+ veces en 90 días
    Genera alertas de tipo FALLA_REPETIDA
    """
    logger.info("🔍 Detector 1: Analizando fallas repetidas...")

    # Obtener partes de los últimos 90 días
    fecha_inicio = (datetime.now() - timedelta(days=90)).isoformat()

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo",
        params={
            "select": "id,fecha_parte,resolucion,maquina_id,maquinas_cartera(identificador,instalacion_id,instalaciones(nombre))",
            "fecha_parte": f"gte.{fecha_inicio}",
            "tipo_parte_normalizado": "eq.AVERIA",
            "maquina_id": "not.is.null"
        },
        headers=HEADERS
    )

    if response.status_code != 200:
        logger.error(f"Error obteniendo partes: {response.status_code}")
        return 0

    partes = response.json()
    logger.info(f"   Analizando {len(partes)} averías de los últimos 90 días...")

    # Obtener componentes críticos con sus keywords
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/componentes_criticos?activo=eq.true",
        headers=HEADERS
    )

    if response.status_code != 200:
        logger.error(f"Error obteniendo componentes críticos: {response.status_code}")
        return 0

    componentes = response.json()

    # Agrupar averías por máquina y componente
    averias_por_maquina_componente = defaultdict(list)

    for parte in partes:
        if not parte.get('resolucion'):
            continue

        maquina_id = parte['maquina_id']
        fecha_parte = datetime.fromisoformat(parte['fecha_parte'].replace('Z', '+00:00'))
        resolucion_upper = parte['resolucion'].upper()

        # Detectar componente involucrado
        for componente in componentes:
            for keyword in componente['keywords']:
                if keyword.upper() in resolucion_upper:
                    clave = (maquina_id, componente['id'])
                    averias_por_maquina_componente[clave].append({
                        'parte_id': parte['id'],
                        'fecha': fecha_parte,
                        'resolucion': parte['resolucion'],
                        'maquina_data': parte.get('maquinas_cartera')
                    })
                    break

    # Detectar patrones de falla repetida
    alertas_creadas = 0
    fecha_30_dias = datetime.now() - timedelta(days=30)

    for (maquina_id, componente_id), averias in averias_por_maquina_componente.items():
        if len(averias) < 2:
            continue

        # Ordenar por fecha
        averias.sort(key=lambda x: x['fecha'])

        # Contar averías en últimos 30 días
        averias_recientes = [a for a in averias if a['fecha'] >= fecha_30_dias]

        nivel_urgencia = 'MEDIA'
        criterio = ''

        if len(averias_recientes) >= 2:
            nivel_urgencia = 'ALTA'
            criterio = f"{len(averias_recientes)} fallas en 30 días"
        elif len(averias) >= 3:
            nivel_urgencia = 'MEDIA'
            criterio = f"{len(averias)} fallas en 90 días"
        else:
            continue  # No cumple criterios

        # Obtener datos de la máquina
        maquina_data = averias[0]['maquina_data']
        if not maquina_data:
            continue

        instalacion_id = maquina_data['instalacion_id']
        instalacion_nombre = maquina_data.get('instalaciones', {}).get('nombre', 'Desconocida')
        maquina_identificador = maquina_data['identificador']

        # Obtener nombre del componente
        componente = next((c for c in componentes if c['id'] == componente_id), None)
        if not componente:
            continue

        componente_nombre = componente['nombre']

        # Verificar si ya existe alerta activa para esta máquina/componente
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            params={
                "maquina_id": f"eq.{maquina_id}",
                "componente_id": f"eq.{componente_id}",
                "tipo_alerta": "eq.FALLA_REPETIDA",
                "estado": f"in.(PENDIENTE,EN_REVISION)"
            },
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            logger.info(f"   ↻ Ya existe alerta activa para {maquina_identificador} / {componente_nombre}")
            continue

        # Crear alerta
        titulo = f"Falla repetida: {componente_nombre} - {maquina_identificador}"
        descripcion = f"""Componente '{componente_nombre}' falla repetidamente en máquina '{maquina_identificador}' ({instalacion_nombre}).

Criterio de detección: {criterio}

Últimas averías:
"""
        for i, averia in enumerate(averias[-3:], 1):  # Últimas 3 averías
            fecha_str = averia['fecha'].strftime('%d/%m/%Y')
            descripcion += f"\n{i}. {fecha_str}: {averia['resolucion'][:100]}..."

        descripcion += f"\n\n⚠️ ACCIÓN RECOMENDADA: Reparación o sustitución del componente para evitar futuras averías."

        alerta_data = {
            "maquina_id": maquina_id,
            "instalacion_id": instalacion_id,
            "componente_id": componente_id,
            "tipo_alerta": "FALLA_REPETIDA",
            "nivel_urgencia": nivel_urgencia,
            "titulo": titulo,
            "descripcion": descripcion,
            "datos_deteccion": {
                "total_fallas_90_dias": len(averias),
                "fallas_ultimos_30_dias": len(averias_recientes),
                "componente_nombre": componente_nombre,
                "criterio": criterio,
                "partes_relacionados": [a['parte_id'] for a in averias]
            },
            "estado": "PENDIENTE",
            "fecha_deteccion": datetime.now().isoformat()
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            json=alerta_data,
            headers=HEADERS
        )

        if response.status_code == 201:
            alertas_creadas += 1
            logger.info(f"   ✓ Alerta creada: {titulo} [{nivel_urgencia}]")
        else:
            logger.error(f"   ✗ Error creando alerta: {response.text}")

    logger.info(f"   📊 Total alertas de fallas repetidas creadas: {alertas_creadas}")
    return alertas_creadas


# ============================================
# DETECTOR 2: RECOMENDACIONES IGNORADAS
# ============================================

def detectar_recomendaciones_ignoradas():
    """
    Detecta recomendaciones no ejecutadas que han generado 2+ averías posteriores
    Genera alertas de tipo RECOMENDACION_IGNORADA
    """
    logger.info("🔍 Detector 2: Analizando recomendaciones ignoradas...")

    # Obtener partes con recomendaciones no ejecutadas (más de 15 días)
    fecha_limite = (datetime.now() - timedelta(days=15)).isoformat()

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo",
        params={
            "select": "id,fecha_parte,recomendaciones_extraidas,maquina_id,maquinas_cartera(identificador,instalacion_id,instalaciones(nombre))",
            "tiene_recomendacion": "eq.true",
            "recomendacion_revisada": "eq.false",
            "oportunidad_creada": "eq.false",
            "fecha_parte": f"lt.{fecha_limite}",
            "maquina_id": "not.is.null"
        },
        headers=HEADERS
    )

    if response.status_code != 200:
        logger.error(f"Error obteniendo recomendaciones: {response.status_code}")
        return 0

    recomendaciones = response.json()
    logger.info(f"   Analizando {len(recomendaciones)} recomendaciones pendientes...")

    alertas_creadas = 0

    for rec in recomendaciones:
        maquina_id = rec['maquina_id']
        fecha_recomendacion = datetime.fromisoformat(rec['fecha_parte'].replace('Z', '+00:00'))

        # Contar averías posteriores a la recomendación
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo",
            params={
                "select": "id,fecha_parte,resolucion",
                "maquina_id": f"eq.{maquina_id}",
                "tipo_parte_normalizado": "eq.AVERIA",
                "fecha_parte": f"gt.{rec['fecha_parte']}"
            },
            headers=HEADERS
        )

        if response.status_code != 200:
            continue

        averias_posteriores = response.json()

        if len(averias_posteriores) < 2:
            continue  # No cumple criterio (menos de 2 averías posteriores)

        # Verificar si ya existe alerta activa
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            params={
                "maquina_id": f"eq.{maquina_id}",
                "tipo_alerta": "eq.RECOMENDACION_IGNORADA",
                "estado": f"in.(PENDIENTE,EN_REVISION)",
                "datos_deteccion->>parte_origen_id": f"eq.{rec['id']}"
            },
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            continue

        # Crear alerta
        maquina_data = rec.get('maquinas_cartera')
        if not maquina_data:
            continue

        instalacion_id = maquina_data['instalacion_id']
        instalacion_nombre = maquina_data.get('instalaciones', {}).get('nombre', 'Desconocida')
        maquina_identificador = maquina_data['identificador']

        dias_desde_recomendacion = (datetime.now() - fecha_recomendacion).days

        titulo = f"Recomendación ignorada: {maquina_identificador}"
        descripcion = f"""Recomendación sin ejecutar en máquina '{maquina_identificador}' ({instalacion_nombre}) ha generado {len(averias_posteriores)} averías adicionales.

Recomendación original ({dias_desde_recomendacion} días atrás):
{rec['recomendaciones_extraidas'][:300]}...

Averías posteriores: {len(averias_posteriores)}

⚠️ ACCIÓN RECOMENDADA: Ejecutar la recomendación para evitar nuevas averías y costes adicionales.
"""

        nivel_urgencia = 'ALTA' if len(averias_posteriores) >= 3 else 'MEDIA'

        alerta_data = {
            "maquina_id": maquina_id,
            "instalacion_id": instalacion_id,
            "tipo_alerta": "RECOMENDACION_IGNORADA",
            "nivel_urgencia": nivel_urgencia,
            "titulo": titulo,
            "descripcion": descripcion,
            "datos_deteccion": {
                "parte_origen_id": rec['id'],
                "fecha_recomendacion": rec['fecha_parte'],
                "dias_desde_recomendacion": dias_desde_recomendacion,
                "averias_posteriores": len(averias_posteriores),
                "partes_averias": [a['id'] for a in averias_posteriores]
            },
            "estado": "PENDIENTE",
            "fecha_deteccion": datetime.now().isoformat()
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            json=alerta_data,
            headers=HEADERS
        )

        if response.status_code == 201:
            alertas_creadas += 1
            logger.info(f"   ✓ Alerta creada: {titulo} [{nivel_urgencia}]")
        else:
            logger.error(f"   ✗ Error creando alerta: {response.text}")

    logger.info(f"   📊 Total alertas de recomendaciones ignoradas: {alertas_creadas}")
    return alertas_creadas


# ============================================
# DETECTOR 3: MANTENIMIENTOS OMITIDOS
# ============================================

def detectar_mantenimientos_omitidos():
    """
    Detecta máquinas sin mantenimiento en 60+ días
    Si además tiene averías recientes, genera alerta de mayor urgencia
    Genera alertas de tipo MANTENIMIENTO_OMITIDO o MANTENIMIENTO_OMITIDO_CON_AVERIAS
    """
    logger.info("🔍 Detector 3: Analizando mantenimientos omitidos...")

    # Obtener todas las máquinas activas
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera",
        params={
            "select": "id,identificador,instalacion_id,instalaciones(nombre)",
            "en_cartera": "eq.true"
        },
        headers=HEADERS
    )

    if response.status_code != 200:
        logger.error(f"Error obteniendo máquinas: {response.status_code}")
        return 0

    maquinas = response.json()
    logger.info(f"   Analizando {len(maquinas)} máquinas activas...")

    alertas_creadas = 0
    fecha_limite_60 = (datetime.now() - timedelta(days=60)).isoformat()
    fecha_limite_30 = (datetime.now() - timedelta(days=30)).isoformat()

    for maquina in maquinas:
        maquina_id = maquina['id']

        # Obtener último mantenimiento
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo",
            params={
                "select": "fecha_parte",
                "maquina_id": f"eq.{maquina_id}",
                "tipo_parte_normalizado": "eq.MANTENIMIENTO",
                "order": "fecha_parte.desc",
                "limit": "1"
            },
            headers=HEADERS
        )

        ultimo_mantenimiento = None
        if response.status_code == 200 and len(response.json()) > 0:
            ultimo_mantenimiento = response.json()[0]['fecha_parte']

        # Si no hay mantenimiento o es muy antiguo
        mantenimiento_atrasado = False
        dias_sin_mantenimiento = 0

        if not ultimo_mantenimiento:
            mantenimiento_atrasado = True
            dias_sin_mantenimiento = 999  # Sin datos
        else:
            fecha_ultimo = datetime.fromisoformat(ultimo_mantenimiento.replace('Z', '+00:00'))
            dias_sin_mantenimiento = (datetime.now() - fecha_ultimo).days
            if dias_sin_mantenimiento >= 60:
                mantenimiento_atrasado = True

        if not mantenimiento_atrasado:
            continue

        # Contar averías en últimos 30 días
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo",
            params={
                "select": "id",
                "maquina_id": f"eq.{maquina_id}",
                "tipo_parte_normalizado": "eq.AVERIA",
                "fecha_parte": f"gte.{fecha_limite_30}"
            },
            headers=HEADERS
        )

        averias_recientes = 0
        if response.status_code == 200:
            averias_recientes = len(response.json())

        # Determinar tipo y urgencia
        if averias_recientes >= 2:
            tipo_alerta = "MANTENIMIENTO_OMITIDO_CON_AVERIAS"
            nivel_urgencia = "ALTA"
        else:
            tipo_alerta = "MANTENIMIENTO_OMITIDO"
            nivel_urgencia = "MEDIA"

        # Verificar si ya existe alerta activa
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            params={
                "maquina_id": f"eq.{maquina_id}",
                "tipo_alerta": f"in.(MANTENIMIENTO_OMITIDO,MANTENIMIENTO_OMITIDO_CON_AVERIAS)",
                "estado": f"in.(PENDIENTE,EN_REVISION)"
            },
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            continue

        # Crear alerta
        maquina_identificador = maquina['identificador']
        instalacion_id = maquina['instalacion_id']
        instalacion_nombre = maquina.get('instalaciones', {}).get('nombre', 'Desconocida')

        titulo = f"Mantenimiento atrasado: {maquina_identificador}"
        descripcion = f"""Máquina '{maquina_identificador}' ({instalacion_nombre}) lleva {dias_sin_mantenimiento} días sin mantenimiento preventivo.
"""

        if averias_recientes > 0:
            descripcion += f"\n⚠️ CRÍTICO: La máquina ha tenido {averias_recientes} averías en los últimos 30 días.\n"

        descripcion += f"\n🔧 ACCIÓN RECOMENDADA: Programar conservación preventiva URGENTE para evitar averías mayores."

        alerta_data = {
            "maquina_id": maquina_id,
            "instalacion_id": instalacion_id,
            "tipo_alerta": tipo_alerta,
            "nivel_urgencia": nivel_urgencia,
            "titulo": titulo,
            "descripcion": descripcion,
            "datos_deteccion": {
                "dias_sin_mantenimiento": dias_sin_mantenimiento,
                "fecha_ultimo_mantenimiento": ultimo_mantenimiento,
                "averias_ultimos_30_dias": averias_recientes
            },
            "estado": "PENDIENTE",
            "fecha_deteccion": datetime.now().isoformat()
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            json=alerta_data,
            headers=HEADERS
        )

        if response.status_code == 201:
            alertas_creadas += 1
            logger.info(f"   ✓ Alerta creada: {titulo} [{nivel_urgencia}]")
        else:
            logger.error(f"   ✗ Error creando alerta: {response.text}")

    logger.info(f"   📊 Total alertas de mantenimientos omitidos: {alertas_creadas}")
    return alertas_creadas


# ============================================
# DETECTOR 4: INSTALACIONES CRÍTICAS
# ============================================

def detectar_instalaciones_criticas():
    """
    Detecta instalaciones completas en estado crítico
    - 2+ máquinas en estado CRITICO, o
    - 5+ averías en los últimos 30 días
    Genera alertas de tipo INSTALACION_CRITICA
    """
    logger.info("🔍 Detector 4: Analizando instalaciones críticas...")

    # Obtener todas las instalaciones con máquinas activas
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/instalaciones?select=id,nombre,municipio",
        headers=HEADERS
    )

    if response.status_code != 200:
        logger.error(f"Error obteniendo instalaciones: {response.status_code}")
        return 0

    instalaciones = response.json()
    logger.info(f"   Analizando {len(instalaciones)} instalaciones...")

    alertas_creadas = 0
    fecha_limite_30 = (datetime.now() - timedelta(days=30)).isoformat()

    for instalacion in instalaciones:
        instalacion_id = instalacion['id']
        instalacion_nombre = instalacion['nombre']

        # Obtener máquinas en estado CRITICO de esta instalación
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/v_estado_maquinas_semaforico",
            params={
                "select": "maquina_id,estado_semaforico",
                "instalacion_id": f"eq.{instalacion_id}",
                "estado_semaforico": "eq.CRITICO"
            },
            headers=HEADERS
        )

        maquinas_criticas = 0
        if response.status_code == 200:
            maquinas_criticas = len(response.json())

        # Contar averías totales en la instalación (últimos 30 días)
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo",
            params={
                "select": "id,maquinas_cartera!inner(instalacion_id)",
                "tipo_parte_normalizado": "eq.AVERIA",
                "fecha_parte": f"gte.{fecha_limite_30}",
                "maquinas_cartera.instalacion_id": f"eq.{instalacion_id}"
            },
            headers=HEADERS
        )

        averias_mes = 0
        if response.status_code == 200:
            averias_mes = len(response.json())

        # Evaluar si cumple criterios de instalación crítica
        es_critica = False
        criterio = ""

        if maquinas_criticas >= 2:
            es_critica = True
            criterio = f"{maquinas_criticas} máquinas en estado CRÍTICO"
        elif averias_mes >= 5:
            es_critica = True
            criterio = f"{averias_mes} averías en los últimos 30 días"

        if not es_critica:
            continue

        # Verificar si ya existe alerta activa para esta instalación
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            params={
                "instalacion_id": f"eq.{instalacion_id}",
                "tipo_alerta": "eq.INSTALACION_CRITICA",
                "estado": f"in.(PENDIENTE,EN_REVISION)",
                "maquina_id": "is.null"  # Alertas de instalación no tienen maquina_id
            },
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            logger.info(f"   ↻ Ya existe alerta activa para {instalacion_nombre}")
            continue

        # Obtener lista de máquinas críticas para el detalle
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/v_estado_maquinas_semaforico",
            params={
                "select": "identificador,estado_semaforico,averias_mes",
                "instalacion_id": f"eq.{instalacion_id}",
                "estado_semaforico": "eq.CRITICO"
            },
            headers=HEADERS
        )

        maquinas_criticas_lista = []
        if response.status_code == 200:
            maquinas_criticas_lista = response.json()

        # Crear alerta de instalación crítica
        titulo = f"🏢 INSTALACIÓN CRÍTICA: {instalacion_nombre}"
        descripcion = f"""La instalación '{instalacion_nombre}' ({instalacion.get('municipio', 'N/A')}) está en estado CRÍTICO.

⚠️ CRITERIO DE DETECCIÓN: {criterio}

📊 MÉTRICAS:
• Máquinas en estado crítico: {maquinas_criticas}
• Averías totales (último mes): {averias_mes}
"""

        if maquinas_criticas_lista:
            descripcion += f"\n🛗 MÁQUINAS CRÍTICAS:\n"
            for maq in maquinas_criticas_lista[:5]:  # Mostrar máximo 5
                descripcion += f"   • {maq['identificador']} - {maq['averias_mes']} averías este mes\n"
            if len(maquinas_criticas_lista) > 5:
                descripcion += f"   ... y {len(maquinas_criticas_lista) - 5} más\n"

        descripcion += f"""
🚨 ACCIÓN RECOMENDADA:
• Revisión urgente de toda la instalación
• Priorizar recursos técnicos en esta ubicación
• Contactar con administrador de la comunidad
• Evaluar si requiere plan de mantenimiento especial

💰 RIESGO: Alta probabilidad de múltiples averías simultáneas y sobrecarga del equipo técnico.
"""

        alerta_data = {
            "maquina_id": None,  # Alerta a nivel de instalación, no de máquina
            "instalacion_id": instalacion_id,
            "tipo_alerta": "INSTALACION_CRITICA",
            "nivel_urgencia": "URGENTE",
            "titulo": titulo,
            "descripcion": descripcion,
            "datos_deteccion": {
                "maquinas_criticas": maquinas_criticas,
                "averias_ultimo_mes": averias_mes,
                "criterio": criterio,
                "maquinas_criticas_ids": [m['identificador'] for m in maquinas_criticas_lista]
            },
            "estado": "PENDIENTE",
            "fecha_deteccion": datetime.now().isoformat()
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas",
            json=alerta_data,
            headers=HEADERS
        )

        if response.status_code == 201:
            alertas_creadas += 1
            logger.info(f"   ✓ Alerta creada: {titulo} [URGENTE]")
        else:
            logger.error(f"   ✗ Error creando alerta: {response.text}")

    logger.info(f"   📊 Total alertas de instalaciones críticas: {alertas_creadas}")
    return alertas_creadas


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def ejecutar_todos_los_detectores():
    """Ejecuta todos los detectores de alertas"""
    logger.info("="*70)
    logger.info("🤖 SISTEMA DE DETECCIÓN AUTOMÁTICA DE ALERTAS - V2")
    logger.info("="*70)
    logger.info(f"Fecha/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("")

    total_alertas = 0

    try:
        # Detector 1: Fallas repetidas
        total_alertas += detectar_fallas_repetidas()
        logger.info("")

        # Detector 2: Recomendaciones ignoradas
        total_alertas += detectar_recomendaciones_ignoradas()
        logger.info("")

        # Detector 3: Mantenimientos omitidos
        total_alertas += detectar_mantenimientos_omitidos()
        logger.info("")

        # Detector 4: Instalaciones críticas
        total_alertas += detectar_instalaciones_criticas()
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

    logger.info("="*70)
    logger.info(f"✅ EJECUCIÓN COMPLETADA")
    logger.info(f"📊 Total de alertas nuevas generadas: {total_alertas}")
    logger.info("="*70)

    return total_alertas


if __name__ == "__main__":
    ejecutar_todos_los_detectores()
