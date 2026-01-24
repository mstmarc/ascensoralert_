"""
AscensorAlert - Aplicación Flask Refactorizada
==================================================
Versión modularizada con servicios separados para mejor mantenibilidad
"""
from flask import Flask
import os
import resend
import helpers
from config import config
from utils.formatters import format_fecha_filter
from services import cache_service

# ============================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Configurar Resend para emails
if config.RESEND_API_KEY:
    resend.api_key = config.RESEND_API_KEY

# Inicializar helpers con configuración
helpers.init_helpers(config.SUPABASE_URL, config.HEADERS)

# ============================================
# FILTROS Y PROCESADORES DE CONTEXTO JINJA2
# ============================================

# Registrar filtro personalizado para formatear fechas
app.template_filter('format_fecha')(format_fecha_filter)

# Inyectar funciones de permisos en todos los templates
@app.context_processor
def inject_permisos():
    """Inyecta funciones de control de acceso en todos los templates"""
    import json

    # Obtener perfil del usuario actual
    perfil_actual = helpers.obtener_perfil_usuario()

    # Construir diccionario de permisos para JavaScript
    permisos_js = {}
    if perfil_actual in helpers.PERMISOS_POR_PERFIL:
        for modulo, permisos in helpers.PERMISOS_POR_PERFIL[perfil_actual].items():
            permisos_js[modulo] = permisos

    return {
        'tiene_permiso': helpers.tiene_permiso,
        'puede_escribir': helpers.puede_escribir,
        'puede_eliminar': helpers.puede_eliminar,
        'obtener_perfil_usuario': helpers.obtener_perfil_usuario,
        'obtener_modulos_permitidos': helpers.obtener_modulos_permitidos,
        'perfil_usuario': perfil_actual,
        'permisos_usuario_json': json.dumps(permisos_js)
    }

# ============================================
# IMPORTAR TODAS LAS RUTAS DEL LEGACY APP
# ============================================
# NOTA: Esto permite mantener la funcionalidad completa mientras
# gradualmente migramos a blueprints en futuras iteraciones

from app_legacy import (
    # Autenticación y Home
    login, logout, home,

    # Leads y Clientes - MIGRADAS A BLUEPRINT (ver routes/leads/leads_bp.py)
    # formulario_lead, leads_dashboard, exportar_leads, ver_lead,
    # eliminar_lead, editar_lead,

    # Equipos
    nuevo_equipo, ver_equipo, eliminar_equipo, editar_equipo,

    # Visitas
    visita_administrador, visitas_administradores_dashboard,
    ver_visita_admin, editar_visita_admin, eliminar_visita_admin,
    crear_visita_seguimiento,

    # Reportes
    reporte_mensual,

    # Oportunidades
    oportunidades, mi_agenda, cambiar_estado_oportunidad,
    crear_oportunidad, editar_oportunidad, ver_oportunidad,
    eliminar_oportunidad, oportunidades_post_ipo,

    # Acciones de Oportunidades
    add_accion, toggle_accion, delete_accion,

    # Tareas Comerciales
    tarea_comercial_aplazar, tarea_comercial_descartar,
    tarea_comercial_convertir, tarea_comercial_agregar_nota,

    # Acciones de Equipos
    add_accion_equipo, toggle_accion_equipo, delete_accion_equipo,

    # Notificaciones
    configuracion_avisos, enviar_avisos_manual,

    # Administradores - MIGRADAS A BLUEPRINT (ver routes/admin/admin_bp.py)
    # administradores_dashboard, nuevo_administrador, ver_administrador,
    # editar_administrador, eliminar_administrador,
    test_dropdown_admin,  # clear_cache migrado a Blueprint

    # Inspecciones e IPOs
    inspecciones_dashboard, nueva_inspeccion, ver_inspeccion,
    editar_inspeccion, cambiar_estado_presupuesto,
    marcar_segunda_realizada, subir_acta_pdf, subir_presupuesto_pdf,
    eliminar_inspeccion, extraer_defectos_pdf, guardar_defectos_importados,

    # Defectos
    defectos_dashboard, exportar_defectos_pdf, nuevo_defecto,
    subsanar_defecto, revertir_defecto, eliminar_defecto,
    ver_defecto, editar_defecto, actualizar_gestion_defecto,

    # OCAs - MIGRADAS A BLUEPRINT (ver routes/ocas/ocas_bp.py)
    # lista_ocas, nuevo_oca, editar_oca, eliminar_oca,

    # Administración de Usuarios - MIGRADAS A BLUEPRINT (ver routes/admin/admin_bp.py)
    # admin_usuarios, admin_crear_usuario, admin_editar_usuario,
    # admin_eliminar_usuario,

    # Cartera
    cartera_dashboard, cartera_importar, cartera_importar_equipos,
    cartera_importar_partes, cartera_reanalizar_recomendaciones,
    cartera_oportunidades, cartera_crear_oportunidad,
    cartera_descartar_recomendacion, cartera_ver_oportunidad,
    cartera_actualizar_oportunidad, cartera_ver_maquina,
    cartera_ver_instalacion, cartera_dar_baja_instalacion,
    cartera_reactivar_instalacion,

    # Cartera V2 - Alertas
    cartera_dashboard_v2, ejecutar_detectores_alertas,
    ver_todas_alertas, ver_detalle_alerta, resolver_alerta,
    ver_pendientes_tecnicos, actualizar_pendiente_tecnico,
    crear_trabajo_desde_alerta,

    # Sistema de IA Predictiva
    dashboard_ia_predictiva, priorizar_recomendaciones_ia,
    prediccion_maquina_ia, patrones_tendencias_ia,
    roi_optimizacion_ia, analizar_parte_ia, analizar_lote_ia,
    ver_prediccion_maquina, generar_prediccion_ia,
    listar_alertas_ia, ver_alerta_ia, resolver_alerta_ia,
    ver_componentes_criticos, ver_metricas_ia,
    mostrar_ejecutar_analisis, ejecutar_analisis_web,
    estado_analisis, api_generar_predicciones_ia,

    # Funciones auxiliares que se usan en templates
    limpiar_none, calcular_color_ipo, calcular_color_contrato,
)

