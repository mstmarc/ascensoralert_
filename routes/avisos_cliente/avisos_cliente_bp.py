"""
Blueprint de Avisos a Cliente

Sistema de notificaciones de parada de ascensores a clientes.
Permite a técnicos y gestores enviar emails informativos cuando
un ascensor queda fuera de servicio.

Funcionalidades:
- Buscar máquina por identificador o dirección
- Seleccionar motivo de parada predefinido
- Enviar email al cliente con copia a configuración
- Registro de todas las notificaciones enviadas
- Histórico de avisos por instalación
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import requests
import resend

from config import config
from helpers import login_required, requiere_permiso, tiene_permiso
from utils.messages import flash_success, flash_error

# Configuración de Supabase
SUPABASE_URL = config.SUPABASE_URL
HEADERS = config.HEADERS

# Crear Blueprint
avisos_cliente_bp = Blueprint('avisos_cliente', __name__, url_prefix='/avisos-cliente')


# ============================================
# RUTA PRINCIPAL: Enviar Aviso
# ============================================

@avisos_cliente_bp.route('/', methods=['GET'])
@login_required
@requiere_permiso('notificaciones_cliente', 'write')
def index():
    """Página principal para enviar avisos a clientes"""

    # Obtener motivos de parada activos
    motivos_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/motivos_parada?activo=eq.true&order=orden",
        headers=HEADERS
    )
    motivos = motivos_response.json() if motivos_response.status_code == 200 else []

    # Obtener nombre del usuario actual
    usuario_nombre = session.get('usuario', 'Técnico')

    return render_template(
        'avisos_cliente/enviar_aviso.html',
        motivos=motivos,
        usuario_nombre=usuario_nombre
    )


# ============================================
# API: Buscar Máquinas
# ============================================

@avisos_cliente_bp.route('/api/buscar-maquinas', methods=['GET'])
@login_required
@requiere_permiso('notificaciones_cliente', 'read')
def buscar_maquinas():
    """API para buscar máquinas por texto (identificador o dirección)"""

    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    # Buscar en vista de máquinas para notificación
    # Busca en identificador, código_maquina e instalación
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_maquinas_para_notificacion"
        f"?or=(identificador.ilike.*{query}*,codigo_maquina.ilike.*{query}*,instalacion_nombre.ilike.*{query}*,municipio.ilike.*{query}*)"
        f"&limit=20",
        headers=HEADERS
    )

    if response.status_code != 200:
        return jsonify([])

    maquinas = response.json()

    # Formatear resultados
    resultados = []
    for m in maquinas:
        resultados.append({
            'id': m.get('id'),
            'identificador': m.get('identificador', ''),
            'codigo': m.get('codigo_maquina', ''),
            'instalacion_id': m.get('instalacion_id'),
            'instalacion': m.get('instalacion_nombre', 'Sin instalación'),
            'municipio': m.get('municipio', ''),
            'email_contacto': m.get('email_contacto', ''),
            'nombre_contacto': m.get('nombre_contacto', ''),
            'tiene_email': bool(m.get('email_contacto'))
        })

    return jsonify(resultados)


# ============================================
# API: Enviar Aviso
# ============================================

@avisos_cliente_bp.route('/enviar', methods=['POST'])
@login_required
@requiere_permiso('notificaciones_cliente', 'write')
def enviar_aviso():
    """Envía el aviso por email y registra en base de datos"""

    # Obtener datos del formulario
    maquina_id = request.form.get('maquina_id')
    instalacion_id = request.form.get('instalacion_id')
    motivo_id = request.form.get('motivo_id')
    email_destino = request.form.get('email_destino', '').strip()
    nombre_destino = request.form.get('nombre_destino', '').strip()
    instalacion_nombre = request.form.get('instalacion_nombre', '').strip()

    # Validaciones básicas
    if not maquina_id or not motivo_id:
        flash_error('Faltan datos obligatorios')
        return redirect(url_for('avisos_cliente.index'))

    if not email_destino:
        flash_error('No hay email de contacto configurado para esta instalación')
        return redirect(url_for('avisos_cliente.index'))

    # Obtener datos del motivo
    motivo_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/motivos_parada?id=eq.{motivo_id}",
        headers=HEADERS
    )

    if motivo_response.status_code != 200 or not motivo_response.json():
        flash_error('Motivo no encontrado')
        return redirect(url_for('avisos_cliente.index'))

    motivo = motivo_response.json()[0]

    # Obtener configuración de notificaciones
    config_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/configuracion_notificaciones_cliente?limit=1",
        headers=HEADERS
    )

    config_notif = {}
    if config_response.status_code == 200 and config_response.json():
        config_notif = config_response.json()[0]

    email_copia = config_notif.get('email_copia', '')
    email_remitente = config_notif.get('email_remitente', 'avisos@fedes.es')
    nombre_remitente = config_notif.get('nombre_remitente', 'Fedes Ascensores')

    # Construir mensaje
    mensaje_html = construir_email_html(
        instalacion_nombre=instalacion_nombre,
        nombre_destino=nombre_destino,
        motivo_texto=motivo.get('mensaje_cliente', '')
    )

    mensaje_texto = construir_email_texto(
        instalacion_nombre=instalacion_nombre,
        nombre_destino=nombre_destino,
        motivo_texto=motivo.get('mensaje_cliente', '')
    )

    # Preparar destinatarios (cliente + copia)
    destinatarios = [email_destino]
    cc_emails = []
    if email_copia:
        cc_emails = [e.strip() for e in email_copia.split(',') if e.strip()]

    # Enviar email
    email_enviado = False
    error_envio = None

    try:
        params = {
            "from": f"{nombre_remitente} <{email_remitente}>",
            "to": destinatarios,
            "subject": f"Aviso - Ascensor fuera de servicio en {instalacion_nombre}",
            "html": mensaje_html,
            "text": mensaje_texto,
            "reply_to": email_remitente
        }

        if cc_emails:
            params["cc"] = cc_emails

        email_response = resend.Emails.send(params)

        if email_response and email_response.get('id'):
            email_enviado = True
        else:
            error_envio = "No se recibió confirmación del servidor de email"

    except Exception as e:
        error_envio = str(e)

    # Registrar en base de datos
    registro = {
        "maquina_id": int(maquina_id) if maquina_id else None,
        "instalacion_id": int(instalacion_id) if instalacion_id else None,
        "motivo_id": int(motivo_id),
        "motivo_texto": motivo.get('descripcion', ''),
        "mensaje_enviado": mensaje_texto,
        "email_destino": email_destino,
        "nombre_destino": nombre_destino or instalacion_nombre,
        "enviado_por_id": session.get('usuario_id'),
        "enviado_por_nombre": session.get('usuario', 'Sistema'),
        "estado": "ENVIADO" if email_enviado else "ERROR",
        "email_enviado": email_enviado,
        "error_envio": error_envio
    }

    requests.post(
        f"{SUPABASE_URL}/rest/v1/notificaciones_cliente",
        json=registro,
        headers=HEADERS
    )

    # Mostrar resultado
    if email_enviado:
        flash_success(f'Aviso enviado correctamente a {email_destino}')
    else:
        flash_error(f'Error al enviar el aviso: {error_envio}')

    return redirect(url_for('avisos_cliente.index'))


# ============================================
# HISTÓRICO DE AVISOS
# ============================================

@avisos_cliente_bp.route('/historico', methods=['GET'])
@login_required
@requiere_permiso('notificaciones_cliente', 'read')
def historico():
    """Muestra el histórico de avisos enviados"""

    # Obtener los últimos 50 avisos
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/notificaciones_cliente"
        f"?select=*,motivos_parada(descripcion),instalaciones(nombre,municipio)"
        f"&order=created_at.desc"
        f"&limit=50",
        headers=HEADERS
    )

    avisos = response.json() if response.status_code == 200 else []

    # Formatear fechas
    for aviso in avisos:
        if aviso.get('created_at'):
            try:
                fecha = datetime.fromisoformat(aviso['created_at'].replace('Z', '+00:00'))
                aviso['fecha_formateada'] = fecha.strftime('%d/%m/%Y %H:%M')
            except:
                aviso['fecha_formateada'] = aviso['created_at']

    return render_template('avisos_cliente/historico.html', avisos=avisos)


# ============================================
# CONFIGURACIÓN
# ============================================

@avisos_cliente_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@requiere_permiso('notificaciones_cliente', 'write')
def configuracion():
    """Configuración del sistema de avisos a clientes"""

    # Solo admin puede acceder a configuración
    if session.get('perfil') != 'admin':
        flash_error('Solo los administradores pueden acceder a la configuración')
        return redirect(url_for('avisos_cliente.index'))

    if request.method == 'POST':
        email_copia = request.form.get('email_copia', '').strip()
        email_remitente = request.form.get('email_remitente', 'avisos@fedes.es').strip()
        nombre_remitente = request.form.get('nombre_remitente', 'Fedes Ascensores').strip()

        # Verificar si existe configuración
        check = requests.get(
            f"{SUPABASE_URL}/rest/v1/configuracion_notificaciones_cliente?limit=1",
            headers=HEADERS
        )

        data = {
            "email_copia": email_copia,
            "email_remitente": email_remitente,
            "nombre_remitente": nombre_remitente,
            "updated_at": datetime.now().isoformat()
        }

        if check.status_code == 200 and check.json():
            # Actualizar
            config_id = check.json()[0]['id']
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/configuracion_notificaciones_cliente?id=eq.{config_id}",
                json=data,
                headers=HEADERS
            )
        else:
            # Insertar
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/configuracion_notificaciones_cliente",
                json=data,
                headers=HEADERS
            )

        if response.status_code in [200, 201, 204]:
            flash_success('Configuración guardada correctamente')
        else:
            flash_error(f'Error al guardar: {response.text}')

        return redirect(url_for('avisos_cliente.configuracion'))

    # GET - Mostrar formulario
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/configuracion_notificaciones_cliente?limit=1",
        headers=HEADERS
    )

    if response.status_code == 200 and response.json():
        config_data = response.json()[0]
    else:
        config_data = {
            'email_copia': '',
            'email_remitente': 'avisos@fedes.es',
            'nombre_remitente': 'Fedes Ascensores'
        }

    return render_template('avisos_cliente/configuracion.html', config=config_data)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def construir_email_html(instalacion_nombre, nombre_destino, motivo_texto):
    """Construye el HTML del email"""

    saludo = f"Estimado/a {nombre_destino}:" if nombre_destino else "Estimado cliente:"

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border-bottom: 2px solid #003366;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .content {{
            padding: 20px 0;
        }}
        .footer {{
            border-top: 1px solid #e6e6e6;
            padding-top: 15px;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }}
        .highlight {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 3px solid #003366;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <strong style="color: #003366; font-size: 18px;">Fedes Ascensores</strong>
    </div>

    <div class="content">
        <p>{saludo}</p>

        <p>Le informamos que el ascensor en <strong>{instalacion_nombre}</strong>
        ha quedado temporalmente fuera de servicio, {motivo_texto}.</p>

        <div class="highlight">
            <p style="margin: 0;">Disculpe las molestias ocasionadas.</p>
        </div>

        <p>Para cualquier consulta puede responder a este email.</p>
    </div>

    <div class="footer">
        <p>Atentamente,<br>
        <strong>Fedes Ascensores</strong></p>
    </div>
</body>
</html>
"""


def construir_email_texto(instalacion_nombre, nombre_destino, motivo_texto):
    """Construye la versión texto plano del email"""

    saludo = f"Estimado/a {nombre_destino}:" if nombre_destino else "Estimado cliente:"

    return f"""{saludo}

Le informamos que el ascensor en {instalacion_nombre} ha quedado temporalmente fuera de servicio, {motivo_texto}.

Disculpe las molestias ocasionadas.

Para cualquier consulta puede responder a este email.

Atentamente,
Fedes Ascensores
"""
