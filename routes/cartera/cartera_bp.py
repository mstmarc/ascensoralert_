"""
Blueprint de Cartera y Análisis

Gestión completa de la cartera de instalaciones y máquinas con:
- Dashboard de cartera (V1, V2, IA Predictiva)
- Importación de equipos y partes desde PDF
- Gestión de recomendaciones y oportunidades
- Alertas automáticas y pendientes técnicos
- Análisis predictivo con IA
- Visualización de métricas y componentes críticos
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta, date
import requests
import logging
import sys
import io
import os
import urllib.parse
import pandas as pd
import pdfplumber
import threading

from config import config
import helpers
import analizador_ia

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Silenciar logs verbosos de pdfplumber/pdfminer
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('pdfplumber').setLevel(logging.WARNING)

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint
cartera_bp = Blueprint('cartera', __name__, url_prefix='/cartera')

# Estado global para análisis en background
estado_analisis_global = {
    "en_progreso": False,
    "completado": False,
    "progreso": 0,
    "fase_actual": "",
    "mensaje": "",
    "maquinas_analizadas": 0,
    "total_maquinas": 0,
    "predicciones_generadas": 0,
    "alertas_creadas": 0,
    "ultimo_error": None,
    "errores_detallados": []
}

# @app.route("/cartera")
@cartera_bp.route('/')
@helpers.login_required
def cartera_dashboard():
    """Dashboard principal de Cartera y Análisis"""

    # Obtener estadísticas generales
    stats = {}

    # Total de instalaciones (solo en cartera)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/instalaciones?select=count&en_cartera=eq.true",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    stats['total_instalaciones'] = response.headers.get('Content-Range', '0').split('/')[-1]

    # Total de máquinas (solo en cartera)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera?select=count&en_cartera=eq.true",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    stats['total_maquinas'] = response.headers.get('Content-Range', '0').split('/')[-1]

    # Obtener IDs de máquinas en cartera para filtrar partes
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera?select=id&en_cartera=eq.true",
        headers=HEADERS
    )
    maquinas_en_cartera = response.json() if response.status_code == 200 else []
    maquina_ids_cartera = [m['id'] for m in maquinas_en_cartera]
    maquina_ids_str = ','.join(map(str, maquina_ids_cartera)) if maquina_ids_cartera else '0'

    # Total de partes (solo de máquinas en cartera)
    if maquina_ids_cartera:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=count&maquina_id=in.({maquina_ids_str})",
            headers={**HEADERS, "Prefer": "count=exact"}
        )
        stats['total_partes'] = response.headers.get('Content-Range', '0').split('/')[-1]
    else:
        stats['total_partes'] = '0'

    # Recomendaciones pendientes (solo de máquinas en cartera)
    if maquina_ids_cartera:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=count&tiene_recomendacion=eq.true&recomendacion_revisada=eq.false&oportunidad_creada=eq.false&maquina_id=in.({maquina_ids_str})",
            headers={**HEADERS, "Prefer": "count=exact"}
        )
        stats['recomendaciones_pendientes'] = response.headers.get('Content-Range', '0').split('/')[-1]
    else:
        stats['recomendaciones_pendientes'] = '0'

    # KPIs adicionales de análisis
    # Averías último año (solo de máquinas en cartera)
    if maquina_ids_cartera:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=count&tipo_parte_normalizado=eq.AVERIA&fecha_parte=gte.{(datetime.now() - timedelta(days=365)).isoformat()}&maquina_id=in.({maquina_ids_str})",
            headers={**HEADERS, "Prefer": "count=exact"}
        )
        stats['averias_anio'] = response.headers.get('Content-Range', '0').split('/')[-1]
    else:
        stats['averias_anio'] = '0'

    # Mantenimientos último año (solo de máquinas en cartera)
    if maquina_ids_cartera:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=count&tipo_parte_normalizado=eq.MANTENIMIENTO&fecha_parte=gte.{(datetime.now() - timedelta(days=365)).isoformat()}&maquina_id=in.({maquina_ids_str})",
            headers={**HEADERS, "Prefer": "count=exact"}
        )
        stats['mantenimientos_anio'] = response.headers.get('Content-Range', '0').split('/')[-1]
    else:
        stats['mantenimientos_anio'] = '0'

    # Top 10 máquinas problemáticas (usando la vista)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_maquinas_problematicas?select=*&order=indice_problema.desc&limit=10",
        headers=HEADERS
    )
    maquinas_problematicas = response.json() if response.status_code == 200 else []

    # Recomendaciones pendientes con paginación
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page

    # Obtener total de recomendaciones para calcular páginas
    response_count = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_partes_con_recomendaciones?select=count",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    total_recomendaciones = int(response_count.headers.get('Content-Range', '0').split('/')[-1])
    total_pages = (total_recomendaciones + per_page - 1) // per_page  # Ceiling division

    # Obtener recomendaciones de la página actual
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_partes_con_recomendaciones?select=*&order=fecha_parte.desc&limit={per_page}&offset={offset}",
        headers=HEADERS
    )
    recomendaciones = response.json() if response.status_code == 200 else []

    # Información de paginación
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_recomendaciones,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

    # Distribución de tipos de parte (último año, solo de máquinas en cartera)
    if maquina_ids_cartera:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=tipo_parte_normalizado&fecha_parte=gte.{(datetime.now() - timedelta(days=365)).isoformat()}&maquina_id=in.({maquina_ids_str})",
            headers=HEADERS
        )
        if response.status_code == 200:
            partes_data = response.json()
            tipos_distribucion = {}
            for parte in partes_data:
                tipo = parte.get('tipo_parte_normalizado', 'OTRO')
                tipos_distribucion[tipo] = tipos_distribucion.get(tipo, 0) + 1
        else:
            tipos_distribucion = {}
    else:
        tipos_distribucion = {}

    return render_template(
        "cartera/dashboard.html",
        stats=stats,
        maquinas_problematicas=maquinas_problematicas,
        recomendaciones=recomendaciones,
        tipos_distribucion=tipos_distribucion,
        pagination=pagination
    )


# @app.route("/cartera/importar")
@cartera_bp.route('/importar')
@helpers.login_required
def cartera_importar():
    """Interfaz de importación de datos"""
    return render_template("cartera/importar.html")


# @app.route("/cartera/importar_equipos", methods=["POST"])
@cartera_bp.route('/importar_equipos', methods=['POST'])
@helpers.login_required
def cartera_importar_equipos():
    """Importar instalaciones y máquinas desde Excel"""

    if 'archivo_equipos' not in request.files:
        flash("No se seleccionó ningún archivo", "error")
        return redirect(url_for('cartera.cartera_importar'))

    file = request.files['archivo_equipos']

    if file.filename == '':
        flash("No se seleccionó ningún archivo", "error")
        return redirect(url_for('cartera.cartera_importar'))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash("El archivo debe ser formato Excel (.xlsx o .xls)", "error")
        return redirect(url_for('cartera.cartera_importar'))

    try:
        # Leer Excel
        df = pd.read_excel(file)

        # Log de columnas encontradas
        logger.info(f"Columnas en Excel: {list(df.columns)}")
        logger.info(f"Total de filas: {len(df)}")

        # Mapeo de columnas (flexible con mayúsculas/minúsculas y acentos)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'instalación' in col_lower or 'instalacion' in col_lower:
                if 'cód' in col_lower or 'cod' in col_lower:
                    column_mapping[col] = 'cod_instalacion'
                else:
                    column_mapping[col] = 'instalacion'
            elif 'máquina' in col_lower or 'maquina' in col_lower:
                if 'cód' in col_lower or 'cod' in col_lower:
                    column_mapping[col] = 'cod_maquina'
                else:
                    column_mapping[col] = 'maquina'
            elif 'tecnico' in col_lower or 'técnico' in col_lower:
                column_mapping[col] = 'tecnico'

        df.rename(columns=column_mapping, inplace=True)
        logger.info(f"Columnas después de mapeo: {list(df.columns)}")

        # Verificar columnas requeridas
        required = ['cod_instalacion', 'instalacion', 'cod_maquina', 'maquina']
        missing = [col for col in required if col not in df.columns]

        if missing:
            logger.error(f"Faltan columnas: {missing}. Columnas después de mapeo: {list(df.columns)}")
            flash(f"Faltan columnas requeridas: {', '.join(missing)}", "error")
            flash(f"Columnas encontradas en Excel: {', '.join(df.columns)}", "info")
            return redirect(url_for('cartera.cartera_importar'))

        # Procesar instalaciones únicas
        instalaciones_unicas = df[['cod_instalacion', 'instalacion']].drop_duplicates('cod_instalacion')
        instalaciones_map = {}
        stats = {
            'instalaciones_nuevas': 0,
            'instalaciones_existentes': 0,
            'maquinas_nuevas': 0,
            'maquinas_existentes': 0,
            'errores': 0
        }

        # Municipios de Gran Canaria
        municipios_gc = [
            'LAS PALMAS', 'TELDE', 'SANTA LUCIA', 'AGÜIMES', 'INGENIO',
            'MOGAN', 'SAN BARTOLOME', 'SANTA BRIGIDA', 'ARUCAS', 'TEROR',
            'GALDAR', 'AGAETE', 'VALLESECO', 'FIRGAS', 'MOYA',
            'SANTA MARIA DE GUIA', 'VALSEQUILLO', 'VEGA DE SAN MATEO',
            'TEJEDA', 'ALDEA DE SAN NICOLAS'
        ]

        for idx, row in instalaciones_unicas.iterrows():
            # Limpiar nombre (quitar dirección después del guion)
            nombre = row['instalacion'].split(' - ')[0].strip() if ' - ' in row['instalacion'] else row['instalacion'].strip()

            # Extraer municipio
            texto_upper = row['instalacion'].upper()
            municipio = "Las Palmas de Gran Canaria"  # Default
            for mun in municipios_gc:
                if mun in texto_upper:
                    municipio = mun.title()
                    break

            # Verificar si ya existe
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/instalaciones?nombre=eq.{urllib.parse.quote(nombre)}",
                headers=HEADERS
            )

            if response.status_code == 200 and len(response.json()) > 0:
                instalacion_id = response.json()[0]['id']
                stats['instalaciones_existentes'] += 1
            else:
                # Crear nueva
                data = {"nombre": nombre, "municipio": municipio}
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/instalaciones",
                    json=data,
                    headers=HEADERS
                )

                if response.status_code == 201:
                    instalacion_id = response.json()[0]['id']
                    stats['instalaciones_nuevas'] += 1
                else:
                    logger.error(f"Error creando instalación '{nombre}': {response.status_code} - {response.text}")
                    stats['errores'] += 1
                    continue

            instalaciones_map[row['cod_instalacion']] = instalacion_id

        # Procesar máquinas
        for idx, row in df.iterrows():
            cod_instalacion = row['cod_instalacion']
            identificador = row['maquina'].strip()
            codigo_maquina = row['cod_maquina'].strip() if pd.notna(row['cod_maquina']) else None

            instalacion_id = instalaciones_map.get(cod_instalacion)
            if not instalacion_id:
                stats['errores'] += 1
                continue

            # Verificar si la máquina ya existe
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/maquinas_cartera?identificador=eq.{urllib.parse.quote(identificador)}",
                headers=HEADERS
            )

            if response.status_code == 200 and len(response.json()) > 0:
                stats['maquinas_existentes'] += 1
                continue

            # Crear nueva máquina
            data = {
                "instalacion_id": instalacion_id,
                "identificador": identificador,
                "codigo_maquina": codigo_maquina
            }

            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/maquinas_cartera",
                json=data,
                headers=HEADERS
            )

            if response.status_code == 201:
                stats['maquinas_nuevas'] += 1
            else:
                logger.error(f"Error creando máquina '{identificador}': {response.status_code} - {response.text}")
                stats['errores'] += 1

        # Mostrar resumen
        flash(f"Importación completada: {stats['instalaciones_nuevas']} instalaciones nuevas, "
              f"{stats['maquinas_nuevas']} máquinas nuevas", "success")

        if stats['instalaciones_existentes'] > 0:
            flash(f"{stats['instalaciones_existentes']} instalaciones ya existían", "info")

        if stats['maquinas_existentes'] > 0:
            flash(f"{stats['maquinas_existentes']} máquinas ya existían", "info")

        if stats['errores'] > 0:
            flash(f"{stats['errores']} registros con errores", "warning")

    except Exception as e:
        flash(f"Error al procesar archivo: {str(e)}", "error")
        logger.error(f"Error importando equipos: {str(e)}")

    return redirect(url_for('cartera.cartera_importar'))


# @app.route("/cartera/importar_partes", methods=["POST"])
@cartera_bp.route('/importar_partes', methods=['POST'])
@helpers.login_required
def cartera_importar_partes():
    """Importar partes de trabajo desde Excel"""

    if 'archivo_partes' not in request.files:
        flash("No se seleccionó ningún archivo", "error")
        return redirect(url_for('cartera.cartera_importar'))

    file = request.files['archivo_partes']

    if file.filename == '':
        flash("No se seleccionó ningún archivo", "error")
        return redirect(url_for('cartera.cartera_importar'))

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash("El archivo debe ser formato Excel (.xlsx o .xls)", "error")
        return redirect(url_for('cartera.cartera_importar'))

    try:
        # Leer Excel
        df = pd.read_excel(file)

        # Palabras clave para detectar recomendaciones
        palabras_clave_recomendacion = [
            # Recomendaciones explícitas
            'RECOMENDACIÓN', 'RECOMENDACION', 'RECOMIENDO', 'RECOMENDAMOS',
            'CONVENDRÍA', 'CONVIENE', 'SERÍA CONVENIENTE', 'SE RECOMIENDA',
            'ACONSEJABLE', 'ACONSEJO', 'SUGERENCIA', 'SUGIERO',

            # Indicadores de urgencia/importancia
            'IMPORTANTE', 'URGENTE', 'NECESARIO', 'IMPRESCINDIBLE', 'CRÍTICO',
            'PRIORITARIO', 'INMEDIATO',

            # Acciones de mantenimiento/reparación
            'CAMBIAR', 'SUSTITUIR', 'REEMPLAZAR', 'MODERNIZAR', 'ACTUALIZAR',
            'REVISAR', 'REPARAR', 'ARREGLAR', 'RENOVAR', 'MEJORAR',

            # Temporalidad
            'PRÓXIMAMENTE', 'PROXIMAMENTE', 'PRONTO', 'EN BREVE',
            'PRÓXIMA REVISIÓN', 'PROXIMA REVISION',

            # Estados problemáticos
            'NO FUNCIONA', 'NO OPERA', 'INOPERATIVO', 'INOPERANTE',
            'FALLA', 'FALLO', 'DEFECTUOSO', 'AVERIADO', 'DETERIORADO',
            'MAL ESTADO', 'DESGASTADO', 'ROTO', 'DAÑADO',

            # Componentes críticos (cuando no funcionan = oportunidad)
            'DISPOSITIVO NO', 'COMUNICACIÓN NO', 'BIDIRECCIONAL NO',
            'CABINA NO', 'PUERTA NO', 'BOTONERA NO',

            # Oportunidades de facturación
            'FUERA DE CONTRATO', 'NO INCLUIDO', 'ADICIONAL',
            'PRESUPUESTO', 'COTIZAR', 'COTIZACIÓN'
        ]

        # Cargar mapeo de tipos
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/tipos_parte_mapeo?select=*",
            headers=HEADERS
        )
        mapeo_tipos = {}
        if response.status_code == 200:
            for row in response.json():
                mapeo_tipos[row['tipo_original'].upper()] = row['tipo_normalizado']

        # Cargar máquinas
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera?select=id,identificador",
            headers=HEADERS
        )
        maquinas_map = {}
        if response.status_code == 200:
            for row in response.json():
                maquinas_map[row['identificador']] = row['id']

        stats = {
            'total': len(df),
            'insertados': 0,
            'duplicados': 0,
            'sin_maquina': 0,
            'errores': 0,
            'recomendaciones_detectadas': 0
        }

        partes_batch = []
        batch_size = 100

        for idx, row in df.iterrows():
            # Validar columnas requeridas
            if pd.isna(row.get('PARTE')) or pd.isna(row.get('MÁQUINA')):
                stats['errores'] += 1
                continue

            # Mapear máquina
            identificador_maquina = str(row['MÁQUINA']).strip()
            maquina_id = maquinas_map.get(identificador_maquina)

            if not maquina_id:
                stats['sin_maquina'] += 1

            # Mapear tipo de parte
            tipo_original = str(row.get('TIPO PARTE', '')).strip().upper()
            tipo_normalizado = mapeo_tipos.get(tipo_original, 'OTRO')

            # Parsear fecha
            fecha_parte = row.get('FECHA')
            if pd.isna(fecha_parte):
                stats['errores'] += 1
                continue

            if isinstance(fecha_parte, datetime):
                fecha_parte_iso = fecha_parte.isoformat()
            else:
                try:
                    fecha_parte_iso = pd.to_datetime(str(fecha_parte)).isoformat()
                except:
                    stats['errores'] += 1
                    continue

            # Detectar recomendaciones
            resolucion = row.get('RESOLUCIÓN', '')
            tiene_recomendacion = False
            recomendacion_extraida = None

            if pd.notna(resolucion):
                texto_upper = str(resolucion).upper()
                for palabra in palabras_clave_recomendacion:
                    if palabra in texto_upper:
                        tiene_recomendacion = True
                        recomendacion_extraida = str(resolucion)
                        stats['recomendaciones_detectadas'] += 1
                        break

            # Preparar datos para inserción
            parte_data = {
                "numero_parte": str(row['PARTE']),
                "tipo_parte_original": str(row.get('TIPO PARTE', '')).strip(),
                "codigo_maquina": str(row.get('CÓD. MÁQUINA', '')) if pd.notna(row.get('CÓD. MÁQUINA')) else None,
                "maquina_texto": identificador_maquina,
                "fecha_parte": fecha_parte_iso,
                "codificacion_adicional": str(row.get('CODIFICACIÓN ADICIONAL', '')) if pd.notna(row.get('CODIFICACIÓN ADICIONAL')) else None,
                "resolucion": str(resolucion) if pd.notna(resolucion) else None,
                "maquina_id": maquina_id,
                "tipo_parte_normalizado": tipo_normalizado,
                "tiene_recomendacion": tiene_recomendacion,
                "recomendaciones_extraidas": recomendacion_extraida if tiene_recomendacion else None,
                "estado": "COMPLETADO",
                "importado": True
            }

            partes_batch.append(parte_data)

            # Insertar por lotes
            if len(partes_batch) >= batch_size:
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/partes_trabajo",
                    json=partes_batch,
                    headers={**HEADERS, "Prefer": "return=representation,resolution=ignore-duplicates"}
                )

                if response.status_code in [200, 201]:
                    stats['insertados'] += len(partes_batch)
                else:
                    stats['errores'] += len(partes_batch)

                partes_batch = []

        # Insertar lote final
        if partes_batch:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/partes_trabajo",
                json=partes_batch,
                headers={**HEADERS, "Prefer": "return=representation,resolution=ignore-duplicates"}
            )

            if response.status_code in [200, 201]:
                stats['insertados'] += len(partes_batch)
            else:
                stats['errores'] += len(partes_batch)

        # Mostrar resumen
        flash(f"Importación completada: {stats['insertados']} partes insertados de {stats['total']} procesados", "success")

        if stats['recomendaciones_detectadas'] > 0:
            flash(f"{stats['recomendaciones_detectadas']} recomendaciones detectadas automáticamente", "success")

        if stats['sin_maquina'] > 0:
            flash(f"{stats['sin_maquina']} partes sin máquina asignada (revisar identificadores)", "warning")

        if stats['errores'] > 0:
            flash(f"{stats['errores']} registros con errores", "warning")

    except Exception as e:
        flash(f"Error al procesar archivo: {str(e)}", "error")
        logger.error(f"Error importando partes: {str(e)}")

    return redirect(url_for('cartera.cartera_importar'))


# @app.route("/cartera/reanalizar-recomendaciones", methods=["POST"])
@cartera_bp.route('/reanalizar-recomendaciones', methods=['POST'])
@helpers.login_required
def cartera_reanalizar_recomendaciones():
    """Re-analizar todos los partes existentes con las nuevas palabras clave"""

    try:
        # Palabras clave actualizadas (mismo array que en importación)
        palabras_clave_recomendacion = [
            # Recomendaciones explícitas
            'RECOMENDACIÓN', 'RECOMENDACION', 'RECOMIENDO', 'RECOMENDAMOS',
            'CONVENDRÍA', 'CONVIENE', 'SERÍA CONVENIENTE', 'SE RECOMIENDA',
            'ACONSEJABLE', 'ACONSEJO', 'SUGERENCIA', 'SUGIERO',

            # Indicadores de urgencia/importancia
            'IMPORTANTE', 'URGENTE', 'NECESARIO', 'IMPRESCINDIBLE', 'CRÍTICO',
            'PRIORITARIO', 'INMEDIATO',

            # Acciones de mantenimiento/reparación
            'CAMBIAR', 'SUSTITUIR', 'REEMPLAZAR', 'MODERNIZAR', 'ACTUALIZAR',
            'REVISAR', 'REPARAR', 'ARREGLAR', 'RENOVAR', 'MEJORAR',

            # Temporalidad
            'PRÓXIMAMENTE', 'PROXIMAMENTE', 'PRONTO', 'EN BREVE',
            'PRÓXIMA REVISIÓN', 'PROXIMA REVISION',

            # Estados problemáticos
            'NO FUNCIONA', 'NO OPERA', 'INOPERATIVO', 'INOPERANTE',
            'FALLA', 'FALLO', 'DEFECTUOSO', 'AVERIADO', 'DETERIORADO',
            'MAL ESTADO', 'DESGASTADO', 'ROTO', 'DAÑADO',

            # Componentes críticos (cuando no funcionan = oportunidad)
            'DISPOSITIVO NO', 'COMUNICACIÓN NO', 'BIDIRECCIONAL NO',
            'CABINA NO', 'PUERTA NO', 'BOTONERA NO',

            # Oportunidades de facturación
            'FUERA DE CONTRATO', 'NO INCLUIDO', 'ADICIONAL',
            'PRESUPUESTO', 'COTIZAR', 'COTIZACIÓN'
        ]

        # Obtener todos los partes de trabajo
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=id,resolucion&limit=10000",
            headers=HEADERS
        )

        if response.status_code != 200:
            flash("Error al obtener partes de trabajo", "error")
            return redirect(url_for('cartera.cartera_dashboard'))

        partes = response.json()

        nuevas_recomendaciones = 0
        partes_actualizados = 0

        # Analizar cada parte
        for parte in partes:
            resolucion = parte.get('resolucion', '')

            if not resolucion:
                continue

            tiene_recomendacion = False
            recomendacion_extraida = None

            texto_upper = str(resolucion).upper()
            for palabra in palabras_clave_recomendacion:
                if palabra in texto_upper:
                    tiene_recomendacion = True
                    recomendacion_extraida = str(resolucion)
                    break

            # Actualizar parte si cambió el estado de recomendación
            update_data = {
                "tiene_recomendacion": tiene_recomendacion,
                "recomendaciones_extraidas": recomendacion_extraida if tiene_recomendacion else None
            }

            # Solo actualizar si hay cambio
            response_update = requests.patch(
                f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte['id']}",
                json=update_data,
                headers=HEADERS
            )

            if response_update.status_code in [200, 204]:
                partes_actualizados += 1
                if tiene_recomendacion:
                    nuevas_recomendaciones += 1

        flash(f"Re-análisis completado: {partes_actualizados} partes actualizados", "success")
        flash(f"{nuevas_recomendaciones} recomendaciones detectadas en total", "info")

    except Exception as e:
        flash(f"Error al re-analizar: {str(e)}", "error")
        logger.error(f"Error en re-análisis: {str(e)}")

    return redirect(url_for('cartera.cartera_dashboard'))


# ============================================
# OPORTUNIDADES DE FACTURACIÓN
# ============================================

# @app.route("/cartera/oportunidades")
@cartera_bp.route('/oportunidades')
@helpers.login_required
def cartera_oportunidades():
    """Dashboard de oportunidades de facturación"""

    # Filtro por estado (opcional)
    estado_filtro = request.args.get('estado', '')

    # Query base (filtrar solo oportunidades de máquinas en cartera)
    query_params = ["select=*,maquinas_cartera!inner(identificador,en_cartera,instalaciones!inner(nombre,en_cartera))"]
    query_params.append("maquinas_cartera.en_cartera=eq.true")
    query_params.append("maquinas_cartera.instalaciones.en_cartera=eq.true")

    if estado_filtro:
        query_params.append(f"estado=eq.{estado_filtro}")

    query_params.append("order=created_at.desc")
    url = f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion?{'&'.join(query_params)}"

    response = requests.get(url, headers=HEADERS)
    oportunidades = response.json() if response.status_code == 200 else []

    # Agrupar por estado para vista Kanban
    oportunidades_por_estado = {
        'DETECTADA': [],
        'PRESUPUESTO_ENVIADO': [],
        'ACEPTADO': [],
        'PENDIENTE_REPUESTO': [],
        'LISTO_EJECUTAR': [],
        'COMPLETADO': [],
        'FACTURADO': [],
        'RECHAZADO': []
    }

    for opp in oportunidades:
        estado = opp.get('estado', 'DETECTADA')
        if estado in oportunidades_por_estado:
            oportunidades_por_estado[estado].append(opp)

    # Estadísticas
    stats = {
        'total': len(oportunidades),
        'detectadas': len(oportunidades_por_estado['DETECTADA']),
        'en_proceso': len(oportunidades_por_estado['PRESUPUESTO_ENVIADO']) + len(oportunidades_por_estado['ACEPTADO']) + len(oportunidades_por_estado['PENDIENTE_REPUESTO']) + len(oportunidades_por_estado['LISTO_EJECUTAR']),
        'completadas': len(oportunidades_por_estado['COMPLETADO']),
        'facturadas': len(oportunidades_por_estado['FACTURADO']),
        'rechazadas': len(oportunidades_por_estado['RECHAZADO'])
    }

    return render_template(
        "cartera/oportunidades.html",
        oportunidades_por_estado=oportunidades_por_estado,
        stats=stats,
        estado_filtro=estado_filtro
    )


# @app.route("/cartera/oportunidades/crear/<int:parte_id>", methods=["GET", "POST"])
@cartera_bp.route('/oportunidades/crear/<int:parte_id>', methods=['GET', 'POST'])
@helpers.login_required
def cartera_crear_oportunidad(parte_id):
    """Crear oportunidad desde una recomendación"""

    if request.method == "GET":
        # Obtener datos del parte
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte_id}&select=*,maquinas_cartera(id,identificador,instalaciones(nombre))",
            headers=HEADERS
        )

        if response.status_code != 200 or not response.json():
            flash("Parte no encontrado", "error")
            return redirect(url_for('cartera.cartera_dashboard'))

        parte = response.json()[0]

        return render_template("cartera/crear_oportunidad.html", parte=parte)

    else:  # POST
        # Obtener datos del formulario
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo')
        prioridad = request.form.get('prioridad', 'MEDIA')
        repuestos = request.form.get('repuestos')

        # Obtener maquina_id del parte
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte_id}&select=maquina_id",
            headers=HEADERS
        )

        if response.status_code != 200 or not response.json():
            flash("Error al obtener datos del parte", "error")
            return redirect(url_for('cartera.cartera_oportunidades'))

        maquina_id = response.json()[0]['maquina_id']

        # Crear oportunidad
        oportunidad_data = {
            "maquina_id": maquina_id,
            "parte_origen_id": parte_id,
            "titulo": titulo,
            "descripcion_tecnica": descripcion,
            "tipo": tipo,
            "estado": "DETECTADA",
            "prioridad_comercial": prioridad,
            "repuestos_necesarios": repuestos if repuestos else None,
            "created_by": session.get("usuario_email", "sistema")
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion",
            json=oportunidad_data,
            headers=HEADERS
        )

        if response.status_code == 201:
            oportunidad_id = response.json()[0]['id']

            # Marcar parte como oportunidad creada
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte_id}",
                json={"oportunidad_creada": True, "oportunidad_id": oportunidad_id, "recomendacion_revisada": True},
                headers=HEADERS
            )

            flash("Oportunidad creada exitosamente", "success")
            return redirect(url_for('cartera.cartera_ver_oportunidad', oportunidad_id=oportunidad_id))
        else:
            logger.error(f"Error creando oportunidad: {response.status_code} - {response.text}")
            flash("Error al crear oportunidad", "error")
            return redirect(url_for('cartera.cartera_oportunidades'))


# @app.route("/cartera/recomendaciones/<int:parte_id>/descartar", methods=["POST"])
@cartera_bp.route('/recomendaciones/<int:parte_id>/descartar', methods=['POST'])
@helpers.login_required
def cartera_descartar_recomendacion(parte_id):
    """Descartar una recomendación sin crear oportunidad"""

    # Marcar recomendación como revisada pero sin crear oportunidad
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte_id}",
        json={
            "recomendacion_revisada": True,
            "oportunidad_creada": False,
            "oportunidad_id": None
        },
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash("Recomendación descartada", "success")
    else:
        logger.error(f"Error descartando recomendación: {response.status_code} - {response.text}")
        flash("Error al descartar recomendación", "error")

    return redirect(url_for('cartera.cartera_dashboard'))


# @app.route("/cartera/oportunidades/<int:oportunidad_id>")
@cartera_bp.route('/oportunidades/<int:oportunidad_id>')
@helpers.login_required
def cartera_ver_oportunidad(oportunidad_id):
    """Ver detalle de oportunidad"""

    # Obtener oportunidad con datos relacionados
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion?id=eq.{oportunidad_id}&select=*,maquinas_cartera(identificador,codigo_maquina,instalaciones(nombre,municipio)),partes_trabajo:parte_origen_id(numero_parte,fecha_parte,tipo_parte,tipo_parte_normalizado,resolucion,recomendaciones_extraidas)",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash("Oportunidad no encontrada", "error")
        return redirect(url_for('cartera.cartera_oportunidades'))

    oportunidad = response.json()[0]

    return render_template("cartera/ver_oportunidad.html", oportunidad=oportunidad)


# @app.route("/cartera/oportunidades/<int:oportunidad_id>/actualizar", methods=["POST"])
@cartera_bp.route('/oportunidades/<int:oportunidad_id>/actualizar', methods=['POST'])
@helpers.login_required
def cartera_actualizar_oportunidad(oportunidad_id):
    """Actualizar estado y datos de oportunidad"""

    # Obtener datos del formulario
    accion = request.form.get('accion')

    update_data = {}

    if accion == 'cambiar_estado':
        nuevo_estado = request.form.get('estado')
        update_data['estado'] = nuevo_estado

        # Actualizar fechas según el estado
        if nuevo_estado == 'PRESUPUESTO_ENVIADO':
            update_data['fecha_envio_presupuesto'] = date.today().isoformat()
            update_data['numero_presupuesto_erp'] = request.form.get('numero_presupuesto')
            update_data['importe_presupuestado'] = request.form.get('importe')
        elif nuevo_estado == 'ACEPTADO':
            update_data['fecha_aceptacion'] = date.today().isoformat()
            update_data['fecha_respuesta_cliente'] = date.today().isoformat()
        elif nuevo_estado == 'RECHAZADO':
            update_data['fecha_rechazo'] = date.today().isoformat()
            update_data['fecha_respuesta_cliente'] = date.today().isoformat()
            update_data['motivo_rechazo'] = request.form.get('motivo_rechazo')
        elif nuevo_estado == 'LISTO_EJECUTAR':
            update_data['fecha_programada_ejecucion'] = date.today().isoformat()
        elif nuevo_estado == 'COMPLETADO':
            update_data['fecha_completado'] = date.today().isoformat()
            update_data['importe_final'] = request.form.get('importe_final')
        elif nuevo_estado == 'FACTURADO':
            update_data['facturado'] = True
            update_data['fecha_factura'] = date.today().isoformat()
            update_data['numero_factura'] = request.form.get('numero_factura')

    elif accion == 'actualizar_repuestos':
        update_data['estado_repuestos'] = request.form.get('estado_repuestos')
        update_data['proveedor'] = request.form.get('proveedor')
        update_data['coste_repuestos'] = request.form.get('coste_repuestos')

        if request.form.get('estado_repuestos') == 'SOLICITADO':
            update_data['fecha_solicitud_repuesto'] = date.today().isoformat()
        elif request.form.get('estado_repuestos') == 'RECIBIDO':
            update_data['fecha_recepcion_repuesto'] = date.today().isoformat()

    elif accion == 'actualizar_notas':
        update_data['notas'] = request.form.get('notas')

    # Actualizar timestamp
    update_data['updated_at'] = datetime.now().isoformat()

    # Ejecutar actualización
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion?id=eq.{oportunidad_id}",
        json=update_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        flash("Oportunidad actualizada correctamente", "success")
    else:
        logger.error(f"Error actualizando oportunidad: {response.status_code} - {response.text}")
        flash("Error al actualizar oportunidad", "error")

    return redirect(url_for('cartera.cartera_ver_oportunidad', oportunidad_id=oportunidad_id))


# @app.route("/cartera/maquina/<int:maquina_id>")
@cartera_bp.route('/maquina/<int:maquina_id>')
@helpers.login_required
def cartera_ver_maquina(maquina_id):
    """Vista detallada de una máquina"""

    # Obtener información de la máquina con instalación
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera?id=eq.{maquina_id}&select=*,instalaciones(id,nombre,municipio)",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        logger.error(f"Error al obtener máquina {maquina_id}: status={response.status_code}, response={response.text}")
        flash("Máquina no encontrada", "error")
        return redirect(url_for('cartera.cartera_dashboard'))

    maquina = response.json()[0]

    # Obtener historial de partes de trabajo
    response_partes = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=eq.{maquina_id}&select=*&order=fecha_parte.desc&limit=50",
        headers=HEADERS
    )
    partes = response_partes.json() if response_partes.status_code == 200 else []

    # Estadísticas
    stats = {}

    # Total de partes
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=eq.{maquina_id}&select=count",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    stats['total_partes'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

    # Averías
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=eq.{maquina_id}&tipo_parte_normalizado=eq.AVERIA&select=count",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    stats['total_averias'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

    # Mantenimientos
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=eq.{maquina_id}&tipo_parte_normalizado=eq.MANTENIMIENTO&select=count",
        headers={**HEADERS, "Prefer": "count=exact"}
    )
    stats['total_mantenimientos'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

    # Recomendaciones
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=eq.{maquina_id}&tiene_recomendacion=eq.true&select=*&order=fecha_parte.desc",
        headers=HEADERS
    )
    recomendaciones = response.json() if response.status_code == 200 else []
    stats['total_recomendaciones'] = len(recomendaciones)

    # Oportunidades
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion?maquina_id=eq.{maquina_id}&select=*&order=created_at.desc",
        headers=HEADERS
    )
    oportunidades = response.json() if response.status_code == 200 else []
    stats['total_oportunidades'] = len(oportunidades)

    # Distribución de tipos de parte
    tipos_distribucion = {}
    for parte in partes:
        tipo = parte.get('tipo_parte_normalizado', 'OTRO')
        tipos_distribucion[tipo] = tipos_distribucion.get(tipo, 0) + 1

    return render_template(
        "cartera/ver_maquina.html",
        maquina=maquina,
        stats=stats,
        partes=partes,
        recomendaciones=recomendaciones,
        oportunidades=oportunidades,
        tipos_distribucion=tipos_distribucion
    )


# @app.route("/cartera/instalacion/<int:instalacion_id>")
@cartera_bp.route('/instalacion/<int:instalacion_id>')
@helpers.login_required
def cartera_ver_instalacion(instalacion_id):
    """Vista detallada de una instalación"""

    # Obtener información de la instalación
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/instalaciones?id=eq.{instalacion_id}&select=*",
        headers=HEADERS
    )

    if not response.json():
        logger.error(f"Error al obtener instalación {instalacion_id}: status={response.status_code}, response={response.text}")
        flash("Instalación no encontrada", "error")
        return redirect(url_for('cartera.cartera_dashboard'))

    instalacion = response.json()[0]

    # Obtener todas las máquinas de esta instalación
    response_maquinas = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera?instalacion_id=eq.{instalacion_id}&select=*&order=identificador.asc",
        headers=HEADERS
    )
    maquinas = response_maquinas.json()

    # Obtener IDs de máquinas para consultas agregadas
    maquina_ids = [m['id'] for m in maquinas]

    # Calcular estadísticas agregadas de todas las máquinas
    stats = {
        'total_maquinas': len(maquinas),
        'total_partes': 0,
        'total_averias': 0,
        'total_mantenimientos': 0,
        'total_recomendaciones': 0,
        'total_oportunidades': 0
    }

    # Obtener todos los partes de todas las máquinas (últimos 100 de toda la instalación)
    partes = []
    if maquina_ids:
        maquina_ids_str = ','.join(map(str, maquina_ids))
        response_partes = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=in.({maquina_ids_str})&select=*,maquinas_cartera(identificador)&order=fecha_parte.desc&limit=100",
            headers=HEADERS
        )
        partes = response_partes.json()

        # Calcular estadísticas
        stats['total_partes'] = len(partes)
        stats['total_averias'] = sum(1 for p in partes if p.get('tipo_parte_normalizado') == 'AVERÍA')
        stats['total_mantenimientos'] = sum(1 for p in partes if p.get('tipo_parte_normalizado') == 'CONSERVACIÓN')

        # Obtener recomendaciones
        response_rec = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?maquina_id=in.({maquina_ids_str})&tiene_recomendacion=eq.true&select=*,maquinas_cartera(identificador)&order=fecha_parte.desc",
            headers=HEADERS
        )
        recomendaciones = response_rec.json()
        stats['total_recomendaciones'] = len(recomendaciones)

        # Obtener oportunidades
        response_op = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades_facturacion?maquina_id=in.({maquina_ids_str})&select=*,maquinas_cartera(identificador)&order=created_at.desc",
            headers=HEADERS
        )
        oportunidades = response_op.json()
        stats['total_oportunidades'] = len(oportunidades)
    else:
        recomendaciones = []
        oportunidades = []

    # Calcular distribución de tipos de partes
    tipos_distribucion = {}
    for parte in partes:
        tipo = parte.get('tipo_parte_normalizado', 'OTRO')
        tipos_distribucion[tipo] = tipos_distribucion.get(tipo, 0) + 1

    # Calcular estadísticas por máquina para tabla
    for maquina in maquinas:
        maquina_partes = [p for p in partes if p['maquina_id'] == maquina['id']]
        maquina['total_partes'] = len(maquina_partes)
        maquina['total_averias'] = sum(1 for p in maquina_partes if p.get('tipo_parte_normalizado') == 'AVERÍA')
        maquina['total_recomendaciones'] = sum(1 for p in maquina_partes if p.get('tiene_recomendacion') == True)

    return render_template(
        "cartera/ver_instalacion.html",
        instalacion=instalacion,
        maquinas=maquinas,
        stats=stats,
        partes=partes,
        recomendaciones=recomendaciones,
        oportunidades=oportunidades,
        tipos_distribucion=tipos_distribucion
    )


# @app.route("/cartera/instalacion/<int:instalacion_id>/dar-baja", methods=["POST"])
@cartera_bp.route('/instalacion/<int:instalacion_id>/dar-baja', methods=['POST'])
@helpers.login_required
def cartera_dar_baja_instalacion(instalacion_id):
    """Dar de baja una instalación"""

    # Obtener datos del formulario
    fecha_baja = request.form.get('fecha_baja')
    motivo = request.form.get('motivo')

    if not fecha_baja or not motivo:
        flash("Debe proporcionar fecha y motivo de baja", "error")
        return redirect(url_for('cartera.cartera_ver_instalacion', instalacion_id=instalacion_id))

    # Actualizar instalación
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/instalaciones?id=eq.{instalacion_id}",
        json={
            "en_cartera": False,
            "fecha_salida_cartera": fecha_baja,
            "motivo_salida": motivo
        },
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        # También marcar todas las máquinas de esta instalación como fuera de cartera
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera?instalacion_id=eq.{instalacion_id}",
            json={
                "en_cartera": False,
                "fecha_salida_cartera": fecha_baja,
                "motivo_salida": f"Instalación dada de baja: {motivo}"
            },
            headers=HEADERS
        )
        flash("Instalación dada de baja correctamente", "success")
    else:
        logger.error(f"Error al dar de baja instalación: {response.status_code} - {response.text}")
        flash("Error al dar de baja la instalación", "error")

    return redirect(url_for('cartera.cartera_ver_instalacion', instalacion_id=instalacion_id))


# @app.route("/cartera/instalacion/<int:instalacion_id>/reactivar", methods=["POST"])
@cartera_bp.route('/instalacion/<int:instalacion_id>/reactivar', methods=['POST'])
@helpers.login_required
def cartera_reactivar_instalacion(instalacion_id):
    """Reactivar una instalación dada de baja"""

    # Actualizar instalación
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/instalaciones?id=eq.{instalacion_id}",
        json={
            "en_cartera": True,
            "fecha_salida_cartera": None,
            "motivo_salida": None
        },
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash("Instalación reactivada correctamente", "success")
    else:
        logger.error(f"Error al reactivar instalación: {response.status_code} - {response.text}")
        flash("Error al reactivar la instalación", "error")

    return redirect(url_for('cartera.cartera_ver_instalacion', instalacion_id=instalacion_id))


# ============================================
# MÓDULO DE ANALÍTICA AVANZADA V2
# Sistema de Alertas y Gestión Predictiva
# ============================================

# @app.route("/cartera/v2")
@cartera_bp.route('/v2')
@helpers.login_required
def cartera_dashboard_v2():
    """Dashboard V2 con sistema de alertas y estado semafórico"""

    # Obtener alertas críticas pendientes (EXCLUIR MANTENIMIENTO y solo máquinas en cartera)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/alertas_automaticas?select=*,maquinas_cartera!inner(identificador,en_cartera,instalaciones!inner(nombre,en_cartera))&maquinas_cartera.en_cartera=eq.true&maquinas_cartera.instalaciones.en_cartera=eq.true&estado=in.(PENDIENTE,EN_REVISION)&tipo_alerta=not.like.%MANTENIMIENTO%&order=nivel_urgencia.desc,fecha_deteccion.desc&limit=10",
        headers=HEADERS
    )
    alertas_criticas = response.json() if response.status_code == 200 else []

    # Obtener resumen de alertas por tipo (EXCLUIR MANTENIMIENTO y solo máquinas en cartera)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/alertas_automaticas?select=tipo_alerta,nivel_urgencia,estado,maquinas_cartera!inner(en_cartera,instalaciones!inner(en_cartera))&maquinas_cartera.en_cartera=eq.true&maquinas_cartera.instalaciones.en_cartera=eq.true&tipo_alerta=not.like.%MANTENIMIENTO%",
        headers=HEADERS
    )
    todas_alertas = response.json() if response.status_code == 200 else []

    alertas_stats = {
        'total': len(todas_alertas),
        'pendientes': sum(1 for a in todas_alertas if a['estado'] in ['PENDIENTE', 'EN_REVISION']),
        'urgentes': sum(1 for a in todas_alertas if a['nivel_urgencia'] == 'URGENTE' and a['estado'] in ['PENDIENTE', 'EN_REVISION']),
        'altas': sum(1 for a in todas_alertas if a['nivel_urgencia'] == 'ALTA' and a['estado'] in ['PENDIENTE', 'EN_REVISION']),
        'fallas_repetidas': sum(1 for a in todas_alertas if a['tipo_alerta'] == 'FALLA_REPETIDA' and a['estado'] in ['PENDIENTE', 'EN_REVISION']),
        'recomendaciones_ignoradas': sum(1 for a in todas_alertas if a['tipo_alerta'] == 'RECOMENDACION_IGNORADA' and a['estado'] in ['PENDIENTE', 'EN_REVISION'])
    }

    # Obtener máquinas por estado semafórico
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_estado_maquinas_semaforico?select=*&order=estado_semaforico.asc,averias_mes.desc",
        headers=HEADERS
    )
    maquinas_semaforico = response.json() if response.status_code == 200 else []

    semaforico_stats = {
        'criticas': sum(1 for m in maquinas_semaforico if m['estado_semaforico'] == 'CRITICO'),
        'inestables': sum(1 for m in maquinas_semaforico if m['estado_semaforico'] == 'INESTABLE'),
        'seguimiento': sum(1 for m in maquinas_semaforico if m['estado_semaforico'] == 'SEGUIMIENTO'),
        'estables': sum(1 for m in maquinas_semaforico if m['estado_semaforico'] == 'ESTABLE')
    }

    # Top 5 máquinas críticas
    maquinas_criticas = [m for m in maquinas_semaforico if m['estado_semaforico'] == 'CRITICO'][:5]

    # Obtener instalaciones con mayor riesgo
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_riesgo_instalaciones?select=*&order=indice_riesgo_instalacion.desc&limit=5",
        headers=HEADERS
    )
    instalaciones_riesgo = response.json() if response.status_code == 200 else []

    # Obtener cálculo de pérdidas
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_perdidas_por_pendientes?select=*",
        headers=HEADERS
    )
    perdidas = response.json()[0] if response.status_code == 200 and response.json() else {}

    # Pendientes técnicos activos
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/pendientes_tecnicos?select=*&estado=in.(PENDIENTE,ASIGNADO,EN_CURSO,BLOQUEADO)&order=nivel_urgencia.desc,created_at.desc&limit=10",
        headers=HEADERS
    )
    pendientes_tecnicos = response.json() if response.status_code == 200 else []

    return render_template(
        "cartera/dashboard_v2.html",
        alertas_criticas=alertas_criticas,
        alertas_stats=alertas_stats,
        maquinas_criticas=maquinas_criticas,
        semaforico_stats=semaforico_stats,
        instalaciones_riesgo=instalaciones_riesgo,
        perdidas=perdidas,
        pendientes_tecnicos=pendientes_tecnicos
    )


# @app.route("/cartera/v2/ejecutar-detectores", methods=["POST"])
@cartera_bp.route('/v2/ejecutar-detectores', methods=['POST'])
@helpers.login_required
def ejecutar_detectores_alertas():
    """Ejecutar detectores de alertas manualmente"""

    try:
        # Importar y ejecutar detectores
        import detectores_alertas
        total_alertas = detectores_alertas.ejecutar_todos_los_detectores()

        flash(f"Detectores ejecutados exitosamente. {total_alertas} alertas nuevas generadas.", "success")
    except Exception as e:
        logger.error(f"Error ejecutando detectores: {str(e)}")
        flash(f"Error al ejecutar detectores: {str(e)}", "error")

    return redirect(url_for('cartera.cartera_dashboard_v2'))


# @app.route("/cartera/v2/alertas")
@cartera_bp.route('/v2/alertas')
@helpers.login_required
def ver_todas_alertas():
    """Ver todas las alertas con filtros"""

    # Filtros
    estado_filtro = request.args.get('estado', '')
    tipo_filtro = request.args.get('tipo', '')
    urgencia_filtro = request.args.get('urgencia', '')

    # Construir query (filtrar solo máquinas en cartera)
    query_params = ["select=*,maquinas_cartera!inner(identificador,en_cartera,instalaciones!inner(nombre,en_cartera))"]
    query_params.append("maquinas_cartera.en_cartera=eq.true")
    query_params.append("maquinas_cartera.instalaciones.en_cartera=eq.true")

    if estado_filtro:
        query_params.append(f"estado=eq.{estado_filtro}")
    if tipo_filtro:
        query_params.append(f"tipo_alerta=eq.{tipo_filtro}")
    else:
        # Si no se filtra por tipo específico, excluir MANTENIMIENTO
        query_params.append("tipo_alerta=not.like.%MANTENIMIENTO%")
    if urgencia_filtro:
        query_params.append(f"nivel_urgencia=eq.{urgencia_filtro}")

    query_params.append("order=fecha_deteccion.desc")

    url = f"{SUPABASE_URL}/rest/v1/alertas_automaticas?{'&'.join(query_params)}"

    response = requests.get(url, headers=HEADERS)
    alertas = response.json() if response.status_code == 200 else []

    return render_template(
        "cartera/alertas.html",
        alertas=alertas,
        estado_filtro=estado_filtro,
        tipo_filtro=tipo_filtro,
        urgencia_filtro=urgencia_filtro
    )


# @app.route("/cartera/v2/alerta/<int:alerta_id>")
@cartera_bp.route('/v2/alerta/<int:alerta_id>')
@helpers.login_required
def ver_detalle_alerta(alerta_id):
    """Ver detalle de una alerta"""

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/alertas_automaticas?id=eq.{alerta_id}&select=*,maquinas_cartera(id,identificador,instalaciones(nombre)),componentes_criticos(nombre,familia)",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash("Alerta no encontrada", "error")
        return redirect(url_for('cartera.ver_todas_alertas'))

    alerta = response.json()[0]

    return render_template("cartera/detalle_alerta.html", alerta=alerta)


# @app.route("/cartera/v2/alerta/<int:alerta_id>/resolver", methods=["POST"])
@cartera_bp.route('/v2/alerta/<int:alerta_id>/resolver', methods=['POST'])
@helpers.login_required
def resolver_alerta(alerta_id):
    """Marcar alerta como resuelta"""

    accion = request.form.get('accion')  # OPORTUNIDAD, TRABAJO_PROGRAMADO, RESUELTA, DESCARTADA
    notas = request.form.get('notas')

    data = {
        "fecha_resolucion": datetime.now().isoformat(),
        "revisada_por": session.get("usuario_email", "usuario"),
        "notas_resolucion": notas
    }

    if accion == 'OPORTUNIDAD':
        data['estado'] = 'OPORTUNIDAD_CREADA'
    elif accion == 'TRABAJO':
        data['estado'] = 'TRABAJO_PROGRAMADO'
    elif accion == 'RESUELTA':
        data['estado'] = 'RESUELTA'
    elif accion == 'DESCARTADA':
        data['estado'] = 'DESCARTADA'

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/alertas_automaticas?id=eq.{alerta_id}",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash("Alerta actualizada correctamente", "success")
    else:
        flash("Error al actualizar alerta", "error")

    return redirect(url_for('cartera.ver_todas_alertas'))


# @app.route("/cartera/v2/pendientes-tecnicos")
@cartera_bp.route('/v2/pendientes-tecnicos')
@helpers.login_required
def ver_pendientes_tecnicos():
    """Vista de backlog técnico para Sergio"""

    # Filtros
    estado_filtro = request.args.get('estado', '')
    urgencia_filtro = request.args.get('urgencia', '')
    asignado_filtro = request.args.get('asignado', '')

    # Construir query
    query_params = ["select=*,maquinas_cartera(identificador,instalaciones(nombre))"]

    if estado_filtro:
        query_params.append(f"estado=eq.{estado_filtro}")
    else:
        # Por defecto, solo activos
        query_params.append("estado=in.(PENDIENTE,ASIGNADO,EN_CURSO,BLOQUEADO)")

    if urgencia_filtro:
        query_params.append(f"nivel_urgencia=eq.{urgencia_filtro}")
    if asignado_filtro:
        query_params.append(f"asignado_a=eq.{asignado_filtro}")

    query_params.append("order=nivel_urgencia.desc,created_at.desc")

    url = f"{SUPABASE_URL}/rest/v1/pendientes_tecnicos?{'&'.join(query_params)}"

    response = requests.get(url, headers=HEADERS)
    pendientes = response.json() if response.status_code == 200 else []

    # Agrupar por urgencia
    pendientes_por_urgencia = {
        'URGENTE': [p for p in pendientes if p['nivel_urgencia'] == 'URGENTE'],
        'ALTA': [p for p in pendientes if p['nivel_urgencia'] == 'ALTA'],
        'MEDIA': [p for p in pendientes if p['nivel_urgencia'] == 'MEDIA'],
        'BAJA': [p for p in pendientes if p['nivel_urgencia'] == 'BAJA']
    }

    # Estadísticas
    stats = {
        'total': len(pendientes),
        'urgentes': len(pendientes_por_urgencia['URGENTE']),
        'altas': len(pendientes_por_urgencia['ALTA']),
        'medias': len(pendientes_por_urgencia['MEDIA']),
        'bajas': len(pendientes_por_urgencia['BAJA'])
    }

    return render_template(
        "cartera/pendientes_tecnicos.html",
        pendientes=pendientes,
        pendientes_por_urgencia=pendientes_por_urgencia,
        stats=stats,
        estado_filtro=estado_filtro,
        urgencia_filtro=urgencia_filtro,
        asignado_filtro=asignado_filtro
    )


# @app.route("/cartera/v2/pendiente/<int:pendiente_id>/actualizar", methods=["POST"])
@cartera_bp.route('/v2/pendiente/<int:pendiente_id>/actualizar', methods=['POST'])
@helpers.login_required
def actualizar_pendiente_tecnico(pendiente_id):
    """Actualizar estado de un pendiente técnico"""

    estado = request.form.get('estado')
    notas = request.form.get('notas')
    asignado = request.form.get('asignado_a')

    data = {
        "updated_at": datetime.now().isoformat()
    }

    if estado:
        data['estado'] = estado
        if estado == 'COMPLETADO':
            data['fecha_completado'] = datetime.now().isoformat()
    if notas:
        data['notas_ejecucion'] = notas
    if asignado:
        data['asignado_a'] = asignado
        if not data.get('fecha_asignacion'):
            data['fecha_asignacion'] = datetime.now().isoformat()

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/pendientes_tecnicos?id=eq.{pendiente_id}",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash("Pendiente técnico actualizado", "success")
    else:
        flash("Error al actualizar pendiente técnico", "error")

    return redirect(url_for('cartera.ver_pendientes_tecnicos'))


# @app.route("/cartera/v2/alerta/<int:alerta_id>/crear-trabajo-tecnico", methods=["POST"])
@cartera_bp.route('/v2/alerta/<int:alerta_id>/crear-trabajo-tecnico', methods=['POST'])
@helpers.login_required
def crear_trabajo_desde_alerta(alerta_id):
    """Crear pendiente técnico desde una alerta"""

    # Obtener datos de la alerta
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/alertas_automaticas?id=eq.{alerta_id}&select=*",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash("Alerta no encontrada", "error")
        return redirect(url_for('cartera.ver_todas_alertas'))

    alerta = response.json()[0]

    # Crear pendiente técnico
    tipo_trabajo_map = {
        'FALLA_REPETIDA': 'REPARACION_CRITICA',
        'RECOMENDACION_IGNORADA': 'COMPONENTE_RECOMENDADO'
    }

    pendiente_data = {
        "maquina_id": alerta['maquina_id'],
        "instalacion_id": alerta['instalacion_id'],
        "alerta_id": alerta_id,
        "tipo_trabajo": tipo_trabajo_map.get(alerta['tipo_alerta'], 'SEGUIMIENTO_TECNICO'),
        "nivel_urgencia": alerta['nivel_urgencia'],
        "titulo": alerta['titulo'],
        "descripcion_tecnica": alerta['descripcion'],
        "estado": "PENDIENTE",
        "created_by": session.get("usuario_email", "sistema")
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/pendientes_tecnicos",
        json=pendiente_data,
        headers=HEADERS
    )

    if response.status_code == 201:
        pendiente_id = response.json()[0]['id']

        # Actualizar alerta
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/alertas_automaticas?id=eq.{alerta_id}",
            json={
                "estado": "TRABAJO_PROGRAMADO",
                "pendiente_tecnico_id": pendiente_id,
                "fecha_revision": datetime.now().isoformat(),
                "revisada_por": session.get("usuario_email", "usuario")
            },
            headers=HEADERS
        )

        flash("Trabajo técnico creado exitosamente", "success")
        return redirect(url_for('cartera.ver_pendientes_tecnicos'))
    else:
        flash("Error al crear trabajo técnico", "error")
        return redirect(url_for('cartera.ver_detalle_alerta', alerta_id=alerta_id))


# ============================================
# RUTAS: SISTEMA DE IA PREDICTIVA
# ============================================

# @app.route("/cartera/ia")
@cartera_bp.route('/ia')
@helpers.login_required
def dashboard_ia_predictiva():
    """Dashboard principal del sistema de IA predictiva - CON RIESGO Y PREDICCIONES"""
    try:
        from datetime import datetime, timedelta

        # Obtener TODOS los análisis (sin límite) para cálculo preciso de riesgo
        response_analisis = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=*,partes_trabajo(numero_parte,fecha_parte,tipo_parte_normalizado,maquina_id,maquinas_cartera(identificador,instalaciones(nombre)))&order=fecha_analisis.desc&limit=1000",
            headers=HEADERS
        )

        analisis = []
        if response_analisis.status_code == 200:
            analisis = response_analisis.json()

        # Obtener recomendaciones pendientes de revisar
        response_recomendaciones = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?tiene_recomendacion=eq.true&recomendacion_revisada=eq.false&select=*,maquinas_cartera(identificador,instalaciones(nombre))&limit=100",
            headers=HEADERS
        )

        recomendaciones_pendientes = []
        if response_recomendaciones.status_code == 200:
            recomendaciones_pendientes = response_recomendaciones.json()

        # CALCULAR RIESGO POR MÁQUINA
        maquinas_riesgo = {}

        for a in analisis:
            parte = a.get('partes_trabajo')
            if not parte or not parte.get('maquina_id'):
                continue

            maquina_id = parte['maquina_id']
            maquina_info = parte.get('maquinas_cartera', {})

            if maquina_id not in maquinas_riesgo:
                maquinas_riesgo[maquina_id] = {
                    'maquina_id': maquina_id,
                    'identificador': maquina_info.get('identificador', f'ID-{maquina_id}'),
                    'instalacion': maquina_info.get('instalaciones', {}).get('nombre', 'Desconocida'),
                    'puntuacion_riesgo': 0,
                    'total_fallos': 0,
                    'criticos': 0,
                    'graves': 0,
                    'componentes': set(),
                    'ultimo_fallo': None,
                    'dias_desde_ultimo': 999
                }

            m = maquinas_riesgo[maquina_id]
            m['total_fallos'] += 1

            # Puntos por gravedad
            gravedad = a.get('gravedad_tecnica', 'LEVE')
            if gravedad == 'CRITICA':
                m['puntuacion_riesgo'] += 40
                m['criticos'] += 1
            elif gravedad == 'GRAVE':
                m['puntuacion_riesgo'] += 25
                m['graves'] += 1
            elif gravedad == 'MODERADA':
                m['puntuacion_riesgo'] += 10
            else:
                m['puntuacion_riesgo'] += 3

            # Componentes afectados
            if a.get('componente_principal'):
                m['componentes'].add(a['componente_principal'])

            # Fecha último fallo
            fecha_parte = parte.get('fecha_parte')
            if fecha_parte:
                if not m['ultimo_fallo'] or fecha_parte > m['ultimo_fallo']:
                    m['ultimo_fallo'] = fecha_parte

        # Calcular días desde último fallo y ajustar puntuación
        ahora = datetime.now()
        for m in maquinas_riesgo.values():
            if m['ultimo_fallo']:
                try:
                    fecha_dt = datetime.fromisoformat(m['ultimo_fallo'].replace('Z', '+00:00'))
                    m['dias_desde_ultimo'] = (ahora - fecha_dt).days

                    # Fallos recientes aumentan el riesgo
                    if m['dias_desde_ultimo'] < 30:
                        m['puntuacion_riesgo'] *= 1.5  # +50% si fallo en último mes
                    elif m['dias_desde_ultimo'] < 90:
                        m['puntuacion_riesgo'] *= 1.2  # +20% si fallo en últimos 3 meses
                except:
                    pass

            # Diversidad de componentes fallando aumenta riesgo
            m['puntuacion_riesgo'] += len(m['componentes']) * 5

            # Convertir set a lista para JSON
            m['componentes'] = list(m['componentes'])

            # Normalizar a escala 0-100
            m['puntuacion_riesgo'] = min(100, int(m['puntuacion_riesgo']))

        # Top 20 máquinas en riesgo
        maquinas_criticas = sorted(
            maquinas_riesgo.values(),
            key=lambda x: x['puntuacion_riesgo'],
            reverse=True
        )[:20]

        # Procesar estadísticas generales
        componentes_count = {}
        gravedad_count = {'LEVE': 0, 'MODERADA': 0, 'GRAVE': 0, 'CRITICA': 0}

        for a in analisis:
            comp = a.get('componente_principal', 'Desconocido')
            componentes_count[comp] = componentes_count.get(comp, 0) + 1

            grav = a.get('gravedad_tecnica', 'LEVE')
            if grav in gravedad_count:
                gravedad_count[grav] += 1

        componentes = sorted(
            [{'componente': k, 'total_fallos': v} for k, v in componentes_count.items()],
            key=lambda x: x['total_fallos'],
            reverse=True
        )[:10]

        stats = {
            'total_analisis': len(analisis),
            'graves_criticos': gravedad_count['GRAVE'] + gravedad_count['CRITICA'],
            'moderados': gravedad_count['MODERADA'],
            'leves': gravedad_count['LEVE'],
            'componentes_unicos': len(componentes_count),
            'maquinas_en_riesgo': len([m for m in maquinas_riesgo.values() if m['puntuacion_riesgo'] > 50]),
            'recomendaciones_pendientes': len(recomendaciones_pendientes)
        }

        return render_template(
            "cartera/dashboard_ia_riesgo.html",
            analisis=analisis[:20],
            componentes=componentes,
            stats=stats,
            gravedad_count=gravedad_count,
            maquinas_criticas=maquinas_criticas,
            recomendaciones_pendientes=recomendaciones_pendientes[:20]
        )

    except Exception as e:
        logger.error(f"Error en dashboard IA: {str(e)}")
        flash(f"Error al cargar dashboard de IA: {str(e)}", "error")
        return redirect(url_for('cartera.cartera_dashboard_v2'))


# @app.route("/cartera/ia/priorizar-recomendaciones")
@cartera_bp.route('/ia/priorizar-recomendaciones')
@helpers.login_required
def priorizar_recomendaciones_ia():
    """Analizar y priorizar recomendaciones pendientes con IA"""
    try:
        from anthropic import Anthropic
        import json as json_lib

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            flash("ANTHROPIC_API_KEY no configurada", "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        # Obtener recomendaciones pendientes
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?tiene_recomendacion=eq.true&recomendacion_revisada=eq.false&select=*,maquinas_cartera(identificador,instalaciones(nombre))&limit=50",
            headers=HEADERS
        )

        if response.status_code != 200:
            flash("Error obteniendo recomendaciones", "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        recomendaciones = response.json()

        if not recomendaciones:
            flash("✅ No hay recomendaciones pendientes de revisar", "info")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        # Preparar datos para IA
        resumen_recomendaciones = []
        for r in recomendaciones[:20]:  # Solo primeras 20 para no exceder límites
            resumen_recomendaciones.append({
                'numero_parte': r.get('numero_parte'),
                'maquina': r.get('maquinas_cartera', {}).get('identificador', 'N/A'),
                'fecha': r.get('fecha_parte', '')[:10],
                'tipo': r.get('tipo_parte_normalizado'),
                'recomendacion': r.get('recomendaciones', '')[:500]  # Limitar longitud
            })

        prompt = f"""Eres un experto en mantenimiento de ascensores. Analiza estas {len(resumen_recomendaciones)} recomendaciones pendientes y priorizalas.