# ============================================
# REGISTRAR LAS RUTAS EN LA APP
# ============================================

# Autenticación y Home
app.add_url_rule("/", "login", login, methods=["GET", "POST"])
app.add_url_rule("/logout", "logout", logout)
app.add_url_rule("/home", "home", home)

# Leads y Clientes - MIGRADAS A BLUEPRINT (ver routes/leads/leads_bp.py)
# app.add_url_rule("/formulario_lead", "formulario_lead", formulario_lead, methods=["GET", "POST"])
# app.add_url_rule("/leads_dashboard", "leads_dashboard", leads_dashboard)
# app.add_url_rule("/exportar_leads", "exportar_leads", exportar_leads)
# app.add_url_rule("/ver_lead/<int:lead_id>", "ver_lead", ver_lead)
# app.add_url_rule("/eliminar_lead/<int:lead_id>", "eliminar_lead", eliminar_lead)
# app.add_url_rule("/editar_lead/<int:lead_id>", "editar_lead", editar_lead, methods=["GET", "POST"])

# Equipos
app.add_url_rule("/nuevo_equipo", "nuevo_equipo", nuevo_equipo, methods=["GET", "POST"])
app.add_url_rule("/ver_equipo/<int:equipo_id>", "ver_equipo", ver_equipo)
app.add_url_rule("/eliminar_equipo/<int:equipo_id>", "eliminar_equipo", eliminar_equipo)
app.add_url_rule("/editar_equipo/<int:equipo_id>", "editar_equipo", editar_equipo, methods=["GET", "POST"])

# Visitas
app.add_url_rule("/visita_administrador", "visita_administrador", visita_administrador, methods=["GET", "POST"])
app.add_url_rule("/visitas_administradores_dashboard", "visitas_administradores_dashboard", visitas_administradores_dashboard)
app.add_url_rule("/ver_visita_admin/<int:visita_id>", "ver_visita_admin", ver_visita_admin)
app.add_url_rule("/editar_visita_admin/<int:visita_id>", "editar_visita_admin", editar_visita_admin, methods=["GET", "POST"])
app.add_url_rule("/eliminar_visita_admin/<int:visita_id>", "eliminar_visita_admin", eliminar_visita_admin)
app.add_url_rule("/crear_visita_seguimiento/<int:cliente_id>", "crear_visita_seguimiento", crear_visita_seguimiento, methods=["GET", "POST"])

# Reportes
app.add_url_rule("/reporte_mensual", "reporte_mensual", reporte_mensual, methods=["GET", "POST"])

