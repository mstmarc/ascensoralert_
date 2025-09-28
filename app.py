from flask import Flask, request, render_template_string, redirect, session, Response
import requests
import os
import urllib.parse
from datetime import date
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
            "fecha_visita": request.form.get("fecha_visita"),  # NUEVO CAMPO
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

        required = [data["fecha_visita"], data["tipo_cliente"], data["direccion"], data["nombre_cliente"], data["localidad"], data["numero_ascensores"]]
        if any(not field for field in required):
            return "Datos del lead inválidos - Fecha de visita es obligatoria", 400

        response = requests.post(f"{SUPABASE_URL}/rest/v1/clientes?select=id", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            cliente_id = response.json()[0]["id"]
            return redirect(f"/nuevo_equipo?cliente_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>❌ Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    # Para GET: mostrar formulario con fecha actual por defecto
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template_string(FORM_TEMPLATE, fecha_hoy=fecha_hoy)

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
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "ubicacion": request.form.get("ubicacion"),
            "descripcion": request.form.get("descripcion"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        required = [equipo_data["cliente_id"], equipo_data["tipo_equipo"], equipo_data["identificacion"]]
        if any(not field for field in required):
            return "Datos del equipo inválidos", 400

        # Limpiar campos vacíos (convertir strings vacíos a None)
        for key, value in equipo_data.items():
            if value == "":
                equipo_data[key] = None

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            return f"""
            <h3>✅ Equipo registrado correctamente</h3>
            <a href='/nuevo_equipo?cliente_id={cliente_id}' class='button'>➕ Añadir otro equipo</a><br><br>
            <a href='/home' class='button'>🏠 Finalizar y volver al inicio</a>
            """
        else:
            return f"<h3 style='color:red;'>❌ Error al registrar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(EQUIPO_TEMPLATE, cliente=cliente_data)

# DESCARGO COMERCIAL MENSUAL
@app.route("/reporte_mensual", methods=["GET", "POST"])
def reporte_mensual():
    if "usuario" not in session:
        return redirect("/")
    
    if request.method == "POST":
        mes = int(request.form.get("mes"))
        año = int(request.form.get("año"))
        
        # Construir filtros de fecha para el mes seleccionado
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_inicio = f"{año}-{mes:02d}-01"
        fecha_fin = f"{año}-{mes:02d}-{ultimo_dia}"
        
        # Consultar leads del mes por fecha_visita
        query_clientes = f"fecha_visita=gte.{fecha_inicio}&fecha_visita=lte.{fecha_fin}"
        response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?{query_clientes}&select=*", headers=HEADERS)
        
        if response.status_code != 200:
            return f"Error al obtener datos: {response.text}"
        
        clientes_mes = response.json()
        
        # Generar Excel con el formato exacto del descargo actual
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "ADM. FINCAS"
        
        # Configurar encabezados exactos del formato original
        headers = ['FECHA', 'COMUNIDAD/EMPRESA', 'DIRECCION', 'ZONA', 'OBSERVACIONES']
        
        # Aplicar encabezados con formato
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            
            # Bordes
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'), 
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            cell.border = thin_border
        
        # Añadir datos de clientes
        row = 2
        for cliente in clientes_mes:
            # FECHA
            ws.cell(row=row, column=1, value=cliente.get('fecha_visita', ''))
            
            # COMUNIDAD/EMPRESA (usamos nombre_cliente)
            comunidad_empresa = cliente.get('nombre_cliente', '')
            ws.cell(row=row, column=2, value=comunidad_empresa)
            
            # DIRECCION
            ws.cell(row=row, column=3, value=cliente.get('direccion', ''))
            
            # ZONA (localidad)
            ws.cell(row=row, column=4, value=cliente.get('localidad', ''))
            
            # OBSERVACIONES
            ws.cell(row=row, column=5, value=cliente.get('observaciones', ''))
            
            # Aplicar bordes a toda la fila
            for col in range(1, 6):
                ws.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        # Ajustar anchos de columna para que se vea bien
        column_widths = {
            'A': 12,  # FECHA
            'B': 40,  # COMUNIDAD/EMPRESA
            'C': 50,  # DIRECCION
            'D': 20,  # ZONA
            'E': 70   # OBSERVACIONES
        }
        
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        # Guardar archivo en memoria
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generar respuesta de descarga
        # Nombre del archivo igual al formato actual
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
    
    # Para GET: mostrar formulario de selección de mes/año
    return render_template_string(REPORTE_TEMPLATE)

# Dashboard CON SISTEMA DE FILTROS
@app.route("/leads_dashboard")
def leads_dashboard():
    if "usuario" not in session:
        return redirect("/")

    # Obtener parámetros de filtro
    filtro_empresa = request.args.get('empresa', '')
    filtro_localidad = request.args.get('localidad', '')
    filtro_ipo_mes = request.args.get('ipo_mes', '')
    filtro_ipo_año = request.args.get('ipo_año', '')
    buscar_texto = request.args.get('buscar', '')

    response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=*", headers=HEADERS)
    if response.status_code != 200:
        return f"<h3 style='color:red;'>❌ Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    leads_data = response.json()
    rows = []
    
    # Obtener listas para filtros
    empresas_disponibles = set()
    localidades_disponibles = set()

    for lead in leads_data:
        lead_id = lead["id"]
        equipos_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
        
        if equipos_response.status_code == 200:
            equipos = equipos_response.json()
            total_equipos = len(equipos)
            
            # Añadir a listas de filtros
            localidades_disponibles.add(lead.get("localidad", ""))
            
            if equipos:
                for equipo in equipos:
                    empresas_disponibles.add(equipo.get("empresa_mantenedora", ""))
                    
                    # Formatear fechas
                    fecha_vencimiento = equipo.get("fecha_vencimiento_contrato", "-")
                    if fecha_vencimiento and fecha_vencimiento != "-" and fecha_vencimiento:
                        partes = fecha_vencimiento.split("-")
                        if len(partes) == 3:
                            fecha_vencimiento = f"{partes[2]}/{partes[1]}/{partes[0]}"

                    ipo_proxima = equipo.get("ipo_proxima", "-")
                    ipo_fecha_original = ipo_proxima
                    if ipo_proxima and ipo_proxima != "-" and ipo_proxima:
                        partes = ipo_proxima.split("-")
                        if len(partes) == 3:
                            ipo_proxima = f"{partes[2]}/{partes[1]}/{partes[0]}"

                    # Crear fila de datos
                    row = {
                        "lead_id": lead_id,
                        "equipo_id": equipo["id"],
                        "direccion": lead.get("direccion", "-"),
                        "localidad": lead.get("localidad", "-"),
                        "codigo_postal": lead.get("codigo_postal", "-"),
                        "identificacion": equipo.get("identificacion", "-"),
                        "total_equipos": total_equipos,
                        "numero_ascensores_previsto": lead.get("numero_ascensores", "-"),
                        "empresa_mantenedora": equipo.get("empresa_mantenedora", "-"),
                        "fecha_vencimiento_contrato": fecha_vencimiento,
                        "ipo_proxima": ipo_proxima,
                        "ipo_fecha_original": ipo_fecha_original
                    }
                    
                    # Aplicar filtros
                    incluir_fila = True
                    
                    # Filtro por empresa
                    if filtro_empresa and filtro_empresa != equipo.get("empresa_mantenedora", ""):
                        incluir_fila = False
                    
                    # Filtro por localidad
                    if filtro_localidad and filtro_localidad != lead.get("localidad", ""):
                        incluir_fila = False
                    
                    # Filtro por IPO (mes y año)
                    if filtro_ipo_mes or filtro_ipo_año:
                        if ipo_fecha_original and ipo_fecha_original != "-":
                            try:
                                partes_fecha = ipo_fecha_original.split("-")
                                if len(partes_fecha) == 3:
                                    año_ipo = partes_fecha[0]
                                    mes_ipo = partes_fecha[1]
                                    
                                    if filtro_ipo_año and filtro_ipo_año != año_ipo:
                                        incluir_fila = False
                                    if filtro_ipo_mes and filtro_ipo_mes != mes_ipo:
                                        incluir_fila = False
                            except:
                                pass
                        else:
                            if filtro_ipo_mes or filtro_ipo_año:
                                incluir_fila = False
                    
                    # Filtro por búsqueda de texto
                    if buscar_texto:
                        texto_busqueda = buscar_texto.lower()
                        campos_busqueda = [
                            str(lead.get("direccion", "")),
                            str(lead.get("localidad", "")),
                            str(equipo.get("identificacion", "")),
                            str(equipo.get("empresa_mantenedora", "")),
                            str(lead.get("nombre_cliente", ""))
                        ]
                        
                        encontrado = any(texto_busqueda in campo.lower() for campo in campos_busqueda)
                        if not encontrado:
                            incluir_fila = False
                    
                    if incluir_fila:
                        rows.append(row)
            else:
                # Lead sin equipos
                row = {
                    "lead_id": lead_id,
                    "equipo_id": None,
                    "direccion": lead.get("direccion", "-"),
                    "localidad": lead.get("localidad", "-"),
                    "codigo_postal": lead.get("codigo_postal", "-"),
                    "identificacion": "-",
                    "total_equipos": 0,
                    "numero_ascensores_previsto": lead.get("numero_ascensores", "-"),
                    "empresa_mantenedora": "-",
                    "fecha_vencimiento_contrato": "-",
                    "ipo_proxima": "-",
                    "ipo_fecha_original": None
                }
                
                # Aplicar filtros para leads sin equipos
                incluir_fila = True
                if filtro_empresa or filtro_ipo_mes or filtro_ipo_año:
                    incluir_fila = False
                if filtro_localidad and filtro_localidad != lead.get("localidad", ""):
                    incluir_fila = False
                if buscar_texto:
                    texto_busqueda = buscar_texto.lower()
                    campos_busqueda = [
                        str(lead.get("direccion", "")),
                        str(lead.get("localidad", "")),
                        str(lead.get("nombre_cliente", ""))
                    ]
                    encontrado = any(texto_busqueda in campo.lower() for campo in campos_busqueda)
                    if not encontrado:
                        incluir_fila = False
                
                if incluir_fila:
                    rows.append(row)

    # Limpiar y ordenar listas para filtros
    empresas_disponibles = sorted([e for e in empresas_disponibles if e and e != "-"])
    localidades_disponibles = sorted([l for l in localidades_disponibles if l and l != "-"])

    return render_template_string(DASHBOARD_TEMPLATE_WITH_FILTERS, 
                                rows=rows, 
                                empresas=empresas_disponibles,
                                localidades=localidades_disponibles,
                                filtro_empresa=filtro_empresa,
                                filtro_localidad=filtro_localidad,
                                filtro_ipo_mes=filtro_ipo_mes,
                                filtro_ipo_año=filtro_ipo_año,
                                buscar_texto=buscar_texto)

# Editar Lead CORREGIDO Y CON FECHA DE VISITA
@app.route("/editar_lead/<int:lead_id>", methods=["GET", "POST"])
def editar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":
        data = {
            "fecha_visita": request.form.get("fecha_visita"),  # NUEVO CAMPO
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
            return f"<h3 style='color:red;'>❌ Error al actualizar Lead</h3><pre>{res.text}</pre><a href='/leads_dashboard'>Volver</a>"

    # GET: Consultar el lead
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{lead_id}",
        headers=HEADERS
    )
    if response.status_code == 200 and response.json():
        lead = response.json()[0]
    else:
        return f"<h3 style='color:red;'>❌ Error al obtener Lead</h3><pre>{response.text}</pre><a href='/leads_dashboard'>Volver</a>"

    return render_template_string(EDIT_LEAD_TEMPLATE, lead=lead)

@app.route("/editar_equipo/<int:equipo_id>", methods=["GET", "POST"])
def editar_equipo(equipo_id):
    if "usuario" not in session:
        return redirect("/")

    response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}", headers=HEADERS)
    if response.status_code != 200 or not response.json():
        return f"<h3 style='color:red;'>❌ Error al obtener equipo</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    equipo = response.json()[0]

    if request.method == "POST":
        data = {
            "tipo_equipo": request.form.get("tipo_equipo"),
            "identificacion": request.form.get("identificacion"),
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "ubicacion": request.form.get("ubicacion"),
            "descripcion": request.form.get("descripcion"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato") or None,
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima") or None
        }

        # Limpiar campos vacíos
        for key, value in data.items():
            if value == "":
                data[key] = None

        update_url = f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{equipo_id}"
        res = requests.patch(update_url, json=data, headers=HEADERS)
        if res.status_code in [200, 204]:
            return redirect("/leads_dashboard")
        else:
            return f"<h3 style='color:red;'>❌ Error al actualizar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(EQUIPO_EDIT_TEMPLATE, equipo=equipo)

# PLANTILLAS HTML
LOGIN_TEMPLATE = """
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
            <h1>Bienvenido, {{ usuario }}</h1>
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
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido</title>
    <link rel='stylesheet' href='/static/styles.css?v=4'>
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
        <div class='menu'>
            <a href="/formulario_lead" class='button'>Añadir Lead</a>
            <a href="/leads_dashboard" class='button'>Visualizar Datos</a>
            <a href="/reporte_mensual" class='button'>Descargo Comercial</a>
            <a href="/logout" class='button'>Cerrar Sesión</a>
        </div>
    </main>
</body>
</html>
"""

FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulario Lead</title>
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
            <h1>Introducir datos</h1>
        </div>
    </div>
</header>
    <main>
        <div class="menu">
            <form method="POST">
                <!-- NUEVO CAMPO: Fecha de Visita como primer campo -->
                <label>Fecha de Visita:</label><br>
                <input type="date" name="fecha_visita" value="{{ fecha_hoy }}" required><br><br>

                <label>Tipo de Lead:</label><br>
                <select name="tipo_lead" required>
                    <option value="Maspalomas">Maspalomas</option>
                    <option value="Mogán">Mogán</option>
                    <option value="Moya">Moya</option>
                    <option value="Playa de Mogán">Playa de Mogán</option>
                    <option value="Playa del Inglés">Playa del Inglés</option>
                    <option value="Puerto Rico">Puerto Rico</option>
                    <option value="San Bartolomé de Tirajana">San Bartolomé de Tirajana</option>
                    <option value="San Fernando">San Fernando</option>
                    <option value="San Mateo">San Mateo</option>
                    <option value="Santa Brígida">Santa Brígida</option>
                    <option value="Santa Lucía de Tirajana">Santa Lucía de Tirajana</option>
                    <option value="Santa María de Guía">Santa María de Guía</option>
                    <option value="Tafira">Tafira</option>
                    <option value="Tejeda">Tejeda</option>
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

                <label>Número de Ascensores:</label><br>
                <select name="numero_ascensores" required>
                    <option value="">-- ¿Cuántos ascensores hay? --</option>
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

                <button type="submit" class="button">Registrar Lead</button>
            </form>
        </div>
    </main>
</body>
</html>
"""

# Resto de templates...
EQUIPO_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulario Equipo</title>
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
                <input type="text" name="identificacion" placeholder="Ej: Ascensor A, Principal, Garaje, etc." required><br><br>

                <label>Empresa Mantenedora:</label><br>
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

                <label>Ubicación:</label><br>
                <input type="text" name="ubicacion"><br><br>

                <label>Descripción:</label><br>
                <input type="text" name="descripcion"><br><br>

                <label>Fecha Vencimiento Contrato:</label><br>
                <input type="date" name="fecha_vencimiento_contrato"><br><br>

                <label>RAE (solo para ascensores):</label><br>
                <input type="text" name="rae"><br><br>

                <label>IPO Próxima: <em>(consultar placa del ascensor)</em></label><br>
                <input type="date" name="ipo_proxima"><br><br>

                <button type="submit" class="button">Registrar Equipo</button>
            </form>
        </div>
    </main>
</body>
</html>
"""

EDIT_LEAD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Lead</title>
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
            <h1>Editar Lead</h1>
        </div>
    </div>
</header>
<main>
    <div class="menu">
        <form method="POST">
            <!-- Campo fecha de visita -->
            <label>Fecha de Visita:</label><br>
            <input type="date" name="fecha_visita" value="{{ lead.fecha_visita }}" required><br><br>

            <label>Tipo de Lead:</label><br>
            <select name="tipo_lead" required>
                <option value="">-- Selecciona un tipo --</option>
                <option value="Comunidad" {% if lead.tipo_cliente == 'Comunidad' %}selected{% endif %}>Comunidad</option>
                <option value="Hotel/Apartamentos" {% if lead.tipo_cliente == 'Hotel/Apartamentos' %}selected{% endif %}>Hotel/Apartamentos</option>
                <option value="Empresa" {% if lead.tipo_cliente == 'Empresa' %}selected{% endif %}>Empresa</option>
                <option value="Otro" {% if lead.tipo_cliente == 'Otro' %}selected{% endif %}>Otro</option>
            </select><br><br>

            <label>Dirección:</label><br>
            <input type="text" name="direccion" value="{{ lead.direccion }}" required><br><br>

            <label>Nombre de la Instalación:</label><br>
            <input type="text" name="nombre_lead" value="{{ lead.nombre_cliente }}" required><br><br>

            <!-- Resto de campos del formulario de edición -->
            <label>Código Postal:</label><br>
            <input type="text" name="codigo_postal" value="{{ lead.codigo_postal }}"><br><br>

            <label>Localidad:</label><br>
            <select name="localidad" required>
                <option value="">-- Selecciona una localidad --</option>
                <!-- ... todas las localidades con selected si coincide ... -->
            </select><br><br>

            <label>Observaciones:</label><br>
            <textarea name="observaciones">{{ lead.observaciones }}</textarea><br><br>

            <button type="submit" class="button">Actualizar Lead</button>
        </form>
    </div>
</main>
</body>
</html>
"""

REPORTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargo Comercial</title>
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
                <h1>Descargo Comercial</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <h3>Generar Descargo Comercial Mensual</h3>
            <p>Selecciona el mes y año para generar el descargo comercial con las visitas realizadas:</p>
            
            <form method="POST">
                <label>Mes:</label><br>
                <select name="mes" required>
                    <option value="">-- Selecciona mes --</option>
                    <option value="1">Enero</option>
                    <option value="2">Febrero</option>
                    <option value="3">Marzo</option>
                    <option value="4">Abril</option>
                    <option value="5">Mayo</option>
                    <option value="6">Junio</option>
                    <option value="7">Julio</option>
                    <option value="8">Agosto</option>
                    <option value="9">Septiembre</option>
                    <option value="10">Octubre</option>
                    <option value="11">Noviembre</option>
                    <option value="12">Diciembre</option>
                </select><br><br>

                <label>Año:</label><br>
                <select name="año" required>
                    <option value="">-- Selecciona año --</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                </select><br><br>

                <button type="submit" class="button">Generar Descargo Excel</button>
            </form>
            <br>
            <a href="/home" class="button">Volver al inicio</a>
        </div>
    </main>
</body>
</html>
"""

# Templates de dashboard y edición de equipos continúan igual...
# [El resto del código con DASHBOARD_TEMPLATE_WITH_FILTERS y EQUIPO_EDIT_TEMPLATE]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)="">-- Selecciona un tipo --</option>
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
                    <option value="El Burrero">El Burrero</option>
                    <option value="El Tablero">El Tablero</option>
                    <option value="Gáldar">Gáldar</option>
                    <option value="Ingenio">Ingenio</option>
                    <option value="Jinémar">Jinémar</option>
                    <option value="La Aldea de San Nicolás">La Aldea de San Nicolás</option>
                    <option value="La Pardilla">La Pardilla</option>
                    <option value="Las Palmas de Gran Canaria">Las Palmas de Gran Canaria</option>
                    <option value