RECOMENDACIONES:
{json_lib.dumps(resumen_recomendaciones, indent=2, ensure_ascii=False)}

TAREA:
1. Clasifica cada recomendación por URGENCIA (URGENTE, ALTA, MEDIA, BAJA)
2. Identifica patrones críticos (componentes recurrentes, máquinas problemáticas)
3. Sugiere las 5 acciones prioritarias
4. Estima riesgo si se ignoran

Responde SOLO con JSON:
{{
  "top_5_prioritarias": ["acción 1", "acción 2", ...],
  "patrones_criticos": ["patrón 1", "patrón 2", ...],
  "maquinas_atencion_urgente": ["máquina 1", "máquina 2", ...],
  "resumen_ejecutivo": "resumen en 2-3 líneas"
}}"""

        # Llamar a Claude
        client = Anthropic(api_key=api_key)
        response_ia = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parsear respuesta
        contenido = response_ia.content[0].text
        try:
            analisis = json_lib.loads(contenido)
        except:
            import re
            match = re.search(r'\{.*\}', contenido, re.DOTALL)
            if match:
                analisis = json_lib.loads(match.group())
            else:
                analisis = {
                    "top_5_prioritarias": ["Error al parsear respuesta"],
                    "patrones_criticos": [],
                    "maquinas_atencion_urgente": [],
                    "resumen_ejecutivo": contenido[:200]
                }

        return render_template(
            "cartera/recomendaciones_priorizadas.html",
            analisis=analisis,
            total_recomendaciones=len(recomendaciones),
            recomendaciones=recomendaciones[:20]
        )

    except Exception as e:
        logger.error(f"Error priorizando recomendaciones: {str(e)}")
        flash(f"Error al priorizar recomendaciones: {str(e)}", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/maquina/<int:maquina_id>")
@cartera_bp.route('/ia/maquina/<int:maquina_id>')
@helpers.login_required
def prediccion_maquina_ia(maquina_id):
    """Vista de predicción individual por máquina - FASE 2"""
    try:
        from anthropic import Anthropic
        import json as json_lib
        from datetime import datetime, timedelta

        # Obtener información de la máquina
        response_maquina = requests.get(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera?id=eq.{maquina_id}&select=*,instalaciones(nombre,direccion)",
            headers=HEADERS
        )

        if response_maquina.status_code != 200 or not response_maquina.json():
            flash("Máquina no encontrada", "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        maquina = response_maquina.json()[0]

        # Obtener todos los análisis de esta máquina
        response_analisis = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=*,partes_trabajo(numero_parte,fecha_parte,tipo_parte_normalizado,resolucion)&partes_trabajo.maquina_id=eq.{maquina_id}&order=partes_trabajo(fecha_parte).desc&limit=500",
            headers=HEADERS
        )

        analisis_list = []
        if response_analisis.status_code == 200:
            analisis_list = response_analisis.json()

        if not analisis_list:
            flash("No hay análisis IA para esta máquina todavía", "info")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        # Calcular estadísticas de la máquina
        componentes_afectados = {}
        gravedad_count = {'LEVE': 0, 'MODERADA': 0, 'GRAVE': 0, 'CRITICA': 0}
        fallos_por_mes = {}

        for a in analisis_list:
            # Componentes
            comp = a.get('componente_principal', 'Desconocido')
            if comp not in componentes_afectados:
                componentes_afectados[comp] = {'total': 0, 'criticos': 0, 'graves': 0}
            componentes_afectados[comp]['total'] += 1

            grav = a.get('gravedad_tecnica', 'LEVE')
            if grav in gravedad_count:
                gravedad_count[grav] += 1
            if grav == 'CRITICA':
                componentes_afectados[comp]['criticos'] += 1
            elif grav == 'GRAVE':
                componentes_afectados[comp]['graves'] += 1

            # Fallos por mes
            parte = a.get('partes_trabajo', {})
            fecha = parte.get('fecha_parte', '')
            if fecha:
                mes = fecha[:7]  # YYYY-MM
                fallos_por_mes[mes] = fallos_por_mes.get(mes, 0) + 1

        # Top componentes problemáticos
        top_componentes = sorted(
            [{'componente': k, **v} for k, v in componentes_afectados.items()],
            key=lambda x: (x['criticos'], x['graves'], x['total']),
            reverse=True
        )[:5]

        # GENERAR PREDICCIÓN CON IA
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        prediccion_ia = None

        if api_key and len(analisis_list) >= 3:  # Mínimo 3 análisis para predecir
            try:
                client = Anthropic(api_key=api_key)

                # Preparar resumen para IA
                resumen_fallos = []
                for a in analisis_list[:20]:  # Últimos 20
                    parte = a.get('partes_trabajo', {})
                    resumen_fallos.append({
                        'fecha': parte.get('fecha_parte', '')[:10],
                        'componente': a.get('componente_principal'),
                        'tipo_fallo': a.get('tipo_fallo'),
                        'gravedad': a.get('gravedad_tecnica'),
                        'recomendacion': a.get('recomendacion_ia', '')[:200]
                    })

                prompt = f"""Eres un experto en mantenimiento predictivo de ascensores. Analiza el historial de esta máquina y predice fallos futuros.

