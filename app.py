from flask import Flask, request, render_template, redirect, session, Response, url_for, flash
import requests
import os
import urllib.parse
from datetime import date, datetime, timedelta
import calendar
import io
import resend

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# Datos de Supabase
SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY environment variable is not set")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Configuración de Resend para emails
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# FUNCIONES AUXILIARES
def calcular_color_ipo(fecha_ipo_str):
    """Calcula el color de fondo para la celda de IPO según la urgencia"""
    if not fecha_ipo_str or fecha_ipo_str == "-":
        return ""
    
    try:
        fecha_ipo = datetime.strptime(fecha_ipo_str, "%d/%m/%Y")
        hoy = datetime.now()
        diferencia = (fecha_ipo - hoy).days
        
        if -15 <= diferencia < 0:
            return "background-color: #FFF59D;"
        
        if diferencia >= 0 and diferencia <= 30:
            return "background-color: #FFCDD2;"
        
        return ""
    except:
        return ""

def calcular_color_contrato(fecha_contrato_str):
    """Calcula el color de fondo para la celda de contrato según vencimiento"""
    if not fecha_contrato_str or fecha_contrato_str == "-":
        return ""
    
    try:
        fecha_contrato = datetime.strptime(fecha_contrato_str, "%d/%m/%Y")
        hoy = datetime.now()
        diferencia = (fecha_contrato - hoy).days
        
        if diferencia <= 30:
            return "background-color: #FFCDD2;"
        
        if 30 < diferencia <= 90:
            return "background-color: #FFF59D;"
        
        return ""
    except:
        return ""

