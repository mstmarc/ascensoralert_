"""
Blueprint para gestión de Inspecciones e IPOs

Este módulo incluye:
- Dashboard con alertas y categorización de inspecciones
- Creación y edición de inspecciones
- Gestión de actas y presupuestos (PDFs)
- Extracción de defectos desde PDFs
- Marcado de segunda inspección realizada
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
import requests
import helpers
from config import config
from datetime import datetime, date
from utils.formatters import limpiar_none
from utils.messages import flash_success, flash_error
import os

# Crear Blueprint con prefijo /inspecciones
inspecciones_bp = Blueprint('inspecciones', __name__, url_prefix='/inspecciones')

# Constantes de configuración
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS
SUPABASE_KEY = config.SUPABASE_KEY

# Storage key para Supabase Storage
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
STORAGE_KEY = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_KEY
STORAGE_HEADERS = {
    "apikey": STORAGE_KEY,
    "Authorization": f"Bearer {STORAGE_KEY}",
}


# ============================================
# DASHBOARD DE INSPECCIONES
# ============================================

@inspecciones_bp.route('')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def dashboard():
    """Dashboard principal de inspecciones con alertas y estados"""

    # Obtener todas las inspecciones con información del OCA
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?select=*,oca:ocas(nombre)&order=fecha_inspeccion.desc",
        headers=HEADERS
    )

    inspecciones = []
    if response.status_code == 200:
        inspecciones = response.json()

    # Calcular alertas y estadísticas basadas en inspecciones
    hoy = date.today()
    alertas_criticas = []
    alertas_urgentes = []
    alertas_proximas = []
    alertas_normales = []  # Inspecciones sin urgencia

    # Procesar inspecciones - categorizar según urgencia de segunda inspección
    for inspeccion in inspecciones:
        # Categorizar según urgencia para solucionar defectos antes de la fecha límite
        if inspeccion.get('fecha_segunda_realizada'):
            inspeccion['categoria_segunda'] = 'realizadas'
            alertas_normales.append(('defectos', inspeccion))
        elif inspeccion.get('fecha_segunda_inspeccion'):
            try:
                fecha_limite = datetime.strptime(inspeccion['fecha_segunda_inspeccion'].split('T')[0], '%Y-%m-%d').date()
                dias_restantes = (fecha_limite - hoy).days
                inspeccion['dias_hasta_segunda'] = dias_restantes

                if fecha_limite < hoy:
                    inspeccion['categoria_segunda'] = 'vencidas'
                    alertas_criticas.append(('defectos', inspeccion))
                elif dias_restantes <= 30:
                    inspeccion['categoria_segunda'] = 'este-mes'
                    alertas_urgentes.append(('defectos', inspeccion))
                elif dias_restantes <= 60:
                    inspeccion['categoria_segunda'] = 'proximo-mes'
                    alertas_proximas.append(('defectos', inspeccion))
                else:
                    inspeccion['categoria_segunda'] = 'pendiente'
                    alertas_normales.append(('defectos', inspeccion))
            except:
                inspeccion['categoria_segunda'] = 'sin-fecha'
                alertas_normales.append(('defectos', inspeccion))
        else:
            inspeccion['categoria_segunda'] = 'sin-fecha'
            alertas_normales.append(('defectos', inspeccion))

    # Ordenar alertas críticas: más antiguas primero
    alertas_criticas.sort(key=lambda x: x[1].get('dias_hasta_segunda', 0))

    # Obtener lista de OCAs para filtros
    response_ocas = requests.get(
        f"{SUPABASE_URL}/rest/v1/ocas?select=id,nombre&activo=eq.true&order=nombre.asc",
        headers=HEADERS
    )
    ocas = []
    if response_ocas.status_code == 200:
        ocas = response_ocas.json()

    # Obtener defectos de todas las inspecciones para contar pendientes por plazo
    response_defectos = requests.get(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?select=inspeccion_id,estado,plazo_meses",
        headers=HEADERS
    )

    defectos_por_inspeccion = {}
    if response_defectos.status_code == 200:
        defectos = response_defectos.json()
        for defecto in defectos:
            insp_id = defecto.get('inspeccion_id')
            if insp_id not in defectos_por_inspeccion:
                defectos_por_inspeccion[insp_id] = {
                    'total': 0,
                    'pendientes': 0,
                    'plazo_6_pendientes': 0,
                    'plazo_12_pendientes': 0
                }

            defectos_por_inspeccion[insp_id]['total'] += 1

            if defecto.get('estado') == 'PENDIENTE':
                defectos_por_inspeccion[insp_id]['pendientes'] += 1
                plazo = defecto.get('plazo_meses')
                if plazo == 6:
                    defectos_por_inspeccion[insp_id]['plazo_6_pendientes'] += 1
                elif plazo == 12:
                    defectos_por_inspeccion[insp_id]['plazo_12_pendientes'] += 1

    # Agregar contador de defectos a cada inspección
    for inspeccion in inspecciones:
        insp_id = inspeccion.get('id')
        if insp_id in defectos_por_inspeccion:
            inspeccion['defectos_total'] = defectos_por_inspeccion[insp_id]['total']
            inspeccion['defectos_pendientes'] = defectos_por_inspeccion[insp_id]['pendientes']
            inspeccion['defectos_plazo_6'] = defectos_por_inspeccion[insp_id]['plazo_6_pendientes']
            inspeccion['defectos_plazo_12'] = defectos_por_inspeccion[insp_id]['plazo_12_pendientes']
        else:
            inspeccion['defectos_total'] = 0
            inspeccion['defectos_pendientes'] = 0
            inspeccion['defectos_plazo_6'] = 0
            inspeccion['defectos_plazo_12'] = 0

    return render_template(
        "inspecciones_dashboard.html",
        inspecciones=inspecciones,
        alertas_criticas=alertas_criticas,
        alertas_urgentes=alertas_urgentes,
        alertas_proximas=alertas_proximas,
        alertas_normales=alertas_normales,
        ocas=ocas
    )


# ============================================
# NUEVA INSPECCIÓN
# ============================================

@inspecciones_bp.route('/nueva', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def nueva():
    """Crear nueva inspección"""

    if request.method == "POST":
        oca_id = request.form.get("oca_id")
        if oca_id:
            try:
                oca_id = int(oca_id)
            except ValueError:
                oca_id = None

        data = {
            "oca_id": oca_id,
            "direccion": request.form.get("direccion"),
            "localidad": request.form.get("localidad"),
            "numero_ascensores": request.form.get("numero_ascensores") or None,
            "fecha_inspeccion": request.form.get("fecha_inspeccion"),
            "fecha_segunda_inspeccion": request.form.get("fecha_segunda_inspeccion") or None,
            "observaciones": request.form.get("observaciones") or None,
            "estado_presupuesto": "PENDIENTE"
        }

        if not data["direccion"] or not data["localidad"] or not data["fecha_inspeccion"]:
            flash_error("Dirección, Localidad y Fecha de Inspección son obligatorios")
            return redirect(request.referrer)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/inspecciones?select=id",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 201]:
            inspeccion_id = response.json()[0]["id"]
            flash_success("Inspección creada correctamente")
            return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))
        else:
            flash_error(f"Error al crear inspección: {response.text}")
            return redirect(request.referrer)

    # GET - Obtener lista de OCAs activos
    response_ocas = requests.get(
        f"{SUPABASE_URL}/rest/v1/ocas?select=id,nombre&activo=eq.true&order=nombre.asc",
        headers=HEADERS
    )
    ocas = []
    if response_ocas.status_code == 200:
        ocas = response.json()

    fecha_hoy = date.today().strftime('%Y-%m-%d')

    return render_template("nueva_inspeccion.html", ocas=ocas, fecha_hoy=fecha_hoy)


# ============================================
# VER INSPECCIÓN
# ============================================

@inspecciones_bp.route('/ver/<int:inspeccion_id>')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def ver(inspeccion_id):
    """Ver detalles de una inspección con sus defectos"""

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}&select=*,oca:ocas(nombre)",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        return f"<h3 style='color:red;'>Error al obtener inspección</h3><pre>{response.text}</pre><a href='{url_for('inspecciones.dashboard')}'>Volver</a>"

    inspeccion = response.json()[0]
    inspeccion = limpiar_none(inspeccion)

    # Obtener defectos de esta inspección
    defectos_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?inspeccion_id=eq.{inspeccion_id}&order=created_at.desc",
        headers=HEADERS
    )
    defectos = []
    if defectos_response.status_code == 200:
        defectos = defectos_response.json()

    return render_template("ver_inspeccion.html", inspeccion=inspeccion, defectos=defectos)


# ============================================
# EDITAR INSPECCIÓN
# ============================================

@inspecciones_bp.route('/editar/<int:inspeccion_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def editar(inspeccion_id):
    """Editar datos de una inspección"""

    if request.method == "POST":
        oca_id = request.form.get("oca_id")
        if oca_id:
            try:
                oca_id = int(oca_id)
            except ValueError:
                oca_id = None

        data = {
            "oca_id": oca_id,
            "direccion": request.form.get("direccion"),
            "localidad": request.form.get("localidad"),
            "numero_ascensores": request.form.get("numero_ascensores") or None,
            "fecha_inspeccion": request.form.get("fecha_inspeccion"),
            "fecha_segunda_inspeccion": request.form.get("fecha_segunda_inspeccion") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        if not data["direccion"] or not data["localidad"] or not data["fecha_inspeccion"]:
            flash_error("Dirección, Localidad y Fecha de Inspección son obligatorios")
            return redirect(request.referrer)

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 204]:
            flash_success("Inspección actualizada correctamente")
            return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))
        else:
            flash_error(f"Error al actualizar inspección: {response.text}")
            return redirect(request.referrer)

    # GET - Obtener datos de la inspección
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
        headers=HEADERS
    )

    if response.status_code == 200 and response.json():
        inspeccion = response.json()[0]
        inspeccion = limpiar_none(inspeccion)
    else:
        return f"<h3 style='color:red;'>Error al obtener inspección</h3><a href='{url_for('inspecciones.dashboard')}'>Volver</a>"

    # Obtener lista de OCAs activos
    response_ocas = requests.get(
        f"{SUPABASE_URL}/rest/v1/ocas?select=id,nombre&activo=eq.true&order=nombre.asc",
        headers=HEADERS
    )
    ocas = []
    if response_ocas.status_code == 200:
        ocas = response_ocas.json()

    return render_template("editar_inspeccion.html", inspeccion=inspeccion, ocas=ocas)


# ============================================
# ELIMINAR INSPECCIÓN
# ============================================

@inspecciones_bp.route('/eliminar/<int:inspeccion_id>')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'delete')
def eliminar(inspeccion_id):
    """Eliminar inspección y sus defectos asociados"""

    # Eliminar defectos asociados primero
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?inspeccion_id=eq.{inspeccion_id}",
        headers=HEADERS
    )

    # Eliminar la inspección
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success("Inspección eliminada correctamente")
        return redirect(url_for('inspecciones.dashboard'))
    else:
        flash_error(f"Error al eliminar inspección: {response.text}")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# CAMBIAR ESTADO DE PRESUPUESTO
# ============================================

@inspecciones_bp.route('/estado_presupuesto/<int:inspeccion_id>', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def cambiar_estado_presupuesto(inspeccion_id):
    """Cambiar el estado del presupuesto de la inspección"""

    nuevo_estado = request.form.get("estado_presupuesto")

    if nuevo_estado not in ["PENDIENTE", "ENVIADO", "ACEPTADO", "RECHAZADO"]:
        flash_error("Estado de presupuesto inválido")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    data = {"estado_presupuesto": nuevo_estado}

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success(f"Estado del presupuesto cambiado a: {nuevo_estado}")
    else:
        flash_error(f"Error al cambiar estado: {response.text}")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# MARCAR SEGUNDA INSPECCIÓN REALIZADA
# ============================================

@inspecciones_bp.route('/marcar_segunda_realizada/<int:inspeccion_id>', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def marcar_segunda_realizada(inspeccion_id):
    """Marcar que la segunda inspección ha sido realizada"""

    fecha_realizada = request.form.get("fecha_segunda_realizada")

    if not fecha_realizada:
        flash_error("Debe especificar la fecha de realización")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    data = {"fecha_segunda_realizada": fecha_realizada}

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success("Segunda inspección marcada como realizada")
    else:
        flash_error(f"Error al marcar segunda inspección: {response.text}")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# SUBIR ACTA PDF
# ============================================

@inspecciones_bp.route('/<int:inspeccion_id>/subir_acta', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def subir_acta_pdf(inspeccion_id):
    """Subir PDF del acta de inspección a Supabase Storage"""

    if 'acta_pdf' not in request.files:
        flash_error("No se seleccionó ningún archivo")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    file = request.files['acta_pdf']

    if file.filename == '':
        flash_error("No se seleccionó ningún archivo")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    # Validar que sea PDF
    if not file.filename.lower().endswith('.pdf'):
        flash_error("Solo se permiten archivos PDF")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    try:
        # Generar nombre de archivo único
        file_name = f"inspeccion_{inspeccion_id}_acta.pdf"
        file_path = f"inspecciones/{file_name}"

        # Leer contenido del archivo
        file_content = file.read()

        # Headers para operaciones de storage con Content-Type
        storage_headers = {
            **STORAGE_HEADERS,
            "Content-Type": "application/pdf",
        }

        # Primero intentar eliminar el archivo existente (si existe)
        requests.delete(
            f"{SUPABASE_URL}/storage/v1/object/inspecciones-pdfs/{file_path}",
            headers=storage_headers
        )

        # Subir nuevo archivo
        upload_response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/inspecciones-pdfs/{file_path}",
            data=file_content,
            headers=storage_headers
        )

        if upload_response.status_code not in [200, 201]:
            flash_error(f"Error al subir archivo: {upload_response.text}")
            return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

        # Obtener URL pública del archivo
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/inspecciones-pdfs/{file_path}"

        # Actualizar base de datos con la URL
        data = {"acta_pdf_url": public_url}

        db_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
            json=data,
            headers=HEADERS
        )

        if db_response.status_code in [200, 204]:
            flash_success("Acta PDF subida correctamente")
        else:
            flash_error(f"Archivo subido pero error al guardar en base de datos: {db_response.text}")

    except Exception as e:
        flash_error(f"Error al procesar archivo: {str(e)}")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# SUBIR PRESUPUESTO PDF
# ============================================

@inspecciones_bp.route('/<int:inspeccion_id>/subir_presupuesto', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def subir_presupuesto_pdf(inspeccion_id):
    """Subir PDF del presupuesto de inspección a Supabase Storage"""

    if 'presupuesto_pdf' not in request.files:
        flash_error("No se seleccionó ningún archivo")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    file = request.files['presupuesto_pdf']

    if file.filename == '':
        flash_error("No se seleccionó ningún archivo")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    # Validar que sea PDF
    if not file.filename.lower().endswith('.pdf'):
        flash_error("Solo se permiten archivos PDF")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    try:
        # Generar nombre de archivo único
        file_name = f"inspeccion_{inspeccion_id}_presupuesto.pdf"
        file_path = f"inspecciones/{file_name}"

        # Leer contenido del archivo
        file_content = file.read()

        # Headers para operaciones de storage con Content-Type
        storage_headers = {
            **STORAGE_HEADERS,
            "Content-Type": "application/pdf",
        }

        # Primero intentar eliminar el archivo existente (si existe)
        requests.delete(
            f"{SUPABASE_URL}/storage/v1/object/inspecciones-pdfs/{file_path}",
            headers=storage_headers
        )

        # Subir nuevo archivo
        upload_response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/inspecciones-pdfs/{file_path}",
            data=file_content,
            headers=storage_headers
        )

        if upload_response.status_code not in [200, 201]:
            flash_error(f"Error al subir archivo: {upload_response.text}")
            return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

        # Obtener URL pública del archivo
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/inspecciones-pdfs/{file_path}"

        # Actualizar base de datos con la URL
        data = {"presupuesto_pdf_url": public_url}

        db_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
            json=data,
            headers=HEADERS
        )

        if db_response.status_code in [200, 204]:
            flash_success("Presupuesto PDF subido correctamente")
        else:
            flash_error(f"Archivo subido pero error al guardar en base de datos: {db_response.text}")

    except Exception as e:
        flash_error(f"Error al procesar archivo: {str(e)}")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# EXTRAER DEFECTOS DESDE PDF
# ============================================

@inspecciones_bp.route('/<int:inspeccion_id>/extraer_defectos_pdf', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def extraer_defectos_pdf(inspeccion_id):
    """Extraer defectos desde PDF del acta usando IA"""

    # Obtener inspección para verificar que existe acta PDF
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash_error("Inspección no encontrada")
        return redirect(url_for('inspecciones.dashboard'))

    inspeccion = response.json()[0]
    acta_pdf_url = inspeccion.get('acta_pdf_url')

    if not acta_pdf_url:
        flash_error("Primero debe subir el PDF del acta de inspección")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    # Aquí iría la lógica de extracción con IA
    # Por ahora solo mostramos mensaje
    flash_success("Función de extracción de defectos en desarrollo")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))


# ============================================
# GUARDAR DEFECTOS IMPORTADOS
# ============================================

@inspecciones_bp.route('/<int:inspeccion_id>/guardar_defectos_importados', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def guardar_defectos_importados(inspeccion_id):
    """Guardar defectos que fueron importados desde PDF"""

    # Obtener JSON de defectos importados
    defectos_json = request.form.get('defectos_json')

    if not defectos_json:
        flash_error("No hay defectos para importar")
        return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))

    try:
        import json
        defectos = json.loads(defectos_json)

        # Guardar cada defecto en la base de datos
        for defecto in defectos:
            data = {
                "inspeccion_id": inspeccion_id,
                "descripcion": defecto.get('descripcion', ''),
                "plazo_meses": defecto.get('plazo_meses', 6),
                "estado": "PENDIENTE"
            }

            requests.post(
                f"{SUPABASE_URL}/rest/v1/defectos_inspeccion",
                json=data,
                headers=HEADERS
            )

        flash_success(f"{len(defectos)} defectos importados correctamente")

    except Exception as e:
        flash_error(f"Error al importar defectos: {str(e)}")

    return redirect(url_for('inspecciones.ver', inspeccion_id=inspeccion_id))