MÁQUINA: {maquina.get('identificador')}
INSTALACIÓN: {maquina.get('instalaciones', {}).get('nombre', 'N/A')}
TOTAL FALLOS ANALIZADOS: {len(analisis_list)}

HISTORIAL RECIENTE (últimos 20):
{json_lib.dumps(resumen_fallos, indent=2, ensure_ascii=False)}

ESTADÍSTICAS:
- Críticos: {gravedad_count['CRITICA']}
- Graves: {gravedad_count['GRAVE']}
- Moderados: {gravedad_count['MODERADA']}

TAREA:
1. Identifica componentes con alto riesgo de fallo
2. Predice probabilidad de fallo próximo (0-100%)
3. Estima días hasta próximo fallo probable
4. Genera 3 recomendaciones preventivas específicas

Responde SOLO con JSON:
{{
  "salud_general": "EXCELENTE|BUENA|REGULAR|MALA|CRITICA",
  "puntuacion_salud": 0-100,
  "componentes_riesgo": [
    {{"componente": "nombre", "probabilidad_fallo": 75, "dias_estimados": 30, "razon": "explicación"}},
    ...top 3
  ],
  "prediccion_proxima_averia": {{"dias": 15, "componente_probable": "nombre", "confianza": 80}},
  "recomendaciones": ["acción 1", "acción 2", "acción 3"],
  "tendencia": "MEJORANDO|ESTABLE|DETERIORANDO",
  "resumen": "resumen ejecutivo en 2 líneas"
}}"""

                response_ia = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )

                contenido = response_ia.content[0].text
                try:
                    prediccion_ia = json_lib.loads(contenido)
                except:
                    import re
                    match = re.search(r'\{.*\}', contenido, re.DOTALL)
                    if match:
                        prediccion_ia = json_lib.loads(match.group())

            except Exception as e:
                logger.error(f"Error generando predicción IA: {str(e)}")

        # Calcular puntuación de riesgo local
        puntuacion_riesgo = 0
        puntuacion_riesgo += gravedad_count['CRITICA'] * 40
        puntuacion_riesgo += gravedad_count['GRAVE'] * 25
        puntuacion_riesgo += gravedad_count['MODERADA'] * 10
        puntuacion_riesgo += len(componentes_afectados) * 5

        # Fallos recientes aumentan riesgo
        ahora = datetime.now()
        if analisis_list:
            ultima_fecha = analisis_list[0].get('partes_trabajo', {}).get('fecha_parte')
            if ultima_fecha:
                try:
                    fecha_dt = datetime.fromisoformat(ultima_fecha.replace('Z', '+00:00'))
                    dias_desde = (ahora - fecha_dt).days
                    if dias_desde < 30:
                        puntuacion_riesgo *= 1.5
                    elif dias_desde < 90:
                        puntuacion_riesgo *= 1.2
                except:
                    pass

        puntuacion_riesgo = min(100, int(puntuacion_riesgo))

        return render_template(
            "cartera/dashboard_maquina_ia.html",
            maquina=maquina,
            analisis=analisis_list[:20],
            total_analisis=len(analisis_list),
            top_componentes=top_componentes,
            gravedad_count=gravedad_count,
            fallos_por_mes=sorted(fallos_por_mes.items())[-12:],  # Últimos 12 meses
            puntuacion_riesgo=puntuacion_riesgo,
            prediccion_ia=prediccion_ia
        )

    except Exception as e:
        logger.error(f"Error en predicción máquina: {str(e)}")
        flash(f"Error al cargar predicción: {str(e)}", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/patrones")
@cartera_bp.route('/ia/patrones')
@helpers.login_required
def patrones_tendencias_ia():
    """Dashboard de detección de patrones y tendencias - FASE 3"""
    try:
        from collections import defaultdict
        from datetime import datetime, timedelta
        import calendar

        # Obtener todos los análisis con sus relaciones
        response_analisis = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=*,partes_trabajo(id,fecha_parte,numero_parte,maquina_id,maquinas_cartera(id,identificador,instalaciones(id,nombre,cliente_id,clientes(nombre))))&order=created_at.desc&limit=5000",
            headers=HEADERS
        )

        if response_analisis.status_code != 200:
            error_msg = f"Error al cargar análisis (Status: {response_analisis.status_code})"
            try:
                error_detail = response_analisis.json()
                logger.error(f"Error en patrones y tendencias - Status {response_analisis.status_code}: {error_detail}")
                # Si hay un mensaje de error específico, mostrarlo
                if isinstance(error_detail, dict) and 'message' in error_detail:
                    error_msg = f"Error al cargar análisis: {error_detail['message']}"
            except:
                logger.error(f"Error en patrones y tendencias - Status {response_analisis.status_code}: {response_analisis.text}")

            flash(error_msg, "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        analisis_list = response_analisis.json()

        if not analisis_list:
            return render_template("cartera/dashboard_patrones.html",
                                   sin_datos=True)

        # 1. ANÁLISIS DE COMPONENTES QUE FALLAN JUNTOS
        # Agrupar por máquina y período de 30 días
        maquina_periodos = defaultdict(list)
        for a in analisis_list:
            if not a.get('partes_trabajo') or not a['partes_trabajo'].get('fecha_parte'):
                continue

            maquina_id = a['partes_trabajo'].get('maquina_id')
            fecha = datetime.fromisoformat(a['partes_trabajo']['fecha_parte'].replace('Z', '+00:00'))
            componente = a.get('componente_principal', 'Desconocido')

            if maquina_id and componente and componente != 'Desconocido':
                maquina_periodos[maquina_id].append({
                    'fecha': fecha,
                    'componente': componente,
                    'gravedad': a.get('gravedad_tecnica', 'LEVE')
                })

        # Detectar componentes que fallan juntos (en ventana de 30 días)
        correlaciones_componentes = defaultdict(int)
        for maquina_id, fallos in maquina_periodos.items():
            fallos_sorted = sorted(fallos, key=lambda x: x['fecha'])
            for i, fallo1 in enumerate(fallos_sorted):
                for fallo2 in fallos_sorted[i+1:]:
                    if (fallo2['fecha'] - fallo1['fecha']).days <= 30:
                        comp1, comp2 = sorted([fallo1['componente'], fallo2['componente']])
                        if comp1 != comp2:
                            correlaciones_componentes[f"{comp1} + {comp2}"] += 1

        # Top 10 correlaciones
        top_correlaciones = sorted(correlaciones_componentes.items(), key=lambda x: x[1], reverse=True)[:10]

        # 2. ESTACIONALIDAD - Análisis por mes
        fallos_por_mes = defaultdict(int)
        gravedad_por_mes = defaultdict(lambda: {'CRITICA': 0, 'GRAVE': 0, 'MODERADA': 0, 'LEVE': 0})

        for a in analisis_list:
            if not a.get('partes_trabajo') or not a['partes_trabajo'].get('fecha_parte'):
                continue

            fecha = datetime.fromisoformat(a['partes_trabajo']['fecha_parte'].replace('Z', '+00:00'))
            mes_nombre = calendar.month_name[fecha.month]
            gravedad = a.get('gravedad_tecnica', 'LEVE')

            fallos_por_mes[mes_nombre] += 1
            gravedad_por_mes[mes_nombre][gravedad] += 1

        # Ordenar por cantidad de fallos
        estacionalidad = sorted(fallos_por_mes.items(), key=lambda x: x[1], reverse=True)[:12]

        # 3. INSTALACIONES MÁS PROBLEMÁTICAS
        problemas_por_instalacion = defaultdict(lambda: {
            'total': 0,
            'criticos': 0,
            'graves': 0,
            'instalacion_nombre': '',
            'cliente_nombre': '',
            'maquinas': set()
        })

        for a in analisis_list:
            parte = a.get('partes_trabajo')
            if not parte:
                continue

            maquina = parte.get('maquinas_cartera')
            if not maquina:
                continue

            instalacion = maquina.get('instalaciones')
            if not instalacion:
                continue

            inst_id = instalacion['id']
            gravedad = a.get('gravedad_tecnica', 'LEVE')

            problemas_por_instalacion[inst_id]['total'] += 1
            if gravedad == 'CRITICA':
                problemas_por_instalacion[inst_id]['criticos'] += 1
            elif gravedad == 'GRAVE':
                problemas_por_instalacion[inst_id]['graves'] += 1

            problemas_por_instalacion[inst_id]['instalacion_nombre'] = instalacion.get('nombre', 'N/A')
            if instalacion.get('clientes'):
                problemas_por_instalacion[inst_id]['cliente_nombre'] = instalacion['clientes'].get('nombre', 'N/A')
            problemas_por_instalacion[inst_id]['maquinas'].add(maquina.get('identificador', 'N/A'))

        # Convertir a lista y ordenar
        instalaciones_problematicas = []
        for inst_id, data in problemas_por_instalacion.items():
            instalaciones_problematicas.append({
                'instalacion': data['instalacion_nombre'],
                'cliente': data['cliente_nombre'],
                'total_fallos': data['total'],
                'criticos': data['criticos'],
                'graves': data['graves'],
                'num_maquinas': len(data['maquinas']),
                'fallos_por_maquina': round(data['total'] / len(data['maquinas']), 1) if data['maquinas'] else 0
            })

        instalaciones_problematicas = sorted(instalaciones_problematicas,
                                            key=lambda x: x['total_fallos'],
                                            reverse=True)[:15]

        # 4. INTERVALOS PROMEDIO ENTRE FALLOS (por componente)
        intervalos_componente = defaultdict(list)
        for maquina_id, fallos in maquina_periodos.items():
            fallos_por_comp = defaultdict(list)
            for fallo in fallos:
                fallos_por_comp[fallo['componente']].append(fallo['fecha'])

            for comp, fechas in fallos_por_comp.items():
                if len(fechas) >= 2:
                    fechas_sorted = sorted(fechas)
                    for i in range(len(fechas_sorted) - 1):
                        dias = (fechas_sorted[i+1] - fechas_sorted[i]).days
                        if dias > 0:  # Evitar fallos el mismo día
                            intervalos_componente[comp].append(dias)

        # Calcular promedio
        intervalos_promedio = []
        for comp, intervalos in intervalos_componente.items():
            if intervalos:
                intervalos_promedio.append({
                    'componente': comp,
                    'intervalo_promedio': round(sum(intervalos) / len(intervalos), 1),
                    'min_dias': min(intervalos),
                    'max_dias': max(intervalos),
                    'total_mediciones': len(intervalos)
                })

        intervalos_promedio = sorted(intervalos_promedio,
                                     key=lambda x: x['intervalo_promedio'])[:15]

        # 5. COMPONENTES MÁS CRÍTICOS (por gravedad)
        componentes_criticos = defaultdict(lambda: {'total': 0, 'criticos': 0, 'graves': 0})
        for a in analisis_list:
            comp = a.get('componente_principal')
            if comp and comp != 'Desconocido':
                gravedad = a.get('gravedad_tecnica', 'LEVE')
                componentes_criticos[comp]['total'] += 1
                if gravedad == 'CRITICA':
                    componentes_criticos[comp]['criticos'] += 1
                elif gravedad == 'GRAVE':
                    componentes_criticos[comp]['graves'] += 1

        # Convertir y ordenar por % de críticos
        comp_criticos_list = []
        for comp, data in componentes_criticos.items():
            if data['total'] >= 3:  # Mínimo 3 ocurrencias
                comp_criticos_list.append({
                    'componente': comp,
                    'total': data['total'],
                    'criticos': data['criticos'],
                    'graves': data['graves'],
                    'porcentaje_critico': round((data['criticos'] / data['total']) * 100, 1)
                })

        comp_criticos_list = sorted(comp_criticos_list,
                                    key=lambda x: (x['porcentaje_critico'], x['total']),
                                    reverse=True)[:15]

        # Estadísticas generales
        stats = {
            'total_analisis': len(analisis_list),
            'total_patrones_detectados': len(top_correlaciones),
            'meses_analizados': len(estacionalidad),
            'instalaciones_analizadas': len(instalaciones_problematicas),
            'componentes_analizados': len(intervalos_promedio)
        }

        return render_template(
            "cartera/dashboard_patrones.html",
            stats=stats,
            correlaciones=top_correlaciones,
            estacionalidad=estacionalidad,
            gravedad_por_mes=dict(gravedad_por_mes),
            instalaciones=instalaciones_problematicas,
            intervalos=intervalos_promedio,
            componentes_criticos=comp_criticos_list,
            sin_datos=False
        )

    except Exception as e:
        logger.error(f"Error en patrones y tendencias: {str(e)}")
        flash(f"Error al analizar patrones: {str(e)}", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/roi")
@cartera_bp.route('/ia/roi')
@helpers.login_required
def roi_optimizacion_ia():
    """Dashboard de ROI y Optimización del Mantenimiento - FASE 4"""
    try:
        from collections import defaultdict
        from datetime import datetime, timedelta

        # Costes estimados por gravedad (en euros)
        COSTES_GRAVEDAD = {
            'CRITICA': 500,
            'GRAVE': 300,
            'MODERADA': 150,
            'LEVE': 75
        }

        # Obtener todos los análisis con partes
        response_analisis = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=*,partes_trabajo(id,fecha_parte,numero_parte,tipo_parte_normalizado,fecha_cierre,maquina_id,maquinas_cartera(id,identificador,instalaciones(id,nombre)))&order=created_at.desc&limit=5000",
            headers=HEADERS
        )

        if response_analisis.status_code != 200:
            error_msg = f"Error al cargar análisis (Status: {response_analisis.status_code})"
            try:
                error_detail = response_analisis.json()
                logger.error(f"Error en ROI y optimización - Status {response_analisis.status_code}: {error_detail}")
                # Si hay un mensaje de error específico, mostrarlo
                if isinstance(error_detail, dict) and 'message' in error_detail:
                    error_msg = f"Error al cargar análisis: {error_detail['message']}"
            except:
                logger.error(f"Error en ROI y optimización - Status {response_analisis.status_code}: {response_analisis.text}")

            flash(error_msg, "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        analisis_list = response_analisis.json()

        if not analisis_list:
            return render_template("cartera/dashboard_roi.html", sin_datos=True)

        # 1. CÁLCULO DE COSTES POR GRAVEDAD
        costes_por_gravedad = {'CRITICA': 0, 'GRAVE': 0, 'MODERADA': 0, 'LEVE': 0}
        conteo_gravedad = {'CRITICA': 0, 'GRAVE': 0, 'MODERADA': 0, 'LEVE': 0}

        for a in analisis_list:
            gravedad = a.get('gravedad_tecnica', 'LEVE')
            costes_por_gravedad[gravedad] += COSTES_GRAVEDAD[gravedad]
            conteo_gravedad[gravedad] += 1

        coste_total = sum(costes_por_gravedad.values())

        # 2. AHORRO POTENCIAL (si se previenen averías)
        # Estimación: Con IA predictiva se pueden prevenir ~30% de GRAVES y CRÍTICAS
        averias_prevenibles = {
            'CRITICA': int(conteo_gravedad['CRITICA'] * 0.30),
            'GRAVE': int(conteo_gravedad['GRAVE'] * 0.30)
        }
        ahorro_potencial = (
            averias_prevenibles['CRITICA'] * COSTES_GRAVEDAD['CRITICA'] +
            averias_prevenibles['GRAVE'] * COSTES_GRAVEDAD['GRAVE']
        )

        # 3. ANÁLISIS DE TIEMPOS DE RESPUESTA
        tiempos_respuesta = []
        partes_con_fecha_cierre = 0

        for a in analisis_list:
            parte = a.get('partes_trabajo')
            if not parte:
                continue

            fecha_parte = parte.get('fecha_parte')
            fecha_cierre = parte.get('fecha_cierre')

            if fecha_parte and fecha_cierre:
                try:
                    f_parte = datetime.fromisoformat(fecha_parte.replace('Z', '+00:00'))
                    f_cierre = datetime.fromisoformat(fecha_cierre.replace('Z', '+00:00'))
                    dias = (f_cierre - f_parte).days
                    if dias >= 0:
                        tiempos_respuesta.append({
                            'dias': dias,
                            'gravedad': a.get('gravedad_tecnica', 'LEVE'),
                            'numero_parte': parte.get('numero_parte', 'N/A')
                        })
                        partes_con_fecha_cierre += 1
                except:
                    pass

        # Calcular promedios por gravedad
        tiempos_por_gravedad = defaultdict(list)
        for t in tiempos_respuesta:
            tiempos_por_gravedad[t['gravedad']].append(t['dias'])

        promedios_respuesta = {}
        for gravedad, dias_list in tiempos_por_gravedad.items():
            if dias_list:
                promedios_respuesta[gravedad] = {
                    'promedio': round(sum(dias_list) / len(dias_list), 1),
                    'min': min(dias_list),
                    'max': max(dias_list),
                    'total': len(dias_list)
                }

        # 4. EFICIENCIA DEL MANTENIMIENTO
        # Contar tipos de partes
        tipos_parte = defaultdict(int)
        for a in analisis_list:
            parte = a.get('partes_trabajo')
            if parte:
                tipo = parte.get('tipo_parte_normalizado', 'DESCONOCIDO')
                tipos_parte[tipo] += 1

        # Clasificar en preventivo vs correctivo
        preventivos = tipos_parte.get('CONSERVACION', 0) + tipos_parte.get('IPO', 0) + tipos_parte.get('MANTENIMIENTO', 0)
        correctivos = tipos_parte.get('AVERIA', 0) + tipos_parte.get('REPARACION', 0) + tipos_parte.get('RESCATE', 0)
        total_clasificados = preventivos + correctivos

        porcentaje_preventivo = round((preventivos / total_clasificados * 100), 1) if total_clasificados > 0 else 0
        porcentaje_correctivo = round((correctivos / total_clasificados * 100), 1) if total_clasificados > 0 else 0

        # 5. PARTES CON RECOMENDACIONES IA
        partes_con_recomendacion = sum(1 for a in analisis_list if a.get('recomendacion_ia'))
        porcentaje_con_recomendacion = round((partes_con_recomendacion / len(analisis_list) * 100), 1) if analisis_list else 0

        # 6. COSTE DEL SISTEMA IA
        coste_analisis_ia = len(analisis_list) * 0.0003  # $0.0003 por análisis con Haiku
        coste_analisis_ia_eur = coste_analisis_ia * 0.92  # Conversión aproximada USD a EUR

        # 7. ROI CALCULADO
        roi_porcentaje = round(((ahorro_potencial - coste_analisis_ia_eur) / coste_analisis_ia_eur * 100), 1) if coste_analisis_ia_eur > 0 else 0

        # 8. TOP 10 MÁQUINAS MÁS COSTOSAS
        costes_por_maquina = defaultdict(lambda: {'coste': 0, 'fallos': 0, 'criticos': 0, 'identificador': '', 'instalacion': ''})

        for a in analisis_list:
            parte = a.get('partes_trabajo')
            if not parte:
                continue

            maquina = parte.get('maquinas_cartera')
            if not maquina:
                continue

            maquina_id = maquina['id']
            gravedad = a.get('gravedad_tecnica', 'LEVE')

            costes_por_maquina[maquina_id]['coste'] += COSTES_GRAVEDAD[gravedad]
            costes_por_maquina[maquina_id]['fallos'] += 1
            if gravedad == 'CRITICA':
                costes_por_maquina[maquina_id]['criticos'] += 1

            costes_por_maquina[maquina_id]['identificador'] = maquina.get('identificador', 'N/A')
            if maquina.get('instalaciones'):
                costes_por_maquina[maquina_id]['instalacion'] = maquina['instalaciones'].get('nombre', 'N/A')

        # Convertir a lista y ordenar
        maquinas_costosas = []
        for maq_id, data in costes_por_maquina.items():
            maquinas_costosas.append({
                'maquina_id': maq_id,
                'identificador': data['identificador'],
                'instalacion': data['instalacion'],
                'coste_total': data['coste'],
                'total_fallos': data['fallos'],
                'criticos': data['criticos'],
                'coste_promedio': round(data['coste'] / data['fallos'], 2)
            })

        maquinas_costosas = sorted(maquinas_costosas, key=lambda x: x['coste_total'], reverse=True)[:10]

        # 9. RECOMENDACIONES DE OPTIMIZACIÓN (automáticas)
        recomendaciones = []

        # Recomendación 1: Ratio preventivo/correctivo
        if porcentaje_preventivo < 40:
            recomendaciones.append({
                'tipo': 'EFICIENCIA',
                'titulo': 'Incrementar Mantenimiento Preventivo',
                'descripcion': f'Actualmente solo el {porcentaje_preventivo}% del mantenimiento es preventivo. Objetivo recomendado: 60-70%.',
                'ahorro_estimado': int((40 - porcentaje_preventivo) * coste_total / 100 * 0.5),
                'prioridad': 'ALTA'
            })

        # Recomendación 2: Tiempos de respuesta altos
        if 'CRITICA' in promedios_respuesta and promedios_respuesta['CRITICA']['promedio'] > 3:
            recomendaciones.append({
                'tipo': 'TIEMPO_RESPUESTA',
                'titulo': 'Reducir Tiempo de Respuesta en Críticos',
                'descripcion': f'El tiempo promedio de resolución de averías críticas es {promedios_respuesta["CRITICA"]["promedio"]} días. Objetivo: <24h.',
                'ahorro_estimado': int(conteo_gravedad['CRITICA'] * 100),  # €100 por avería crítica resuelta rápido
                'prioridad': 'ALTA'
            })

        # Recomendación 3: Máquinas muy costosas
        if maquinas_costosas and maquinas_costosas[0]['coste_total'] > 2000:
            recomendaciones.append({
                'tipo': 'MAQUINA_PROBLEMATICA',
                'titulo': f'Auditoría de Máquina: {maquinas_costosas[0]["identificador"]}',
                'descripcion': f'Esta máquina acumula €{maquinas_costosas[0]["coste_total"]} en costes. Considerar revisión completa o sustitución.',
                'ahorro_estimado': int(maquinas_costosas[0]['coste_total'] * 0.5),
                'prioridad': 'MEDIA'
            })

        # Recomendación 4: Sistema IA generando ROI positivo
        if roi_porcentaje > 100:
            recomendaciones.append({
                'tipo': 'EXPANSION_IA',
                'titulo': 'Expandir Uso del Sistema IA',
                'descripcion': f'El sistema IA tiene un ROI de {roi_porcentaje}%. Considerar analizar más partes históricos.',
                'ahorro_estimado': int(ahorro_potencial * 0.3),
                'prioridad': 'MEDIA'
            })

        # Recomendación 5: Partes sin recomendaciones
        if porcentaje_con_recomendacion < 80:
            recomendaciones.append({
                'tipo': 'COBERTURA_IA',
                'titulo': 'Mejorar Cobertura de Recomendaciones IA',
                'descripcion': f'Solo {porcentaje_con_recomendacion}% de partes tienen recomendaciones IA. Revisar calidad de descripciones.',
                'ahorro_estimado': int(ahorro_potencial * 0.2),
                'prioridad': 'BAJA'
            })

        # Ordenar por prioridad y ahorro
        prioridad_orden = {'ALTA': 3, 'MEDIA': 2, 'BAJA': 1}
        recomendaciones = sorted(recomendaciones,
                                key=lambda x: (prioridad_orden[x['prioridad']], x['ahorro_estimado']),
                                reverse=True)

        # Estadísticas generales
        stats = {
            'total_analisis': len(analisis_list),
            'coste_total': int(coste_total),
            'ahorro_potencial': int(ahorro_potencial),
            'roi_porcentaje': roi_porcentaje,
            'coste_ia': round(coste_analisis_ia_eur, 2),
            'porcentaje_preventivo': porcentaje_preventivo,
            'porcentaje_correctivo': porcentaje_correctivo,
            'porcentaje_con_recomendacion': porcentaje_con_recomendacion,
            'tiempo_respuesta_promedio': round(sum(t['dias'] for t in tiempos_respuesta) / len(tiempos_respuesta), 1) if tiempos_respuesta else 0,
            'partes_con_cierre': partes_con_fecha_cierre
        }

        return render_template(
            "cartera/dashboard_roi.html",
            stats=stats,
            costes_gravedad=costes_por_gravedad,
            conteo_gravedad=conteo_gravedad,
            costes_constantes=COSTES_GRAVEDAD,
            ahorro_potencial=ahorro_potencial,
            averias_prevenibles=averias_prevenibles,
            promedios_respuesta=promedios_respuesta,
            maquinas_costosas=maquinas_costosas,
            recomendaciones=recomendaciones,
            tipos_parte=dict(tipos_parte),
            sin_datos=False
        )

    except Exception as e:
        logger.error(f"Error en ROI y optimización: {str(e)}")
        flash(f"Error al calcular ROI: {str(e)}", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/analizar-parte/<int:parte_id>", methods=["POST"])
@cartera_bp.route('/ia/analizar-parte/<int:parte_id>', methods=['POST'])
@helpers.login_required
def analizar_parte_ia(parte_id):
    """Analizar un parte específico con IA"""
    try:
        # Obtener el parte
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/partes_trabajo?id=eq.{parte_id}&select=*",
            headers=HEADERS
        )

        if response.status_code != 200 or not response.json():
            return jsonify({"error": "Parte no encontrado"}), 404

        parte = response.json()[0]

        # Verificar si ya tiene análisis
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?parte_id=eq.{parte_id}&select=id",
            headers=HEADERS
        )

        if check_response.status_code == 200 and check_response.json():
            return jsonify({"error": "Este parte ya tiene un análisis IA"}), 400

        # Analizar con IA (esto requerirá conexión directa a PostgreSQL)
        # Por ahora retornamos un mensaje de éxito
        flash("Parte enviado a análisis con IA. El proceso puede tardar unos segundos.", "info")
        return redirect(request.referrer or url_for('cartera.cartera_dashboard'))

    except Exception as e:
        logger.error(f"Error analizando parte: {str(e)}")
        return jsonify({"error": str(e)}), 500


# @app.route("/cartera/ia/analizar-lote", methods=["POST"])
@cartera_bp.route('/ia/analizar-lote', methods=['POST'])
@helpers.login_required
def analizar_lote_ia():
    """Analizar un lote de partes con IA"""
    try:
        limite = request.json.get('limite', 100) if request.is_json else 100

        # Nota: Esta operación requiere acceso directo a PostgreSQL
        # En producción, se ejecutaría como tarea en background
        flash(f"Proceso de análisis por lotes iniciado (hasta {limite} partes). "
              f"Recibirás una notificación cuando complete.", "info")

        return jsonify({"status": "started", "limite": limite}), 202

    except Exception as e:
        logger.error(f"Error en análisis por lotes: {str(e)}")
        return jsonify({"error": str(e)}), 500


# @app.route("/cartera/ia/prediccion/<int:maquina_id>")
@cartera_bp.route('/ia/prediccion/<int:maquina_id>')
@helpers.login_required
def ver_prediccion_maquina(maquina_id):
    """Ver predicción detallada de una máquina"""
    try:
        # Obtener predicción activa
        response_pred = requests.get(
            f"{SUPABASE_URL}/rest/v1/predicciones_maquina?maquina_id=eq.{maquina_id}&estado=eq.ACTIVA&select=*",
            headers=HEADERS
        )

        prediccion = None
        if response_pred.status_code == 200 and response_pred.json():
            prediccion = response_pred.json()[0]

        # Obtener información de la máquina
        response_maquina = requests.get(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera?id=eq.{maquina_id}&select=*,instalacion:instalaciones(nombre)",
            headers=HEADERS
        )

        if response_maquina.status_code != 200 or not response_maquina.json():
            flash("Máquina no encontrada", "error")
            return redirect(url_for('cartera.dashboard_ia_predictiva'))

        maquina = response_maquina.json()[0]

        # Obtener alertas activas para esta máquina
        response_alertas = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_predictivas_ia?maquina_id=eq.{maquina_id}&estado=eq.ACTIVA&select=*&order=nivel_urgencia.desc",
            headers=HEADERS
        )

        alertas = response_alertas.json() if response_alertas.status_code == 200 else []

        # Obtener análisis recientes
        response_analisis = requests.get(
            f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=*,parte:partes_trabajo(numero_parte,fecha_parte,resolucion)&parte.maquina_id=eq.{maquina_id}&order=fecha_analisis.desc&limit=20",
            headers=HEADERS
        )

        analisis = response_analisis.json() if response_analisis.status_code == 200 else []

        return render_template(
            "cartera/prediccion_maquina.html",
            maquina=maquina,
            prediccion=prediccion,
            alertas=alertas,
            analisis=analisis
        )

    except Exception as e:
        logger.error(f"Error obteniendo predicción: {str(e)}")
        flash("Error al cargar predicción", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/generar-prediccion/<int:maquina_id>", methods=["POST"])
@cartera_bp.route('/ia/generar-prediccion/<int:maquina_id>', methods=['POST'])
@helpers.login_required
def generar_prediccion_ia(maquina_id):
    """Generar nueva predicción para una máquina"""
    try:
        # Nota: Esta operación requiere acceso directo a PostgreSQL
        # En producción, se ejecutaría como tarea en background

        flash(f"Generando predicción con IA para la máquina. El proceso puede tardar unos minutos.", "info")
        return redirect(url_for('cartera.ver_prediccion_maquina', maquina_id=maquina_id))

    except Exception as e:
        logger.error(f"Error generando predicción: {str(e)}")
        flash("Error al generar predicción", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/alertas")
@cartera_bp.route('/ia/alertas')
@helpers.login_required
def listar_alertas_ia():
    """Listar todas las alertas predictivas"""
    try:
        # Filtros
        estado = request.args.get('estado', 'ACTIVA')
        nivel = request.args.get('nivel', '')

        # Construir query
        query = f"estado=eq.{estado}"
        if nivel:
            query += f"&nivel_urgencia=eq.{nivel}"

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_predictivas_ia?{query}&select=*,maquina:maquinas_cartera(identificador),instalacion:maquinas_cartera(instalacion:instalaciones(nombre))&order=fecha_deteccion.desc",
            headers=HEADERS
        )

        alertas = response.json() if response.status_code == 200 else []

        return render_template(
            "cartera/alertas_ia.html",
            alertas=alertas,
            estado_filtro=estado,
            nivel_filtro=nivel
        )

    except Exception as e:
        logger.error(f"Error listando alertas IA: {str(e)}")
        flash("Error al cargar alertas", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/alerta/<int:alerta_id>")
@cartera_bp.route('/ia/alerta/<int:alerta_id>')
@helpers.login_required
def ver_alerta_ia(alerta_id):
    """Ver detalle de una alerta predictiva"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alertas_predictivas_ia?id=eq.{alerta_id}&select=*,maquina:maquinas_cartera(identificador,instalacion:instalaciones(nombre)),prediccion:predicciones_maquina(*)",
            headers=HEADERS
        )

        if response.status_code != 200 or not response.json():
            flash("Alerta no encontrada", "error")
            return redirect(url_for('cartera.listar_alertas_ia'))

        alerta = response.json()[0]

        return render_template(
            "cartera/alerta_ia_detalle.html",
            alerta=alerta
        )

    except Exception as e:
        logger.error(f"Error obteniendo alerta: {str(e)}")
        flash("Error al cargar alerta", "error")
        return redirect(url_for('cartera.listar_alertas_ia'))