def enviar_avisos_email(config):
    """Función que revisa fechas y envía emails"""
    
    if not RESEND_API_KEY:
        return "Error: No se ha configurado RESEND_API_KEY"
    
    email_destino = config['email_destino']
    dias_ipo = config['dias_anticipacion_ipo']
    dias_contrato = config['dias_anticipacion_contrato']
    
    fecha_limite_ipo = (datetime.now() + timedelta(days=dias_ipo)).date().isoformat()
    fecha_limite_contrato = (datetime.now() + timedelta(days=dias_contrato)).date().isoformat()
    fecha_hoy = datetime.now().date().isoformat()
    
    # Obtener equipos con IPO próxima
    equipos_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=*,clientes(nombre_cliente,direccion)&ipo_proxima=not.is.null",
        headers=HEADERS
    )
    
    alertas_ipo = []
    alertas_contrato = []
    
    if equipos_response.status_code == 200:
        equipos = equipos_response.json()
        
        for equipo in equipos:
            # Revisar IPOs
            if equipo.get('ipo_proxima'):
                try:
                    fecha_ipo = datetime.strptime(equipo['ipo_proxima'], '%Y-%m-%d').date()
                    dias_restantes = (fecha_ipo - datetime.now().date()).days
                    
                    if 0 <= dias_restantes <= dias_ipo:
                        cliente = equipo.get('clientes', {})
                        if isinstance(cliente, list) and cliente:
                            cliente = cliente[0]
                        
                        alertas_ipo.append({
                            'cliente': cliente.get('nombre_cliente', 'Sin nombre') if cliente else 'Sin nombre',
                            'direccion': cliente.get('direccion', 'Sin dirección') if cliente else 'Sin dirección',
                            'identificacion': equipo.get('identificacion', 'N/A'),
                            'fecha': fecha_ipo.strftime('%d/%m/%Y'),
                            'dias_restantes': dias_restantes
                        })
                except:
                    pass
            
            # Revisar contratos
            if equipo.get('fecha_vencimiento_contrato'):
                try:
                    fecha_contrato = datetime.strptime(equipo['fecha_vencimiento_contrato'], '%Y-%m-%d').date()
                    dias_restantes = (fecha_contrato - datetime.now().date()).days
                    
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
    if not alertas_ipo and not alertas_contrato:
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
    
    if alertas_ipo:
        html_content += """
            <h2>🔍 IPOs Próximas</h2>
            <table>
                <tr>
                    <th>Cliente</th>
                    <th>Dirección</th>
                    <th>Equipo</th>
                    <th>Fecha IPO</th>
                    <th>Días Restantes</th>
                </tr>
        """
        for alerta in alertas_ipo:
            clase = 'urgente' if alerta['dias_restantes'] <= 7 else 'proximo'
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
    
    # Enviar email con Resend
    try:
        params = {
            "from": EMAIL_FROM,
            "to": [email_destino],
            "subject": f"🔔 Avisos AscensorAlert - {len(alertas_ipo)} IPOs y {len(alertas_contrato)} Contratos",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        return f"Email enviado correctamente: {len(alertas_ipo)} IPOs, {len(alertas_contrato)} contratos"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"

# ============================================
# RUTAS
# ============================================

# Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contrasena = request.form.get("contrasena")
        if not usuario or not contrasena:
            return render_template("login.html", error="Usuario y contraseña requeridos")
        encoded_user = urllib.parse.quote(usuario, safe="")
        query = f"?nombre_usuario=eq.{encoded_user}"
        response = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios{query}", headers=HEADERS)

        if response.status_code == 200 and len(response.json()) == 1:
            user = response.json()[0]
            if user.get("contrasena", "") == contrasena:
                session["usuario"] = usuario
                session["usuario_id"] = user.get("id")
                session["email"] = user.get("email", "")
                return redirect("/home")
        return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Home - ACTUALIZADO: Dashboard en desktop, menú simple en móvil
@app.route("/home")
def home():
    """Homepage - Dashboard en desktop, menú simple en móvil"""
    if "usuario" not in session:
        return redirect("/")
    
    # Detectar si es móvil
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone'])
    
    # Si es móvil, mostrar homepage antigua (menú simple)
    if is_mobile:
        usuario = session.get('usuario', 'Usuario')
        return render_template('home_mobile.html', usuario=usuario)
    
    # Desktop: Dashboard completo
    
    # ========== MÉTRICAS ==========
    
    # Total de comunidades (leads únicos)
    response_leads = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?select=id",
        headers=HEADERS
    )
    total_comunidades = len(response_leads.json()) if response_leads.ok else 0
    
    # Total de equipos
    response_equipos = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=id",
        headers=HEADERS
    )
    total_equipos = len(response_equipos.json()) if response_equipos.ok else 0
    
    # Total de oportunidades
    response_oportunidades = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?select=id",
        headers=HEADERS
    )
    total_oportunidades = len(response_oportunidades.json()) if response_oportunidades.ok else 0
    
    # IPOs hoy
    hoy = date.today().isoformat()
    response_ipos_hoy = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=id&ipo_proxima=eq.{hoy}",
        headers=HEADERS
    )
    ipos_hoy = len(response_ipos_hoy.json()) if response_ipos_hoy.ok else 0
    
    metricas = {
        'total_comunidades': total_comunidades,
        'total_equipos': total_equipos,
        'total_oportunidades': total_oportunidades,
        'ipos_hoy': ipos_hoy
    }
    
    # ========== ALERTAS ==========
    
    # Contratos que vencen en 30 días
    fecha_limite = (date.today() + timedelta(days=30)).isoformat()
    response_contratos = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=id&fecha_vencimiento_contrato=lte.{fecha_limite}&fecha_vencimiento_contrato=gte.{hoy}",
        headers=HEADERS
    )
    contratos_criticos = len(response_contratos.json()) if response_contratos.ok else 0
    
    # IPOs esta semana
    fin_semana = (date.today() + timedelta(days=7)).isoformat()
    response_ipos_semana = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=id&ipo_proxima=gte.{hoy}&ipo_proxima=lte.{fin_semana}",
        headers=HEADERS
    )
    ipos_semana = len(response_ipos_semana.json()) if response_ipos_semana.ok else 0
    
    # Oportunidades pendientes (estado "activa")
    response_op_pendientes = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?select=id&estado=eq.activa",
        headers=HEADERS
    )
    oportunidades_pendientes = len(response_op_pendientes.json()) if response_op_pendientes.ok else 0
    
    alertas = {
        'contratos_criticos': contratos_criticos,
        'ipos_semana': ipos_semana,
        'oportunidades_pendientes': oportunidades_pendientes
    }
    
    # ========== ÚLTIMAS INSTALACIONES ==========
    
    response_ultimas = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?select=*&order=fecha_visita.desc&limit=5",
        headers=HEADERS
    )
    
    ultimas_instalaciones = []
    if response_ultimas.ok:
        leads_data = response_ultimas.json()
        for lead in leads_data:
            # Contar equipos de este lead
            response_count = requests.get(
                f"{SUPABASE_URL}/rest/v1/equipos?select=id&cliente_id=eq.{lead['id']}",
                headers=HEADERS
            )
            num_equipos = len(response_count.json()) if response_count.ok else 0
            
            # Formatear fecha
            fecha_str = lead.get('fecha_visita', '')
            if fecha_str:
                try:
                    fecha_obj = datetime.strptime(fecha_str.split('T')[0], '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_formateada = fecha_str.split('T')[0]
            else:
                fecha_formateada = '-'
            
            ultimas_instalaciones.append({
                'id': lead['id'],
                'direccion': lead.get('direccion', 'Sin dirección'),
                'localidad': lead.get('localidad', '-'),
                'num_equipos': num_equipos,
                'fecha_registro': fecha_formateada
            })
    
    # ========== ÚLTIMAS OPORTUNIDADES ==========
    
    response_oport = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?select=*,clientes(nombre_cliente,direccion)&order=fecha_creacion.desc&limit=5",
        headers=HEADERS
    )
    
    ultimas_oportunidades = []
    if response_oport.ok:
        for op in response_oport.json():
            # Obtener nombre del cliente de la relación
            cliente_info = op.get('clientes', {})
            if isinstance(cliente_info, list) and len(cliente_info) > 0:
                cliente_info = cliente_info[0]
            
            nombre_cliente = cliente_info.get('nombre_cliente', 'Sin nombre') if cliente_info else 'Sin nombre'
            
            # Formatear importe
            importe = op.get('valor_estimado', 0)
            if importe:
                try:
                    importe_formateado = f"{float(importe):,.0f}".replace(',', '.')
                except:
                    importe_formateado = str(importe)
            else:
                importe_formateado = '-'
            
            ultimas_oportunidades.append({
                'id': op['id'],
                'nombre_cliente': nombre_cliente,
                'tipo_oportunidad': op.get('tipo', '-'),
                'estado': op.get('estado', '-'),
                'importe_estimado': importe_formateado
            })
    
    # ========== PRÓXIMAS IPOs ESTA SEMANA ==========
    
    response_ipos = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=*,clientes(direccion,localidad)&ipo_proxima=gte.{hoy}&ipo_proxima=lte.{fin_semana}&order=ipo_proxima.asc",
        headers=HEADERS
    )
    
    proximas_ipos = []
    if response_ipos.ok:
        for equipo in response_ipos.json():
            fecha_ipo_str = equipo.get('ipo_proxima', '')
            if fecha_ipo_str:
                try:
                    fecha_ipo = datetime.strptime(fecha_ipo_str, '%Y-%m-%d').date()
                    dias_restantes = (fecha_ipo - date.today()).days
                    
                    # Obtener dirección del lead
                    lead_info = equipo.get('clientes', {})
                    if isinstance(lead_info, list) and len(lead_info) > 0:
                        lead_info = lead_info[0]
                    
                    proximas_ipos.append({
                        'lead_id': equipo.get('cliente_id'),
                        'direccion': lead_info.get('direccion', 'Sin dirección') if lead_info else 'Sin dirección',
                        'localidad': lead_info.get('localidad', '-') if lead_info else '-',
                        'fecha_ipo': fecha_ipo.strftime('%d/%m/%Y'),
                        'dias_restantes': dias_restantes
                    })
                except Exception as e:
                    print(f"Error procesando IPO: {e}")
                    continue
    
    return render_template(
        'home.html',
        metricas=metricas,
        alertas=alertas,
        ultimas_instalaciones=ultimas_instalaciones,
        ultimas_oportunidades=ultimas_oportunidades,
        proximas_ipos=proximas_ipos
    )

