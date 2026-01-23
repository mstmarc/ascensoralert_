"""
Helpers para operaciones con acciones (oportunidades, equipos, etc.)
"""
import requests
from flask import flash, redirect, url_for, request


def gestionar_accion(tabla, registro_id, operacion, index=None, redirect_to=None):
    """
    Gestiona operaciones de acciones (añadir, completar/descompletar, eliminar) para cualquier tabla.

    Args:
        tabla: Nombre de la tabla en Supabase ('oportunidades', 'equipos', etc.)
        registro_id: ID del registro
        operacion: 'add', 'toggle', 'delete'
        index: Índice de la acción (para toggle y delete)
        redirect_to: Ruta para redireccionar después de la operación

    Returns:
        Flask redirect response
    """
    from config import config

    # Obtener acciones actuales
    response = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/{tabla}?id=eq.{registro_id}&select=acciones",
        headers=config.HEADERS
    )

    if response.status_code != 200 or not response.json():
        flash('Error al obtener datos', 'error')
        return redirect(redirect_to)

    acciones = response.json()[0].get('acciones', [])
    if not isinstance(acciones, list):
        acciones = []

    # Ejecutar operación
    if operacion == 'add':
        texto_accion = request.form.get('texto_accion', '').strip()
        if not texto_accion:
            flash('Debes escribir una acción', 'error')
            return redirect(redirect_to)

        acciones.append({
            'texto': texto_accion,
            'completada': False
        })
        mensaje = 'Acción añadida correctamente'

    elif operacion == 'toggle':
        if index is None or index >= len(acciones):
            flash('Acción no encontrada', 'error')
            return redirect(redirect_to)

        acciones[index]['completada'] = not acciones[index].get('completada', False)
        mensaje = 'Estado de la acción actualizado'

    elif operacion == 'delete':
        if index is None or index >= len(acciones):
            flash('Acción no encontrada', 'error')
            return redirect(redirect_to)

        acciones.pop(index)
        mensaje = 'Acción eliminada'

    else:
        flash('Operación no válida', 'error')
        return redirect(redirect_to)

    # Actualizar en BD
    response = requests.patch(
        f"{config.SUPABASE_URL}/rest/v1/{tabla}?id=eq.{registro_id}",
        headers=config.HEADERS,
        json={'acciones': acciones}
    )

    if response.status_code == 200:
        flash(mensaje, 'success')
    else:
        flash('Error al actualizar la acción', 'error')

    return redirect(redirect_to)


def obtener_conteos_por_tabla(tabla_principal, tabla_relacionada, campo_relacion, filtros_principal=None):
    """
    Obtiene conteos de registros relacionados sin queries N+1.

    Ejemplo: Para obtener el conteo de inspecciones por OCA:
        obtener_conteos_por_tabla('ocas', 'inspecciones', 'oca_id')

    Args:
        tabla_principal: Tabla principal (ej: 'ocas')
        tabla_relacionada: Tabla relacionada (ej: 'inspecciones')
        campo_relacion: Campo de relación en tabla relacionada (ej: 'oca_id')
        filtros_principal: Filtros opcionales para tabla principal

    Returns:
        Lista de diccionarios con los datos de la tabla principal y 'total_count' para cada registro
    """
    from config import config

    # Obtener registros principales
    url_principal = f"{config.SUPABASE_URL}/rest/v1/{tabla_principal}?select=*"
    if filtros_principal:
        url_principal += f"&{filtros_principal}"

    response_principal = requests.get(url_principal, headers=config.HEADERS)
    if response_principal.status_code != 200:
        return []

    registros = response_principal.json()

    # Obtener TODOS los registros relacionados de una sola vez
    response_relacionados = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/{tabla_relacionada}?select={campo_relacion}",
        headers=config.HEADERS
    )

    if response_relacionados.status_code != 200:
        # Si falla, devolver registros con conteo 0
        for registro in registros:
            registro['total_count'] = 0
        return registros

    # Contar manualmente (en Python, rápido)
    conteos = {}
    for item in response_relacionados.json():
        id_relacion = item.get(campo_relacion)
        if id_relacion:
            conteos[id_relacion] = conteos.get(id_relacion, 0) + 1

    # Agregar conteos a registros principales
    for registro in registros:
        registro['total_count'] = conteos.get(registro['id'], 0)

    return registros
