"""
Blueprint de Oportunidades

Gestión de oportunidades comerciales con funcionalidades de:
- Dashboard de oportunidades (por estado)
- Agenda personal comercial (Mi Agenda)
- Seguimiento post-IPO (tareas automáticas)
- CRUD completo de oportunidades
- Sistema de acciones/tareas para seguimiento
- Cambio rápido de estado (AJAX)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
import requests

import helpers
from config import config
from utils.messages import flash_success, flash_error

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint
oportunidades_bp = Blueprint('oportunidades', __name__)


# ============================================
# DASHBOARD Y VISTAS PRINCIPALES
# ============================================

@oportunidades_bp.route('/oportunidades')
def oportunidades():
    """Dashboard principal de oportunidades con contadores por estado"""
    if "usuario" not in session:
        return redirect("/")

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?"
            f"select=*,clientes(nombre_cliente,direccion,localidad)"
            f"&order=fecha_creacion.desc",
            headers=HEADERS
        )

        if response.status_code == 200:
            oportunidades_list = response.json()

            # Contar por estado
            nuevas = sum(1 for o in oportunidades_list if o['estado'] == 'nueva')
            presupuesto_preparacion = sum(1 for o in oportunidades_list if o['estado'] == 'presupuesto_preparacion')
            presupuesto_enviado = sum(1 for o in oportunidades_list if o['estado'] == 'presupuesto_enviado')
            ganadas = sum(1 for o in oportunidades_list if o['estado'] == 'ganada')
            perdidas = sum(1 for o in oportunidades_list if o['estado'] == 'perdida')

            return render_template("oportunidades.html",
                                        oportunidades=oportunidades_list,
                                        nuevas=nuevas,
                                        presupuesto_preparacion=presupuesto_preparacion,
                                        presupuesto_enviado=presupuesto_enviado,
                                        ganadas=ganadas,
                                        perdidas=perdidas)
        else:
            flash_error("Error al cargar oportunidades")
            return redirect(url_for("home"))

    except Exception as e:
        flash_error(f"Error: {str(e)}")
        return redirect(url_for("home"))


@oportunidades_bp.route('/mi_agenda')
def mi_agenda():
    """Dashboard personal - Mi Agenda Comercial con pipeline de oportunidades"""
    if "usuario" not in session:
        return redirect("/")

    try:
        # Obtener TODAS las oportunidades que NO estén ganadas ni perdidas
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?"
            f"select=*,clientes(nombre_cliente,direccion,localidad,telefono,email,persona_contacto)"
            f"&estado=not.in.(ganada,perdida)"
            f"&order=fecha_creacion.desc",
            headers=HEADERS
        )

        if response.status_code == 200:
            oportunidades_list = response.json()

            # Agrupar por estado
            por_estado = {
                'nueva': [],
                'en_contacto': [],
                'presupuesto_preparacion': [],
                'presupuesto_enviado': [],
                'activa': []  # Para compatibilidad con oportunidades antiguas
            }

            for opp in oportunidades_list:
                estado = opp.get('estado', 'activa')
                if estado in por_estado:
                    por_estado[estado].append(opp)
                else:
                    # Si tiene un estado que no conocemos, lo ponemos en activa
                    por_estado['activa'].append(opp)

            # Contadores
            total_activas = len(oportunidades_list)

            return render_template("mi_agenda.html",
                                 por_estado=por_estado,
                                 total_activas=total_activas)
        else:
            flash_error(f"Error al cargar oportunidades: {response.status_code} - {response.text}")
            return redirect(url_for("home"))

    except Exception as e:
        flash_error(f"Error: {str(e)}")
        return redirect(url_for("home"))


@oportunidades_bp.route('/oportunidades_post_ipo')
def oportunidades_post_ipo():
    """Seguimiento Comercial - Sistema de tareas automáticas"""
    if "usuario" not in session:
        return redirect("/")

    # Determinar pestaña activa (abiertas o futuras)
    tab = request.args.get("tab", "abiertas")
    hoy = datetime.now().date()

    try:
        # === 1. OBTENER EQUIPOS CON IPO ===
        equipos_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/equipos?select=id,ipo_proxima,rae,cliente_id,clientes(direccion,localidad,telefono,persona_contacto,empresa_mantenedora)&ipo_proxima=not.is.null",
            headers=HEADERS,
            timeout=10
        )
        equipos_data = equipos_response.json() if equipos_response.status_code == 200 else []

        # === 2. PROCESAR IPOs Y CREAR TAREAS AUTOMÁTICAS ===
        # Agrupar equipos por cliente (solo el más próximo)
        clientes_con_ipo = {}
        for equipo in equipos_data:
            if not equipo.get('ipo_proxima'):
                continue

            try:
                ipo_date = datetime.strptime(equipo['ipo_proxima'], '%Y-%m-%d').date()
            except:
                continue

            dias_desde_ipo = (hoy - ipo_date).days
            cliente_id = equipo['cliente_id']

            # Solo guardar el equipo con IPO más reciente por cliente
            if cliente_id not in clientes_con_ipo or dias_desde_ipo < clientes_con_ipo[cliente_id]['dias_desde_ipo']:
                clientes_con_ipo[cliente_id] = {
                    'cliente_id': cliente_id,
                    'equipo_id': equipo['id'],
                    'ipo_date': ipo_date,
                    'dias_desde_ipo': dias_desde_ipo,
                    'dias_hasta_ipo': abs(dias_desde_ipo) if dias_desde_ipo < 0 else 0,
                    'rae': equipo.get('rae'),
                    'cliente': equipo.get('clientes', {})
                }

        # === 3. CREAR TAREAS AUTOMÁTICAS (IPO >= 15 días) ===
        for cliente_id, data in clientes_con_ipo.items():
            if data['dias_desde_ipo'] >= 15:
                # Verificar si ya existe tarea abierta para este cliente
                tarea_existe = requests.get(
                    f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas?cliente_id=eq.{cliente_id}&estado=eq.abierta",
                    headers=HEADERS
                ).json()

                # Verificar si el cliente tiene tareas descartadas (para no crear nuevas)
                tarea_descartada = requests.get(
                    f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas?cliente_id=eq.{cliente_id}&estado=eq.cerrada&tipo_cierre=not.is.null",
                    headers=HEADERS
                ).json()

                if not tarea_existe and not tarea_descartada:
                    # Crear tarea automáticamente solo si no hay tareas abiertas ni descartadas
                    nueva_tarea = {
                        'cliente_id': cliente_id,
                        'equipo_id': data['equipo_id'],
                        'estado': 'abierta',
                        'motivo_creacion': 'ipo_15_dias',
                        'dias_desde_ipo': data['dias_desde_ipo'],
                        'creado_por': 'sistema'
                    }
                    requests.post(
                        f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas",
                        headers=HEADERS,
                        json=nueva_tarea
                    )

        # === 3B. OBTENER CLIENTES CON FECHA_FIN_CONTRATO Y CREAR TAREAS AUTOMÁTICAS ===
        clientes_fin_contrato_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/clientes?select=id,fecha_fin_contrato,direccion,localidad,telefono,persona_contacto,empresa_mantenedora&fecha_fin_contrato=not.is.null",
            headers=HEADERS,
            timeout=10
        )
        clientes_fin_contrato_data = clientes_fin_contrato_response.json() if clientes_fin_contrato_response.status_code == 200 else []

        clientes_con_fin_contrato = {}
        for cliente in clientes_fin_contrato_data:
            if not cliente.get('fecha_fin_contrato'):
                continue

            try:
                fecha_fin = datetime.strptime(cliente['fecha_fin_contrato'], '%Y-%m-%d').date()
            except:
                continue

            dias_hasta_fin = (fecha_fin - hoy).days
            cliente_id = cliente['id']

            clientes_con_fin_contrato[cliente_id] = {
                'cliente_id': cliente_id,
                'fecha_fin_contrato': fecha_fin,
                'dias_hasta_fin': dias_hasta_fin,
                'cliente': cliente
            }

            # Crear tarea automática si faltan 120 días o menos
            if dias_hasta_fin <= 120 and dias_hasta_fin >= 0:
                # Verificar si ya existe tarea abierta para este cliente
                tarea_existe = requests.get(
                    f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas?cliente_id=eq.{cliente_id}&estado=eq.abierta",
                    headers=HEADERS
                ).json()

                # Verificar si el cliente tiene tareas descartadas (para no crear nuevas)
                tarea_descartada = requests.get(
                    f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas?cliente_id=eq.{cliente_id}&estado=eq.cerrada&tipo_cierre=not.is.null",
                    headers=HEADERS
                ).json()

                if not tarea_existe and not tarea_descartada:
                    # Crear tarea automáticamente solo si no hay tareas abiertas ni descartadas
                    nueva_tarea = {
                        'cliente_id': cliente_id,
                        'equipo_id': None,
                        'estado': 'abierta',
                        'motivo_creacion': 'fin_contrato_120_dias',
                        'dias_desde_ipo': None,
                        'creado_por': 'sistema'
                    }
                    requests.post(
                        f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas",
                        headers=HEADERS,
                        json=nueva_tarea
                    )

        # === 4. OBTENER TAREAS EXISTENTES CON DATOS DEL CLIENTE ===
        tareas_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/seguimiento_comercial_tareas?select=*,clientes(direccion,localidad,telefono,persona_contacto,empresa_mantenedora)&estado=eq.abierta&order=fecha_creacion.asc",
            headers=HEADERS
        )
        tareas_data = tareas_response.json() if tareas_response.status_code == 200 else []

        # === 5. CLASIFICAR TAREAS ===
        tareas_abiertas = []
        tareas_aplazadas = []

        for tarea in tareas_data:
            # Obtener datos del cliente
            cliente_info = tarea.get('clientes', {})
            cliente_id = tarea['cliente_id']

            # Buscar días desde IPO actualizado
            dias_desde_ipo = clientes_con_ipo.get(cliente_id, {}).get('dias_desde_ipo', tarea.get('dias_desde_ipo', 0))

            tarea_enriched = {
                'id': tarea['id'],
                'cliente_id': cliente_id,
                'direccion': cliente_info.get('direccion', 'Sin dirección'),
                'localidad': cliente_info.get('localidad', ''),
                'telefono': cliente_info.get('telefono'),
                'persona_contacto': cliente_info.get('persona_contacto'),
                'empresa_mantenedora': cliente_info.get('empresa_mantenedora'),
                'dias_desde_ipo': dias_desde_ipo,
                'fecha_creacion': tarea['fecha_creacion'],
                'aplazada_hasta': tarea.get('aplazada_hasta'),
                'motivo_aplazamiento': tarea.get('motivo_aplazamiento'),
                'notas': tarea.get('notas', [])
            }

            # Clasificar: ABIERTAS vs FUTURAS (aplazadas)
            if tarea.get('aplazada_hasta'):
                try:
                    fecha_aplazada = datetime.strptime(tarea['aplazada_hasta'], '%Y-%m-%d').date()
                    if fecha_aplazada > hoy:
                        # Aún aplazada
                        tarea_enriched['dias_para_reabrir'] = (fecha_aplazada - hoy).days
                        tareas_aplazadas.append(tarea_enriched)
                    else:
                        # Aplazamiento venció, pasa a abiertas
                        tareas_abiertas.append(tarea_enriched)
                except:
                    tareas_abiertas.append(tarea_enriched)
            else:
                tareas_abiertas.append(tarea_enriched)

        # === 6. FUTURAS - PRÓXIMAS AUTOMÁTICAS (IPO próximos 30 días + hace 0-14 días) ===
        proximas_automaticas = []
        for cliente_id, data in clientes_con_ipo.items():
            # IPO en próximos 30 días O ya ocurrió hace 0-14 días (antes de crear tarea)
            if -30 <= data['dias_desde_ipo'] < 15:
                # Verificar que no tenga tarea
                tiene_tarea = any(t['cliente_id'] == cliente_id for t in tareas_abiertas + tareas_aplazadas)
                if not tiene_tarea:
                    # Determinar si es futura o pasada
                    es_futura = data['dias_desde_ipo'] < 0

                    if es_futura:
                        # IPO aún no ocurrió
                        dias_hasta_ipo = abs(data['dias_desde_ipo'])
                        dias_para_activar = dias_hasta_ipo + 15
                    else:
                        # IPO ya ocurrió, esperando llegar a 15 días
                        dias_desde_ipo = data['dias_desde_ipo']
                        dias_hasta_ipo = None  # No aplica
                        dias_para_activar = 15 - dias_desde_ipo

                    proximas_automaticas.append({
                        'cliente_id': cliente_id,
                        'direccion': data['cliente'].get('direccion', 'Sin dirección'),
                        'localidad': data['cliente'].get('localidad', ''),
                        'telefono': data['cliente'].get('telefono'),
                        'es_futura': es_futura,
                        'dias_hasta_ipo': dias_hasta_ipo,  # Solo para futuras
                        'dias_desde_ipo': dias_desde_ipo if not es_futura else None,  # Solo para pasadas
                        'dias_para_activar': dias_para_activar,
                        'rae': data['rae'],
                        'motivo': 'IPO'
                    })

        # === 6B. FUTURAS - PRÓXIMAS POR FIN DE CONTRATO (121-150 días) ===
        for cliente_id, data in clientes_con_fin_contrato.items():
            # Fin de contrato entre 121 y 150 días
            if 121 <= data['dias_hasta_fin'] <= 150:
                # Verificar que no tenga tarea
                tiene_tarea = any(t['cliente_id'] == cliente_id for t in tareas_abiertas + tareas_aplazadas)
                if not tiene_tarea:
                    proximas_automaticas.append({
                        'cliente_id': cliente_id,
                        'direccion': data['cliente'].get('direccion', 'Sin dirección'),
                        'localidad': data['cliente'].get('localidad', ''),
                        'telefono': data['cliente'].get('telefono'),
                        'es_futura': True,
                        'dias_hasta_fin_contrato': data['dias_hasta_fin'],
                        'dias_para_activar': data['dias_hasta_fin'] - 120,  # Días hasta que se active (120 días antes)
                        'fecha_fin_contrato': data['fecha_fin_contrato'].strftime('%d/%m/%Y'),
                        'motivo': 'Fin de Contrato'
                    })

        # Ordenar
        tareas_abiertas.sort(key=lambda x: x['dias_desde_ipo'], reverse=True)  # Más urgente primero
        tareas_aplazadas.sort(key=lambda x: x['aplazada_hasta'])
        # Ordenar próximas: primero las que ya pasaron (más urgentes), luego las futuras
        proximas_automaticas.sort(key=lambda x: x['dias_para_activar'])

        return render_template(
            "oportunidades_post_ipo.html",
            tab=tab,
            tareas_abiertas=tareas_abiertas,
            tareas_aplazadas=tareas_aplazadas,
            proximas_automaticas=proximas_automaticas,
            abiertas_count=len(tareas_abiertas),
            aplazadas_count=len(tareas_aplazadas),
            proximas_count=len(proximas_automaticas)
        )

    except Exception as e:
        print(f"Error en seguimiento comercial: {str(e)}")
        flash_error(f"Error al cargar seguimiento comercial: {str(e)}")
        return redirect("/home")


# ============================================
# CRUD DE OPORTUNIDADES
# ============================================

@oportunidades_bp.route('/crear_oportunidad/<int:cliente_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('oportunidades', 'write')
def crear_oportunidad(cliente_id):
    """Crear nueva oportunidad para un cliente"""

    if request.method == "POST":
        try:
            data = {
                "cliente_id": cliente_id,
                "tipo": request.form["tipo"],
                "descripcion": request.form.get("descripcion", ""),
                "valor_estimado": request.form.get("valor_estimado") or None,
                "observaciones": request.form.get("observaciones", ""),
                "estado": "nueva"
            }

            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/oportunidades",
                headers=HEADERS,
                json=data
            )

            if response.status_code == 201:
                flash_success("Oportunidad creada exitosamente!")
                return redirect(url_for("leads.ver", lead_id=cliente_id))
            else:
                flash_error("Error al crear oportunidad")

        except Exception as e:
            flash_error(f"Error: {str(e)}")

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}",
            headers=HEADERS
        )
        if response.status_code == 200:
            cliente = response.json()[0]
            return render_template("crear_oportunidad.html", cliente=cliente)
    except:
        flash_error("Error al cargar datos del cliente")
        return redirect(url_for("leads.dashboard"))


@oportunidades_bp.route('/ver_oportunidad/<int:oportunidad_id>')
def ver_oportunidad(oportunidad_id):
    """Ver detalle de una oportunidad con visitas relacionadas"""
    if "usuario" not in session:
        return redirect("/")

    try:
        # Obtener oportunidad con datos del cliente
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion,localidad)",
            headers=HEADERS
        )

        if response.status_code == 200 and response.json():
            oportunidad = response.json()[0]

            # Asegurar que acciones sea una lista
            if not oportunidad.get('acciones') or not isinstance(oportunidad.get('acciones'), list):
                oportunidad['acciones'] = []

            # Obtener visitas de seguimiento asociadas a esta oportunidad
            visitas_seguimiento_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?oportunidad_id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion)&order=fecha_visita.desc",
                headers=HEADERS
            )

            visitas_seguimiento = []
            if visitas_seguimiento_response.status_code == 200:
                for v in visitas_seguimiento_response.json():
                    visitas_seguimiento.append({
                        'id': v.get('id'),
                        'fecha_visita': v.get('fecha_visita'),
                        'tipo_visita': 'Visita a Instalación',
                        'tipo': 'instalacion',
                        'observaciones': v.get('observaciones', ''),
                        'cliente_nombre': v.get('clientes', {}).get('nombre_cliente', 'Sin nombre') if v.get('clientes') else 'Sin nombre'
                    })

            # Obtener visitas a administradores asociadas a esta oportunidad
            visitas_admin_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/visitas_administradores?oportunidad_id=eq.{oportunidad_id}&order=fecha_visita.desc",
                headers=HEADERS
            )

            visitas_admin = []
            if visitas_admin_response.status_code == 200:
                for v in visitas_admin_response.json():
                    visitas_admin.append({
                        'id': v.get('id'),
                        'fecha_visita': v.get('fecha_visita'),
                        'tipo_visita': f"Visita a Administrador: {v.get('administrador_fincas', 'N/A')}",
                        'tipo': 'administrador',
                        'observaciones': v.get('observaciones', ''),
                        'persona_contacto': v.get('persona_contacto', '')
                    })

            # Combinar y ordenar todas las visitas por fecha
            todas_visitas = visitas_seguimiento + visitas_admin
            todas_visitas.sort(key=lambda x: x['fecha_visita'], reverse=True)

            return render_template("ver_oportunidad.html",
                                 oportunidad=oportunidad,
                                 visitas=todas_visitas)
        else:
            flash_error("Oportunidad no encontrada")
            return redirect(url_for("oportunidades.oportunidades"))
    except Exception as e:
        flash_error(f"Error: {str(e)}")
        return redirect(url_for("oportunidades.oportunidades"))


@oportunidades_bp.route('/editar_oportunidad/<int:oportunidad_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('oportunidades', 'write')
def editar_oportunidad(oportunidad_id):
    """Editar oportunidad existente"""

    if request.method == "POST":
        try:
            data = {
                "tipo": request.form["tipo"],
                "descripcion": request.form.get("descripcion", ""),
                "estado": request.form["estado"],
                "valor_estimado": request.form.get("valor_estimado") or None,
                "notas": request.form.get("notas", ""),
                "estado_presupuesto": request.form.get("estado_presupuesto", "No")
            }

            if data["estado"] in ["ganada", "perdida"]:
                data["fecha_cierre"] = datetime.now().isoformat()

            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
                headers=HEADERS,
                json=data
            )

            if response.status_code in [200, 204]:
                flash_success("Oportunidad actualizada correctamente")
                return redirect(url_for("oportunidades.ver_oportunidad", oportunidad_id=oportunidad_id))
            else:
                flash_error("Error al actualizar")

        except Exception as e:
            flash_error(f"Error: {str(e)}")

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion)",
            headers=HEADERS
        )
        if response.status_code == 200:
            oportunidad = response.json()[0]
            return render_template("editar_oportunidad.html", oportunidad=oportunidad)
    except:
        flash_error("Error al cargar oportunidad")
        return redirect(url_for("oportunidades.oportunidades"))


@oportunidades_bp.route('/eliminar_oportunidad/<int:oportunidad_id>')
@helpers.login_required
@helpers.requiere_permiso('oportunidades', 'delete')
def eliminar_oportunidad(oportunidad_id):
    """Eliminar oportunidad"""

    try:
        response_get = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=cliente_id",
            headers=HEADERS
        )

        if response_get.status_code == 200 and response_get.json():
            cliente_id = response_get.json()[0]["cliente_id"]

            response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
                headers=HEADERS
            )

            if response.status_code in [200, 204]:
                flash_success("Oportunidad eliminada correctamente")
                return redirect(f"/ver_lead/{cliente_id}")
            else:
                flash_error("Error al eliminar oportunidad")
                return redirect(url_for("oportunidades.oportunidades"))
        else:
            flash_error("Oportunidad no encontrada")
            return redirect(url_for("oportunidades.oportunidades"))
    except Exception as e:
        flash_error(f"Error: {str(e)}")
        return redirect(url_for("oportunidades.oportunidades"))


# ============================================
# ENDPOINTS AJAX
# ============================================

@oportunidades_bp.route('/cambiar_estado_oportunidad/<int:oportunidad_id>', methods=["POST"])
def cambiar_estado_oportunidad(oportunidad_id):
    """Endpoint para cambio rápido de estado desde Mi Agenda"""
    if "usuario" not in session:
        return {"error": "No autorizado"}, 401

    try:
        nuevo_estado = request.json.get("estado")
        if not nuevo_estado:
            return {"error": "Estado requerido"}, 400

        # Validar estados permitidos
        estados_validos = ["nueva", "en_contacto", "presupuesto_preparacion",
                          "presupuesto_enviado", "ganada", "perdida"]
        if nuevo_estado not in estados_validos:
            return {"error": "Estado no válido"}, 400

        data = {"estado": nuevo_estado}

        # Si se marca como ganada o perdida, agregar fecha de cierre
        if nuevo_estado in ["ganada", "perdida"]:
            data["fecha_cierre"] = datetime.now().isoformat()

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
            headers=HEADERS,
            json=data
        )

        if response.status_code in [200, 204]:
            return {"success": True, "estado": nuevo_estado}, 200
        else:
            return {"error": "Error al actualizar"}, 500

    except Exception as e:
        return {"error": str(e)}, 500


# ============================================
# SISTEMA DE ACCIONES
# ============================================

@oportunidades_bp.route('/oportunidad/<int:oportunidad_id>/accion/add', methods=["POST"])
@helpers.login_required
def add_accion(oportunidad_id):
    """Agregar nueva acción a una oportunidad"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='oportunidades',
        registro_id=oportunidad_id,
        operacion='add',
        redirect_to=url_for('oportunidades.ver_oportunidad', oportunidad_id=oportunidad_id)
    )


@oportunidades_bp.route('/oportunidad/<int:oportunidad_id>/accion/toggle/<int:index>', methods=["POST"])
@helpers.login_required
def toggle_accion(oportunidad_id, index):
    """Marcar/desmarcar acción como completada"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='oportunidades',
        registro_id=oportunidad_id,
        operacion='toggle',
        index=index,
        redirect_to=url_for('oportunidades.ver_oportunidad', oportunidad_id=oportunidad_id)
    )


@oportunidades_bp.route('/oportunidad/<int:oportunidad_id>/accion/delete/<int:index>', methods=["POST"])
@helpers.login_required
def delete_accion(oportunidad_id, index):
    """Eliminar acción de una oportunidad"""
    from utils.helpers_actions import gestionar_accion
    return gestionar_accion(
        tabla='oportunidades',
        registro_id=oportunidad_id,
        operacion='delete',
        index=index,
        redirect_to=url_for('oportunidades.ver_oportunidad', oportunidad_id=oportunidad_id)
    )
