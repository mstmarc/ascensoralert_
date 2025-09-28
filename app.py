from flask import Flask, request, render_template_string, redirect, session
import requests
import os
from werkzeug.security import check_password_hash
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# Datos de Supabase ACTUALIZADOS
SUPABASE_URL = "https://hvkifgguxsgegzaxwcmj.supabase.co"
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
            if check_password_hash(user.get("contrasena", ""), contrasena):
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

# Alta de Lead
@app.route("/formulario_lead", methods=["GET", "POST"])
def formulario_lead():
    if "usuario" not in session:
        return redirect("/")
    if request.method == "POST":
        data = {
            "tipo_cliente": request.form.get("tipo_lead"),
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead"),
            "codigo_postal": request.form.get("codigo_postal"),
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona"),
            "persona_contacto": request.form.get("persona_contacto"),
            "telefono": request.form.get("telefono"),
            "email": request.form.get("email"),
            "observaciones": request.form.get("observaciones")
        }

        required = [data["tipo_cliente"], data["direccion"], data["nombre_cliente"], data["localidad"]]
        if any(not field for field in required):
            return "Datos del lead inválidos", 400

        response = requests.post(f"{SUPABASE_URL}/rest/v1/clientes?select=id", json=data, headers=HEADERS)
        if response.status_code in [200, 201]:
            cliente_id = response.json()[0]["id"]
            return redirect(f"/nuevo_equipo?cliente_id={cliente_id}")
        else:
            return f"<h3 style='color:red;'>❌ Error al registrar lead</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(FORM_TEMPLATE)

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
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "ubicacion": request.form.get("ubicacion"),
            "descripcion": request.form.get("descripcion"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato"),
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima")
        }

        required = [equipo_data["cliente_id"], equipo_data["tipo_equipo"]]
        if any(not field for field in required):
            return "Datos del equipo inválidos", 400

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

# Dashboard CORREGIDO
@app.route("/leads_dashboard")
def leads_dashboard():
    if "usuario" not in session:
        return redirect("/")

    response = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?select=*", headers=HEADERS)
    if response.status_code != 200:
        return f"<h3 style='color:red;'>❌ Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

    leads_data = response.json()
    rows = []

    for lead in leads_data:
        lead_id = lead["id"]
        equipos_response = requests.get(f"{SUPABASE_URL}/rest/v1/equipos?cliente_id=eq.{lead_id}", headers=HEADERS)
        if equipos_response.status_code == 200:
            equipos = equipos_response.json()
            total_equipos = len(equipos)
            if equipos:
                for equipo in equipos:
                    # Formatear fechas a dd/mm/yyyy
                    fecha_vencimiento = equipo.get("fecha_vencimiento_contrato", "-")
                    if fecha_vencimiento and fecha_vencimiento != "-":
                        partes = fecha_vencimiento.split("-")
                        if len(partes) == 3:
                            fecha_vencimiento = f"{partes[2]}/{partes[1]}/{partes[0]}"

                    ipo_proxima = equipo.get("ipo_proxima", "-")
                    if ipo_proxima and ipo_proxima != "-":
                        partes = ipo_proxima.split("-")
                        if len(partes) == 3:
                            ipo_proxima = f"{partes[2]}/{partes[1]}/{partes[0]}"

                    rows.append({
                        "lead_id": lead_id,
                        "equipo_id": equipo["id"],  # CORREGIDO: Agregado equipo_id
                        "direccion": lead.get("direccion", "-"),
                        "localidad": lead.get("localidad", "-"),
                        "codigo_postal": lead.get("codigo_postal", "-"),
                        "total_equipos": total_equipos,
                        "empresa_mantenedora": equipo.get("empresa_mantenedora", "-"),
                        "fecha_vencimiento_contrato": fecha_vencimiento,
                        "ipo_proxima": ipo_proxima
                    })
            else:
                # Si no hay equipos, mostrar una fila sin equipo
                rows.append({
                    "lead_id": lead_id,
                    "equipo_id": None,
                    "direccion": lead.get("direccion", "-"),
                    "localidad": lead.get("localidad", "-"),
                    "codigo_postal": lead.get("codigo_postal", "-"),
                    "total_equipos": 0,
                    "empresa_mantenedora": "-",
                    "fecha_vencimiento_contrato": "-",
                    "ipo_proxima": "-"
                })

    return render_template_string(DASHBOARD_TEMPLATE, rows=rows)