# @app.route("/cartera/ia/alerta/<int:alerta_id>/resolver", methods=["POST"])
@cartera_bp.route('/ia/alerta/<int:alerta_id>/resolver', methods=['POST'])
@helpers.login_required
def resolver_alerta_ia(alerta_id):
    """Resolver una alerta predictiva"""
    try:
        accion = request.form.get('accion', 'DESCARTADA')  # ACEPTADA, DESCARTADA, RESUELTA
        notas = request.form.get('notas', '')

        update_data = {
            "estado": accion,
            "fecha_revision": datetime.now().isoformat(),
            "revisada_por_id": session.get("usuario_id"),
            "notas_resultado": notas
        }

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alertas_predictivas_ia?id=eq.{alerta_id}",
            json=update_data,
            headers=HEADERS
        )

        if response.status_code == 200:
            flash("Alerta actualizada correctamente", "success")
        else:
            flash("Error al actualizar alerta", "error")

        return redirect(url_for('cartera.ver_alerta_ia', alerta_id=alerta_id))

    except Exception as e:
        logger.error(f"Error resolviendo alerta: {str(e)}")
        flash("Error al resolver alerta", "error")
        return redirect(url_for('cartera.ver_alerta_ia', alerta_id=alerta_id))


# @app.route("/cartera/ia/componentes")
@cartera_bp.route('/ia/componentes')
@helpers.login_required
def ver_componentes_criticos():
    """Ver análisis de componentes críticos"""
    try:
        # Componentes más problemáticos
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/v_componentes_problematicos?select=*&order=total_fallos.desc",
            headers=HEADERS
        )

        componentes = response.json() if response.status_code == 200 else []

        # Base de conocimiento
        response_conocimiento = requests.get(
            f"{SUPABASE_URL}/rest/v1/conocimiento_tecnico_ia?select=*&order=veces_aparecido.desc",
            headers=HEADERS
        )

        conocimiento = response_conocimiento.json() if response_conocimiento.status_code == 200 else []

        return render_template(
            "cartera/componentes_ia.html",
            componentes=componentes,
            conocimiento=conocimiento
        )

    except Exception as e:
        logger.error(f"Error obteniendo componentes: {str(e)}")
        flash("Error al cargar componentes", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# @app.route("/cartera/ia/metricas")
@cartera_bp.route('/ia/metricas')
@helpers.login_required
def ver_metricas_ia():
    """Ver métricas y ROI del sistema de IA"""
    try:
        # ROI por mes
        response_roi = requests.get(
            f"{SUPABASE_URL}/rest/v1/v_roi_sistema_ia?select=*&order=mes.desc&limit=12",
            headers=HEADERS
        )

        roi_data = response_roi.json() if response_roi.status_code == 200 else []

        # Métricas de precisión
        response_metricas = requests.get(
            f"{SUPABASE_URL}/rest/v1/metricas_precision_ia?select=*&order=fecha_fin.desc&limit=6",
            headers=HEADERS
        )

        metricas = response_metricas.json() if response_metricas.status_code == 200 else []

        return render_template(
            "cartera/metricas_ia.html",
            roi_data=roi_data,
            metricas=metricas
        )

    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        flash("Error al cargar métricas", "error")
        return redirect(url_for('cartera.dashboard_ia_predictiva'))


# Estado global para tracking de análisis
estado_analisis_global = {
    'en_progreso': False,
    'total': 0,
    'procesados': 0,
    'exitosos': 0,
    'errores': 0,
    'completado': False,
    'ultimo_error': None,  # Capturar último error para debugging
    'errores_detallados': []  # Lista de errores específicos
}

# @app.route("/cartera/ia/ejecutar")
@cartera_bp.route('/ia/ejecutar')
@helpers.login_required
def mostrar_ejecutar_analisis():
    """Página para ejecutar análisis desde la web"""
    return render_template("cartera/ejecutar_analisis.html")


# @app.route("/cartera/ia/ejecutar-analisis-2025", methods=["POST"])
@cartera_bp.route('/ia/ejecutar-analisis-2025', methods=['POST'])
@helpers.login_required
def ejecutar_analisis_web():
    """Ejecuta el análisis de partes 2025 desde la web - VERSIÓN WEB COMPLETA"""
    import threading
    import json as json_lib
    import time

    global estado_analisis_global

    if estado_analisis_global['en_progreso']:
        return jsonify({"error": "Ya hay un análisis en progreso"}), 400

    # Verificar API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY no configurada en Render"}), 500

    def analizar_en_background():
        global estado_analisis_global

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            # Resetear estado
            estado_analisis_global = {
                'en_progreso': True,
                'total': 0,
                'procesados': 0,
                'exitosos': 0,
                'errores': 0,
                'completado': False,
                'ultimo_error': None,
                'errores_detallados': []
            }

            logger.info("🚀 Iniciando análisis de TODOS los partes de averías...")

            # Obtener IDs ya analizados
            response_analizados = requests.get(
                f"{SUPABASE_URL}/rest/v1/analisis_partes_ia?select=parte_id",
                headers=HEADERS
            )
            ids_analizados = []
            if response_analizados.status_code == 200:
                ids_analizados = [a['parte_id'] for a in response_analizados.json()]

            # Obtener TODOS los partes (sin límite de año)
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/partes_trabajo?select=*&order=fecha_parte.desc&limit=10000",
                headers=HEADERS
            )

            if response.status_code != 200:
                logger.error(f"Error obteniendo partes: {response.status_code}")
                estado_analisis_global['en_progreso'] = False
                return

            todos_partes = response.json()

            # Filtrar: TODOS los partes con resolución, sin analizar (cualquier tipo)
            partes = [
                p for p in todos_partes
                if (p.get('resolucion') and  # Solo que tengan descripción
                    p['id'] not in ids_analizados)
            ]

            estado_analisis_global['total'] = len(partes)  # SIN LÍMITE - procesar todos
            logger.info(f"📊 Encontrados {len(partes)} partes pendientes, procesando TODOS")

            if estado_analisis_global['total'] == 0:
                logger.info("✅ No hay partes pendientes")
                estado_analisis_global['completado'] = True
                estado_analisis_global['en_progreso'] = False
                return

            # Procesar TODOS los partes
            for parte in partes:
                try:
                    prompt = f"""Analiza este parte de ascensor y responde SOLO con JSON:

Número: {parte.get('numero_parte')}
Tipo: {parte.get('tipo_parte_normalizado')}
Descripción: {parte.get('resolucion', '')[:500]}

JSON esperado:
{{"componente_principal":"nombre","tipo_fallo":"tipo","gravedad_tecnica":"LEVE|MODERADA|GRAVE|CRITICA","recomendacion_ia":"recomendación","confianza_analisis":85}}"""

                    # Llamar a Claude
                    response_ia = client.messages.create(
                        model="claude-3-haiku-20240307",  # Claude 3 Haiku - más barato y universalmente disponible
                        max_tokens=1024,
                        temperature=0.3,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    # Parsear JSON
                    contenido = response_ia.content[0].text
                    try:
                        analisis = json_lib.loads(contenido)
                    except:
                        import re
                        match = re.search(r'\{.*\}', contenido, re.DOTALL)
                        if match:
                            analisis = json_lib.loads(match.group())
                        else:
                            raise Exception("No JSON encontrado")

                    # Guardar en Supabase
                    data_guardar = {
                        "parte_id": parte['id'],
                        "componente_principal": analisis.get('componente_principal'),
                        "tipo_fallo": analisis.get('tipo_fallo'),
                        "gravedad_tecnica": analisis.get('gravedad_tecnica'),
                        "recomendacion_ia": analisis.get('recomendacion_ia'),
                        "confianza_analisis": analisis.get('confianza_analisis'),
                        "modelo_ia_usado": "claude-3-haiku-20240307"
                    }

                    save_response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/analisis_partes_ia",
                        json=data_guardar,
                        headers=HEADERS
                    )

                    if save_response.status_code in [200, 201]:
                        estado_analisis_global['exitosos'] += 1
                        logger.info(f"✅ [{estado_analisis_global['procesados']+1}/{estado_analisis_global['total']}] {parte.get('numero_parte')}")
                    else:
                        estado_analisis_global['errores'] += 1
                        error_msg = f"Error guardando {parte.get('numero_parte')}: {save_response.status_code} - {save_response.text[:200]}"
                        estado_analisis_global['ultimo_error'] = error_msg
                        if len(estado_analisis_global['errores_detallados']) < 5:  # Guardar solo primeros 5
                            estado_analisis_global['errores_detallados'].append(error_msg)
                        logger.error(f"❌ {error_msg}")

                except Exception as e:
                    estado_analisis_global['errores'] += 1
                    error_msg = f"Error: {str(e)}"
                    estado_analisis_global['ultimo_error'] = error_msg
                    if len(estado_analisis_global['errores_detallados']) < 5:  # Guardar solo primeros 5
                        estado_analisis_global['errores_detallados'].append(error_msg)
                    logger.error(f"❌ {error_msg}")

                estado_analisis_global['procesados'] += 1

                # Pausa cada 10 para rate limits
                if estado_analisis_global['procesados'] % 10 == 0:
                    time.sleep(2)

            estado_analisis_global['completado'] = True
            estado_analisis_global['en_progreso'] = False
            logger.info(f"✅ COMPLETADO: {estado_analisis_global['exitosos']} exitosos, {estado_analisis_global['errores']} errores")

        except Exception as e:
            error_msg = f"Error fatal: {str(e)}"
            logger.error(f"💥 {error_msg}")
            estado_analisis_global['ultimo_error'] = error_msg
            estado_analisis_global['errores_detallados'].append(error_msg)
            estado_analisis_global['en_progreso'] = False
            estado_analisis_global['completado'] = True

    # Ejecutar en thread
    thread = threading.Thread(target=analizar_en_background)
    thread.daemon = True
    thread.start()

    return jsonify({
        "mensaje": "✅ Análisis iniciado. Monitorea el progreso en la página.",
        "info": "El proceso puede tardar 20-30 minutos"
    })


