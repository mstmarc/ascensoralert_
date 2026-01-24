"""
Blueprint de Equipos

Gestión de equipos de clientes con funcionalidades de:
- Creación de nuevos equipos vinculados a clientes
- CRUD completo de equipos
- Visualización de detalles
- Sistema de acciones/tareas para seguimiento
"""

from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date
import requests

import helpers
from config import config
from utils.formatters import limpiar_none
from utils.messages import flash_success, flash_error

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint
equipos_bp = Blueprint('equipos', __name__, url_prefix='/equipos')


@equipos_bp.route('/nuevo', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('clientes', 'write')
def nuevo():
    """Crear nuevo equipo vinculado a un cliente"""
    
    # VALIDAR que viene con lead_id
    lead_id = request.args.get("lead_id")
    
    if not lead_id:
        flash_error("Debes añadir equipos desde un lead específico")
        return redirect(url_for('leads.dashboard'))
    
    # Verificar que el lead existe
    lead_url = f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}"
    lead_response = requests.get(lead_url, headers=HEADERS)
    
    if lead_response.status_code != 200 or not lead_response.json():
        flash_error("Lead no encontrado")
        return redirect(url_for('leads.dashboard'))
    
    lead_data = lead_response.json()[0]
    # Limpiar valores None para evitar mostrar "none"
    lead_data = limpiar_none(lead_data)
    
    if request.method == "POST":
        equipo_data = {
            "cliente_id": int(lead_id),
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion") or None,
            "descripcion": request.form.get("observaciones") or None,
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae") or None,
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        # Solo tipo_equipo es obligatorio
        if not equipo_data["tipo_equipo"]:
            return render_template("nuevo_equipo.html", 
                                 lead=lead_data, 
                                 error="Tipo de equipo es obligatorio")

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            flash_success("Equipo añadido correctamente")
            return redirect(url_for('leads.ver', lead_id=lead_id))
        else:
            return render_template("nuevo_equipo.html", 
                                 lead=lead_data, 
                                 error="Error al crear el equipo")

    return render_template("nuevo_equipo.html", lead=lead_data)


@equipos_bp.route('/<int:equipo_id>')
@helpers.login_required
@helpers.requiere_permiso('clientes', 'read')
def ver(equipo_id):
    """Ver detalle de un equipo"""
    
    # Obtener equipo con JOIN a cliente
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}&select=*,cliente:clientes(id,direccion,localidad,nombre_cliente)",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash_error("Equipo no encontrado")
        return redirect(url_for('leads.dashboard'))

    equipo = limpiar_none(response.json()[0])

    # El cliente viene como un objeto dentro de equipo
    cliente = equipo.pop('cliente', None) if 'cliente' in equipo else None

    return render_template("ver_equipo.html", equipo=equipo, cliente=cliente)


@equipos_bp.route('/<int:equipo_id>/editar', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('clientes', 'write')
def editar(equipo_id):
    """Editar un equipo existente"""
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        return f"<h3 style='color:red;'>Error al obtener equipo</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    equipo = response.json()[0]

    if request.method == "POST":
        data = {
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion") or None,
            "descripcion": request.form.get("observaciones") or None,
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae") or None,
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        # Solo tipo_equipo es obligatorio
        if not data["tipo_equipo"]:
            flash_error("Tipo de equipo es obligatorio")
            return redirect(request.referrer)

        update_url = f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}"
        res = requests.patch(update_url, json=data, headers=HEADERS)
        if res.status_code in [200, 204]:
            # Obtener el cliente_id del equipo para volver a su vista
            cliente_id = equipo.get("cliente_id")
            return redirect(url_for('leads.ver', lead_id=cliente_id))
        else:
            return f"<h3 style='color:red;'>Error al actualizar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    # LIMPIAR VALORES NONE PARA NO MOSTRAR "none" EN EL FORMULARIO
    equipo = limpiar_none(equipo)
    return render_template("editar_equipo.html", equipo=equipo)


@equipos_bp.route('/<int:equipo_id>/eliminar')
@helpers.login_required
@helpers.requiere_permiso('clientes', 'delete')
def eliminar(equipo_id):
    """Eliminar un equipo"""
    
    equipo_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
    if equipo_response.status_code == 200 and equipo_response.json():
        cliente_id = equipo_response.json()[0].get("cliente_id")
        
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
        
        if response.status_code in [200, 204]:
            return redirect(url_for('leads.ver', lead_id=cliente_id))
        else:
            return f"<h3 style='color:red;'>Error al eliminar Equipo</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    else:
        return f"<h3 style='color:red;'>Error al obtener Equipo</h3><a href='/home'>Volver</a>"


# ============================================
# ACCIONES DE EQUIPOS (Sistema de tareas)
# ============================================

@equipos_bp.route('/<int:equipo_id>/accion/add', methods=['POST'])
@helpers.login_required
@helpers.requiere_permiso('clientes', 'write')
def add_accion(equipo_id):
    """Añadir acción/tarea a un equipo"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='equipos',
        registro_id=equipo_id,
        operacion='add',
        redirect_to=url_for('equipos.ver', equipo_id=equipo_id)
    )


@equipos_bp.route('/<int:equipo_id>/accion/toggle/<int:index>', methods=['POST'])
@helpers.login_required
@helpers.requiere_permiso('clientes', 'write')
def toggle_accion(equipo_id, index):
    """Marcar acción como completada/pendiente"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='equipos',
        registro_id=equipo_id,
        operacion='toggle',
        index=index,
        redirect_to=url_for('equipos.ver', equipo_id=equipo_id)
    )


@equipos_bp.route('/<int:equipo_id>/accion/delete/<int:index>', methods=['POST'])
@helpers.login_required
@helpers.requiere_permiso('clientes', 'write')
def delete_accion(equipo_id, index):
    """Eliminar acción de un equipo"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='equipos',
        registro_id=equipo_id,
        operacion='delete',
        index=index,
        redirect_to=url_for('equipos.ver', equipo_id=equipo_id)
    )