# Oportunidades
app.add_url_rule("/oportunidades", "oportunidades", oportunidades)
app.add_url_rule("/mi_agenda", "mi_agenda", mi_agenda)
app.add_url_rule("/cambiar_estado_oportunidad/<int:oportunidad_id>", "cambiar_estado_oportunidad", cambiar_estado_oportunidad, methods=["POST"])
app.add_url_rule("/crear_oportunidad/<int:cliente_id>", "crear_oportunidad", crear_oportunidad, methods=["GET", "POST"])
app.add_url_rule("/editar_oportunidad/<int:oportunidad_id>", "editar_oportunidad", editar_oportunidad, methods=["GET", "POST"])
app.add_url_rule("/ver_oportunidad/<int:oportunidad_id>", "ver_oportunidad", ver_oportunidad)
app.add_url_rule("/eliminar_oportunidad/<int:oportunidad_id>", "eliminar_oportunidad", eliminar_oportunidad)
app.add_url_rule("/oportunidades_post_ipo", "oportunidades_post_ipo", oportunidades_post_ipo)

# Acciones de Oportunidades
app.add_url_rule("/oportunidad/<int:oportunidad_id>/accion/add", "add_accion", add_accion, methods=["POST"])
app.add_url_rule("/oportunidad/<int:oportunidad_id>/accion/toggle/<int:index>", "toggle_accion", toggle_accion, methods=["POST"])
app.add_url_rule("/oportunidad/<int:oportunidad_id>/accion/delete/<int:index>", "delete_accion", delete_accion, methods=["POST"])

# Tareas Comerciales
app.add_url_rule("/tarea_comercial_aplazar/<int:cliente_id>", "tarea_comercial_aplazar", tarea_comercial_aplazar, methods=["POST"])
app.add_url_rule("/tarea_comercial_descartar/<int:cliente_id>", "tarea_comercial_descartar", tarea_comercial_descartar, methods=["POST"])
app.add_url_rule("/tarea_comercial_convertir/<int:cliente_id>", "tarea_comercial_convertir", tarea_comercial_convertir, methods=["POST"])
app.add_url_rule("/tarea_comercial_agregar_nota/<int:cliente_id>", "tarea_comercial_agregar_nota", tarea_comercial_agregar_nota, methods=["POST"])

# Acciones de Equipos
app.add_url_rule("/equipo/<int:equipo_id>/accion/add", "add_accion_equipo", add_accion_equipo, methods=["POST"])
app.add_url_rule("/equipo/<int:equipo_id>/accion/toggle/<int:index>", "toggle_accion_equipo", toggle_accion_equipo, methods=["POST"])
app.add_url_rule("/equipo/<int:equipo_id>/accion/delete/<int:index>", "delete_accion_equipo", delete_accion_equipo, methods=["POST"])

# Notificaciones
app.add_url_rule("/configuracion_avisos", "configuracion_avisos", configuracion_avisos, methods=["GET", "POST"])
app.add_url_rule("/enviar_avisos_manual", "enviar_avisos_manual", enviar_avisos_manual)

# Administradores - MIGRADAS A BLUEPRINT (ver routes/admin/admin_bp.py)
# app.add_url_rule("/administradores_dashboard", "administradores_dashboard", administradores_dashboard)
# app.add_url_rule("/nuevo_administrador", "nuevo_administrador", nuevo_administrador, methods=["GET", "POST"])
# app.add_url_rule("/ver_administrador/<int:admin_id>", "ver_administrador", ver_administrador)
# app.add_url_rule("/editar_administrador/<int:admin_id>", "editar_administrador", editar_administrador, methods=["GET", "POST"])
# app.add_url_rule("/eliminar_administrador/<int:admin_id>", "eliminar_administrador", eliminar_administrador)
app.add_url_rule("/test_dropdown_admin", "test_dropdown_admin", test_dropdown_admin)
# app.add_url_rule("/admin/clear_cache", "clear_cache", clear_cache)  # Migrado a Blueprint

# Inspecciones e IPOs
app.add_url_rule("/inspecciones", "inspecciones_dashboard", inspecciones_dashboard)
app.add_url_rule("/inspecciones/nueva", "nueva_inspeccion", nueva_inspeccion, methods=["GET", "POST"])
app.add_url_rule("/inspecciones/ver/<int:inspeccion_id>", "ver_inspeccion", ver_inspeccion)
app.add_url_rule("/inspecciones/editar/<int:inspeccion_id>", "editar_inspeccion", editar_inspeccion, methods=["GET", "POST"])
app.add_url_rule("/inspecciones/estado_presupuesto/<int:inspeccion_id>", "cambiar_estado_presupuesto", cambiar_estado_presupuesto, methods=["POST"])
app.add_url_rule("/inspecciones/marcar_segunda_realizada/<int:inspeccion_id>", "marcar_segunda_realizada", marcar_segunda_realizada, methods=["POST"])
app.add_url_rule("/inspecciones/<int:inspeccion_id>/subir_acta", "subir_acta_pdf", subir_acta_pdf, methods=["POST"])
app.add_url_rule("/inspecciones/<int:inspeccion_id>/subir_presupuesto", "subir_presupuesto_pdf", subir_presupuesto_pdf, methods=["POST"])
app.add_url_rule("/inspecciones/eliminar/<int:inspeccion_id>", "eliminar_inspeccion", eliminar_inspeccion)
app.add_url_rule("/inspecciones/<int:inspeccion_id>/extraer_defectos_pdf", "extraer_defectos_pdf", extraer_defectos_pdf, methods=["POST"])
app.add_url_rule("/inspecciones/<int:inspeccion_id>/guardar_defectos_importados", "guardar_defectos_importados", guardar_defectos_importados, methods=["POST"])