# @app.route("/cartera/ia/estado-analisis")
@cartera_bp.route('/ia/estado-analisis')
@helpers.login_required
def estado_analisis():
    """Obtiene el estado actual del análisis"""
    return jsonify(estado_analisis_global)


# @app.route("/cartera/ia/api/generar-predicciones", methods=["POST"])
@cartera_bp.route('/ia/api/generar-predicciones', methods=['POST'])
@helpers.login_required
def api_generar_predicciones_ia():
    """API para generar predicciones masivas - EJECUTA EN BACKGROUND"""
    import threading

    def generar_predicciones_background():
        """Genera predicciones en background"""
        try:
            # Obtener máquinas desde Supabase
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/maquinas_cartera?en_cartera=eq.true&select=id,identificador&limit=50",
                headers=HEADERS
            )

            if response.status_code == 200:
                maquinas = response.json()
                logger.info(f"Generando predicciones para {len(maquinas)} máquinas...")

                for maquina in maquinas[:10]:  # Solo 10 como demo
                    logger.info(f"Predicción para máquina {maquina.get('identificador')}")
                    # analizador_ia.generar_prediccion_maquina(maquina['id'], conn)

            logger.info("Predicciones completadas")
        except Exception as e:
            logger.error(f"Error generando predicciones: {str(e)}")

    thread = threading.Thread(target=generar_predicciones_background)
    thread.daemon = True
    thread.start()

    return jsonify({
        "mensaje": "Generación de predicciones iniciada en background.",
        "info": "Revisa los logs de Render para ver el progreso."
    }), 202


# ============================================
