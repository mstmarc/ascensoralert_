"""
Blueprint de OCAs (Organismos de Control Autorizado)
====================================================
Migración completa del módulo OCAs a Blueprint modular.

RUTAS:
- GET  /ocas                 → Lista de OCAs
- GET  /ocas/nuevo           → Formulario nuevo OCA
- POST /ocas/nuevo           → Crear OCA
- GET  /ocas/editar/<id>     → Formulario editar OCA
- POST /ocas/editar/<id>     → Actualizar OCA
- GET  /ocas/eliminar/<id>   → Eliminar OCA
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests
import helpers
from config import config
from utils.helpers_actions import obtener_conteos_por_tabla
from utils.formatters import limpiar_none
from utils.messages import flash_success, flash_error

# ============================================
# CREAR BLUEPRINT
# ============================================

ocas_bp = Blueprint(
    'ocas',
    __name__,
    url_prefix='/ocas'
)


# ============================================
# RUTAS
# ============================================

@ocas_bp.route('/')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def lista():
    """Listado de todos los OCAs con conteo optimizado de inspecciones"""

    # Obtener OCAs con conteos en una sola query (optimización N+1)
    ocas = obtener_conteos_por_tabla(
        tabla_principal='ocas',
        tabla_relacionada='inspecciones',
        campo_relacion='oca_id',
        filtros_principal='order=nombre.asc'
    )

    # Renombrar el campo para compatibilidad con el template
    for oca in ocas:
        oca['total_inspecciones'] = oca.pop('total_count', 0)

    return render_template("lista_ocas.html", ocas=ocas)


@ocas_bp.route('/nuevo', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def nuevo():
    """Crear un nuevo OCA"""

    if request.method == "POST":
        data = {
            "nombre": request.form.get("nombre"),
            "contacto_nombre": request.form.get("contacto_nombre") or None,
            "contacto_email": request.form.get("contacto_email") or None,
            "contacto_telefono": request.form.get("contacto_telefono") or None,
            "direccion": request.form.get("direccion") or None,
            "observaciones": request.form.get("observaciones") or None,
            "activo": True
        }

        if not data["nombre"]:
            flash_error("El nombre del OCA es obligatorio")
            return redirect(request.referrer)

        response = requests.post(
            f"{config.SUPABASE_URL}/rest/v1/ocas",
            json=data,
            headers=config.HEADERS
        )

        if response.status_code in [200, 201]:
            flash_success("OCA creado correctamente")
            return redirect(url_for('ocas.lista'))
        else:
            flash_error(f"Error al crear OCA: {response.text}")
            return redirect(request.referrer)

    # GET - Mostrar formulario
    return render_template("nuevo_oca.html")


@ocas_bp.route('/editar/<int:oca_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def editar(oca_id):
    """Editar un OCA existente"""

    if request.method == "POST":
        data = {
            "nombre": request.form.get("nombre"),
            "contacto_nombre": request.form.get("contacto_nombre") or None,
            "contacto_email": request.form.get("contacto_email") or None,
            "contacto_telefono": request.form.get("contacto_telefono") or None,
            "direccion": request.form.get("direccion") or None,
            "observaciones": request.form.get("observaciones") or None,
            "activo": request.form.get("activo") == "true"
        }

        response = requests.patch(
            f"{config.SUPABASE_URL}/rest/v1/ocas?id=eq.{oca_id}",
            json=data,
            headers=config.HEADERS
        )

        if response.status_code in [200, 204]:
            flash_success("OCA actualizado correctamente")
            return redirect(url_for('ocas.lista'))
        else:
            flash_error(f"Error al actualizar OCA: {response.text}")
            return redirect(request.referrer)

    # GET - Obtener OCA para editar
    response = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/ocas?id=eq.{oca_id}",
        headers=config.HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash_error("OCA no encontrado")
        return redirect(url_for('ocas.lista'))

    oca = limpiar_none(response.json()[0])

    return render_template("editar_oca.html", oca=oca)


@ocas_bp.route('/eliminar/<int:oca_id>')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'delete')
def eliminar(oca_id):
    """Eliminar un OCA"""

    response = requests.delete(
        f"{config.SUPABASE_URL}/rest/v1/ocas?id=eq.{oca_id}",
        headers=config.HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success("OCA eliminado correctamente")
    else:
        flash_error("Error al eliminar OCA")

    return redirect(url_for('ocas.lista'))
