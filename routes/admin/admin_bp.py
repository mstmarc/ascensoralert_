"""
Blueprint para gestión de Administradores y Usuarios del Sistema

Este módulo incluye:
- Gestión de administradores (fincas)
- Gestión de usuarios del sistema
- Utilidades de administración (cache)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import requests
import helpers
from config import config
from utils.formatters import limpiar_none
from utils.messages import flash_success, flash_error
from services.cache_service import get_administradores_cached, cache_administradores

# Crear Blueprint sin prefijo (las rutas mantienen su estructura original)
admin_bp = Blueprint('admin', __name__)

# Constantes de configuración
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS


# ============================================
# GESTIÓN DE ADMINISTRADORES (FINCAS)
# ============================================

@admin_bp.route('/admin/administradores')
def admin_administradores_redirect():
    """Redirect de /admin/administradores a /administradores_dashboard para compatibilidad"""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/administradores_dashboard')
@helpers.login_required
def dashboard():
    """Dashboard principal de administradores con tabs (administradores y visitas)"""

    # Determinar pestaña activa
    tab = request.args.get("tab", "administradores")  # administradores | visitas

    # ============================================
    # TAB: ADMINISTRADORES
    # ============================================
    if tab == "administradores":
        # Búsqueda
        buscar = request.args.get("buscar", "")

        # Paginación
        try:
            page = int(request.args.get("page", 1))
        except (ValueError, TypeError):
            page = 1

        limit = 10  # Paginación de 10 administradores por página
        offset = (page - 1) * limit

        # Si hay búsqueda, usar RPC para búsqueda sin acentos
        if buscar:
            # Usar función RPC para búsqueda sin acentos
            rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/buscar_administradores_sin_acentos"

            rpc_params = {
                "termino_busqueda": buscar,
                "limite": limit,
                "desplazamiento": offset
            }

            try:
                response = requests.post(rpc_url, json=rpc_params, headers=HEADERS, timeout=10)

                if response.status_code != 200:
                    print(f"Error al buscar administradores: {response.status_code} - {response.text}")
                    flash_error(f"Error al buscar administradores (Código: {response.status_code})")
                    return render_template(
                        "administradores_dashboard.html",
                        tab=tab,
                        administradores=[],
                        buscar=buscar,
                        page=1,
                        total_pages=1,
                        total_registros=0
                    )

                administradores_data = response.json()

                # Obtener total_count del primer resultado si existe
                total_registros = administradores_data[0].get('total_count', 0) if administradores_data else 0
                total_pages = max(1, (total_registros + limit - 1) // limit)

                # Remover total_count de cada registro (no es parte del modelo)
                administradores_base = [{k: v for k, v in admin.items() if k != 'total_count'} for admin in administradores_data]

                # Obtener IDs de los administradores encontrados
                admin_ids = [admin['id'] for admin in administradores_base]

                if admin_ids:
                    # Obtener conteos de clientes para estos administradores
                    clientes_response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/clientes?select=administrador_id&administrador_id=in.({','.join(map(str, admin_ids))})",
                        headers=HEADERS,
                        timeout=10
                    )
                    clientes_data = clientes_response.json() if clientes_response.status_code == 200 else []

                    # Obtener conteos de oportunidades (a través de clientes)
                    oportunidades_response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/oportunidades?select=cliente_id,clientes!inner(administrador_id)&clientes.administrador_id=in.({','.join(map(str, admin_ids))})",
                        headers=HEADERS,
                        timeout=10
                    )
                    oportunidades_data = oportunidades_response.json() if oportunidades_response.status_code == 200 else []

                    # Contar clientes por administrador
                    clientes_por_admin = {}
                    for cliente in clientes_data:
                        admin_id = cliente.get('administrador_id')
                        if admin_id:
                            clientes_por_admin[admin_id] = clientes_por_admin.get(admin_id, 0) + 1

                    # Contar oportunidades por administrador
                    oportunidades_por_admin = {}
                    for oportunidad in oportunidades_data:
                        cliente_info = oportunidad.get('clientes')
                        if cliente_info:
                            admin_id = cliente_info.get('administrador_id')
                            if admin_id:
                                oportunidades_por_admin[admin_id] = oportunidades_por_admin.get(admin_id, 0) + 1

                    # Agregar conteos a cada administrador
                    for admin in administradores_base:
                        admin_id = admin['id']
                        admin['num_oportunidades'] = oportunidades_por_admin.get(admin_id, 0)
                        admin['num_instalaciones'] = clientes_por_admin.get(admin_id, 0)

                    # Ordenar por: 1) num_oportunidades DESC, 2) num_instalaciones DESC
                    administradores_base.sort(
                        key=lambda x: (x.get('num_oportunidades', 0), x.get('num_instalaciones', 0)),
                        reverse=True
                    )

                administradores = administradores_base

            except Exception as e:
                print(f"Excepción al buscar administradores: {str(e)}")
                flash_error(f"Error de conexión al buscar administradores")
                administradores = []
                total_registros = 0
                total_pages = 1

        else:
            # Búsqueda normal sin filtro de texto
            # Primero obtener todos los administradores con conteo
            url_count = f"{SUPABASE_URL}/rest/v1/administradores?select=*"
            headers_with_count = HEADERS.copy()
            headers_with_count["Prefer"] = "count=exact"

            try:
                response = requests.get(url_count, headers=headers_with_count, timeout=10)

                # 200 = OK, 206 = Partial Content (respuesta válida con paginación)
                if response.status_code not in [200, 206]:
                    print(f"Error al cargar administradores: {response.status_code} - {response.text}")
                    flash_error(f"Error al cargar administradores desde la base de datos (Código: {response.status_code})")
                    # Renderizar con datos vacíos
                    return render_template(
                        "administradores_dashboard.html",
                        tab=tab,
                        administradores=[],
                        buscar=buscar,
                        page=1,
                        total_pages=1,
                        total_registros=0
                    )

                # Obtener total de registros del header Content-Range
                content_range = response.headers.get("Content-Range", "*/0")
                total_registros = int(content_range.split("/")[-1])

                # Parsear respuesta JSON
                administradores_base = response.json()

                # Obtener conteos de clientes por administrador
                clientes_response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/clientes?select=administrador_id",
                    headers=HEADERS,
                    timeout=10
                )
                clientes_data = clientes_response.json() if clientes_response.status_code == 200 else []

                # Obtener conteos de oportunidades (a través de clientes)
                oportunidades_response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/oportunidades?select=cliente_id,clientes!inner(administrador_id)",
                    headers=HEADERS,
                    timeout=10
                )
                oportunidades_data = oportunidades_response.json() if oportunidades_response.status_code == 200 else []

                # Contar clientes por administrador
                clientes_por_admin = {}
                for cliente in clientes_data:
                    admin_id = cliente.get('administrador_id')
                    if admin_id:
                        clientes_por_admin[admin_id] = clientes_por_admin.get(admin_id, 0) + 1

                # Contar oportunidades por administrador
                oportunidades_por_admin = {}
                for oportunidad in oportunidades_data:
                    cliente_info = oportunidad.get('clientes')
                    if cliente_info:
                        admin_id = cliente_info.get('administrador_id')
                        if admin_id:
                            oportunidades_por_admin[admin_id] = oportunidades_por_admin.get(admin_id, 0) + 1

                # Agregar conteos a cada administrador
                for admin in administradores_base:
                    admin_id = admin['id']
                    admin['num_oportunidades'] = oportunidades_por_admin.get(admin_id, 0)
                    admin['num_instalaciones'] = clientes_por_admin.get(admin_id, 0)

                # Ordenar por: 1) num_oportunidades DESC, 2) num_instalaciones DESC
                administradores_base.sort(
                    key=lambda x: (x.get('num_oportunidades', 0), x.get('num_instalaciones', 0)),
                    reverse=True
                )

                # Aplicar paginación después del ordenamiento
                start_idx = offset
                end_idx = offset + limit
                administradores = administradores_base[start_idx:end_idx]

            except Exception as e:
                print(f"Excepción al cargar administradores: {str(e)}")
                flash_error(f"Error de conexión al cargar administradores")
                administradores = []
                total_registros = 0

            # Calcular páginas
            total_pages = max(1, (total_registros + limit - 1) // limit)  # Al menos 1 página

        # Limpiar None en todos los casos
        try:
            administradores = [limpiar_none(admin) for admin in administradores]
        except Exception as e:
            print(f"Error al limpiar datos: {e}")
            administradores = []

        # Renderizar template con los resultados
        return render_template(
            "administradores_dashboard.html",
            tab=tab,
            administradores=administradores,
            buscar=buscar,
            page=page,
            total_pages=total_pages,
            total_registros=total_registros
        )

    # ============================================
    # TAB: VISITAS
    # ============================================
    elif tab == "visitas":
        # Paginación
        try:
            page = int(request.args.get("page", 1))
        except (ValueError, TypeError):
            page = 1

        per_page = 25
        offset = (page - 1) * per_page

        # Obtener registros paginados con JOIN a administradores y conteo
        data_url = f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=*,administradores(nombre_empresa)&order=fecha_visita.desc&limit={per_page}&offset={offset}"

        # Headers para obtener el conteo total
        headers_with_count = HEADERS.copy()
        headers_with_count["Prefer"] = "count=exact"

        try:
            response = requests.get(data_url, headers=headers_with_count, timeout=10)

            # 200 = OK, 206 = Partial Content (respuesta válida con paginación)
            if response.status_code not in [200, 206]:
                print(f"Error al cargar visitas: {response.status_code} - {response.text}")
                flash_error(f"Error al cargar visitas desde la base de datos (Código: {response.status_code})")
                # Renderizar con datos vacíos
                return render_template(
                    "administradores_dashboard.html",
                    tab=tab,
                    visitas=[],
                    page=1,
                    total_pages=1,
                    total_registros=0
                )

            # Obtener total de registros del header Content-Range
            try:
                content_range = response.headers.get("Content-Range", "*/0")
                total_registros = int(content_range.split("/")[-1])
            except Exception as e:
                print(f"Error al parsear Content-Range: {e}")
                total_registros = 0

            # Parsear respuesta JSON
            try:
                visitas = response.json()
            except Exception as e:
                print(f"Error al parsear JSON: {e}")
                flash_error(f"Error al procesar datos de visitas")
                return render_template(
                    "administradores_dashboard.html",
                    tab=tab,
                    visitas=[],
                    page=1,
                    total_pages=1,
                    total_registros=0
                )

            # Calcular páginas
            total_pages = max(1, (total_registros + per_page - 1) // per_page)

            # Limpiar None
            try:
                visitas = [limpiar_none(v) for v in visitas]
            except Exception as e:
                print(f"Error al limpiar datos: {e}")
                visitas = []

            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                visitas=visitas,
                page=page,
                total_pages=total_pages,
                total_registros=total_registros
            )

        except requests.exceptions.Timeout:
            print(f"Error de timeout al cargar visitas")
            flash_error(f"Error de conexión: La base de datos tardó demasiado en responder. Por favor, intente nuevamente.")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                visitas=[],
                page=1,
                total_pages=1,
                total_registros=0
            )
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar visitas: {e}")
            flash_error(f"Error de conexión al cargar visitas. Por favor, verifique su conexión a internet.")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                visitas=[],
                page=1,
                total_pages=1,
                total_registros=0
            )
        except Exception as e:
            print(f"Error inesperado al cargar visitas: {e}")
            flash_error(f"Error inesperado al cargar visitas. Por favor, contacte al administrador del sistema.")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                visitas=[],
                page=1,
                total_pages=1,
                total_registros=0
            )

    # ============================================
    # TAB INVÁLIDO - Redirigir a tab por defecto
    # ============================================
    else:
        print(f"Tab inválido recibido: {tab}")
        return redirect(url_for('admin.dashboard', tab='administradores'))


@admin_bp.route('/nuevo_administrador', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('administradores', 'write')
def nuevo():
    """Alta de nuevo administrador"""

    if request.method == "POST":
        data = {
            "nombre_empresa": request.form.get("nombre_empresa"),
            "telefono": request.form.get("telefono") or None,
            "email": request.form.get("email") or None,
            "direccion": request.form.get("direccion") or None,
            "localidad": request.form.get("localidad") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        # Validar campo obligatorio
        if not data["nombre_empresa"]:
            flash_error("El nombre de la empresa es obligatorio")
            return redirect(request.referrer)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/administradores",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 201]:
            flash_success("Administrador creado correctamente")
            return redirect(url_for('admin.dashboard'))
        else:
            flash_error(f"Error al crear administrador: {response.text}")
            return redirect(request.referrer)

    return render_template("nuevo_administrador.html")


@admin_bp.route('/ver_administrador/<int:admin_id>')
@helpers.login_required
def ver(admin_id):
    """Ver detalles de un administrador"""

    # Obtener administrador
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        return "Administrador no encontrado", 404

    administrador = limpiar_none(response.json()[0])

    # Obtener clientes asociados
    clientes_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?administrador_id=eq.{admin_id}&select=*",
        headers=HEADERS
    )

    clientes = []
    if clientes_response.status_code == 200:
        clientes = [limpiar_none(c) for c in clientes_response.json()]

    # Obtener oportunidades de todos los clientes asociados
    oportunidades = []
    stats = {
        'total': 0,
        'activas': 0,
        'ganadas': 0,
        'perdidas': 0,
        'valor_total': 0,
        'valor_activas': 0
    }

    if clientes:
        # Obtener IDs de clientes
        cliente_ids = [str(c['id']) for c in clientes]

        # Consultar oportunidades de estos clientes
        oportunidades_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?cliente_id=in.({','.join(cliente_ids)})&select=*,clientes(direccion,localidad)&order=fecha_creacion.desc",
            headers=HEADERS
        )

        if oportunidades_response.status_code == 200:
            oportunidades = oportunidades_response.json()

            # Calcular estadísticas
            for op in oportunidades:
                stats['total'] += 1
                estado = op.get('estado', '').lower()

                if estado == 'activa':
                    stats['activas'] += 1
                    if op.get('valor_estimado'):
                        stats['valor_activas'] += float(op.get('valor_estimado', 0))
                elif estado == 'ganada':
                    stats['ganadas'] += 1
                elif estado == 'perdida':
                    stats['perdidas'] += 1

                if op.get('valor_estimado'):
                    stats['valor_total'] += float(op.get('valor_estimado', 0))

    return render_template(
        "ver_administrador.html",
        administrador=administrador,
        clientes=clientes,
        oportunidades=oportunidades,
        stats=stats
    )


@admin_bp.route('/editar_administrador/<int:admin_id>', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('administradores', 'write')
def editar(admin_id):
    """Editar datos de un administrador"""

    if request.method == "POST":
        data = {
            "nombre_empresa": request.form.get("nombre_empresa"),
            "telefono": request.form.get("telefono") or None,
            "email": request.form.get("email") or None,
            "direccion": request.form.get("direccion") or None,
            "localidad": request.form.get("localidad") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        # Validar campo obligatorio
        if not data["nombre_empresa"]:
            flash_error("El nombre de la empresa es obligatorio")
            return redirect(request.referrer)

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 201, 204]:
            flash_success("Administrador actualizado correctamente")
            return redirect(url_for('admin.ver', admin_id=admin_id))
        else:
            flash_error(f"Error al actualizar administrador: {response.text}")
            return redirect(request.referrer)

    # GET - Obtener datos del administrador
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        return "Administrador no encontrado", 404

    administrador = limpiar_none(response.json()[0])

    return render_template("editar_administrador.html", administrador=administrador)


@admin_bp.route('/eliminar_administrador/<int:admin_id>')
@helpers.login_required
@helpers.requiere_permiso('administradores', 'delete')
def eliminar(admin_id):
    """Eliminar un administrador"""

    # Verificar si tiene clientes asociados
    clientes_check = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?administrador_id=eq.{admin_id}&select=count",
        headers=HEADERS
    )

    if clientes_check.status_code == 200 and clientes_check.json():
        num_clientes = len(clientes_check.json())
        if num_clientes > 0:
            flash_error(f"No se puede eliminar: el administrador tiene {num_clientes} cliente(s) asociado(s)")
            return redirect(url_for('admin.ver', admin_id=admin_id))

    # Eliminar administrador
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success("Administrador eliminado correctamente")
        return redirect(url_for('admin.dashboard'))
    else:
        flash_error(f"Error al eliminar administrador: {response.text}")
        return redirect(url_for('admin.ver', admin_id=admin_id))


# ============================================
# GESTIÓN DE USUARIOS DEL SISTEMA
# ============================================

@admin_bp.route('/admin/usuarios')
@helpers.login_required
@helpers.solo_admin
def usuarios():
    """Panel de administración de usuarios - Solo para admin"""

    # Obtener todos los usuarios
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios?select=*&order=id",
        headers=HEADERS
    )

    usuarios = []
    if response.status_code == 200:
        usuarios = response.json()

    return render_template("admin_usuarios.html", usuarios=usuarios)


@admin_bp.route('/admin/usuarios/crear', methods=["POST"])
@helpers.login_required
@helpers.solo_admin
def crear_usuario():
    """Crear un nuevo usuario"""

    nombre_usuario = request.form.get("nombre_usuario", "").strip()
    email = request.form.get("email", "").strip()
    contrasena = request.form.get("contrasena", "").strip()
    perfil = request.form.get("perfil", "visualizador")

    # Validaciones
    if not nombre_usuario or not contrasena:
        flash_error("Nombre de usuario y contraseña son obligatorios")
        return redirect(url_for('admin.usuarios'))

    if perfil not in ['admin', 'gestor', 'visualizador']:
        flash_error("Perfil inválido")
        return redirect(url_for('admin.usuarios'))

    # Crear usuario
    data = {
        "nombre_usuario": nombre_usuario,
        "email": email or None,
        "contrasena": contrasena,  # NOTA: En producción deberías usar hash
        "perfil": perfil
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/usuarios",
        json=data,
        headers=HEADERS
    )

    if response.status_code in [200, 201]:
        flash_success(f"Usuario '{nombre_usuario}' creado exitosamente con perfil '{perfil}'")
    else:
        flash_error(f"Error al crear usuario: {response.text}")

    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/admin/usuarios/editar/<int:usuario_id>', methods=["POST"])
@helpers.login_required
@helpers.solo_admin
def editar_usuario(usuario_id):
    """Editar perfil de un usuario"""

    perfil = request.form.get("perfil", "visualizador")

    if perfil not in ['admin', 'gestor', 'visualizador']:
        flash_error("Perfil inválido")
        return redirect(url_for('admin.usuarios'))

    # Actualizar perfil
    data = {"perfil": perfil}

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{usuario_id}",
        json=data,
        headers=HEADERS
    )

    if response.status_code == 200:
        flash_success("Perfil actualizado correctamente")
    else:
        flash_error(f"Error al actualizar perfil: {response.text}")

    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/admin/usuarios/eliminar/<int:usuario_id>')
@helpers.login_required
@helpers.solo_admin
def eliminar_usuario(usuario_id):
    """Eliminar un usuario"""

    # Evitar que el admin se elimine a sí mismo
    if usuario_id == session.get("usuario_id"):
        flash_error("No puedes eliminar tu propio usuario")
        return redirect(url_for('admin.usuarios'))

    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{usuario_id}",
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash_success("Usuario eliminado correctamente")
    else:
        flash_error(f"Error al eliminar usuario: {response.text}")

    return redirect(url_for('admin.usuarios'))


# ============================================
# UTILIDADES DE ADMINISTRACIÓN
# ============================================

@admin_bp.route('/admin/clear_cache')
@helpers.login_required
def clear_cache():
    """Endpoint para limpiar manualmente el caché de administradores"""

    # Limpiar el caché
    cache_administradores['data'] = []
    cache_administradores['timestamp'] = None

    # Forzar recarga inmediata
    administradores = get_administradores_cached()

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Caché Actualizado</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; text-align: center; }}
            .success {{ color: #28a745; font-size: 48px; margin-bottom: 20px; }}
            h1 {{ color: #333; }}
            .count {{ font-size: 32px; font-weight: bold; color: #366092; margin: 20px 0; }}
            .btn {{ display: inline-block; margin: 10px; padding: 12px 24px; background: #366092; color: white; text-decoration: none; border-radius: 5px; }}
            .btn:hover {{ background: #2a4a70; }}
        </style>
    </head>
    <body>
        <div class="success">✅</div>
        <h1>Caché Actualizado Correctamente</h1>
        <p class="count">{len(administradores)} administradores cargados</p>
        <p>El caché se ha limpiado y recargado exitosamente desde la base de datos.</p>
        <a href="{url_for('admin.dashboard')}" class="btn">Volver al Dashboard</a>
    </body>
    </html>
    """
