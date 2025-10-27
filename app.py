from flask import Flask, request, render_template, redirect, session, Response, url_for, flash
import requests
import os
import urllib.parse
from datetime import date, datetime, timedelta
import calendar
import io
import resend
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# ============================================
# SISTEMA DE CACHÉ PARA ADMINISTRADORES
# ============================================
# Evita consultas repetidas a Supabase, mejorando el rendimiento
cache_administradores = {
    'data': [],
    'timestamp': None
}

def get_administradores_cached():
    """
    Obtiene la lista de administradores usando caché.
    Se renueva automáticamente cada 5 minutos.
    Esto reduce drásticamente las consultas a Supabase.
    """
    now = datetime.now()

    # Si no hay caché o pasaron 5 minutos, renovar
    if not cache_administradores['timestamp'] or \
       (now - cache_administradores['timestamp']) > timedelta(minutes=5):

        try:
            print(f"🔄 Consultando administradores desde Supabase...")
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/administradores?select=id,nombre_empresa&order=nombre_empresa.asc",
                headers=HEADERS,
                timeout=10  # Aumentado a 10 segundos
            )

            print(f"📡 Respuesta de Supabase - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                cache_administradores['data'] = data
                cache_administradores['timestamp'] = now
                print(f"✅ Caché de administradores actualizado: {len(data)} registros")
            else:
                print(f"⚠️ Error al actualizar caché de administradores: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                # Si falla pero hay caché previo, usarlo
                if cache_administradores['data']:
                    print(f"ℹ️ Usando caché anterior: {len(cache_administradores['data'])} registros")

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout al consultar Supabase (>10s)")
        except Exception as e:
            print(f"❌ Excepción al actualizar caché de administradores: {type(e).__name__}: {str(e)}")
            # Si falla, devolver lo que haya en caché (aunque esté desactualizado)

    return cache_administradores['data']

# FUNCIONES AUXILIARES

def limpiar_none(data):
    """Convierte valores None a strings vacíos para evitar mostrar 'none' en formularios"""
    if isinstance(data, dict):
        return {k: (v if v is not None else '') for k, v in data.items()}
    return data

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
    
    # Procesar múltiples emails
    emails_raw = config['email_destinatario']
    emails_destino = [email.strip() for email in emails_raw.split(',')] if ',' in emails_raw else [emails_raw.strip()]
    primer_aviso_ipo = config['primer_aviso_despues_ipo']
    segundo_aviso_ipo = config['segundo_aviso_despues_ipo']
    dias_contrato = config['dias_aviso_antes_contrato']
    
    fecha_hoy = datetime.now().date()
    
    # Obtener equipos con IPO próxima
    equipos_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/equipos?select=*,clientes(nombre_cliente,direccion)&ipo_proxima=not.is.null",
        headers=HEADERS
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
        params = {
            "from": EMAIL_FROM,
            "to": emails_destino,
            "subject": f"🔔 Avisos AscensorAlert - {total_ipos} IPOs y {len(alertas_contrato)} Contratos",
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        return f"Email enviado correctamente a {len(emails_destino)} destinatario(s): {total_ipos} IPOs, {len(alertas_contrato)} contratos"
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
    """Homepage - Dashboard responsive para todos los dispositivos"""
    if "usuario" not in session:
        return redirect("/")

    # Dashboard responsive (funciona en desktop, tablet y móvil)
    
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
    # OPTIMIZACIÓN: Usar join de Supabase para obtener equipos en una sola query
    # En lugar de hacer 1 + 5 queries (1 para leads + 5 para equipos), hacemos solo 1 query
    response_ultimas = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?select=*,equipos(id)&order=fecha_visita.desc&limit=5",
        headers=HEADERS
    )

    ultimas_instalaciones = []
    if response_ultimas.ok:
        leads_data = response_ultimas.json()
        for lead in leads_data:
            # Los equipos ya están incluidos gracias al join de Supabase
            equipos_data = lead.get('equipos', [])
            num_equipos = len(equipos_data) if equipos_data else lead.get('numero_ascensores', 0)

            # Obtener empresa mantenedora del cliente (no de equipos)
            empresa_mantenedora = lead.get('empresa_mantenedora', '-')

            ultimas_instalaciones.append({
                'id': lead['id'],
                'direccion': lead.get('direccion', 'Sin dirección'),
                'nombre_cliente': lead.get('nombre_cliente', ''),
                'localidad': lead.get('localidad', '-'),
                'num_equipos': num_equipos,
                'empresa_mantenedora': empresa_mantenedora
            })
    
    # ========== ÚLTIMAS OPORTUNIDADES ==========
    
    response_oport = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?select=*,clientes(nombre_cliente,direccion)&order=fecha_creacion.desc&limit=5",
        headers=HEADERS
    )
    
    ultimas_oportunidades = []
    if response_oport.ok:
        for op in response_oport.json():
            # Obtener nombre y dirección del cliente de la relación
            cliente_info = op.get('clientes', {})
            if isinstance(cliente_info, list) and len(cliente_info) > 0:
                cliente_info = cliente_info[0]

            nombre_cliente = cliente_info.get('nombre_cliente', 'Sin nombre') if cliente_info else 'Sin nombre'
            direccion_cliente = cliente_info.get('direccion', 'Sin dirección') if cliente_info else 'Sin dirección'

            ultimas_oportunidades.append({
                'id': op['id'],
                'nombre_cliente': nombre_cliente,
                'direccion': direccion_cliente,
                'tipo': op.get('tipo', '-'),
                'estado': op.get('estado', '-')
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
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get("administrador_id")
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        data = {
            "fecha_visita": request.form.get("fecha_visita") or None,
            "tipo_cliente": request.form.get("tipo_lead") or None,
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead") or None,
            "codigo_postal": request.form.get("codigo_postal") or None,
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona") or None,
            "persona_contacto": request.form.get("persona_contacto") or None,
            "telefono": request.form.get("telefono") or None,
            "email": request.form.get("email") or None,
            "administrador_fincas": request.form.get("administrador_fincas") or None,
            "administrador_id": administrador_id,
            "empresa_mantenedora": request.form.get("empresa_mantenedora") or None,
            "numero_ascensores": request.form.get("numero_ascensores") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        # Solo dirección y localidad son obligatorios
        required = [data["direccion"], data["localidad"]]
        if any(not field for field in required):
            return "Datos del lead inválidos - Dirección y Localidad son obligatorios", 400

        response = requests.post(f"{SUPABASE_URL}/rest/v1/clientes?select=id", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            cliente_id = response.json()[0]["id"]
            return redirect(f"/nuevo_equipo?lead_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    # GET - Obtener lista de administradores (usando caché)
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    administradores = get_administradores_cached()

    return render_template("formulario_lead.html", fecha_hoy=fecha_hoy, administradores=administradores)

# Visita a Administrador
@app.route("/visita_administrador", methods=["GET", "POST"])
def visita_administrador():
    if "usuario" not in session:
        return redirect("/")
    
    # Puede venir con oportunidad_id desde la vista de oportunidad
    oportunidad_id = request.args.get("oportunidad_id")
    oportunidad_data = None
    
    if oportunidad_id:
        # Obtener datos de la oportunidad
        oportunidad_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(*)",
            headers=HEADERS
        )
        if oportunidad_response.status_code == 200 and oportunidad_response.json():
            oportunidad_data = oportunidad_response.json()[0]
    
    if request.method == "POST":
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get("administrador_id")
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_fincas": request.form.get("administrador_fincas") or None,
            "administrador_id": administrador_id,
            "persona_contacto": request.form.get("persona_contacto") or None,
            "observaciones": request.form.get("observaciones") or None,
            "oportunidad_id": int(request.form.get("oportunidad_id")) if request.form.get("oportunidad_id") else None
        }

        # Solo fecha es obligatoria, al menos uno de los dos campos de administrador debe estar
        if not data["fecha_visita"] or (not data["administrador_fincas"] and not data["administrador_id"]):
            flash("Fecha y Administrador son obligatorios", "error")
            return redirect(request.referrer)

        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_administradores", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            # Si viene de una oportunidad, volver a la oportunidad
            if data["oportunidad_id"]:
                flash("Visita a administrador registrada correctamente", "success")
                return redirect(url_for('ver_oportunidad', oportunidad_id=data["oportunidad_id"]))
            else:
                return render_template("visita_admin_success.html")
        else:
            flash(f"Error al registrar visita: {response.text}", "error")
            return redirect(request.referrer)

    # GET - Obtener lista de administradores (usando caché)
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    administradores = get_administradores_cached()

    return render_template("visita_administrador.html",
                         fecha_hoy=fecha_hoy,
                         oportunidad=oportunidad_data,
                         administradores=administradores)

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

    # Obtener visita con JOIN a administradores
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_administradores?id=eq.{visita_id}&select=*,administradores(nombre_empresa)",
        headers=HEADERS
    )
    if response.status_code != 200 or not response.json():
        flash("Visita no encontrada", "error")
        return redirect("/visitas_administradores_dashboard")

    visita = limpiar_none(response.json()[0])
    return render_template("ver_visita_admin.html", visita=visita)

@app.route("/editar_visita_admin/<int:visita_id>", methods=["GET", "POST"])
def editar_visita_admin(visita_id):
    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get("administrador_id")
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        data = {
            "fecha_visita": request.form.get("fecha_visita"),
            "administrador_fincas": request.form.get("administrador_fincas") or None,
            "administrador_id": administrador_id,
            "persona_contacto": request.form.get("persona_contacto") or None,
            "observaciones": request.form.get("observaciones") or None
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

    visita = limpiar_none(response.json()[0])

    # Obtener lista de administradores (usando caché)
    administradores = get_administradores_cached()

    return render_template("editar_visita_admin.html", visita=visita, administradores=administradores)

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
            "oportunidad_id": int(request.form.get("oportunidad_id")) if request.form.get("oportunidad_id") else None,
            "fecha_visita": request.form.get("fecha_visita"),
            "observaciones": request.form.get("observaciones")
        }
        
        if not data["fecha_visita"]:
            flash("La fecha de visita es obligatoria", "error")
            return redirect(request.referrer)
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/visitas_seguimiento", json=data, headers=HEADERS)
        
        if response.status_code in [200, 201]:
            flash("Visita de seguimiento registrada correctamente", "success")
            # Si viene de una oportunidad, volver a la oportunidad
            if data["oportunidad_id"]:
                return redirect(url_for('ver_oportunidad', oportunidad_id=data["oportunidad_id"]))
            else:
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

        # Obtener oportunidades activas (no filtradas por mes)
        response_oportunidades = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?estado=eq.activa&select=*,clientes(direccion)",
            headers=HEADERS
        )

        if response_clientes.status_code != 200:
            return f"Error al obtener datos: {response_clientes.text}"

        clientes_mes = response_clientes.json()
        visitas_seguimiento_mes = response_seguimiento.json() if response_seguimiento.status_code == 200 else []
        visitas_admin_mes = response_admin.json() if response_admin.status_code == 200 else []
        oportunidades_activas = response_oportunidades.json() if response_oportunidades.status_code == 200 else []
        
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

        # Tercera pestaña: OPORTUNIDADES ACTIVAS
        ws3 = wb.create_sheet(title="OPORTUNIDADES ACTIVAS")

        headers_oportunidades = ['DIRECCION', 'TIPO DE OPORTUNIDAD', 'DESCRIPCION']

        for col, header in enumerate(headers_oportunidades, 1):
            cell = ws3.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        row = 2
        for oportunidad in oportunidades_activas:
            # Obtener dirección del cliente relacionado
            direccion = oportunidad.get('clientes', {}).get('direccion', '') if oportunidad.get('clientes') else ''

            ws3.cell(row=row, column=1, value=direccion)
            ws3.cell(row=row, column=2, value=oportunidad.get('tipo', ''))
            ws3.cell(row=row, column=3, value=oportunidad.get('descripcion', ''))

            for col in range(1, 4):
                ws3.cell(row=row, column=col).border = thin_border

            row += 1

        ws3.column_dimensions['A'].width = 50
        ws3.column_dimensions['B'].width = 30
        ws3.column_dimensions['C'].width = 70

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
    
    # OPTIMIZACIÓN: Usar join de Supabase para obtener equipos en una sola query
    # En lugar de hacer 25 queries separadas (1 por lead), obtenemos todo en 1 query
    data_url = f"{SUPABASE_URL}/rest/v1/clientes?select=*,equipos(ipo_proxima,fecha_vencimiento_contrato)&limit={per_page}&offset={offset}"
    if query_string:
        data_url += f"&{query_string}"

    response = requests.get(data_url, headers=HEADERS)

    if response.status_code != 200:
        return f"<h3 style='color:red;'>Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    leads_data = response.json()
    rows = []
    localidades_disponibles = set()
    empresas_disponibles = set()

    # OPTIMIZACIÓN: Obtener solo las localidades y empresas únicas
    # En lugar de cargar todos los leads completos, solo pedimos los campos necesarios
    localidades_response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=localidad", headers=HEADERS)
    empresas_response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=empresa_mantenedora", headers=HEADERS)

    if localidades_response.status_code == 200:
        for item in localidades_response.json():
            if item.get("localidad"):
                localidades_disponibles.add(item["localidad"])

    if empresas_response.status_code == 200:
        for item in empresas_response.json():
            if item.get("empresa_mantenedora"):
                empresas_disponibles.add(item["empresa_mantenedora"])

    # OPTIMIZACIÓN: Procesar equipos que ya vienen embedidos en la respuesta
    for lead in leads_data:
        # Los equipos ya están incluidos gracias al join de Supabase
        equipos = lead.get("equipos", [])

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

    # Obtener datos del administrador si existe relación
    administrador = None
    if lead.get('administrador_id'):
        admin_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{lead['administrador_id']}",
            headers=HEADERS
        )
        if admin_response.status_code == 200 and admin_response.json():
            administrador = admin_response.json()[0]

    return render_template("ver_lead.html",
        lead=lead,
        equipos=equipos,
        oportunidades=oportunidades,
        visitas_seguimiento=visitas_seguimiento,
        administrador=administrador
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

# Editar Lead - CON LIMPIEZA DE NONE
@app.route("/editar_lead/<int:lead_id>", methods=["GET", "POST"])
def editar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":
        # Obtener administrador_id y convertir a int o None
        administrador_id = request.form.get("administrador_id")
        if administrador_id and administrador_id.strip():
            try:
                administrador_id = int(administrador_id)
            except ValueError:
                administrador_id = None
        else:
            administrador_id = None

        data = {
            "fecha_visita": request.form.get("fecha_visita") or None,
            "tipo_cliente": request.form.get("tipo_lead") or None,
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead") or None,
            "codigo_postal": request.form.get("codigo_postal") or None,
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona") or None,
            "persona_contacto": request.form.get("persona_contacto") or None,
            "telefono": request.form.get("telefono") or None,
            "email": request.form.get("email") or None,
            "administrador_fincas": request.form.get("administrador_fincas") or None,
            "administrador_id": administrador_id,
            "empresa_mantenedora": request.form.get("empresa_mantenedora") or None,
            "numero_ascensores": request.form.get("numero_ascensores") or None,
            "observaciones": request.form.get("observaciones") or None
        }

        # Solo dirección y localidad son obligatorios
        if not data["direccion"] or not data["localidad"]:
            flash("Dirección y Localidad son obligatorios", "error")
            return redirect(request.referrer)

        res = requests.patch(
            f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}",
            json=data,
            headers=HEADERS
        )
        if res.status_code in [200, 204]:
            return redirect(f"/ver_lead/{lead_id}")
        else:
            return f"<h3 style='color:red;'>Error al actualizar Lead</h3><pre>{res.text}</pre><a href='/leads_dashboard'>Volver</a>"

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}",
        headers=HEADERS
    )
    if response.status_code == 200 and response.json():
        lead = response.json()[0]
        # LIMPIAR VALORES NONE PARA NO MOSTRAR "none" EN EL FORMULARIO
        lead = limpiar_none(lead)
    else:
        return f"<h3 style='color:red;'>Error al obtener Lead</h3><pre>{response.text}</pre><a href='/leads_dashboard'>Volver</a>"

    # Obtener lista de administradores (usando caché)
    administradores = get_administradores_cached()

    return render_template("editar_lead.html", lead=lead, administradores=administradores)