# Alta de Lead CON FECHA DE VISITA
@app.route("/formulario_lead", methods=["GET", "POST"])
def formulario_lead():
    if "usuario" not in session:
        return redirect("/")
    if request.method == "POST":
        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "tipo_cliente": request.form.get("tipo_lead"),
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead"),
            "codigo_postal": request.form.get("codigo_postal"),
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona"),
            "persona_contacto": request.form.get("persona_contacto"),
            "telefono": request.form.get("telefono"),
            "email": request.form.get("email"),
            "administrador_fincas": request.form.get("administrador_fincas"),
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "numero_ascensores": request.form.get("numero_ascensores"),
            "observaciones": request.form.get("observaciones")
        }

        required = [data["fecha_visita"], data["tipo_cliente"], data["direccion"], data["nombre_cliente"], data["localidad"], data["numero_ascensores"]]
        if any(not field for field in required):
            return "Datos del lead inválidos - Fecha de visita es obligatoria", 400

        response = requests.post(f"{SUPABASE_URL}/rest/v1/clientes?select=id", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            cliente_id = response.json()[0]["id"]
            return redirect(f"/nuevo_equipo?lead_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template("formulario_lead.html", fecha_hoy=fecha_hoy)

# Visita a Administrador
@app.route("/visita_administrador", methods=["GET", "POST"])
def visita_administrador():
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_fincas": request.form.get("administrador_fincas"),
            "persona_contacto": request.form.get("persona_contacto"),
            "observaciones": request.form.get("observaciones")
        }
        
        required = [data["fecha_visita"], data["administrador_fincas"]]
        if any(not field for field in required):
            return "Datos inválidos - Fecha y Administrador son obligatorios", 400
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_administradores", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            return render_template("visita_admin_success.html")
        else:
            return f"<h3 style='color:red;'>Error al registrar visita</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template("visita_administrador.html", fecha_hoy=fecha_hoy)

# Dashboard de visitas a administradores
@app.route("/visitas_administradores_dashboard")
def visitas_administradores_dashboard():
    if "usuario" not in session:
        return redirect("/")
    
    page = int(request.args.get("page", 1))
    per_page = 25
    offset = (page - 1) * per_page
    
    count_url = f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=*"
    count_response = requests.get(count_url, headers={**HEADERS, "Prefer": "count=exact"})
    total_registros = int(count_response.headers.get("Content-Range", "0").split("/")[-1])
    total_pages = max(1, (total_registros + per_page - 1) // per_page)
    
    data_url = f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=*&order=fecha_visita.desc&limit={per_page}&offset={offset}"
    response = requests.get(data_url, headers=HEADERS)
    
    if response.status_code != 200:
        return f"<h3 style='color:red;'>Error al obtener visitas</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    
    visitas = response.json()
    
    return render_template("visitas_admin_dashboard.html",
        visitas=visitas,
        page=page,
        total_pages=total_pages,
        total_registros=total_registros
    )

@app.route("/ver_visita_admin/<int:visita_id>")
def ver_visita_admin(visita_id):
    if "usuario" not in session:
        return redirect("/")
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        flash("Visita no encontrada", "error")
        return redirect("/visitas_administradores_dashboard")
    
    visita = response.json()[0]
    return render_template("ver_visita_admin.html", visita=visita)

@app.route("/editar_visita_admin/<int:visita_id>", methods=["GET", "POST"])
def editar_visita_admin(visita_id):
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_fincas": request.form.get("administrador_fincas"),
            "persona_contacto": request.form.get("persona_contacto"),
            "observaciones": request.form.get("observaciones")
        }
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}",
            json=data,
            headers=HEADERS
        )
        
        if response.status_code in [200, 204]:
            flash("Visita actualizada correctamente", "success")
            return redirect("/visitas_administradores_dashboard")
        else:
            flash("Error al actualizar visita", "error")
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        flash("Visita no encontrada", "error")
        return redirect("/visitas_administradores_dashboard")
    
    visita = response.json()[0]
    return render_template("editar_visita_admin.html", visita=visita)