# Defectos
app.add_url_rule("/defectos_dashboard", "defectos_dashboard", defectos_dashboard)
app.add_url_rule("/exportar_defectos_pdf", "exportar_defectos_pdf", exportar_defectos_pdf)
app.add_url_rule("/inspecciones/<int:inspeccion_id>/defectos/nuevo", "nuevo_defecto", nuevo_defecto, methods=["GET", "POST"])
app.add_url_rule("/defectos/<int:defecto_id>/subsanar", "subsanar_defecto", subsanar_defecto, methods=["POST"])
app.add_url_rule("/defectos/<int:defecto_id>/revertir", "revertir_defecto", revertir_defecto, methods=["POST"])
app.add_url_rule("/defectos/<int:defecto_id>/eliminar", "eliminar_defecto", eliminar_defecto)
app.add_url_rule("/defectos/<int:defecto_id>", "ver_defecto", ver_defecto)
app.add_url_rule("/defectos/<int:defecto_id>/editar", "editar_defecto", editar_defecto, methods=["GET", "POST"])
app.add_url_rule("/defectos/<int:defecto_id>/actualizar_gestion", "actualizar_gestion_defecto", actualizar_gestion_defecto, methods=["POST"])

# OCAs - MIGRADAS A BLUEPRINT (ver routes/ocas/ocas_bp.py)
# Las rutas de OCAs ahora se registran automáticamente via Blueprint

# Administración de Usuarios - MIGRADAS A BLUEPRINT (ver routes/admin/admin_bp.py)
# app.add_url_rule("/admin/usuarios", "admin_usuarios", admin_usuarios)
# app.add_url_rule("/admin/usuarios/crear", "admin_crear_usuario", admin_crear_usuario, methods=["POST"])
# app.add_url_rule("/admin/usuarios/editar/<int:usuario_id>", "admin_editar_usuario", admin_editar_usuario, methods=["POST"])
# app.add_url_rule("/admin/usuarios/eliminar/<int:usuario_id>", "admin_eliminar_usuario", admin_eliminar_usuario)

# Cartera
app.add_url_rule("/cartera", "cartera_dashboard", cartera_dashboard)
app.add_url_rule("/cartera/importar", "cartera_importar", cartera_importar)
app.add_url_rule("/cartera/importar_equipos", "cartera_importar_equipos", cartera_importar_equipos, methods=["POST"])
app.add_url_rule("/cartera/importar_partes", "cartera_importar_partes", cartera_importar_partes, methods=["POST"])
app.add_url_rule("/cartera/reanalizar-recomendaciones", "cartera_reanalizar_recomendaciones", cartera_reanalizar_recomendaciones, methods=["POST"])
app.add_url_rule("/cartera/oportunidades", "cartera_oportunidades", cartera_oportunidades)
app.add_url_rule("/cartera/oportunidades/crear/<int:maquina_id>", "cartera_crear_oportunidad", cartera_crear_oportunidad, methods=["GET", "POST"])
app.add_url_rule("/cartera/recomendaciones/<int:recomendacion_id>/descartar", "cartera_descartar_recomendacion", cartera_descartar_recomendacion, methods=["POST"])
app.add_url_rule("/cartera/oportunidades/<int:oportunidad_id>", "cartera_ver_oportunidad", cartera_ver_oportunidad)
app.add_url_rule("/cartera/oportunidades/<int:oportunidad_id>/actualizar", "cartera_actualizar_oportunidad", cartera_actualizar_oportunidad, methods=["POST"])
app.add_url_rule("/cartera/maquina/<int:maquina_id>", "cartera_ver_maquina", cartera_ver_maquina)
app.add_url_rule("/cartera/instalacion/<int:instalacion_id>", "cartera_ver_instalacion", cartera_ver_instalacion)
app.add_url_rule("/cartera/instalacion/<int:instalacion_id>/dar-baja", "cartera_dar_baja_instalacion", cartera_dar_baja_instalacion, methods=["POST"])
app.add_url_rule("/cartera/instalacion/<int:instalacion_id>/reactivar", "cartera_reactivar_instalacion", cartera_reactivar_instalacion, methods=["POST"])