# Editar Equipo - CON LIMPIEZA DE NONE
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
            "identificacion": request.form.get("identificacion") or None,
            "descripcion": request.form.get("observaciones") or None,
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae") or None,
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        # Solo tipo_equipo es obligatorio
        if not data["tipo_equipo"]:
            flash("Tipo de equipo es obligatorio", "error")
            return redirect(request.referrer)

        update_url = f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}"
        res = requests.patch(update_url, json=data, headers=HEADERS)
        if res.status_code in [200, 204]:
            # Obtener el cliente_id del equipo para volver a su vista
            cliente_id = equipo.get("cliente_id")
            return redirect(f"/ver_lead/{cliente_id}")
        else:
            return f"<h3 style='color:red;'>Error al actualizar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    # LIMPIAR VALORES NONE PARA NO MOSTRAR "none" EN EL FORMULARIO
    equipo = limpiar_none(equipo)
    return render_template("editar_equipo.html", equipo=equipo)

# ============================================
# MÓDULO DE OPORTUNIDADES - ACTUALIZADO
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


# ACTUALIZADO: editar_oportunidad con nuevos campos
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
                flash("Oportunidad actualizada correctamente", "success")
                return redirect(url_for("ver_oportunidad", oportunidad_id=oportunidad_id))
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


