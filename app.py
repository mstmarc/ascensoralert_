from flask import Flask, request, render_template_string, redirect, session, Response, url_for, flash
import requests
import os
import urllib.parse
from datetime import date, datetime, timedelta
import calendar
import io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# Datos de Supabase ACTUALIZADOS
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

# FUNCIONES AUXILIARES PARA COLORES DEL DASHBOARD
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

# Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contrasena = request.form.get("contrasena")
        if not usuario or not contrasena:
            return render_template_string(LOGIN_TEMPLATE, error="Usuario y contraseña requeridos")
        encoded_user = urllib.parse.quote(usuario, safe="")
        query = f"?nombre_usuario=eq.{encoded_user}"
        response = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios{query}", headers=HEADERS)

        if response.status_code == 200 and len(response.json()) == 1:
            user = response.json()[0]
            if user.get("contrasena", "") == contrasena:
                session["usuario"] = usuario
                return redirect("/home")
        return render_template_string(LOGIN_TEMPLATE, error="Usuario o contraseña incorrectos")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Home
@app.route("/home")
def home():
    if "usuario" not in session:
        return redirect("/")
    return render_template_string(HOME_TEMPLATE, usuario=session["usuario"])

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
            return redirect(f"/nuevo_equipo?cliente_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template_string(FORM_TEMPLATE, fecha_hoy=fecha_hoy)

# NUEVA: Visita a Administrador
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
            return render_template_string(VISITA_ADMIN_SUCCESS_TEMPLATE)
        else:
            return f"<h3 style='color:red;'>Error al registrar visita</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template_string(VISITA_ADMIN_TEMPLATE, fecha_hoy=fecha_hoy)

# Alta de Equipo
@app.route("/nuevo_equipo", methods=["GET", "POST"])
def nuevo_equipo():
    if "usuario" not in session:
        return redirect("/")
    cliente_id = request.args.get("cliente_id")

    cliente_data = None
    if cliente_id:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}", headers=HEADERS)
        if r.status_code == 200 and r.json():
            cliente_data = r.json()[0]

    if request.method == "POST":
        equipo_data = {
            "cliente_id": request.form.get("cliente_id"),
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion"),
            "descripcion": request.form.get("observaciones"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        required = [equipo_data["cliente_id"], equipo_data["tipo_equipo"]]
        if any(not field for field in required):
            return "Datos del equipo inválidos", 400

        for key, value in equipo_data.items():
            if value == "":
                equipo_data[key] = None

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            return render_template_string(EQUIPO_SUCCESS_TEMPLATE, cliente_id=cliente_id)
        else:
            return f"<h3 style='color:red;'>Error al registrar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(EQUIPO_TEMPLATE, cliente=cliente_data)

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
        
        response_admin = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?{query_clientes}&select=*", headers=HEADERS)
        
        if response_clientes.status_code != 200:
            return f"Error al obtener datos: {response_clientes.text}"
        
        clientes_mes = response_clientes.json()
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
    
    return render_template_string(REPORTE_TEMPLATE)

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
    
    return render_template_string(
        DASHBOARD_TEMPLATE_PAGINADO,
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
    
    # Obtener oportunidades de esta comunidad
    oportunidades_response = requests.get(
        f"{SUPABASE_URL}/rest/v1/oportunidades?cliente_id=eq.{lead_id}&order=fecha_creacion.desc",
        headers=HEADERS
    )
    oportunidades = []
    if oportunidades_response.status_code == 200:
        oportunidades = oportunidades_response.json()
    
    return render_template_string(VER_LEAD_TEMPLATE, lead=lead, equipos=equipos, oportunidades=oportunidades)

# Eliminar Lead
@app.route("/eliminar_lead/<int:lead_id>")
def eliminar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")
    
    requests.delete(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
    
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

    return render_template_string(EDIT_LEAD_TEMPLATE, lead=lead)

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

    return render_template_string(EQUIPO_EDIT_TEMPLATE, equipo=equipo)

# ============================================
# MÓDULO DE OPORTUNIDADES
# ============================================

@app.route("/oportunidades")
def oportunidades():
    """Dashboard de oportunidades activas"""
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
            
            return render_template_string(OPORTUNIDADES_TEMPLATE,
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
    """Crear nueva oportunidad desde vista de comunidad"""
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
            return render_template_string(CREAR_OPORTUNIDAD_TEMPLATE, cliente=cliente)
    except:
        flash("Error al cargar datos del cliente", "error")
        return redirect(url_for("leads_dashboard"))


@app.route("/editar_oportunidad/<int:oportunidad_id>", methods=["GET", "POST"])
def editar_oportunidad(oportunidad_id):
    """Editar oportunidad existente"""
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
                flash("Oportunidad actualizada", "success")
                
                response_get = requests.get(
                    f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=cliente_id",
                    headers=HEADERS
                )
                if response_get.status_code == 200:
                    cliente_id = response_get.json()[0]["cliente_id"]
                    return redirect(url_for("ver_lead", lead_id=cliente_id))
                else:
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
            return render_template_string(EDITAR_OPORTUNIDAD_TEMPLATE, oportunidad=oportunidad)
    except:
        flash("Error al cargar oportunidad", "error")
        return redirect(url_for("oportunidades"))


@app.route("/ver_oportunidad/<int:oportunidad_id>")
def ver_oportunidad(oportunidad_id):
    """Ver detalle de una oportunidad"""
    if "usuario" not in session:
        return redirect("/")
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?id=eq.{oportunidad_id}&select=*,clientes(nombre_cliente,direccion,localidad)",
            headers=HEADERS
        )
        if response.status_code == 200 and response.json():
            oportunidad = response.json()[0]
            return render_template_string(VER_OPORTUNIDAD_TEMPLATE, oportunidad=oportunidad)
        else:
            flash("Oportunidad no encontrada", "error")
            return redirect(url_for("oportunidades"))
    except:
        flash("Error al cargar oportunidad", "error")
        return redirect(url_for("oportunidades"))


@app.route("/eliminar_oportunidad/<int:oportunidad_id>")
def eliminar_oportunidad(oportunidad_id):
    """Eliminar una oportunidad"""
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
# PLANTILLAS HTML
# ============================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>AscensorAlert</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Usuario:</label><br>
                <input type="text" name="usuario" required><br><br>
                <label>Contraseña:</label><br>
                <input type="password" name="contrasena" required><br><br>
                <button type="submit" class="button">Iniciar Sesión</button>
            </form>
            {% if error %}
            <p style="color: red;">{{ error }}</p>
            {% endif %}
        </div>
    </main>
</body>
</html>
'''

HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Bienvenido, {{ usuario }}</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <a href="/formulario_lead" class="button">Añadir Visita a Instalación</a>
            <a href="/visita_administrador" class="button">Añadir Visita a Administrador</a>
            <a href="/leads_dashboard" class="button">Visualizar Datos</a>
            <a href="/oportunidades" class="button">Gestion de Oportunidades</a>
            <a href="/reporte_mensual" class="button">Descargo Comercial</a>
            <a href="/logout" class="button">Cerrar Sesión</a>
        </div>
    </main>
</body>
</html>
'''

VISITA_ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visita a Administrador</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .botones-form {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Visita a Administrador de Fincas</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Fecha de Visita:</label><br>
                <input type="date" name="fecha_visita" value="{{ fecha_hoy }}" required><br><br>

                <label>Administrador de Fincas:</label><br>
                <input type="text" name="administrador_fincas" required placeholder="Nombre del administrador"><br><br>

                <label>Persona de Contacto:</label><br>
                <input type="text" name="persona_contacto" placeholder="Opcional"><br><br>

                <label>Resultado de la Visita / Observaciones:</label><br>
                <textarea name="observaciones" rows="8" required></textarea><br><br>

                <div class="botones-form">
                    <button type="submit" class="button">Registrar Visita</button>
                    <a href="/home" class="button">Volver</a>
                </div>
            </form>
        </div>
    </main>
</body>
</html>
'''

FORM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulario Lead</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .botones-form {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Introducir datos</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Fecha de Visita:</label><br>
                <input type="date" name="fecha_visita" value="{{ fecha_hoy }}" required><br><br>

                <label>Tipo de Lead:</label><br>
                <select name="tipo_lead" required>
                    <option value="">-- Selecciona un tipo --</option>
                    <option value="Comunidad">Comunidad</option>
                    <option value="Hotel/Apartamentos">Hotel/Apartamentos</option>
                    <option value="Empresa">Empresa</option>
                    <option value="Otro">Otro</option>
                </select><br><br>

                <label>Dirección:</label><br>
                <input type="text" name="direccion" required><br><br>

                <label>Nombre de la Instalación:</label><br>
                <input type="text" name="nombre_lead" required><br><br>

                <label>Código Postal:</label><br>
                <input type="text" name="codigo_postal"><br><br>

                <label>Localidad:</label><br>
                <select name="localidad" required>
                    <option value="">-- Selecciona una localidad --</option>
                    <option value="Agaete">Agaete</option>
                    <option value="Agüimes">Agüimes</option>
                    <option value="Arguineguín">Arguineguín</option>
                    <option value="Arinaga">Arinaga</option>
                    <option value="Artenara">Artenara</option>
                    <option value="Arucas">Arucas</option>
                    <option value="Carrizal">Carrizal</option>
                    <option value="Cruce de Arinaga">Cruce de Arinaga</option>
                    <option value="Cruce de Melenara">Cruce de Melenara</option>
                    <option value="Cruce de Sardina">Cruce de Sardina</option>
                    <option value="El Burrero">El Burrero</option>
                    <option value="El Tablero">El Tablero</option>
                    <option value="Firgas">Firgas</option>
                    <option value="Gáldar">Gáldar</option>
                    <option value="Ingenio">Ingenio</option>
                    <option value="Jinámar">Jinámar</option>
                    <option value="La Aldea de San Nicolás">La Aldea de San Nicolás</option>
                    <option value="La Pardilla">La Pardilla</option>
                    <option value="Las Palmas de Gran Canaria">Las Palmas de Gran Canaria</option>
                    <option value="Maspalomas">Maspalomas</option>
                    <option value="Melenara">Melenara</option>
                    <option value="Mogán">Mogán</option>
                    <option value="Moya">Moya</option>
                    <option value="Playa de Mogán">Playa de Mogán</option>
                    <option value="Playa del Inglés">Playa del Inglés</option>
                    <option value="Puerto Rico">Puerto Rico</option>
                    <option value="Salinetas">Salinetas</option>
                    <option value="San Bartolomé de Tirajana">San Bartolomé de Tirajana</option>
                    <option value="San Fernando">San Fernando</option>
                    <option value="San Mateo">San Mateo</option>
                    <option value="Santa Brígida">Santa Brígida</option>
                    <option value="Santa Lucía de Tirajana">Santa Lucía de Tirajana</option>
                    <option value="Santa María de Guía">Santa María de Guía</option>
                    <option value="Sardina del Norte">Sardina del Norte</option>
                    <option value="Tafira">Tafira</option>
                    <option value="Tejeda">Tejeda</option>
                    <option value="Telde">Telde</option>
                    <option value="Teror">Teror</option>
                    <option value="Valleseco">Valleseco</option>
                    <option value="Valsequillo">Valsequillo</option>
                    <option value="Vecindario">Vecindario</option>
                </select><br><br>

                <label>Zona:</label><br>
                <input type="text" name="zona"><br><br>

                <label>Persona de Contacto:</label><br>
                <input type="text" name="persona_contacto"><br><br>

                <label>Teléfono:</label><br>
                <input type="text" name="telefono"><br><br>

                <label>Email:</label><br>
                <input type="email" name="email"><br><br>

                <label>Administrador de Fincas:</label><br>
                <input type="text" name="administrador_fincas" placeholder="Nombre de la empresa administradora"><br><br>

                <label>Empresa Mantenedora Actual:</label><br>
                <select name="empresa_mantenedora">
                    <option value="">-- Selecciona una empresa --</option>
                    <option value="FAIN Ascensores">FAIN Ascensores</option>
                    <option value="KONE">KONE</option>
                    <option value="Otis">Otis</option>
                    <option value="Schindler">Schindler</option>
                    <option value="TKE">TKE</option>
                    <option value="Orona">Orona</option>
                    <option value="APlus Ascensores">APlus Ascensores</option>
                    <option value="Ascensores Canarias">Ascensores Canarias</option>
                    <option value="Ascensores Domingo">Ascensores Domingo</option>
                    <option value="Ascensores Vulcano Canarias">Ascensores Vulcano Canarias</option>
                    <option value="Elevadores Canarios">Elevadores Canarios</option>
                    <option value="Fedes Ascensores">Fedes Ascensores</option>
                    <option value="Gratecsa">Gratecsa</option>
                    <option value="Lift Technology">Lift Technology</option>
                    <option value="Omega Elevadores">Omega Elevadores</option>
                    <option value="Q Ascensores">Q Ascensores</option>
                </select><br><br>

                <label>Número de Ascensores:</label><br>
                <select name="numero_ascensores" required>
                    <option value="">-- Cuantos ascensores hay? --</option>
                    <option value="1">1 ascensor</option>
                    <option value="2">2 ascensores</option>
                    <option value="3">3 ascensores</option>
                    <option value="4">4 ascensores</option>
                    <option value="5">5 ascensores</option>
                    <option value="6">6 ascensores</option>
                    <option value="7">7 ascensores</option>
                    <option value="8">8 ascensores</option>
                    <option value="9">9 ascensores</option>
                    <option value="10">10 ascensores</option>
                    <option value="11">11 ascensores</option>
                    <option value="12">12 ascensores</option>
                    <option value="13">13 ascensores</option>
                    <option value="14">14 ascensores</option>
                    <option value="15">15 ascensores</option>
                    <option value="16">16 ascensores</option>
                    <option value="17">17 ascensores</option>
                    <option value="18">18 ascensores</option>
                    <option value="19">19 ascensores</option>
                    <option value="20">20 ascensores</option>
                    <option value="20+">Más de 20 ascensores</option>
                </select><br><br>

                <label>Observaciones:</label><br>
                <textarea name="observaciones"></textarea><br><br>

                <div class="botones-form">
                    <button type="submit" class="button">Registrar Lead</button>
                    <a href="/home" class="button">Volver</a>
                </div>
            </form>
        </div>
    </main>
</body>
</html>
'''

EQUIPO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulario Equipo</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .botones-form {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
<header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Introducir datos</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <input type="hidden" name="cliente_id" value="{{ cliente['id'] }}">

                <label>Tipo de Equipo:</label><br>
                <select name="tipo_equipo" required>
                    <option value="">-- Selecciona un tipo --</option>
                    <option value="Ascensor">Ascensor</option>
                    <option value="Elevador">Elevador</option>
                    <option value="Montaplatos">Montaplatos</option>
                    <option value="Montacargas">Montacargas</option>
                    <option value="Plataforma Salvaescaleras">Plataforma Salvaescaleras</option>
                    <option value="Otro">Otro</option>
                </select><br><br>

                <label>Identificación del Ascensor:</label><br>
                <input type="text" name="identificacion" placeholder="Ej: Ascensor A, Principal, Garaje, etc."><br><br>

                <label>Fecha Vencimiento Contrato:</label><br>
                <input type="date" name="fecha_vencimiento_contrato"><br><br>

                <label>RAE (solo para ascensores):</label><br>
                <input type="text" name="rae"><br><br>

                <label>Próxima IPO: <em>(consultar placa del ascensor)</em></label><br>
                <input type="date" name="ipo_proxima"><br><br>

                <label>Observaciones:</label><br>
                <textarea name="observaciones"></textarea><br><br>

                <div class="botones-form">
                    <button type="submit" class="button">Registrar Equipo</button>
                    <a href="/home" class="button">Volver</a>
                </div>
            </form>
        </div>
    </main>
</body>
</html>
'''

EDIT_LEAD_TEMPLATE = '''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Editar Lead</title><link rel="stylesheet" href="/static/styles.css?v=4"><style>.botones-form{display:flex;gap:10px;margin-top:20px;}.btn-eliminar-form{background:#dc3545;}.btn-eliminar-form:hover{background:#c82333;}</style><script>function confirmarEliminacionComunidad(){return confirm('⚠️ ATENCIÓN: Esto eliminará la comunidad y TODOS sus equipos asociados.\\n\\n¿Estás seguro de que quieres continuar?\\n\\nEsta acción no se puede deshacer.');}</script></head><body><header><div class="header-container"><div class="logo-container"><a href="/home"><img src="/static/logo-fedes-ascensores.png" alt="Logo" class="logo"></a></div><div class="title-container"><h1>Editar Lead</h1></div></div></header><main><div class="menu"><form method="POST"><label>Fecha:</label><br><input type="date" name="fecha_visita" value="{{ lead.fecha_visita }}" required><br><br><label>Tipo:</label><br><select name="tipo_lead" required><option value="">-- Tipo --</option><option value="Comunidad" {% if lead.tipo_cliente == 'Comunidad' %}selected{% endif %}>Comunidad</option><option value="Hotel/Apartamentos" {% if lead.tipo_cliente == 'Hotel/Apartamentos' %}selected{% endif %}>Hotel/Apartamentos</option><option value="Empresa" {% if lead.tipo_cliente == 'Empresa' %}selected{% endif %}>Empresa</option><option value="Otro" {% if lead.tipo_cliente == 'Otro' %}selected{% endif %}>Otro</option></select><br><br><label>Dirección:</label><br><input type="text" name="direccion" value="{{ lead.direccion }}" required><br><br><label>Nombre:</label><br><input type="text" name="nombre_lead" value="{{ lead.nombre_cliente }}" required><br><br><label>CP:</label><br><input type="text" name="codigo_postal" value="{{ lead.codigo_postal }}"><br><br><label>Localidad:</label><br><input type="text" name="localidad" value="{{ lead.localidad }}" required><br><br><label>Zona:</label><br><input type="text" name="zona" value="{{ lead.zona }}"><br><br><label>Contacto:</label><br><input type="text" name="persona_contacto" value="{{ lead.persona_contacto }}"><br><br><label>Teléfono:</label><br><input type="text" name="telefono" value="{{ lead.telefono }}"><br><br><label>Email:</label><br><input type="email" name="email" value="{{ lead.email }}"><br><br><label>Admin Fincas:</label><br><input type="text" name="administrador_fincas" value="{{ lead.administrador_fincas }}"><br><br><label>Num Ascensores:</label><br><input type="text" name="numero_ascensores" value="{{ lead.numero_ascensores }}" required><br><br><label>Observaciones:</label><br><textarea name="observaciones">{{ lead.observaciones }}</textarea><br><br><div class="botones-form"><button type="submit" class="button">Actualizar</button><a href="/leads_dashboard" class="button">Volver</a><a href="/eliminar_lead/{{ lead.id }}" class="button btn-eliminar-form" onclick="return confirmarEliminacionComunidad()">Eliminar Comunidad</a></div></form></div></main></body></html>'''

VER_LEAD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detalle Lead</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .detalle-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .seccion {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        
        .seccion h2 {
            color: #366092;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #366092;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .info-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .info-item label {
            font-weight: bold;
            color: #366092;
            display: block;
            margin-bottom: 5px;
            font-size: 14px;
        }
        
        .info-item span {
            color: #333;
            font-size: 15px;
        }
        
        .equipos-tabla {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .equipos-tabla th {
            background: #366092;
            color: white;
            padding: 10px;
            text-align: left;
            border: 1px solid #2a4a70;
        }
        
        .equipos-tabla td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        .equipos-tabla tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .equipos-tabla tr:hover {
            background: #e9ecef;
        }
        
        .btn-accion-small {
            background: #366092;
            color: white;
            padding: 5px 10px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
            display: inline-block;
            transition: all 0.3s;
            margin: 2px;
        }
        
        .btn-accion-small:hover {
            background: #2a4a70;
        }
        
        .botones-accion {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .no-equipos {
            text-align: center;
            padding: 30px;
            color: #999;
            font-style: italic;
        }
        
        .oportunidad-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 4px solid #366092;
        }
        
        .oportunidad-card.activa {
            border-left-color: #28a745;
            background: #d4edda;
        }
        
        .oportunidad-card.ganada {
            border-left-color: #007bff;
            background: #d1ecf1;
        }
        
        .oportunidad-card.perdida {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        
        .oportunidad-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .oportunidad-tipo {
            font-weight: bold;
            font-size: 16px;
        }
        
        .oportunidad-estado {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .oportunidad-estado.activa {
            background: #28a745;
            color: white;
        }
        
        .oportunidad-estado.ganada {
            background: #007bff;
            color: white;
        }
        
        .oportunidad-estado.perdida {
            background: #dc3545;
            color: white;
        }
        
        .oportunidad-detalles {
            font-size: 14px;
            color: #555;
            line-height: 1.6;
        }
        
        .btn-crear-oportunidad {
            background: #28a745;
        }
        
        .btn-crear-oportunidad:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-container">
            <div class="logo-container">
                <a href="/home">
                    <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
                </a>
            </div>
            <div class="title-container">
                <h1>Detalle de la Comunidad</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <div class="detalle-container">
                
                <!-- DATOS DE LA COMUNIDAD -->
                <div class="seccion">
                    <h2>Informacion de la Comunidad</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Direccion:</label>
                            <span>{{ lead.direccion or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Nombre:</label>
                            <span>{{ lead.nombre_cliente or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Tipo:</label>
                            <span>{{ lead.tipo_cliente or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Localidad:</label>
                            <span>{{ lead.localidad or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Codigo Postal:</label>
                            <span>{{ lead.codigo_postal or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Zona:</label>
                            <span>{{ lead.zona or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Fecha de Visita:</label>
                            <span>{{ lead.fecha_visita or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Num Ascensores Previsto:</label>
                            <span>{{ lead.numero_ascensores or '-' }}</span>
                        </div>
                    </div>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Persona de Contacto:</label>
                            <span>{{ lead.persona_contacto or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Telefono:</label>
                            <span>{{ lead.telefono or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Email:</label>
                            <span>{{ lead.email or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Administrador de Fincas:</label>
                            <span>{{ lead.administrador_fincas or '-' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Empresa Mantenedora Actual:</label>
                            <span>{{ lead.empresa_mantenedora or '-' }}</span>
                        </div>
                    </div>
                    
                    {% if lead.observaciones %}
                    <div class="info-item" style="grid-column: 1/-1;">
                        <label>Observaciones:</label>
                        <span>{{ lead.observaciones }}</span>
                    </div>
                    {% endif %}
                </div>
                
                <!-- OPORTUNIDADES COMERCIALES -->
                <div class="seccion">
                    <h2>Oportunidades Comerciales ({{ oportunidades|length }})</h2>
                    
                    {% if oportunidades %}
                        {% for op in oportunidades %}
                        <div class="oportunidad-card {{ op.estado }}">
                            <div class="oportunidad-header">
                                <div class="oportunidad-tipo">{{ op.tipo }}</div>
                                <span class="oportunidad-estado {{ op.estado }}">{{ op.estado|upper }}</span>
                            </div>
                            <div class="oportunidad-detalles">
                                {% if op.descripcion %}
                                <p><strong>Descripcion:</strong> {{ op.descripcion }}</p>
                                {% endif %}
                                {% if op.valor_estimado %}
                                <p><strong>Valor estimado:</strong> {{ "%.2f"|format(op.valor_estimado) }} EUR</p>
                                {% endif %}
                                <p><strong>Creada:</strong> {{ op.fecha_creacion[:10] }}</p>
                                {% if op.observaciones %}
                                <p><strong>Observaciones:</strong> {{ op.observaciones }}</p>
                                {% endif %}
                                <div style="margin-top: 10px;">
                                    <a href="/ver_oportunidad/{{ op.id }}" class="btn-accion-small">Ver Detalle</a>
                                    <a href="/editar_oportunidad/{{ op.id }}" class="btn-accion-small">Editar</a>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="no-equipos">
                            No hay oportunidades registradas para esta comunidad
                        </div>
                    {% endif %}
                    
                    <div style="margin-top: 15px;">
                        <a href="/crear_oportunidad/{{ lead.id }}" class="button btn-crear-oportunidad">+ Crear Oportunidad</a>
                    </div>
                </div>
                
                <!-- EQUIPOS/ASCENSORES -->
                <div class="seccion">
                    <h2>Equipos/Ascensores ({{ equipos|length }})</h2>
                    
                    {% if equipos %}
                    <table class="equipos-tabla">
                        <thead>
                            <tr>
                                <th>Tipo</th>
                                <th>Identificacion</th>
                                <th>RAE</th>
                                <th>Proxima IPO</th>
                                <th>Contrato Vence</th>
                                <th>Observaciones</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for equipo in equipos %}
                            <tr>
                                <td>{{ equipo.tipo_equipo }}</td>
                                <td>{{ equipo.identificacion }}</td>
                                <td>{{ equipo.rae }}</td>
                                <td>{{ equipo.ipo_proxima }}</td>
                                <td>{{ equipo.fecha_vencimiento_contrato }}</td>
                                <td>{{ equipo.descripcion }}</td>
                                <td style="white-space: nowrap;">
                                    <a href="/editar_equipo/{{ equipo.id }}" class="btn-accion-small">Editar</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div class="no-equipos">
                        No hay equipos registrados para esta comunidad
                    </div>
                    {% endif %}
                </div>
                
                <!-- BOTONES DE ACCIÓN -->
                <div class="botones-accion">
                    <a href="/editar_lead/{{ lead.id }}" class="button">Editar Comunidad</a>
                    <a href="/nuevo_equipo?cliente_id={{ lead.id }}" class="button">Añadir Equipo</a>
                    <a href="/leads_dashboard" class="button">Volver al Dashboard</a>
                </div>
                
            </div>
        </div>
    </main>
</body>
</html>
'''

REPORTE_TEMPLATE = '''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Descargo Comercial</title><link rel="stylesheet" href="/static/styles.css?v=4"></head><body><header><div class="header-container"><div class="logo-container"><a href="/home"><img src="/static/logo-fedes-ascensores.png" alt="Logo" class="logo"></a></div><div class="title-container"><h1>Descargo Comercial</h1></div></div></header><main><div class="menu"><h3>Generar Descargo Mensual</h3><form method="POST"><label>Mes:</label><br><select name="mes" required><option value="">-- Mes --</option><option value="1">Enero</option><option value="2">Febrero</option><option value="3">Marzo</option><option value="4">Abril</option><option value="5">Mayo</option><option value="6">Junio</option><option value="7">Julio</option><option value="8">Agosto</option><option value="9">Septiembre</option><option value="10">Octubre</option><option value="11">Noviembre</option><option value="12">Diciembre</option></select><br><br><label>Año:</label><br><select name="año" required><option value="">-- Año --</option><option value="2024">2024</option><option value="2025">2025</option><option value="2026">2026</option></select><br><br><button type="submit" class="button">Generar Excel</button></form><br><a href="/home" class="button">Volver</a></div></main></body></html>'''

EQUIPO_EDIT_TEMPLATE = '''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Editar Equipo</title><link rel="stylesheet" href="/static/styles.css?v=4"><style>.botones-form{display:flex;gap:10px;margin-top:20px;}.btn-eliminar-form{background:#dc3545;}.btn-eliminar-form:hover{background:#c82333;}</style><script>function confirmarEliminacion(){return confirm('¿Estás seguro de que quieres eliminar este equipo?\\n\\nEsta acción no se puede deshacer.');}</script></head><body><header><div class="header-container"><div class="logo-container"><a href="/home"><img src="/static/logo-fedes-ascensores.png" alt="Logo" class="logo"></a></div><div class="title-container"><h1>Editar Equipo</h1></div></div></header><main><div class="menu"><form method="POST"><label>Tipo:</label><br><input type="text" name="tipo_equipo" value="{{ equipo.tipo_equipo }}" required><br><br><label>Identificación:</label><br><input type="text" name="identificacion" value="{{ equipo.identificacion }}"><br><br><label>Vencimiento Contrato:</label><br><input type="date" name="fecha_vencimiento_contrato" value="{{ equipo.fecha_vencimiento_contrato }}"><br><br><label>RAE:</label><br><input type="text" name="rae" value="{{ equipo.rae }}"><br><br><label>Próxima IPO:</label><br><input type="date" name="ipo_proxima" value="{{ equipo.ipo_proxima }}"><br><br><label>Observaciones:</label><br><textarea name="observaciones">{{ equipo.descripcion }}</textarea><br><br><div class="botones-form"><button type="submit" class="button">Actualizar</button><a href="/home" class="button">Volver</a><a href="/eliminar_equipo/{{ equipo.id }}" class="button btn-eliminar-form" onclick="return confirmarEliminacion()">Eliminar Equipo</a></div></form></div></main></body></html>'''

EQUIPO_SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Equipo Registrado</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .botones-form {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Equipo Registrado</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <h3>Equipo registrado correctamente</h3>
            <p>El equipo se ha añadido a la base de datos.</p>
            <div class="botones-form">
                <a href="/nuevo_equipo?cliente_id={{ cliente_id }}" class="button">Añadir otro equipo</a>
                <a href="/home" class="button">Finalizar y volver al inicio</a>
            </div>
        </div>
    </main>
</body>
</html>
'''

VISITA_ADMIN_SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visita Registrada</title>
    <link rel="stylesheet" href="/static/styles.css?v=4">
    <style>
        .botones-form {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <header>
    <div class="header-container">
        <div class="logo-container">
            <a href="/home">
                <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
            </a>
        </div>
        <div class="title-container">
            <h1>Visita Registrada</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <h3>Visita registrada correctamente</h3>
            <p>La visita al administrador se ha registrado en la base de datos.</p>
            <div class="botones-form">
                <a href="/visita_administrador" class="button">Añadir otra visita</a>
                <a href="/home" class="button">Volver al inicio</a>
            </div>
        </div>
    </main>
</body>
</html>
'''

DASHBOARD_TEMPLATE_PAGINADO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Leads - AscensorAlert</title>
    <link rel="stylesheet" href="/static/styles.css?v=5">
    <style>
        .buscador-destacado {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .buscador-input-container {
            display: flex;
            gap: 10px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .buscador-input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .buscador-input:focus {
            outline: 3px solid rgba(255,255,255,0.5);
        }
        
        .btn-buscar {
            background: white;
            color: #667eea;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .btn-buscar:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .buscador-label {
            color: white;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
            font-size: 18px;
        }
        
        .filtros {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            border: 1px solid #ddd;
        }
        
        .filtro-grupo {
            display: flex;
            flex-direction: column;
        }
        
        .filtro-grupo label {
            font-weight: bold;
            color: #366092;
            margin-bottom: 5px;
            font-size: 14px;
            height: 20px;
        }
        
        .filtro-grupo select {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border 0.3s;
            height: 44px;
        }
        
        .filtro-grupo select:focus {
            outline: none;
            border-color: #366092;
        }
        
        .btn-limpiar {
            background: #6c757d;
            color: white;
            padding: 0 25px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            height: 44px;
        }
        
        .btn-limpiar:hover {
            background: #5a6268;
        }
        
        .paginacion {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .paginacion-info {
            color: #366092;
            font-weight: bold;
            font-size: 16px;
        }
        
        .btn-paginacion {
            background: #366092;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        
        .btn-paginacion:hover:not(:disabled) {
            background: #2a4a70;
            transform: translateY(-2px);
        }
        
        .btn-paginacion:disabled {
            background: #ccc;
            cursor: not-allowed;
            opacity: 0.5;
        }
        
        .info-resultados {
            text-align: center;
            color: #366092;
            margin: 15px 0;
            font-weight: bold;
            font-size: 16px;
            background: #e7f3ff;
            padding: 12px;
            border-radius: 8px;
        }
        
        .tabla-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #ddd;
        }
        
        th {
            background: #366092;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #2a4a70;
        }
        
        td {
            padding: 10px 12px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        tr:hover {
            background: #e9ecef;
        }
        
        .btn-accion {
            background: #366092;
            color: white;
            padding: 6px 12px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 13px;
            display: inline-block;
            transition: all 0.3s;
            margin: 2px;
        }
        
        .btn-accion:hover {
            background: #2a4a70;
        }
        
        .btn-ver {
            background: #28a745;
        }
        
        .btn-ver:hover {
            background: #218838;
        }
        
        .acciones-cell {
            white-space: nowrap;
        }
        
        .leyenda {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #ddd;
        }
        
        .leyenda h3 {
            color: #366092;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .leyenda-items {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .leyenda-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .color-box {
            width: 30px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #999;
        }
        
        .color-amarillo { background-color: #FFF59D; }
        .color-rojo { background-color: #FFCDD2; }
        
        @media (max-width: 768px) {
            .filtros {
                grid-template-columns: 1fr;
            }
            
            table {
                font-size: 12px;
            }
            
            th, td {
                padding: 8px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-container">
            <div class="logo-container">
                <a href="/home">
                    <img src="/static/logo-fedes-ascensores.png" alt="Logo Fedes Ascensores" class="logo">
                </a>
            </div>
            <div class="title-container">
                <h1>Dashboard de Leads por Comunidades</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <!-- Buscador destacado por dirección -->
            <form method="GET" action="/leads_dashboard">
                <div class="buscador-destacado">
                    <div class="buscador-label">Buscar por Direccion</div>
                    <div class="buscador-input-container">
                        <input 
                            type="text" 
                            name="buscar_direccion" 
                            class="buscador-input"
                            value="{{ buscar_direccion }}" 
                            placeholder="Ej: Calle Mayor, Avenida..."
                            autofocus
                        >
                        <button type="submit" class="btn-buscar">Buscar</button>
                    </div>
                </div>
                
                <!-- Filtros adicionales -->
                <div class="filtros">
                    <div class="filtro-grupo">
                        <label>Localidad:</label>
                        <select name="localidad">
                            <option value="">Todas</option>
                            {% for loc in localidades %}
                            <option value="{{ loc }}" {% if filtro_localidad == loc %}selected{% endif %}>{{ loc }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="filtro-grupo">
                        <label>Empresa Mantenedora:</label>
                        <select name="empresa">
                            <option value="">Todas</option>
                            {% for emp in empresas %}
                            <option value="{{ emp }}" {% if filtro_empresa == emp %}selected{% endif %}>{{ emp }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="filtro-grupo">
                        <label>Urgencia IPO:</label>
                        <select name="ipo_urgencia">
                            <option value="">Todas</option>
                            <option value="15_dias" {% if filtro_ipo_urgencia == '15_dias' %}selected{% endif %}>15 dias antes</option>
                            <option value="ipo_pasada_30" {% if filtro_ipo_urgencia == 'ipo_pasada_30' %}selected{% endif %}>IPO pasada hasta 30 dias</option>
                            <option value="30_90_dias" {% if filtro_ipo_urgencia == '30_90_dias' %}selected{% endif %}>30-90 dias</option>
                        </select>
                    </div>
                    
                    <div class="filtro-grupo">
                        <label>&nbsp;</label>
                        <a href="/leads_dashboard" class="btn-limpiar">Limpiar Filtros</a>
                    </div>
                </div>
                
                <!-- Mantener página en filtros -->
                <input type="hidden" name="page" value="1">
            </form>
            
            <div class="info-resultados">
                Mostrando {{ rows|length }} registros de {{ total_registros }} totales
            </div>
            
            <!-- Paginación superior -->
            <div class="paginacion">
                {% if page > 1 %}
                    <a href="?page={{ page - 1 }}&localidad={{ filtro_localidad }}&empresa={{ filtro_empresa }}&buscar_direccion={{ buscar_direccion }}&ipo_urgencia={{ filtro_ipo_urgencia }}" class="btn-paginacion">Anterior</a>
                {% else %}
                    <button class="btn-paginacion" disabled>Anterior</button>
                {% endif %}
                
                <span class="paginacion-info">Pagina {{ page }} de {{ total_pages }}</span>
                
                {% if page < total_pages %}
                    <a href="?page={{ page + 1 }}&localidad={{ filtro_localidad }}&empresa={{ filtro_empresa }}&buscar_direccion={{ buscar_direccion }}&ipo_urgencia={{ filtro_ipo_urgencia }}" class="btn-paginacion">Siguiente</a>
                {% else %}
                    <button class="btn-paginacion" disabled>Siguiente</button>
                {% endif %}
            </div>
            
            <!-- Leyenda de colores -->
            <div class="leyenda">
                <h3>Leyenda de Colores:</h3>
                <div class="leyenda-items">
                    <div class="leyenda-item">
                        <span class="color-box color-amarillo"></span>
                        <span><strong>IPO:</strong> 15 dias antes</span>
                    </div>
                    <div class="leyenda-item">
                        <span class="color-box color-rojo"></span>
                        <span><strong>IPO:</strong> Pasada hasta 30 dias (OPORTUNIDAD)</span>
                    </div>
                    <div class="leyenda-item">
                        <span class="color-box color-amarillo"></span>
                        <span><strong>Contrato:</strong> Vence 30-90 dias</span>
                    </div>
                    <div class="leyenda-item">
                        <span class="color-box color-rojo"></span>
                        <span><strong>Contrato:</strong> Vencido o menos 30 dias</span>
                    </div>
                </div>
            </div>
            
            <!-- Tabla de resultados -->
            <div class="tabla-container">
                <table>
                    <thead>
                        <tr>
                            <th>Direccion</th>
                            <th>Localidad</th>
                            <th>Num Ascensores</th>
                            <th>Empresa Mantenedora</th>
                            <th>Proxima IPO</th>
                            <th>Contrato Vence</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if rows %}
                            {% for row in rows %}
                            <tr>
                                <td>{{ row.direccion }}</td>
                                <td>{{ row.localidad }}</td>
                                <td style="text-align: center;">{{ row.total_equipos }}</td>
                                <td>{{ row.empresa_mantenedora }}</td>
                                <td style="{{ row.color_ipo }}">{{ row.ipo_proxima }}</td>
                                <td style="{{ row.color_contrato }}">{{ row.contrato_vence }}</td>
                                <td class="acciones-cell">
                                    <a href="/ver_lead/{{ row.lead_id }}" class="btn-accion btn-ver">Ver</a>
                                    <a href="/editar_lead/{{ row.lead_id }}" class="btn-accion">Editar</a>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="7" style="text-align: center; padding: 40px; color: #999;">
                                    No se encontraron comunidades con los filtros aplicados
                                </td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
            
            <!-- Paginación inferior -->
            <div class="paginacion">
                {% if page > 1 %}
                    <a href="?page={{ page - 1 }}&localidad={{ filtro_localidad }}&empresa={{ filtro_empresa }}&buscar_direccion={{ buscar_direccion }}&ipo_urgencia={{ filtro_ipo_urgencia }}" class="btn-paginacion">Anterior</a>
                {% else %}
                    <button class="btn-paginacion" disabled>Anterior</button>
                {% endif %}
                
                <span class="paginacion-info">Pagina {{ page }} de {{ total_pages }}</span>
                
                {% if page < total_pages %}
                    <a href="?page={{ page + 1 }}&localidad={{ filtro_localidad }}&empresa={{ filtro_empresa }}&buscar_direccion={{ buscar_direccion }}&ipo_urgencia={{ filtro_ipo_urgencia }}" class="btn-paginacion">Siguiente</a>
                {% else %}
                    <button class="btn-paginacion" disabled>Siguiente</button>
                {% endif %}
            </div>
            
            <br>
            <a href="/home" class="button">Volver al Home</a>
        </div>
    </main>
</body>
</html>
"""

# TEMPLATES DE OPORTUNIDADES

OPORTUNIDADES_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oportunidades - AscensorAlert</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        
        .header { background: #2c3e50; color: white; padding: 20px; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header-nav { margin-top: 15px; }
        .header-nav a { color: white; text-decoration: none; margin-right: 20px; opacity: 0.9; }
        .header-nav a:hover { opacity: 1; text-decoration: underline; }
        
        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
        
        .stats { display: flex; gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { font-size: 14px; color: #666; margin-bottom: 10px; }
        .stat-card .number { font-size: 32px; font-weight: bold; }
        .stat-card.activas .number { color: #27ae60; }
        .stat-card.ganadas .number { color: #3498db; }
        .stat-card.perdidas .number { color: #95a5a6; }
        
        .oportunidades-list { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .oportunidad-item { padding: 20px; border-bottom: 1px solid #eee; }
        .oportunidad-item:last-child { border-bottom: none; }
        .oportunidad-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px; }
        .oportunidad-info h3 { font-size: 16px; margin-bottom: 5px; }
        .oportunidad-info .ubicacion { color: #666; font-size: 14px; }
        
        .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .badge.activa { background: #d4edda; color: #155724; }
        .badge.ganada { background: #d1ecf1; color: #0c5460; }
        .badge.perdida { background: #f8d7da; color: #721c24; }
        
        .oportunidad-detalles { margin-top: 10px; }
        .oportunidad-detalles p { color: #666; font-size: 14px; margin-bottom: 5px; }
        .oportunidad-detalles strong { color: #333; }
        
        .actions { margin-top: 10px; }
        .btn { display: inline-block; padding: 8px 16px; background: #3498db; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }
        .btn:hover { background: #2980b9; }
        
        .empty-state { padding: 60px 20px; text-align: center; color: #666; }
        .empty-state p { margin-top: 10px; }
        
        .alert { padding: 12px 20px; margin-bottom: 20px; border-radius: 4px; }
        .alert.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Oportunidades Comerciales</h1>
        <div class="header-nav">
            <a href="/home">Inicio</a>
            <a href="/leads_dashboard">Ver Comunidades</a>
            <a href="/logout">Cerrar Sesion</a>
        </div>
    </div>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="stats">
            <div class="stat-card activas">
                <h3>Activas</h3>
                <div class="number">{{ activas }}</div>
            </div>
            <div class="stat-card ganadas">
                <h3>Ganadas (Total)</h3>
                <div class="number">{{ ganadas }}</div>
            </div>
            <div class="stat-card perdidas">
                <h3>Perdidas</h3>
                <div class="number">{{ perdidas }}</div>
            </div>
        </div>
        
        <div class="oportunidades-list">
            {% if oportunidades %}
                {% for op in oportunidades %}
                <div class="oportunidad-item">
                    <div class="oportunidad-header">
                        <div class="oportunidad-info">
                            <h3>{{ op.clientes.nombre_cliente or op.clientes.direccion }}</h3>
                            <div class="ubicacion">{{ op.clientes.direccion }} - {{ op.clientes.localidad }}</div>
                        </div>
                        <span class="badge {{ op.estado }}">{{ op.estado|upper }}</span>
                    </div>
                    
                    <div class="oportunidad-detalles">
                        <p><strong>Tipo:</strong> {{ op.tipo }}</p>
                        {% if op.descripcion %}
                        <p><strong>Descripcion:</strong> {{ op.descripcion }}</p>
                        {% endif %}
                        {% if op.valor_estimado %}
                        <p><strong>Valor estimado:</strong> {{ "%.2f"|format(op.valor_estimado) }} EUR</p>
                        {% endif %}
                        <p><strong>Creada:</strong> {{ op.fecha_creacion[:10] }}</p>
                        {% if op.fecha_cierre %}
                        <p><strong>Cerrada:</strong> {{ op.fecha_cierre[:10] }}</p>
                        {% endif %}
                    </div>
                    
                    <div class="actions">
                        <a href="/ver_oportunidad/{{ op.id }}" class="btn">Ver Detalle</a>
                        <a href="/ver_lead/{{ op.cliente_id }}" class="btn">Ver Comunidad</a>
                        <a href="/editar_oportunidad/{{ op.id }}" class="btn">Editar</a>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <h2>No hay oportunidades todavia</h2>
                    <p>Las oportunidades apareceran aqui cuando las crees desde la vista de comunidades</p>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

CREAR_OPORTUNIDAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nueva Oportunidad - AscensorAlert</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        
        .header { background: #2c3e50; color: white; padding: 20px; }
        .header h1 { font-size: 24px; }
        
        .container { max-width: 800px; margin: 20px auto; padding: 0 20px; }
        
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { margin-bottom: 10px; }
        .comunidad-info { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .comunidad-info p { margin-bottom: 5px; color: #666; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .form-group small { color: #666; font-size: 12px; display: block; margin-top: 5px; }
        
        .form-actions { display: flex; gap: 10px; margin-top: 30px; }
        .btn { padding: 12px 24px; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background: #27ae60; color: white; }
        .btn-primary:hover { background: #229954; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-secondary:hover { background: #7f8c8d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nueva Oportunidad</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>Crear Oportunidad Comercial</h2>
            
            <div class="comunidad-info">
                <p><strong>Comunidad:</strong> {{ cliente.nombre_cliente or cliente.direccion }}</p>
                <p><strong>Direccion:</strong> {{ cliente.direccion }}, {{ cliente.localidad }}</p>
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="tipo">Tipo de Oportunidad *</label>
                    <select name="tipo" id="tipo" required>
                        <option value="">Seleccionar...</option>
                        <option value="Descontento con empresa mantenedora">Descontento con empresa mantenedora</option>
                        <option value="Fecha de finalizacion de contrato proxima">Fecha de finalizacion de contrato proxima</option>
                        <option value="Presupuesto elevado de subsanacion IPO">Presupuesto elevado de subsanacion IPO</option>
                        <option value="Modernizacion / Sustitucion prevista">Modernizacion / Sustitucion prevista</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="descripcion">Descripcion</label>
                    <textarea name="descripcion" id="descripcion" placeholder="Detalles de la oportunidad..."></textarea>
                </div>
                
                <div class="form-group">
                    <label for="valor_estimado">Valor Estimado (EUR)</label>
                    <input type="number" name="valor_estimado" id="valor_estimado" step="0.01" placeholder="Ej: 5000">
                    <small>Valor estimado del contrato o servicio</small>
                </div>
                
                <div class="form-group">
                    <label for="observaciones">Observaciones</label>
                    <textarea name="observaciones" id="observaciones" placeholder="Notas adicionales, contactos, proximos pasos..."></textarea>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Crear Oportunidad</button>
                    <a href="/ver_lead/{{ cliente.id }}" class="btn btn-secondary">Cancelar</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

EDITAR_OPORTUNIDAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Oportunidad - AscensorAlert</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        
        .header { background: #2c3e50; color: white; padding: 20px; }
        .header h1 { font-size: 24px; }
        
        .container { max-width: 800px; margin: 20px auto; padding: 0 20px; }
        
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { margin-bottom: 10px; }
        .comunidad-info { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .comunidad-info p { margin-bottom: 5px; color: #666; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .form-group small { color: #666; font-size: 12px; display: block; margin-top: 5px; }
        
        .estado-group { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .estado-option { position: relative; }
        .estado-option input[type="radio"] { position: absolute; opacity: 0; }
        .estado-option label { display: block; padding: 15px; border: 2px solid #ddd; border-radius: 4px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .estado-option input[type="radio"]:checked + label { border-color: #3498db; background: #ebf5fb; font-weight: bold; }
        
        .form-actions { display: flex; gap: 10px; margin-top: 30px; flex-wrap: wrap; }
        .btn { padding: 12px 24px; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-secondary:hover { background: #7f8c8d; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Editar Oportunidad</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>Actualizar Oportunidad</h2>
            
            <div class="comunidad-info">
                <p><strong>Comunidad:</strong> {{ oportunidad.clientes.nombre_cliente or oportunidad.clientes.direccion }}</p>
                <p><strong>Direccion:</strong> {{ oportunidad.clientes.direccion }}</p>
                <p><strong>Creada:</strong> {{ oportunidad.fecha_creacion[:10] }}</p>
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="tipo">Tipo de Oportunidad *</label>
                    <select name="tipo" id="tipo" required>
                        <option value="Descontento con empresa mantenedora" {% if oportunidad.tipo == "Descontento con empresa mantenedora" %}selected{% endif %}>Descontento con empresa mantenedora</option>
                        <option value="Fecha de finalizacion de contrato proxima" {% if oportunidad.tipo == "Fecha de finalizacion de contrato proxima" %}selected{% endif %}>Fecha de finalizacion de contrato proxima</option>
                        <option value="Presupuesto elevado de subsanacion IPO" {% if oportunidad.tipo == "Presupuesto elevado de subsanacion IPO" %}selected{% endif %}>Presupuesto elevado de subsanacion IPO</option>
                        <option value="Modernizacion / Sustitucion prevista" {% if oportunidad.tipo == "Modernizacion / Sustitucion prevista" %}selected{% endif %}>Modernizacion / Sustitucion prevista</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Estado *</label>
                    <div class="estado-group">
                        <div class="estado-option">
                            <input type="radio" name="estado" id="activa" value="activa" {% if oportunidad.estado == "activa" %}checked{% endif %} required>
                            <label for="activa">Activa</label>
                        </div>
                        <div class="estado-option">
                            <input type="radio" name="estado" id="ganada" value="ganada" {% if oportunidad.estado == "ganada" %}checked{% endif %}>
                            <label for="ganada">Ganada</label>
                        </div>
                        <div class="estado-option">
                            <input type="radio" name="estado" id="perdida" value="perdida" {% if oportunidad.estado == "perdida" %}checked{% endif %}>
                            <label for="perdida">Perdida</label>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="descripcion">Descripcion</label>
                    <textarea name="descripcion" id="descripcion" placeholder="Detalles de la oportunidad...">{{ oportunidad.descripcion or '' }}</textarea>
                </div>
                
                <div class="form-group">
                    <label for="valor_estimado">Valor Estimado (EUR)</label>
                    <input type="number" name="valor_estimado" id="valor_estimado" step="0.01" value="{{ oportunidad.valor_estimado or '' }}" placeholder="Ej: 5000">
                </div>
                
                <div class="form-group">
                    <label for="observaciones">Observaciones</label>
                    <textarea name="observaciones" id="observaciones" placeholder="Notas, seguimiento, proximos pasos...">{{ oportunidad.observaciones or '' }}</textarea>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Guardar Cambios</button>
                    <a href="/ver_lead/{{ oportunidad.cliente_id }}" class="btn btn-secondary">Cancelar</a>
                    <a href="/eliminar_oportunidad/{{ oportunidad.id }}" class="btn btn-danger" onclick="return confirm('¿Estas seguro de eliminar esta oportunidad?\n\nEsta accion no se puede deshacer.')">Eliminar Oportunidad</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

VER_OPORTUNIDAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ver Oportunidad - AscensorAlert</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        
        .header { background: #2c3e50; color: white; padding: 20px; }
        .header h1 { font-size: 24px; }
        
        .container { max-width: 800px; margin: 20px auto; padding: 0 20px; }
        
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card h2 { margin-bottom: 15px; color: #2c3e50; }
        
        .comunidad-info { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .comunidad-info p { margin-bottom: 5px; color: #666; }
        
        .info-row { display: grid; grid-template-columns: 150px 1fr; gap: 10px; padding: 12px 0; border-bottom: 1px solid #eee; }
        .info-row:last-child { border-bottom: none; }
        .info-label { font-weight: bold; color: #555; }
        .info-value { color: #333; }
        
        .badge { display: inline-block; padding: 6px 14px; border-radius: 12px; font-size: 13px; font-weight: 500; }
        .badge.activa { background: #d4edda; color: #155724; }
        .badge.ganada { background: #d1ecf1; color: #0c5460; }
        .badge.perdida { background: #f8d7da; color: #721c24; }
        
        .form-actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
        .btn { padding: 12px 24px; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-secondary:hover { background: #7f8c8d; }
        
        @media (max-width: 600px) {
            .info-row { grid-template-columns: 1fr; gap: 5px; }
            .info-label { font-size: 13px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Detalle de Oportunidad</h1>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>Informacion de la Comunidad</h2>
            <div class="comunidad-info">
                <p><strong>Nombre:</strong> {{ oportunidad.clientes.nombre_cliente or oportunidad.clientes.direccion }}</p>
                <p><strong>Direccion:</strong> {{ oportunidad.clientes.direccion }}, {{ oportunidad.clientes.localidad }}</p>
            </div>
        </div>
        
        <div class="card">
            <h2>Detalles de la Oportunidad</h2>
            
            <div class="info-row">
                <div class="info-label">Estado:</div>
                <div class="info-value">
                    <span class="badge {{ oportunidad.estado }}">{{ oportunidad.estado|upper }}</span>
                </div>
            </div>
            
            <div class="info-row">
                <div class="info-label">Tipo:</div>
                <div class="info-value">{{ oportunidad.tipo }}</div>
            </div>
            
            {% if oportunidad.descripcion %}
            <div class="info-row">
                <div class="info-label">Descripcion:</div>
                <div class="info-value">{{ oportunidad.descripcion }}</div>
            </div>
            {% endif %}
            
            {% if oportunidad.valor_estimado %}
            <div class="info-row">
                <div class="info-label">Valor Estimado:</div>
                <div class="info-value">{{ "%.2f"|format(oportunidad.valor_estimado) }} EUR</div>
            </div>
            {% endif %}
            
            <div class="info-row">
                <div class="info-label">Fecha Creacion:</div>
                <div class="info-value">{{ oportunidad.fecha_creacion[:10] }}</div>
            </div>
            
            {% if oportunidad.fecha_cierre %}
            <div class="info-row">
                <div class="info-label">Fecha Cierre:</div>
                <div class="info-value">{{ oportunidad.fecha_cierre[:10] }}</div>
            </div>
            {% endif %}
            
            {% if oportunidad.observaciones %}
            <div class="info-row">
                <div class="info-label">Observaciones:</div>
                <div class="info-value">{{ oportunidad.observaciones }}</div>
            </div>
            {% endif %}
            
            <div class="form-actions">
                <a href="/editar_oportunidad/{{ oportunidad.id }}" class="btn btn-primary">Editar</a>
                <a href="/ver_lead/{{ oportunidad.cliente_id }}" class="btn btn-secondary">Ver Comunidad</a>
                <a href="/oportunidades" class="btn btn-secondary">Volver a Oportunidades</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

# ============================================
# CIERRE DEL ARCHIVO
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