@app.route("/eliminar_visita_admin/<int:visita_id>")
def eliminar_visita_admin(visita_id):
    if "usuario" not in session:
        return redirect("/")
    
    response = requests.delete(f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}", headers=HEADERS)
    
    if response.status_code in [200, 204]:
        flash("Visita eliminada correctamente", "success")
    else:
        flash("Error al eliminar visita", "error")
    
    return redirect("/visitas_administradores_dashboard")

# Alta de Equipo (ahora requiere lead_id)
@app.route("/nuevo_equipo", methods=["GET", "POST"])
def nuevo_equipo():
    if "usuario" not in session:
        return redirect("/")
    
    # VALIDAR que viene con lead_id
    lead_id = request.args.get("lead_id")
    
    if not lead_id:
        flash("Debes añadir equipos desde un lead específico", "error")
        return redirect("/leads_dashboard")
    
    # Verificar que el lead existe
    lead_url = f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}"
    lead_response = requests.get(lead_url, headers=HEADERS)
    
    if lead_response.status_code != 200 or not lead_response.json():
        flash("Lead no encontrado", "error")
        return redirect("/leads_dashboard")
    
    lead_data = lead_response.json()[0]
    
    if request.method == "POST":
        equipo_data = {
            "cliente_id": int(lead_id),
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion"),
            "descripcion": request.form.get("observaciones"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        required = [equipo_data["tipo_equipo"]]
        if any(not field for field in required):
            return render_template("nuevo_equipo.html", 
                                 lead=lead_data, 
                                 error="Tipo de equipo es obligatorio")

        for key, value in equipo_data.items():
            if value == "":
                equipo_data[key] = None

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            flash("Equipo añadido correctamente", "success")
            return redirect(f"/ver_lead/{lead_id}")
        else:
            return render_template("nuevo_equipo.html", 
                                 lead=lead_data, 
                                 error="Error al crear el equipo")

    return render_template("nuevo_equipo.html", lead=lead_data)

# Crear visita de seguimiento
@app.route("/crear_visita_seguimiento/<int:cliente_id>", methods=["GET", "POST"])
def crear_visita_seguimiento(cliente_id):
    if "usuario" not in session:
        return redirect("/")
    
    oportunidad_id = request.args.get("oportunidad_id")
    
    if request.method == "POST":
        data = {
            "cliente_id": cliente_id,
            "oportunidad_id": request.form.get("oportunidad_id") or None,
            "fecha_visita": request.form.get("fecha_visita"),
            "observaciones": request.form.get("observaciones")
        }
        
        if not data["fecha_visita"]:
            flash("La fecha de visita es obligatoria", "error")
            return redirect(request.referrer)
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_seguimiento", json=data, headers=HEADERS)
        
        if response.status_code in [200, 201]:
            flash("Visita de seguimiento registrada correctamente", "success")
            return redirect(f"/ver_lead/{cliente_id}")
        else:
            flash("Error al registrar visita", "error")
    
    response_cliente = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}", headers=HEADERS)
    response_oportunidades = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?cliente_id=eq.{cliente_id}&estado=eq.activa",
        headers=HEADERS
    )
    
    if response_cliente.status_code != 200 or not response_cliente.json():
        flash("Cliente no encontrado", "error")
        return redirect("/leads_dashboard")
    
    cliente = response_cliente.json()[0]
    oportunidades = response_oportunidades.json() if response_oportunidades.status_code == 200 else []
    
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    
    return render_template("crear_visita_seguimiento.html",
        cliente=cliente,
        oportunidades=oportunidades,
        oportunidad_id_preseleccionada=oportunidad_id,
        fecha_hoy=fecha_hoy
    )