# ACTUALIZADO: ver_oportunidad con visitas y acciones
@app.route("/ver_oportunidad/<int:oportunidad_id>")
def ver_oportunidad(oportunidad_id):
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
            flash("Oportunidad no encontrada", "error")
            return redirect(url_for("oportunidades"))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
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
# NUEVAS RUTAS PARA ACCIONES
# ============================================

@app.route('/oportunidad/<int:oportunidad_id>/accion/add', methods=['POST'])
def add_accion(oportunidad_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    texto_accion = request.form.get('texto_accion', '').strip()
    
    if not texto_accion:
        flash('Debes escribir una acción', 'error')
        return redirect(url_for('ver_oportunidad', oportunidad_id=oportunidad_id))
    
    # Obtener acciones actuales
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=acciones",
        headers=HEADERS
    )
    
    if response.status_code == 200 and response.json():
        acciones = response.json()[0].get('acciones', [])
        if not isinstance(acciones, list):
            acciones = []
        
        # Añadir nueva acción
        acciones.append({
            'texto': texto_accion,
            'completada': False
        })
        
        # Actualizar en BD
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
            headers=HEADERS,
            json={'acciones': acciones}
        )
        
        flash('Acción añadida correctamente', 'success')
    
    return redirect(url_for('ver_oportunidad', oportunidad_id=oportunidad_id))


