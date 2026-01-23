"""
Servicio para envío de emails con Resend
"""
from datetime import datetime, timedelta
import requests
import resend
from config import config


def enviar_avisos_email(aviso_config):
    """
    Función que revisa fechas y envía emails de avisos

    Args:
        aviso_config: Diccionario con configuración de avisos
            - email_destinatario: emails separados por coma
            - primer_aviso_despues_ipo: días después de IPO para primer aviso
            - segundo_aviso_despues_ipo: días después de IPO para segundo aviso
            - dias_aviso_antes_contrato: días antes de vencimiento de contrato

    Returns:
        String con resultado del envío
    """

    if not config.RESEND_API_KEY:
        return "Error: No se ha configurado RESEND_API_KEY"

    # Procesar múltiples emails
    emails_raw = aviso_config['email_destinatario']
    emails_destino = [email.strip() for email in emails_raw.split(',')] if ',' in emails_raw else [emails_raw.strip()]
    primer_aviso_ipo = aviso_config['primer_aviso_despues_ipo']
    segundo_aviso_ipo = aviso_config['segundo_aviso_despues_ipo']
    dias_contrato = aviso_config['dias_aviso_antes_contrato']

    fecha_hoy = datetime.now().date()

    # Obtener equipos con IPO próxima
    equipos_response = requests.get(
        f"{config.SUPABASE_URL}/rest/v1/equipos?select=*,clientes(nombre_cliente,direccion)&ipo_proxima=not.is.null",
        headers=config.HEADERS
    )

    alertas_ipo_primer_aviso = []
    alertas_ipo_segundo_aviso = []
    alertas_contrato = []

    if equipos_response.status_code == 200:
        equipos = equipos_response.json()

        for equipo in equipos:
            # Revisar IPOs - SOLO DESPUÉS de la fecha
            if equipo.get('ipo_proxima'):
                try:
                    fecha_ipo = datetime.strptime(equipo['ipo_proxima'], '%Y-%m-%d').date()
                    dias_desde_ipo = (fecha_hoy - fecha_ipo).days

                    cliente = equipo.get('clientes', {})
                    if isinstance(cliente, list) and cliente:
                        cliente = cliente[0]

                    equipo_data = {
                        'cliente': cliente.get('nombre_cliente', 'Sin nombre') if cliente else 'Sin nombre',
                        'direccion': cliente.get('direccion', 'Sin dirección') if cliente else 'Sin dirección',
                        'identificacion': equipo.get('identificacion', 'N/A'),
                        'fecha': fecha_ipo.strftime('%d/%m/%Y'),
                        'dias_desde_ipo': dias_desde_ipo
                    }

                    # Primer aviso (ej: día 15)
                    if dias_desde_ipo == primer_aviso_ipo:
                        alertas_ipo_primer_aviso.append(equipo_data)

                    # Segundo aviso (ej: día 30)
                    if dias_desde_ipo == segundo_aviso_ipo:
                        alertas_ipo_segundo_aviso.append(equipo_data)

                except:
                    pass

            # Revisar contratos - X días ANTES del vencimiento
            if equipo.get('fecha_vencimiento_contrato'):
                try:
                    fecha_contrato = datetime.strptime(equipo['fecha_vencimiento_contrato'], '%Y-%m-%d').date()
                    dias_restantes = (fecha_contrato - fecha_hoy).days

                    if 0 <= dias_restantes <= dias_contrato:
                        cliente = equipo.get('clientes', {})
                        if isinstance(cliente, list) and cliente:
                            cliente = cliente[0]

                        alertas_contrato.append({
                            'cliente': cliente.get('nombre_cliente', 'Sin nombre') if cliente else 'Sin nombre',
                            'direccion': cliente.get('direccion', 'Sin dirección') if cliente else 'Sin dirección',
                            'identificacion': equipo.get('identificacion', 'N/A'),
                            'fecha': fecha_contrato.strftime('%d/%m/%Y'),
                            'dias_restantes': dias_restantes
                        })
                except:
                    pass

    # Si no hay alertas, no enviar email
    if not alertas_ipo_primer_aviso and not alertas_ipo_segundo_aviso and not alertas_contrato:
        return "No hay avisos pendientes"

    # Construir contenido del email
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Montserrat', Arial, sans-serif; background: white; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; }}
            h1 {{ color: #366092; border-bottom: 3px solid #366092; padding-bottom: 10px; }}
            h2 {{ color: #366092; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background: #366092; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .urgente {{ color: #dc3545; font-weight: bold; }}
            .proximo {{ color: #ffc107; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔔 Avisos AscensorAlert - Fedes Ascensores</h1>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
    """

    if alertas_ipo_primer_aviso:
        html_content += f"""
            <h2>🔍 IPOs - Primer Aviso ({primer_aviso_ipo} días después)</h2>
            <p style="color: #666;">Es momento de visitar para verificar la subsanación de defectos</p>
            <table>
                <tr>
                    <th>Cliente</th>
                    <th>Dirección</th>
                    <th>Equipo</th>
                    <th>Fecha IPO</th>
                    <th>Días Transcurridos</th>
                </tr>
        """
        for alerta in alertas_ipo_primer_aviso:
            html_content += f"""
                <tr>
                    <td>{alerta['cliente']}</td>
                    <td>{alerta['direccion']}</td>
                    <td>{alerta['identificacion']}</td>
                    <td>{alerta['fecha']}</td>
                    <td class="proximo">{alerta['dias_desde_ipo']} días</td>
                </tr>
            """
        html_content += "</table>"

    if alertas_ipo_segundo_aviso:
        html_content += f"""
            <h2>⚠️ IPOs - Segundo Aviso ({segundo_aviso_ipo} días después)</h2>
            <p style="color: #dc3545; font-weight: bold;">¡URGENTE! Últimos días para verificar subsanación</p>
            <table>
                <tr>
                    <th>Cliente</th>
                    <th>Dirección</th>
                    <th>Equipo</th>
                    <th>Fecha IPO</th>
                    <th>Días Transcurridos</th>
                </tr>
        """
        for alerta in alertas_ipo_segundo_aviso:
            html_content += f"""
                <tr>
                    <td>{alerta['cliente']}</td>
                    <td>{alerta['direccion']}</td>
                    <td>{alerta['identificacion']}</td>
                    <td>{alerta['fecha']}</td>
                    <td class="urgente">{alerta['dias_desde_ipo']} días</td>
                </tr>
            """
        html_content += "</table>"

    if alertas_contrato:
        html_content += """
            <h2>📋 Contratos por Vencer</h2>
            <table>
                <tr>
                    <th>Cliente</th>
                    <th>Dirección</th>
                    <th>Equipo</th>
                    <th>Vencimiento</th>
                    <th>Días Restantes</th>
                </tr>
        """
        for alerta in alertas_contrato:
            clase = 'urgente' if alerta['dias_restantes'] <= 15 else 'proximo'
            html_content += f"""
                <tr>
                    <td>{alerta['cliente']}</td>
                    <td>{alerta['direccion']}</td>
                    <td>{alerta['identificacion']}</td>
                    <td>{alerta['fecha']}</td>
                    <td class="{clase}">{alerta['dias_restantes']} días</td>
                </tr>
            """
        html_content += "</table>"

    html_content += """
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Este es un email automático generado por AscensorAlert.<br>
                Para gestionar tus alertas, accede a la configuración en la aplicación.
            </p>
        </div>
    </body>
    </html>
    """

    total_ipos = len(alertas_ipo_primer_aviso) + len(alertas_ipo_segundo_aviso)

    # Enviar email con Resend
    try:
        # Configurar API key
        resend.api_key = config.RESEND_API_KEY

        params = {
            "from": config.EMAIL_FROM,
            "to": emails_destino,
            "subject": f"🔔 Avisos AscensorAlert - {total_ipos} IPOs y {len(alertas_contrato)} Contratos",
            "html": html_content
        }

        email = resend.Emails.send(params)
        return f"Email enviado correctamente a {len(emails_destino)} destinatario(s): {total_ipos} IPOs, {len(alertas_contrato)} contratos"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"
