"""
Blueprint de Visitas

Gestión de visitas con funcionalidades de:
- Visitas a administradores de fincas
- Dashboard de visitas a administradores
- CRUD completo de visitas a administradores
- Visitas de seguimiento a clientes
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import date
import requests

import helpers
from config import config
from utils.messages import flash_success, flash_error
from utils.formatters import limpiar_none
from services.cache_service import get_administradores_cached

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint (sin url_prefix para mantener compatibilidad con rutas existentes)
visitas_bp = Blueprint('visitas', __name__)


# ============================================
# VISITAS A ADMINISTRADORES
# ============================================

@visitas_bp.route('/visita_administrador', methods=["GET", "POST"])
def visita_administrador():
    """Crear nueva visita a administrador de fincas"""
    if "usuario" not in session:
        return redirect("/")

    # Puede venir con oportunidad_id desde la vista de oportunidad
    oportunidad_id = request.args.get("oportunidad_id")
    oportunidad_data = None

    if oportunidad_id:
        # Obtener datos de la oportunidad
        oportunidad_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(*)",
            headers=HEADERS
        )
        if oportunidad_response.status_code == 200 and oportunidad_response.json():
            oportunidad_data = oportunidad_response.json()[0]

    if request.method == "POST":
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get('administrador_id')
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        # Validación: fecha y administrador son obligatorios
        if not request.form.get("fecha_visita") or not administrador_id:
            flash_error("Fecha y Administrador son obligatorios")
            return redirect(request.referrer)

        # Buscar el nombre del administrador para el campo administrador_fincas (NOT NULL en BD)
        administrador_nombre = None
        if administrador_id:
            admin_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{administrador_id}&select=nombre_empresa",
                headers=HEADERS
            )
            if admin_response.status_code == 200 and admin_response.json():
                administrador_nombre = admin_response.json()[0].get("nombre_empresa")
            else:
                flash_error(f"No se encontró el administrador seleccionado")
                return redirect(request.referrer)

        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_id": administrador_id,
            "administrador_fincas": administrador_nombre,  # Campo NOT NULL en BD
            "persona_contacto": request.form.get("persona_contacto") or None,
            "observaciones": request.form.get("observaciones") or None,
            "oportunidad_id": int(request.form.get("oportunidad_id")) if request.form.get("oportunidad_id") else None
        }

        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_administradores", json=data, headers=HEADERS)

        if response.status_code in [200, 201]:
            # Si viene de una oportunidad, volver a la oportunidad
            if data["oportunidad_id"]:
                flash_success("Visita a administrador registrada correctamente")
                return redirect(url_for('oportunidades.ver_oportunidad', oportunidad_id=data["oportunidad_id"]))
            else:
                return render_template("visita_admin_success.html")
        else:
            flash_error(f"Error al registrar visita: {response.text}")
            return redirect(request.referrer)

    # GET - Obtener lista de administradores (usando caché)
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    administradores = get_administradores_cached()

    return render_template("visita_administrador.html",
                         fecha_hoy=fecha_hoy,
                         oportunidad=oportunidad_data,
                         administradores=administradores)


@visitas_bp.route('/visitas_administradores_dashboard')
@helpers.login_required
@helpers.requiere_permiso('visitas', 'read')
def visitas_administradores_dashboard():
    """Dashboard de visitas a administradores con paginación"""
    from utils.pagination import get_pagination

    # Usar helper de paginación
    pagination = get_pagination(per_page_default=25)

    # OPTIMIZACIÓN: Para count solo necesitamos id, no todos los campos
    count_url = f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=id"
    count_response = requests.get(count_url, headers={**HEADERS, "Prefer": "count=exact"})
    total_registros = int(count_response.headers.get("Content-Range", "0").split("/")[-1])
    pagination.total = total_registros

    # OPTIMIZACIÓN: Seleccionar campos específicos con JOIN a administradores
    data_url = f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=id,fecha_visita,administrador_id,administradores(nombre_empresa),persona_contacto,observaciones,oportunidad_id&order=fecha_visita.desc&limit={pagination.limit}&offset={pagination.offset}"
    response = requests.get(data_url, headers=HEADERS)

    if response.status_code != 200:
        return f"<h3 style='color:red;'>Error al obtener visitas</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    visitas = response.json()

    return render_template("visitas_admin_dashboard.html",
        visitas=visitas,
        pagination=pagination,
        page=pagination.page,
        total_pages=pagination.total_pages,
        total_registros=pagination.total
    )


@visitas_bp.route('/ver_visita_admin/<int:visita_id>')
def ver_visita_admin(visita_id):
    """Ver detalle de una visita a administrador"""
    if "usuario" not in session:
        return redirect("/")

    # Obtener visita con JOIN a administradores
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}&select=*,administradores(nombre_empresa)",
        headers=HEADERS
    )
    if response.status_code != 200 or not response.json():
        flash_error("Visita no encontrada")
        return redirect(url_for("visitas.visitas_administradores_dashboard"))

    visita = limpiar_none(response.json()[0])
    return render_template("ver_visita_admin.html", visita=visita)


@visitas_bp.route('/editar_visita_admin/<int:visita_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('visitas', 'write')
def editar_visita_admin(visita_id):
    """Editar visita a administrador existente"""

    if request.method == "POST":
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get("administrador_id")
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        # Buscar el nombre del administrador para el campo administrador_fincas (NOT NULL en BD)
        administrador_nombre = None
        if administrador_id:
            admin_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{administrador_id}&select=nombre_empresa",
                headers=HEADERS
            )
            if admin_response.status_code == 200 and admin_response.json():
                administrador_nombre = admin_response.json()[0].get("nombre_empresa")

        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_id": administrador_id,
            "administrador_fincas": administrador_nombre,  # Campo NOT NULL en BD
            "persona_contacto": request.form.get("persona_contacto") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 204]:
            flash_success("Visita actualizada correctamente")
            return redirect(url_for("visitas.visitas_administradores_dashboard"))
        else:
            flash_error("Error al actualizar visita")

    response = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        flash_error("Visita no encontrada")
        return redirect(url_for("visitas.visitas_administradores_dashboard"))

    visita = limpiar_none(response.json()[0])

    # Obtener lista de administradores (usando caché)
    administradores = get_administradores_cached()

    return render_template("editar_visita_admin.html", visita=visita, administradores=administradores)


@visitas_bp.route('/eliminar_visita_admin/<int:visita_id>')
@helpers.login_required
@helpers.requiere_permiso('visitas', 'delete')
def eliminar_visita_admin(visita_id):
    """Eliminar visita a administrador"""

    response = requests.delete(f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}", headers=HEADERS)

    if response.status_code in [200, 204]:
        flash_success("Visita eliminada correctamente")
    else:
        flash_error("Error al eliminar visita")

    return redirect(url_for("visitas.visitas_administradores_dashboard"))


# ============================================
# VISITAS DE SEGUIMIENTO A CLIENTES
# ============================================

@visitas_bp.route('/crear_visita_seguimiento/<int:cliente_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('visitas', 'write')
def crear_visita_seguimiento(cliente_id):
    """Crear visita de seguimiento a cliente"""

    oportunidad_id = request.args.get("oportunidad_id")

    if request.method == "POST":
        data = {
            "cliente_id": cliente_id,
            "oportunidad_id": int(request.form.get("oportunidad_id")) if request.form.get("oportunidad_id") else None,
            "fecha_visita": request.form.get("fecha_visita"),
            "observaciones": request.form.get("observaciones")
        }

        if not data["fecha_visita"]:
            flash_error("La fecha de visita es obligatoria")
            return redirect(request.referrer)

        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_seguimiento", json=data, headers=HEADERS)

        if response.status_code in [200, 201]:
            flash_success("Visita de seguimiento registrada correctamente")
            # Si viene de una oportunidad, volver a la oportunidad
            if data["oportunidad_id"]:
                return redirect(url_for('oportunidades.ver_oportunidad', oportunidad_id=data["oportunidad_id"]))
            else:
                return redirect(url_for("leads.ver", lead_id=cliente_id))
        else:
            flash_error("Error al registrar visita")

    response_cliente = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}", headers=HEADERS)
    response_oportunidades = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?cliente_id=eq.{cliente_id}&estado=neq.ganada&estado=neq.perdida",
        headers=HEADERS
    )

    if response_cliente.status_code != 200 or not response_cliente.json():
        flash_error("Cliente no encontrado")
        return redirect(url_for("leads.dashboard"))

    cliente = response_cliente.json()[0]
    oportunidades = response_oportunidades.json() if response_oportunidades.status_code == 200 else []

    fecha_hoy = date.today().strftime('%Y-%m-%d')

    return render_template("crear_visita_seguimiento.html",
        cliente=cliente,
        oportunidades=oportunidades,
        oportunidad_id_preseleccionada=oportunidad_id,
        fecha_hoy=fecha_hoy
    )