@app.route('/oportunidad/<int:oportunidad_id>/accion/toggle/<int:index>', methods=['POST'])
def toggle_accion(oportunidad_id, index):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Obtener acciones actuales
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=acciones",
        headers=HEADERS
    )
    
    if response.status_code == 200 and response.json():
        acciones = response.json()[0].get('acciones', [])
        
        if 0 <= index < len(acciones):
            # Toggle el estado
            acciones[index]['completada'] = not acciones[index]['completada']
            
            # Actualizar en BD
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
                headers=HEADERS,
                json={'acciones': acciones}
            )
    
    return redirect(url_for('ver_oportunidad', oportunidad_id=oportunidad_id))


@app.route('/oportunidad/<int:oportunidad_id>/accion/delete/<int:index>', methods=['POST'])
def delete_accion(oportunidad_id, index):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Obtener acciones actuales
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=acciones",
        headers=HEADERS
    )
    
    if response.status_code == 200 and response.json():
        acciones = response.json()[0].get('acciones', [])
        
        if 0 <= index < len(acciones):
            # Eliminar acción
            acciones.pop(index)
            
            # Actualizar en BD
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}",
                headers=HEADERS,
                json={'acciones': acciones}
            )
            
            flash('Acción eliminada', 'success')
    
    return redirect(url_for('ver_oportunidad', oportunidad_id=oportunidad_id))