# Cartera V2 - Alertas
app.add_url_rule("/cartera/v2", "cartera_dashboard_v2", cartera_dashboard_v2)
app.add_url_rule("/cartera/v2/ejecutar-detectores", "ejecutar_detectores_alertas", ejecutar_detectores_alertas, methods=["POST"])
app.add_url_rule("/cartera/v2/alertas", "ver_todas_alertas", ver_todas_alertas)
app.add_url_rule("/cartera/v2/alerta/<int:alerta_id>", "ver_detalle_alerta", ver_detalle_alerta)
app.add_url_rule("/cartera/v2/alerta/<int:alerta_id>/resolver", "resolver_alerta", resolver_alerta, methods=["POST"])
app.add_url_rule("/cartera/v2/pendientes-tecnicos", "ver_pendientes_tecnicos", ver_pendientes_tecnicos)
app.add_url_rule("/cartera/v2/pendiente/<int:pendiente_id>/actualizar", "actualizar_pendiente_tecnico", actualizar_pendiente_tecnico, methods=["POST"])
app.add_url_rule("/cartera/v2/alerta/<int:alerta_id>/crear-trabajo-tecnico", "crear_trabajo_desde_alerta", crear_trabajo_desde_alerta, methods=["POST"])

# Sistema de IA Predictiva
app.add_url_rule("/cartera/ia", "dashboard_ia_predictiva", dashboard_ia_predictiva)
app.add_url_rule("/cartera/ia/priorizar-recomendaciones", "priorizar_recomendaciones_ia", priorizar_recomendaciones_ia)
app.add_url_rule("/cartera/ia/maquina/<int:maquina_id>", "prediccion_maquina_ia", prediccion_maquina_ia)
app.add_url_rule("/cartera/ia/patrones", "patrones_tendencias_ia", patrones_tendencias_ia)
app.add_url_rule("/cartera/ia/roi", "roi_optimizacion_ia", roi_optimizacion_ia)
app.add_url_rule("/cartera/ia/analizar-parte/<int:parte_id>", "analizar_parte_ia", analizar_parte_ia, methods=["POST"])
app.add_url_rule("/cartera/ia/analizar-lote", "analizar_lote_ia", analizar_lote_ia, methods=["POST"])
app.add_url_rule("/cartera/ia/prediccion/<int:prediccion_id>", "ver_prediccion_maquina", ver_prediccion_maquina)
app.add_url_rule("/cartera/ia/generar-prediccion/<int:maquina_id>", "generar_prediccion_ia", generar_prediccion_ia, methods=["POST"])
app.add_url_rule("/cartera/ia/alertas", "listar_alertas_ia", listar_alertas_ia)
app.add_url_rule("/cartera/ia/alerta/<int:alerta_id>", "ver_alerta_ia", ver_alerta_ia)
app.add_url_rule("/cartera/ia/alerta/<int:alerta_id>/resolver", "resolver_alerta_ia", resolver_alerta_ia, methods=["POST"])
app.add_url_rule("/cartera/ia/componentes", "ver_componentes_criticos", ver_componentes_criticos)
app.add_url_rule("/cartera/ia/metricas", "ver_metricas_ia", ver_metricas_ia)
app.add_url_rule("/cartera/ia/ejecutar", "mostrar_ejecutar_analisis", mostrar_ejecutar_analisis)
app.add_url_rule("/cartera/ia/ejecutar-analisis-2025", "ejecutar_analisis_web", ejecutar_analisis_web, methods=["POST"])
app.add_url_rule("/cartera/ia/estado-analisis", "estado_analisis", estado_analisis)
app.add_url_rule("/cartera/ia/api/generar-predicciones", "api_generar_predicciones_ia", api_generar_predicciones_ia, methods=["POST"])

# ============================================
# REGISTRAR BLUEPRINTS
# ============================================

# Blueprint de OCAs (primer módulo migrado)
from routes.ocas import ocas_bp
app.register_blueprint(ocas_bp)

# Blueprint de Administradores y Usuarios (segundo módulo migrado)
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Blueprint de Leads/Clientes (tercer módulo migrado)
from routes.leads import leads_bp
app.register_blueprint(leads_bp)

# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == "__main__":
    # Render requiere escuchar en 0.0.0.0 (todas las interfaces)
    # y usar el puerto de la variable de entorno PORT
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_ENV") == "development"

    app.run(
        host='0.0.0.0',  # CRÍTICO: Necesario para Render
        port=port,
        debug=debug
    )