# Editar Lead CORREGIDO
@app.route("/editar_lead/<int:lead_id>", methods=["GET", "POST"])
def editar_lead(lead_id):
    if "usuario" not in session:
        return redirect("/")

    if request.method == "POST":
        data = {
            "tipo_cliente": request.form.get("tipo_lead"),
            "direccion": request.form.get("direccion"),
            "nombre_cliente": request.form.get("nombre_lead"),
            "codigo_postal": request.form.get("codigo_postal"),
            "localidad": request.form.get("localidad"),
            "zona": request.form.get("zona"),
            "persona_contacto": request.form.get("persona_contacto"),
            "telefono": request.form.get("telefono"),  # CORREGIDO: Agregado
            "email": request.form.get("email"),        # CORREGIDO: Agregado
            "observaciones": request.form.get("observaciones")  # CORREGIDO: Agregado
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
            "empresa_mantenedora": request.form.get("empresa_mantenedora"),
            "ubicacion": request.form.get("ubicacion"),
            "descripcion": request.form.get("descripcion"),
            "fecha_vencimiento_contrato": request.form.get("fecha_vencimiento_contrato"),
            "rae": request.form.get("rae"),
            "ipo_proxima": request.form.get("ipo_proxima")
        }

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
    <title>Login</title>
    <link rel="stylesheet" href="/static/styles.css">
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
    <title>Bienvenido</title>
    <link rel='stylesheet' href='/static/styles.css'>
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
            <a href="/formulario_lead" class='button'>➕ Añadir Lead</a>
            <a href="/leads_dashboard" class='button'>📊 Visualizar Datos</a>
            <a href="/logout" class='button'>🚪 Cerrar Sesión</a>
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
    <title>Formulario Lead</title>
    <link rel="stylesheet" href="/static/styles.css">
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
                    <option value="El Burrero">El Burrero</option>
                    <option value="El Tablero">El Tablero</option>
                    <option value="Gáldar">Gáldar</option>
                    <option value="Ingenio">Ingenio</option>
                    <option value="Jinámar">Jinámar</option>
                    <option value="La Aldea de San Nicolás">La Aldea de San Nicolás</option>
                    <option value="La Pardilla">La Pardilla</option>
                    <option value="Las Palmas de Gran Canaria">Las Palmas de Gran Canaria</option>
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

                <label>Observaciones:</label><br>
                <textarea name="observaciones"></textarea><br><br>

                <button type="submit" class="button">Registrar Lead</button>
            </form>
        </div>
    </main>