# ============================================
# MÓDULO DE NOTIFICACIONES POR EMAIL
# ============================================

@app.route('/configuracion_avisos', methods=['GET', 'POST'])
def configuracion_avisos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['usuario_id']
    
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
            flash('✅ Configuración guardada correctamente', 'success')
        else:
            flash(f'❌ Error al guardar configuración: {response.text}', 'error')
        
        return redirect(url_for('configuracion_avisos'))
    
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
    
    if not config_data.get('sistema_activo'):
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
# ADMINISTRADORES
# ============================================

# Dashboard de Administradores (con pestañas)
@app.route("/administradores_dashboard", methods=["GET"])
def administradores_dashboard():
    if "usuario" not in session:
        return redirect("/")

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

        # Construir URL con filtros
        url = f"{SUPABASE_URL}/rest/v1/administradores?select=*&order=nombre_empresa.asc"

        if buscar:
            url += f"&or=(nombre_empresa.ilike.%{buscar}%,localidad.ilike.%{buscar}%,email.ilike.%{buscar}%)"

        # Obtener registros paginados con conteo
        url += f"&limit={limit}&offset={offset}"

        # Headers para obtener el conteo total
        headers_with_count = HEADERS.copy()
        headers_with_count["Prefer"] = "count=exact"

        try:
            response = requests.get(url, headers=headers_with_count, timeout=10)

            # 200 = OK, 206 = Partial Content (respuesta válida con paginación)
            if response.status_code not in [200, 206]:
                print(f"Error al cargar administradores: {response.status_code} - {response.text}")
                flash(f"Error al cargar administradores desde la base de datos (Código: {response.status_code})", "error")
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
            try:
                content_range = response.headers.get("Content-Range", "*/0")
                total_registros = int(content_range.split("/")[-1])
            except Exception as e:
                print(f"Error al parsear Content-Range: {e}")
                total_registros = 0

            # Parsear respuesta JSON
            try:
                administradores = response.json()
            except Exception as e:
                print(f"Error al parsear JSON: {e}")
                flash(f"Error al procesar datos de administradores", "error")
                return render_template(
                    "administradores_dashboard.html",
                    tab=tab,
                    administradores=[],
                    buscar=buscar,
                    page=1,
                    total_pages=1,
                    total_registros=0
                )

            # Limpiar None
            try:
                administradores = [limpiar_none(admin) for admin in administradores]
            except Exception as e:
                print(f"Error al limpiar datos: {e}")
                administradores = []

            # Calcular páginas
            total_pages = max(1, (total_registros + limit - 1) // limit)  # Al menos 1 página

            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                administradores=administradores,
                buscar=buscar,
                page=page,
                total_pages=total_pages,
                total_registros=total_registros
            )

        except requests.exceptions.Timeout:
            print(f"Error de timeout al cargar administradores")
            flash(f"Error de conexión: La base de datos tardó demasiado en responder. Por favor, intente nuevamente.", "error")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                administradores=[],
                buscar=buscar,
                page=1,
                total_pages=1,
                total_registros=0
            )
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al cargar administradores: {e}")
            flash(f"Error de conexión al cargar administradores. Por favor, verifique su conexión a internet.", "error")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                administradores=[],
                buscar=buscar,
                page=1,
                total_pages=1,
                total_registros=0
            )
        except Exception as e:
            print(f"Error inesperado al cargar administradores: {e}")
            flash(f"Error inesperado al cargar administradores. Por favor, contacte al administrador del sistema.", "error")
            return render_template(
                "administradores_dashboard.html",
                tab=tab,
                administradores=[],
                buscar=buscar,
                page=1,
                total_pages=1,
                total_registros=0
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
                flash(f"Error al cargar visitas desde la base de datos (Código: {response.status_code})", "error")
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
                flash(f"Error al procesar datos de visitas", "error")
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
            flash(f"Error de conexión: La base de datos tardó demasiado en responder. Por favor, intente nuevamente.", "error")
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
            flash(f"Error de conexión al cargar visitas. Por favor, verifique su conexión a internet.", "error")
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
            flash(f"Error inesperado al cargar visitas. Por favor, contacte al administrador del sistema.", "error")
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
        return redirect("/administradores_dashboard?tab=administradores")


# Alta de Administrador
@app.route("/nuevo_administrador", methods=["GET", "POST"])
def nuevo_administrador():
    if "usuario" not in session:
        return redirect("/")

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
            flash("El nombre de la empresa es obligatorio", "error")
            return redirect(request.referrer)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/administradores",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 201]:
            flash("Administrador creado correctamente", "success")
            return redirect("/administradores_dashboard")
        else:
            flash(f"Error al crear administrador: {response.text}", "error")
            return redirect(request.referrer)

    return render_template("nuevo_administrador.html")


# Ver Administrador
@app.route("/ver_administrador/<int:admin_id>", methods=["GET"])
def ver_administrador(admin_id):
    if "usuario" not in session:
        return redirect("/")

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


# Editar Administrador
@app.route("/editar_administrador/<int:admin_id>", methods=["GET", "POST"])
def editar_administrador(admin_id):
    if "usuario" not in session:
        return redirect("/")

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
            flash("El nombre de la empresa es obligatorio", "error")
            return redirect(request.referrer)

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
            json=data,
            headers=HEADERS
        )

        if response.status_code in [200, 201, 204]:
            flash("Administrador actualizado correctamente", "success")
            return redirect(f"/ver_administrador/{admin_id}")
        else:
            flash(f"Error al actualizar administrador: {response.text}", "error")
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