# DESCARGO COMERCIAL MENSUAL
@app.route("/reporte_mensual", methods=["GET", "POST"])
def reporte_mensual():
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        mes = int(request.form.get("mes"))
        año = int(request.form.get("año"))
        
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_inicio = f"{año}-{mes:02d}-01"
        fecha_fin = f"{año}-{mes:02d}-{ultimo_dia}"
        
        query_clientes = f"fecha_visita=gte.{fecha_inicio}&fecha_visita=lte.{fecha_fin}"
        response_clientes = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?{query_clientes}&select=*", headers=HEADERS)
        
        response_seguimiento = requests.get(
            f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?fecha_visita=gte.{fecha_inicio}&fecha_visita=lte.{fecha_fin}&select=*,clientes(nombre_cliente,direccion,localidad)",
            headers=HEADERS
        )
        
        response_admin = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?{query_clientes}&select=*", headers=HEADERS)
        
        if response_clientes.status_code != 200:
            return f"Error al obtener datos: {response_clientes.text}"
        
        clientes_mes = response_clientes.json()
        visitas_seguimiento_mes = response_seguimiento.json() if response_seguimiento.status_code == 200 else []
        visitas_admin_mes = response_admin.json() if response_admin.status_code == 200 else []
        
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        
        ws1 = wb.active
        ws1.title = "VISITAS INSTALACIONES"
        
        headers = ['FECHA', 'COMUNIDAD/EMPRESA', 'DIRECCION', 'ZONA', 'OBSERVACIONES']
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'), 
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        row = 2
        
        for cliente in clientes_mes:
            ws1.cell(row=row, column=1, value=cliente.get('fecha_visita', ''))
            ws1.cell(row=row, column=2, value=cliente.get('nombre_cliente', ''))
            ws1.cell(row=row, column=3, value=cliente.get('direccion', ''))
            ws1.cell(row=row, column=4, value=cliente.get('localidad', ''))
            ws1.cell(row=row, column=5, value=cliente.get('observaciones', ''))
            
            for col in range(1, 6):
                ws1.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        for visita in visitas_seguimiento_mes:
            ws1.cell(row=row, column=1, value=visita.get('fecha_visita', ''))
            ws1.cell(row=row, column=2, value=visita.get('clientes', {}).get('nombre_cliente', ''))
            ws1.cell(row=row, column=3, value=visita.get('clientes', {}).get('direccion', ''))
            ws1.cell(row=row, column=4, value=visita.get('clientes', {}).get('localidad', ''))
            ws1.cell(row=row, column=5, value=visita.get('observaciones', ''))
            
            for col in range(1, 6):
                ws1.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        ws1.column_dimensions['A'].width = 12
        ws1.column_dimensions['B'].width = 40
        ws1.column_dimensions['C'].width = 50
        ws1.column_dimensions['D'].width = 20
        ws1.column_dimensions['E'].width = 70
        
        ws2 = wb.create_sheet(title="VISITAS ADMINISTRADORES")
        
        headers_admin = ['FECHA', 'ADMINISTRADOR', 'PERSONA CONTACTO', 'OBSERVACIONES']
        
        for col, header in enumerate(headers_admin, 1):
            cell = ws2.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        row = 2
        for visita in visitas_admin_mes:
            ws2.cell(row=row, column=1, value=visita.get('fecha_visita', ''))
            ws2.cell(row=row, column=2, value=visita.get('administrador_fincas', ''))
            ws2.cell(row=row, column=3, value=visita.get('persona_contacto', ''))
            ws2.cell(row=row, column=4, value=visita.get('observaciones', ''))
            
            for col in range(1, 5):
                ws2.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        ws2.column_dimensions['A'].width = 12
        ws2.column_dimensions['B'].width = 50
        ws2.column_dimensions['C'].width = 30
        ws2.column_dimensions['D'].width = 70
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        meses = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
                'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
        filename = f"DESCARGO COMERCIAL GRAN CANARIA {meses[mes]} {año}.xlsx"
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
    
    return render_template("reporte_mensual.html")