</body>
</html>
"""

EQUIPO_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Formulario Equipo</title>
    <link rel="stylesheet" href="/static/styles.css">
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

                <label>IPO Próxima:</label><br>
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
    <title>Editar Lead</title>
    <link rel="stylesheet" href="/static/styles.css">
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

            <label>Código Postal:</label><br>
            <input type="text" name="codigo_postal" value="{{ lead.codigo_postal }}"><br><br>

            <label>Localidad:</label><br>
            <select name="localidad" required>
                <option value="">-- Selecciona una localidad --</option>
                <option value="Agaete" {% if lead.localidad == 'Agaete' %}selected{% endif %}>Agaete</option>
                <option value="Agüimes" {% if lead.localidad == 'Agüimes' %}selected{% endif %}>Agüimes</option>
                <option value="Arguineguín" {% if lead.localidad == 'Arguineguín' %}selected{% endif %}>Arguineguín</option>
                <option value="Arinaga" {% if lead.localidad == 'Arinaga' %}selected{% endif %}>Arinaga</option>
                <option value="Artenara" {% if lead.localidad == 'Artenara' %}selected{% endif %}>Artenara</option>
                <option value="Arucas" {% if lead.localidad == 'Arucas' %}selected{% endif %}>Arucas</option>
                <option value="Carrizal" {% if lead.localidad == 'Carrizal' %}selected{% endif %}>Carrizal</option>
                <option value="Cruce de Arinaga" {% if lead.localidad == 'Cruce de Arinaga' %}selected{% endif %}>Cruce de Arinaga</option>
                <option value="El Burrero" {% if lead.localidad == 'El Burrero' %}selected{% endif %}>El Burrero</option>
                <option value="El Tablero" {% if lead.localidad == 'El Tablero' %}selected{% endif %}>El Tablero</option>
                <option value="Gáldar" {% if lead.localidad == 'Gáldar' %}selected{% endif %}>Gáldar</option>
                <option value="Ingenio" {% if lead.localidad == 'Ingenio' %}selected{% endif %}>Ingenio</option>
                <option value="Jinámar" {% if lead.localidad == 'Jinámar' %}selected{% endif %}>Jinámar</option>
                <option value="La Aldea de San Nicolás" {% if lead.localidad == 'La Aldea de San Nicolás' %}selected{% endif %}>La Aldea de San Nicolás</option>
                <option value="La Pardilla" {% if lead.localidad == 'La Pardilla' %}selected{% endif %}>La Pardilla</option>
                <option value="Las Palmas de Gran Canaria" {% if lead.localidad == 'Las Palmas de Gran Canaria' %}selected{% endif %}>Las Palmas de Gran Canaria</option>
                <option value="Maspalomas" {% if lead.localidad == 'Maspalomas' %}selected{% endif %}>Maspalomas</option>
                <option value="Mogán" {% if lead.localidad == 'Mogán' %}selected{% endif %}>Mogán</option>
                <option value="Moya" {% if lead.localidad == 'Moya' %}selected{% endif %}>Moya</option>
                <option value="Playa de Mogán" {% if lead.localidad == 'Playa de Mogán' %}selected{% endif %}>Playa de Mogán</option>
                <option value="Playa del Inglés" {% if lead.localidad == 'Playa del Inglés' %}selected{% endif %}>Playa del Inglés</option>
                <option value="Puerto Rico" {% if lead.localidad == 'Puerto Rico' %}selected{% endif %}>Puerto Rico</option>
                <option value="San Bartolomé de Tirajana" {% if lead.localidad == 'San Bartolomé de Tirajana' %}selected{% endif %}>San Bartolomé de Tirajana</option>
                <option value="San Fernando" {% if lead.localidad == 'San Fernando' %}selected{% endif %}>San Fernando</option>
                <option value="San Mateo" {% if lead.localidad == 'San Mateo' %}selected{% endif %}>San Mateo</option>
                <option value="Santa Brígida" {% if lead.localidad == 'Santa Brígida' %}selected{% endif %}>Santa Brígida</option>
                <option value="Santa Lucía de Tirajana" {% if lead.localidad == 'Santa Lucía de Tirajana' %}selected{% endif %}>Santa Lucía de Tirajana</option>
                <option value="Santa María de Guía" {% if lead.localidad == 'Santa María de Guía' %}selected{% endif %}>Santa María de Guía</option>
                <option value="Tafira" {% if lead.localidad == 'Tafira' %}selected{% endif %}>Tafira</option>
                <option value="Tejeda" {% if lead.localidad == 'Tejeda' %}selected{% endif %}>Tejeda</option>
                <option value="Teror" {% if lead.localidad == 'Teror' %}selected{% endif %}>Teror</option>
                <option value="Valleseco" {% if lead.localidad == 'Valleseco' %}selected{% endif %}>Valleseco</option>
                <option value="Valsequillo" {% if lead.localidad == 'Valsequillo' %}selected{% endif %}>Valsequillo</option>
                <option value="Vecindario" {% if lead.localidad == 'Vecindario' %}selected{% endif %}>Vecindario</option>
            </select><br><br>

            <label>Zona:</label><br>
            <input type="text" name="zona" value="{{ lead.zona }}"><br><br>

            <label>Persona de Contacto:</label><br>
            <input type="text" name="persona_contacto" value="{{ lead.persona_contacto }}"><br><br>

            <label>Teléfono:</label><br>
            <input type="text" name="telefono" value="{{ lead.telefono }}"><br><br>

            <label>Email:</label><br>
            <input type="email" name="email" value="{{ lead.email }}"><br><br>

            <label>Observaciones:</label><br>
            <textarea name="observaciones">{{ lead.observaciones }}</textarea><br><br>

            <a href="/nuevo_equipo?cliente_id={{ lead.id }}" class="button">➕ Añadir nuevo equipo</a>
            <button type="submit" class="button">Actualizar Lead</button>
        </form>
    </div>
</main>
</body>
</html>
"""