# Eliminar Administrador
@app.route("/eliminar_administrador/<int:admin_id>", methods=["GET"])
def eliminar_administrador(admin_id):
    if "usuario" not in session:
        return redirect("/")

    # Verificar si tiene clientes asociados
    clientes_check = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?administrador_id=eq.{admin_id}&select=count",
        headers=HEADERS
    )

    if clientes_check.status_code == 200 and clientes_check.json():
        num_clientes = len(clientes_check.json())
        if num_clientes > 0:
            flash(f"No se puede eliminar: el administrador tiene {num_clientes} cliente(s) asociado(s)", "error")
            return redirect(f"/ver_administrador/{admin_id}")

    # Eliminar administrador
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/administradores?id=eq.{admin_id}",
        headers=HEADERS
    )

    if response.status_code in [200, 204]:
        flash("Administrador eliminado correctamente", "success")
        return redirect("/administradores_dashboard")
    else:
        flash(f"Error al eliminar administrador: {response.text}", "error")
        return redirect(f"/ver_administrador/{admin_id}")


# ============================================
# RUTA DE PRUEBA - DROPDOWN ADMINISTRADORES
# ============================================

@app.route("/test_dropdown_admin")
def test_dropdown_admin():
    if "usuario" not in session:
        return redirect("/")

    # Test 1: Consulta directa (sin caché)
    test_direct = {"success": False, "status": 0, "count": 0, "error": ""}
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/administradores?select=id,nombre_empresa&order=nombre_empresa.asc",
            headers=HEADERS,
            timeout=10
        )
        test_direct["status"] = response.status_code
        if response.status_code == 200:
            test_direct["success"] = True
            test_direct["data"] = response.json()
            test_direct["count"] = len(test_direct["data"])
        else:
            test_direct["error"] = response.text[:500]
    except Exception as e:
        test_direct["error"] = f"{type(e).__name__}: {str(e)}"

    # Test 2: Obtener desde caché
    administradores_cached = get_administradores_cached()

    # HTML de prueba mejorado
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Dropdown Administradores - Diagnóstico</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; background: #f5f5f5; }}
            .debug-info {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .success {{ color: #28a745; font-weight: bold; }}
            .error {{ color: #dc3545; font-weight: bold; }}
            .warning {{ color: #ffc107; font-weight: bold; }}
            h1 {{ color: #333; }}
            h3 {{ color: #666; margin-top: 0; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #dee2e6; }}
            .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 5px; font-size: 14px; }}
            .badge-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .badge-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
            td:first-child {{ font-weight: bold; width: 200px; }}
            .back-link {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #366092; color: white; text-decoration: none; border-radius: 5px; }}
            .back-link:hover {{ background: #2a4a70; }}
        </style>
    </head>
    <body>
        <h1>🧪 Test Dropdown Administradores - Diagnóstico Completo</h1>

        <div class="debug-info">
            <h3>🔍 Test 1: Consulta Directa a Supabase (sin caché)</h3>
            <table>
                <tr>
                    <td>Estado:</td>
                    <td>
                        {'<span class="status-badge badge-success">✅ Éxito</span>' if test_direct['success'] else '<span class="status-badge badge-error">❌ Error</span>'}
                    </td>
                </tr>
                <tr>
                    <td>Status Code:</td>
                    <td><strong>{test_direct['status']}</strong></td>
                </tr>
                <tr>
                    <td>Administradores encontrados:</td>
                    <td><strong class="{'success' if test_direct['count'] > 0 else 'error'}">{test_direct['count']}</strong></td>
                </tr>
                {'<tr><td>Error:</td><td><pre>' + test_direct['error'] + '</pre></td></tr>' if test_direct['error'] else ''}
            </table>

            {f"<h4>📋 Datos obtenidos:</h4><pre>{test_direct.get('data', [])}</pre>" if test_direct['success'] and test_direct['count'] > 0 else ''}
        </div>

        <div class="debug-info">
            <h3>💾 Test 2: Sistema de Caché</h3>
            <table>
                <tr>
                    <td>Administradores en caché:</td>
                    <td><strong class="{'success' if len(administradores_cached) > 0 else 'error'}">{len(administradores_cached)}</strong></td>
                </tr>
                <tr>
                    <td>Timestamp del caché:</td>
                    <td>{cache_administradores['timestamp'] or 'Sin inicializar'}</td>
                </tr>
            </table>

            {f"<h4>📋 Datos en caché:</h4><pre>{administradores_cached}</pre>" if len(administradores_cached) > 0 else ''}
        </div>

        <div class="debug-info">
            <h3>🔧 Configuración de Supabase</h3>
            <table>
                <tr>
                    <td>URL:</td>
                    <td><code>{SUPABASE_URL}</code></td>
                </tr>
                <tr>
                    <td>API Key configurada:</td>
                    <td>{'✅ Sí' if SUPABASE_KEY else '❌ No'}</td>
                </tr>
            </table>
        </div>

        <div class="debug-info">
            <h3>💡 Diagnóstico</h3>
            {'<p class="success">✅ Todo funciona correctamente. Hay ' + str(test_direct['count']) + ' administradores en la base de datos.</p>' if test_direct['success'] and test_direct['count'] > 0 else ''}
            {'<p class="warning">⚠️ La conexión a Supabase funciona pero <strong>NO HAY ADMINISTRADORES</strong> en la base de datos. Necesitas crear administradores primero en <a href="/nuevo_administrador">/nuevo_administrador</a></p>' if test_direct['success'] and test_direct['count'] == 0 else ''}
            {'<p class="error">❌ Error al conectar con Supabase. Verifica:<br>1. Que la URL de Supabase sea correcta<br>2. Que el API Key esté configurado<br>3. Que la tabla "administradores" exista<br>4. Que tengas permisos de lectura</p>' if not test_direct['success'] else ''}
        </div>

        <a href="/home" class="back-link">← Volver al inicio</a>

        <script>
            console.log('📊 Diagnóstico completo:');
            console.log('Test directo:', {test_direct});
            console.log('Caché:', {administradores_cached});
        </script>
    </body>
    </html>
    """

    return html

@app.route("/admin/clear_cache")
def clear_cache():
    """Endpoint para limpiar manualmente el caché de administradores"""
    if "usuario" not in session:
        return redirect("/")

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
        <h1>Caché Actualizado</h1>
        <div class="count">{len(administradores)} administradores cargados</div>
        <p>El caché se ha limpiado y recargado correctamente.</p>
        <a href="/test_dropdown_admin" class="btn">Ver Diagnóstico</a>
        <a href="/visita_administrador" class="btn">Probar Dropdown</a>
        <a href="/home" class="btn">Volver al Inicio</a>
    </body>
    </html>
    """

# ============================================
# CIERRE
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