# DASHBOARD MEJORADO CON PAGINACIÓN Y BÚSQUEDA
@app.route("/leads_dashboard")
def leads_dashboard():
    if "usuario" not in session:
        return redirect("/")
    
    page = int(request.args.get("page", 1))
    per_page = 25
    offset = (page - 1) * per_page
    
    filtro_localidad = request.args.get("localidad", "")
    filtro_empresa = request.args.get("empresa", "")
    buscar_direccion = request.args.get("buscar_direccion", "")
    filtro_ipo_urgencia = request.args.get("ipo_urgencia", "")
    
    query_params = []
    
    if filtro_localidad:
        query_params.append(f"localidad=eq.{filtro_localidad}")
    
    if filtro_empresa:
        query_params.append(f"empresa_mantenedora=eq.{filtro_empresa}")
    
    if buscar_direccion:
        query_params.append(f"direccion=ilike.*{buscar_direccion}*")
    
    query_string = "&".join(query_params) if query_params else ""
    
    count_url = f"{SUPABASE_URL}/rest/v1/clientes?select=*"
    if query_string:
        count_url += f"&{query_string}"
    
    count_response = requests.get(count_url, headers={**HEADERS, "Prefer": "count=exact"})
    total_registros = int(count_response.headers.get("Content-Range", "0").split("/")[-1])
    total_pages = max(1, (total_registros + per_page - 1) // per_page)
    
    data_url = f"{SUPABASE_URL}/rest/v1/clientes?select=*&limit={per_page}&offset={offset}"
    if query_string:
        data_url += f"&{query_string}"
    
    response = requests.get(data_url, headers=HEADERS)
    
    if response.status_code != 200:
        return f"<h3 style='color:red;'>Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    
    leads_data = response.json()
    rows = []
    localidades_disponibles = set()
    empresas_disponibles = set()
    
    all_leads_response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=localidad,empresa_mantenedora", headers=HEADERS)
    if all_leads_response.status_code == 200:
        all_leads = all_leads_response.json()
        for lead in all_leads:
            if lead.get("localidad"):
                localidades_disponibles.add(lead["localidad"])
            if lead.get("empresa_mantenedora"):
                empresas_disponibles.add(lead["empresa_mantenedora"])
    
    for lead in leads_data:
        lead_id = lead["id"]
        
        equipos_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", 
            headers=HEADERS
        )
        
        if equipos_response.status_code == 200:
            equipos = equipos_response.json()
            
            direccion = lead.get("direccion", "-")
            localidad = lead.get("localidad", "-")
            empresa_mantenedora = lead.get("empresa_mantenedora", "-")
            total_equipos = len(equipos) if equipos else lead.get("numero_ascensores", 0)
            
            ipo_proxima = None
            contrato_vence = None
            
            if equipos:
                for equipo in equipos:
                    ipo_equipo = equipo.get("ipo_proxima")
                    if ipo_equipo:
                        try:
                            ipo_date = datetime.strptime(ipo_equipo, "%Y-%m-%d")
                            if ipo_proxima is None or ipo_date < ipo_proxima:
                                ipo_proxima = ipo_date
                        except:
                            pass
                    
                    contrato_equipo = equipo.get("fecha_vencimiento_contrato")
                    if contrato_equipo:
                        try:
                            contrato_date = datetime.strptime(contrato_equipo, "%Y-%m-%d")
                            if contrato_vence is None or contrato_date < contrato_vence:
                                contrato_vence = contrato_date
                        except:
                            pass
            
            ipo_proxima_str = ipo_proxima.strftime("%d/%m/%Y") if ipo_proxima else "-"
            contrato_vence_str = contrato_vence.strftime("%d/%m/%Y") if contrato_vence else "-"
            
            color_ipo = calcular_color_ipo(ipo_proxima_str)
            color_contrato = calcular_color_contrato(contrato_vence_str)
            
            row = {
                "lead_id": lead_id,
                "direccion": direccion,
                "localidad": localidad,
                "total_equipos": total_equipos,
                "empresa_mantenedora": empresa_mantenedora,
                "ipo_proxima": ipo_proxima_str,
                "ipo_fecha_original": ipo_proxima,
                "contrato_vence": contrato_vence_str,
                "contrato_fecha_original": contrato_vence,
                "color_ipo": color_ipo,
                "color_contrato": color_contrato
            }
            
            incluir_fila = True
            if filtro_ipo_urgencia and ipo_proxima:
                hoy = datetime.now()
                diferencia_dias = (ipo_proxima - hoy).days
                
                if filtro_ipo_urgencia == "15_dias" and not (-15 <= diferencia_dias < 0):
                    incluir_fila = False
                elif filtro_ipo_urgencia == "ipo_pasada_30" and not (0 <= diferencia_dias <= 30):
                    incluir_fila = False
                elif filtro_ipo_urgencia == "30_90_dias" and not (30 < diferencia_dias <= 90):
                    incluir_fila = False
            
            if incluir_fila:
                rows.append(row)
    
    rows.sort(key=lambda x: x["ipo_fecha_original"] if x["ipo_fecha_original"] else datetime.max)
    
    localidades_disponibles = sorted([l for l in localidades_disponibles if l])
    empresas_disponibles = sorted([e for e in empresas_disponibles if e])
    
    return render_template("dashboard.html",
        rows=rows,
        localidades=localidades_disponibles,
        empresas=empresas_disponibles,
        filtro_localidad=filtro_localidad,
        filtro_empresa=filtro_empresa,
        buscar_direccion=buscar_direccion,
        filtro_ipo_urgencia=filtro_ipo_urgencia,
        page=page,
        total_pages=total_pages,
        total_registros=total_registros,
        per_page=per_page
    )

# Ver detalle completo del Lead
@app.route("/ver_lead/<int:lead_id>")
def ver_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        return f"<h3 style='color:red;'>Error al obtener Lead</h3><pre>{response.text}</pre><a href='/leads_dashboard'>Volver</a>"
    
    lead = response.json()[0]
    
    equipos_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
    equipos = []
    if equipos_response.status_code == 200:
        equipos_raw = equipos_response.json()
        for equipo in equipos_raw:
            fecha_venc = equipo.get("fecha_vencimiento_contrato", "-")
            if fecha_venc and fecha_venc != "-":
                try:
                    partes = fecha_venc.split("-")
                    if len(partes) == 3:
                        fecha_venc = f"{partes[2]}/{partes[1]}/{partes[0]}"
                except:
                    pass
            
            ipo = equipo.get("ipo_proxima", "-")
            if ipo and ipo != "-":
                try:
                    partes = ipo.split("-")
                    if len(partes) == 3:
                        ipo = f"{partes[2]}/{partes[1]}/{partes[0]}"
                except:
                    pass
            
            equipos.append({
                "id": equipo.get("id"),
                "tipo_equipo": equipo.get("tipo_equipo", "-"),
                "identificacion": equipo.get("identificacion", "-"),
                "rae": equipo.get("rae", "-"),
                "ipo_proxima": ipo,
                "fecha_vencimiento_contrato": fecha_venc,
                "descripcion": equipo.get("descripcion", "-")
            })
    
    oportunidades_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?cliente_id=eq.{lead_id}&order=fecha_creacion.desc",
        headers=HEADERS
    )
    oportunidades = []
    if oportunidades_response.status_code == 200:
        oportunidades = oportunidades_response.json()
    
    visitas_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?cliente_id=eq.{lead_id}&select=*,oportunidades(tipo)&order=fecha_visita.desc",
        headers=HEADERS
    )
    visitas_seguimiento = []
    if visitas_response.status_code == 200:
        visitas_seguimiento = visitas_response.json()
    
    return render_template("ver_lead.html", 
        lead=lead, 
        equipos=equipos, 
        oportunidades=oportunidades,
        visitas_seguimiento=visitas_seguimiento
    )

# Eliminar Lead
@app.route("/eliminar_lead/<int:lead_id>")
def eliminar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")
    
    requests.delete(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
    requests.delete(f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?cliente_id=eq.{lead_id}", headers=HEADERS)
    
    response = requests.delete(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}", headers=HEADERS)
    
    if response.status_code in [200, 204]:
        return redirect("/leads_dashboard")
    else:
        return f"<h3 style='color:red;'>Error al eliminar Lead</h3><pre>{response.text}</pre><a href='/leads_dashboard'>Volver</a>"

# Eliminar Equipo
@app.route("/eliminar_equipo/<int:equipo_id>")
def eliminar_equipo(equipo_id):
    if "usuario" not in session:
        return redirect("/")
    
    equipo_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
    if equipo_response.status_code == 200 and equipo_response.json():
        cliente_id = equipo_response.json()[0].get("cliente_id")
        
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
        
        if response.status_code in [200, 204]:
            return redirect(f"/ver_lead/{cliente_id}")
        else:
            return f"<h3 style='color:red;'>Error al eliminar Equipo</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    else:
        return f"<h3 style='color:red;'>Error al obtener Equipo</h3><a href='/home'>Volver</a>"

# Editar Lead
@app.route("/editar_lead/<int:lead_id>", methods=["GET", "POST"])
def editar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":
        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "tipo_cliente": request.form.get("tipo_lead"),
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead"),
            "codigo_postal": request.form.get("codigo_postal"),
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona"),
            "persona_contacto": request.form.get("persona_contacto"),
            "telefono": request.form.get("telefono"),
            "email": request.form.get("email"),
            "administrador_fincas": request.form.get("administrador_fincas"),
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "numero_ascensores": request.form.get("numero_ascensores"),
            "observaciones": request.form.get("observaciones")
        }
        res = requests.patch(
            f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}",
            json=data,
            headers=HEADERS
        )
        if res.status_code in [200, 204]:
            return redirect("/leads_dashboard")
        else:
            return f"<h3 style='color:red;'>Error al actualizar Lead</h3><pre>{res.text}</pre><a href='/leads_dashboard'>Volver</a>"

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}",
        headers=HEADERS
    )
    if response.status_code == 200 and response.json():
        lead = response.json()[0]
    else:
        return f"<h3 style='color:red;'>Error al obtener Lead</h3><pre>{response.text}</pre><a href='/leads_dashboard'>Volver</a>"

    return render_template("editar_lead.html", lead=lead)

@app.route("/editar_equipo/<int:equipo_id>", methods=["GET", "POST"])
def editar_equipo(equipo_id):
    if "usuario" not in session:
        return redirect("/")

    response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        return f"<h3 style='color:red;'>Error al obtener equipo</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    equipo = response.json()[0]

    if request.method == "POST":
        data = {
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion"),
            "descripcion": request.form.get("observaciones"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        for key, value in data.items():
            if value == "":
                data[key] = None

        update_url = f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}"
        res = requests.patch(update_url, json=data, headers=HEADERS)
        if res.status_code in [200, 204]:
            return redirect("/leads_dashboard")
        else:
            return f"<h3 style='color:red;'>Error al actualizar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template("editar_equipo.html", equipo=equipo)

# ============================================
# MÓDULO DE OPORTUNIDADES
# ============================================

@app.route("/oportunidades")
def oportunidades():
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
            
            activas = sum(1 for o in oportunidades_list if o['estado'] == 'activa')
            ganadas = sum(1 for o in oportunidades_list if o['estado'] == 'ganada')
            perdidas = sum(1 for o in oportunidades_list if o['estado'] == 'perdida')
            
            return render_template("oportunidades.html",
                                        oportunidades=oportunidades_list,
                                        activas=activas,
                                        ganadas=ganadas,
                                        perdidas=perdidas)
        else:
            flash("Error al cargar oportunidades", "error")
            return redirect(url_for("home"))
            
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("home"))


@app.route("/crear_oportunidad/<int:cliente_id>", methods=["GET", "POST"])
def crear_oportunidad(cliente_id):
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        try:
            data = {
                "cliente_id": cliente_id,
                "tipo": request.form["tipo"],
                "descripcion": request.form.get("descripcion", ""),
                "valor_estimado": request.form.get("valor_estimado") or None,
                "observaciones": request.form.get("observaciones", ""),
                "estado": "activa"
            }
            
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/oportunidades",
                headers=HEADERS,
                json=data
            )
            
            if response.status_code == 201:
                flash("Oportunidad creada exitosamente!", "success")
                return redirect(url_for("ver_lead", lead_id=cliente_id))
            else:
                flash("Error al crear oportunidad", "error")
                
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}",
            headers=HEADERS
        )
        if response.status_code == 200:
            cliente = response.json()[0]
            return render_template("crear_oportunidad.html", cliente=cliente)
    except:
        flash("Error al cargar datos del cliente", "error")
        return redirect(url_for("leads_dashboard"))