# DASHBOARD TEMPLATE CORREGIDO
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Leads Dashboard</title>
    <link rel='stylesheet' href='/static/styles.css'>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f5f5f5; }
        a { text-decoration: none; color: #0065a3; }
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
                <h1>AscensorAlert</h1>
            </div>
        </div>
    </header>
    <main>
        <div class='menu'>
            <table>
                <thead>
                    <tr>
                        <th>Dirección</th>
                        <th>Localidad</th>
                        <th>Código Postal</th>
                        <th>Total Equipos</th>
                        <th>Empresa Mantenedora</th>
                        <th>Vencimiento Contrato</th>
                        <th>IPO Próxima</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td><a href='/editar_lead/{{ row.lead_id }}'>{{ row.direccion }}</a></td>
                        <td>{{ row.localidad }}</td>
                        <td>{{ row.codigo_postal }}</td>
                        <td>
                            <a href='/nuevo_equipo?cliente_id={{ row.lead_id }}'>{{ row.total_equipos }}</a>
                        </td>
                        <td>{{ row.empresa_mantenedora }}</td>
                        <td>{{ row.fecha_vencimiento_contrato }}</td>
                        <td>{{ row.ipo_proxima }}</td>
                        <td>
                            {% if row.equipo_id %}
                                <a href="/editar_equipo/{{ row.equipo_id }}" class="button-small">✏️ Editar Equipo</a>
                            {% else %}
                                <span style="color: #999;">Sin equipos</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href='/home' class='button'>🏠 Volver al inicio</a>
        </div>
    </main>
</body>
</html>
"""

EQUIPO_EDIT_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Editar Equipo</title>
    <link rel="stylesheet" href="/static/styles.css">
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
                <h1>Editar Equipo</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Tipo de Equipo:</label><br>
                <input type="text" name="tipo_equipo" value="{{ equipo.tipo_equipo }}" required><br><br>

                <label>Empresa Mantenedora:</label><br>
                <input type="text" name="empresa_mantenedora" value="{{ equipo.empresa_mantenedora }}"><br><br>

                <label>Ubicación:</label><br>
                <input type="text" name="ubicacion" value="{{ equipo.ubicacion }}"><br><br>

                <label>Descripción:</label><br>
                <input type="text" name="descripcion" value="{{ equipo.descripcion }}"><br><br>

                <label>Fecha Vencimiento Contrato:</label><br>
                <input type="date" name="fecha_vencimiento_contrato" value="{{ equipo.fecha_vencimiento_contrato }}"><br><br>

                <label>RAE:</label><br>
                <input type="text" name="rae" value="{{ equipo.rae }}"><br><br>

                <label>IPO Próxima:</label><br>
                <input type="date" name="ipo_proxima" value="{{ equipo.ipo_proxima }}"><br><br>

                <button type="submit" class="button">Actualizar Equipo</button>
            </form>
            <br>
            <a href="/home" class="button">🏠 Volver al inicio</a>
        </div>
    </main>
</body>
</html>
"""

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug)