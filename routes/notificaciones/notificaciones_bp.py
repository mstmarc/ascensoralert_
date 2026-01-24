"""
Blueprint de Notificaciones

Sistema de notificaciones automáticas con funcionalidades de:
- Configuración de avisos por email
- Avisos de IPOs próximas (15 y 30 días después)
- Avisos de contratos próximos a vencer
- Ejecución manual de envío de avisos
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
import requests

from config import config
from utils.messages import flash_success, flash_error

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint
notificaciones_bp = Blueprint('notificaciones', __name__)


@notificaciones_bp.route('/configuracion_avisos', methods=["GET", "POST"])
def configuracion_avisos():
    """Configurar sistema de avisos automáticos por email"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('usuario_id')

    if request.method == 'POST':
        email = request.form.get('email_destinatario')
        primer_aviso = request.form.get('primer_aviso_despues_ipo')
        segundo_aviso = request.form.get('segundo_aviso_despues_ipo')
        dias_contratos = request.form.get('dias_aviso_antes_contrato')
        sistema_activo = request.form.get('sistema_activo') == 'on'
        frecuencia = request.form.get('frecuencia_chequeo')

        # Verificar si ya existe configuración
        config_check = requests.get(
            f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{user_id}",
            headers=HEADERS
        )

        data = {
            "email_destinatario": email,
            "primer_aviso_despues_ipo": primer_aviso,
            "segundo_aviso_despues_ipo": segundo_aviso,
            "dias_aviso_antes_contrato": dias_contratos,
            "sistema_activo": sistema_activo,
            "frecuencia_chequeo": frecuencia
        }

        if config_check.status_code == 200 and config_check.json():
            # Actualizar
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{user_id}",
                json=data,
                headers=HEADERS
            )
        else:
            # Insertar
            data["usuario_id"] = user_id
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/configuracion_avisos",
                json=data,
                headers=HEADERS
            )

        if response.status_code in [200, 201, 204]:
            flash_success('✅ Configuración guardada correctamente')
        else:
            flash_error(f'❌ Error al guardar configuración: {response.text}')

        return redirect(url_for('notificaciones.configuracion_avisos'))

    # GET - Mostrar formulario
    config_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{user_id}",
        headers=HEADERS
    )

    if config_response.status_code == 200 and config_response.json():
        config_data = config_response.json()[0]

        # Formatear fecha si existe
        if config_data.get('ultima_ejecucion'):
            try:
                fecha_obj = datetime.fromisoformat(config_data['ultima_ejecucion'].replace('Z', '+00:00'))
                config_data['ultima_ejecucion'] = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except:
                pass
    else:
        # Valores por defecto
        config_data = {
            'email_destinatario': session.get('email', ''),
            'primer_aviso_despues_ipo': 15,
            'segundo_aviso_despues_ipo': 30,
            'dias_aviso_antes_contrato': 30,
            'sistema_activo': True,
            'frecuencia_chequeo': 'diario',
            'ultima_ejecucion': None
        }

    return render_template('configuracion_avisos.html', config=config_data)


@notificaciones_bp.route('/enviar_avisos_manual')
def enviar_avisos_manual():
    """Enviar avisos por email manualmente (ejecución inmediata)"""
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario_id = session.get("usuario_id")

    # Obtener configuración del usuario
    config = requests.get(
        f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
        headers=HEADERS
    )

    if config.status_code != 200 or not config.json():
        return "No hay configuración de avisos", 400

    config_data = config.json()[0]

    if not config_data.get('sistema_activo'):
        return "Las notificaciones están desactivadas", 400

    # Importar función de envío de avisos desde app_legacy
    from app_legacy import enviar_avisos_email

    # Enviar avisos
    resultado = enviar_avisos_email(config_data)

    # Actualizar última ejecución
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
        json={"ultima_ejecucion": datetime.now().isoformat()},
        headers=HEADERS
    )

    return f"<h3>{resultado}</h3><br><a href='/home'>Volver al inicio</a>"
