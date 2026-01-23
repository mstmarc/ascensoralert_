"""
Blueprint de Inspecciones - Ejemplo de migración modular
NOTA: Este es un ejemplo de cómo migrar a Blueprints.
      El resto de rutas permanecen en app_legacy.py por compatibilidad.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date, timedelta
import requests
import helpers
from config import config

# Crear Blueprint
inspecciones_bp = Blueprint(
    'inspecciones',
    __name__,
    url_prefix='/inspecciones'  # Todas las rutas empiezan con /inspecciones
)


# ============================================
# EJEMPLO: Dashboard de Inspecciones
# ============================================

@inspecciones_bp.route('/')  # Equivalente a /inspecciones
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def dashboard():
    """
    Dashboard principal de inspecciones con alertas y estados

    NOTA: Esta es una versión simplificada para demostrar el patrón de Blueprint.
          La versión completa está en app_legacy.py
    """

    # Obtener todas las inspecciones con información del OCA
    response = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/inspecciones?select=*,oca:ocas(nombre)&order=fecha_inspeccion.desc&limit=50",
        headers=config.HEADERS
    )

    inspecciones = []
    if response.status_code == 200:
        inspecciones = response.json()

    # Calcular alertas (versión simplificada)
    hoy = date.today()
    alertas_criticas = []
    alertas_urgentes = []
    alertas_proximas = []

    for inspeccion in inspecciones:
        if inspeccion.get('fecha_segunda_realizada'):
            continue  # Ya completada

        if inspeccion.get('fecha_segunda_inspeccion'):
            try:
                fecha_limite = datetime.strptime(
                    inspeccion['fecha_segunda_inspeccion'].split('T')[0],
                    '%Y-%m-%d'
                ).date()
                dias_restantes = (fecha_limite - hoy).days
                inspeccion['dias_hasta_segunda'] = dias_restantes

                if fecha_limite < hoy:
                    alertas_criticas.append(('defectos', inspeccion))
                elif dias_restantes <= 30:
                    alertas_urgentes.append(('defectos', inspeccion))
                elif dias_restantes <= 60:
                    alertas_proximas.append(('defectos', inspeccion))
            except:
                pass

    # Obtener OCAs para filtros
    response_ocas = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/ocas?select=id,nombre&activo=eq.true&order=nombre.asc",
        headers=config.HEADERS
    )
    ocas = response_ocas.json() if response_ocas.status_code == 200 else []

    return render_template(
        "inspecciones_dashboard.html",
        inspecciones=inspecciones[:20],  # Mostrar solo las primeras 20
        alertas_criticas=alertas_criticas,
        alertas_urgentes=alertas_urgentes,
        alertas_proximas=alertas_proximas,
        ocas=ocas
    )


# ============================================
# NOTA SOBRE MIGRACIÓN COMPLETA
# ============================================
"""
Para migrar completamente el módulo de inspecciones:

1. Mover todas las rutas de app_legacy.py a este Blueprint
2. Actualizar las rutas internas (url_for('inspecciones.dashboard') en lugar de url_for('inspecciones_dashboard'))
3. Actualizar los templates para usar el nuevo namespace
4. Hacer lo mismo con defectos.py y ocas.py

Por ahora, este Blueprint coexiste con app_legacy.py como demostración del patrón.
La ruta completa /inspecciones sigue funcionando desde app_legacy.py
"""