@app.route("/editar_oportunidad/<int:oportunidad_id>", methods=["GET", "POST"])
def editar_oportunidad(oportunidad_id):
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        try:
            data = {
                "tipo": request.form["tipo"],
                "descripcion": request.form.get("descripcion", ""),
                "estado": request.form["estado"],
                "valor_estimado": request.form.get("valor_estimado") or None,
                "observaciones": request.form.get("observaciones", "")
            }
            
            if data["estado"] in ["ganada", "perdida"]:
                data["fecha_cierre"] = datetime.now().isoformat()
            
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
                headers=HEADERS,
                json=data
            )
            
            if response.status_code == 204:
                flash("Oportunidad actualizada correctamente", "success")
                return redirect(url_for("oportunidades"))
            else:
                flash("Error al actualizar", "error")
                
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion)",
            headers=HEADERS
        )
        if response.status_code == 200:
            oportunidad = response.json()[0]
            return render_template("editar_oportunidad.html", oportunidad=oportunidad)
    except:
        flash("Error al cargar oportunidad", "error")
        return redirect(url_for("oportunidades"))


@app.route("/ver_oportunidad/<int:oportunidad_id>")
def ver_oportunidad(oportunidad_id):
    if "usuario" not in session:
        return redirect("/")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion,localidad)",
            headers=HEADERS
        )
        if response.status_code == 200 and response.json():
            oportunidad = response.json()[0]
            return render_template("ver_oportunidad.html", oportunidad=oportunidad)
        else:
            flash("Oportunidad no encontrada", "error")
            return redirect(url_for("oportunidades"))
    except:
        flash("Error al cargar oportunidad", "error")
        return redirect(url_for("oportunidades"))


@app.route("/eliminar_oportunidad/<int:oportunidad_id>")
def eliminar_oportunidad(oportunidad_id):
    if "usuario" not in session:
        return redirect("/")
    
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
                flash("Oportunidad eliminada correctamente", "success")
                return redirect(f"/ver_lead/{cliente_id}")
            else:
                flash("Error al eliminar oportunidad", "error")
                return redirect(url_for("oportunidades"))
        else:
            flash("Oportunidad no encontrada", "error")
            return redirect(url_for("oportunidades"))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("oportunidades"))

# ============================================
# MÓDULO DE NOTIFICACIONES POR EMAIL
# ============================================

@app.route('/configuracion_avisos', methods=['GET', 'POST'])
def configuracion_avisos():
    if "usuario" not in session:
        return redirect(url_for("login"))
    
    usuario_id = session.get("usuario_id")
    
    if request.method == 'POST':
        # Obtener datos del formulario
        email_destino = request.form.get('email_destino')
        dias_anticipacion_ipo = int(request.form.get('dias_anticipacion_ipo', 30))
        dias_anticipacion_contrato = int(request.form.get('dias_anticipacion_contrato', 60))
        notificaciones_activas = request.form.get('notificaciones_activas') == 'true'
        frecuencia_chequeo = request.form.get('frecuencia_chequeo', 'diario')
        
        # Verificar si ya existe configuración
        config_existente = requests.get(
            f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
            headers=HEADERS
        )
        
        if config_existente.status_code == 200 and config_existente.json():
            # Actualizar configuración existente
            data = {
                "email_destino": email_destino,
                "dias_anticipacion_ipo": dias_anticipacion_ipo,
                "dias_anticipacion_contrato": dias_anticipacion_contrato,
                "notificaciones_activas": notificaciones_activas,
                "frecuencia_chequeo": frecuencia_chequeo
            }
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
                json=data,
                headers=HEADERS
            )
        else:
            # Crear nueva configuración
            data = {
                "usuario_id": usuario_id,
                "email_destino": email_destino,
                "dias_anticipacion_ipo": dias_anticipacion_ipo,
                "dias_anticipacion_contrato": dias_anticipacion_contrato,
                "notificaciones_activas": notificaciones_activas,
                "frecuencia_chequeo": frecuencia_chequeo
            }
            requests.post(
                f"{SUPABASE_URL}/rest/v1/configuracion_avisos",
                json=data,
                headers=HEADERS
            )
        
        return render_template('configuracion_avisos.html', 
                             config={
                                 'email_destino': email_destino,
                                 'dias_anticipacion_ipo': dias_anticipacion_ipo,
                                 'dias_anticipacion_contrato': dias_anticipacion_contrato,
                                 'notificaciones_activas': notificaciones_activas,
                                 'frecuencia_chequeo': frecuencia_chequeo,
                                 'ultima_ejecucion': None
                             },
                             mensaje='Configuración guardada correctamente')
    
    # GET - Obtener configuración actual
    config = requests.get(
        f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
        headers=HEADERS
    )
    
    if config.status_code == 200 and config.json():
        config_data = config.json()[0]
    else:
        # Configuración por defecto
        config_data = {
            'email_destino': session.get('email', 'admin@fedesascensores.com'),
            'dias_anticipacion_ipo': 30,
            'dias_anticipacion_contrato': 60,
            'notificaciones_activas': True,
            'frecuencia_chequeo': 'diario',
            'ultima_ejecucion': None
        }
    
    return render_template('configuracion_avisos.html', config=config_data, mensaje=None)


@app.route('/enviar_avisos_manual')
def enviar_avisos_manual():
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
    
    if not config_data.get('notificaciones_activas'):
        return "Las notificaciones están desactivadas", 400
    
    # Enviar avisos
    resultado = enviar_avisos_email(config_data)
    
    # Actualizar última ejecución
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/configuracion_avisos?usuario_id=eq.{usuario_id}",
        json={"ultima_ejecucion": datetime.now().isoformat()},
        headers=HEADERS
    )
    
    return f"<h3>{resultado}</h3><br><a href='/home'>Volver al inicio</a>"

# ============================================
# CIERRE
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
