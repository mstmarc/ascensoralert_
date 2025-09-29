'''

EQUIPO_TEMPLATE = '''
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
            <h1>Introducir datos de equipo</h1>
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

                <button type="submit" class="button">Registrar Equipo</button>
            </form>
            <a href="/home" class="button">Volver</a>
        </div>
    </main>
</body>
</html>
'''

EDIT_LEAD_TEMPLATE = '''
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
                <option value="Cruce de Melenara" {% if lead.localidad == 'Cruce de Melenara' %}selected{% endif %}>Cruce de Melenara</option>
                <option value="Cruce de Sardina" {% if lead.localidad == 'Cruce de Sardina' %}selected{% endif %}>Cruce de Sardina</option>
                <option value="El Burrero" {% if lead.localidad == 'El Burrero' %}selected{% endif %}>El Burrero</option>
                <option value="El Tablero" {% if lead.localidad == 'El Tablero' %}selected{% endif %}>El Tablero</option>
                <option value="Firgas" {% if lead.localidad == 'Firgas' %}selected{% endif %}>Firgas</option>
                <option value="Gáldar" {% if lead.localidad == 'Gáldar' %}selected{% endif %}>Gáldar</option>
                <option value="Ingenio" {% if lead.localidad == 'Ingenio' %}selected{% endif %}>Ingenio</option>
                <option value="Jinámar" {% if lead.localidad == 'Jinámar' %}selected{% endif %}>Jinámar</option>
                <option value="La Aldea de San Nicolás" {% if lead.localidad == 'La Aldea de San Nicolás' %}selected{% endif %}>La Aldea de San Nicolás</option>
                <option value="La Pardilla" {% if lead.localidad == 'La Pardilla' %}selected{% endif %}>La Pardilla</option>
                <option value="Las Palmas de Gran Canaria" {% if lead.localidad == 'Las Palmas de Gran Canaria' %}selected{% endif %}>Las Palmas de Gran Canaria</option>
                <option value="Maspalomas" {% if lead.localidad == 'Maspalomas' %}selected{% endif %}>Maspalomas</option>
                <option value="Melenara" {% if lead.localidad == 'Melenara' %}selected{% endif %}>Melenara</option>
                <option value="Mogán" {% if lead.localidad == 'Mogán' %}selected{% endif %}>Mogán</option>
                <option value="Moya" {% if lead.localidad == 'Moya' %}selected{% endif %}>Moya</option>
                <option value="Playa de Mogán" {% if lead.localidad == 'Playa de Mogán' %}selected{% endif %}>Playa de Mogán</option>
                <option value="Playa del Inglés" {% if lead.localidad == 'Playa del Inglés' %}selected{% endif %}>Playa del Inglés</option>
                <option value="Puerto Rico" {% if lead.localidad == 'Puerto Rico' %}selected{% endif %}>Puerto Rico</option>
                <option value="Salinetas" {% if lead.localidad == 'Salinetas' %}selected{% endif %}>Salinetas</option>
                <option value="San Bartolomé de Tirajana" {% if lead.localidad == 'San Bartolomé de Tirajana' %}selected{% endif %}>San Bartolomé de Tirajana</option>
                <option value="San Fernando" {% if lead.localidad == 'San Fernando' %}selected{% endif %}>San Fernando</option>
                <option value="San Mateo" {% if lead.localidad == 'San Mateo' %}selected{% endif %}>San Mateo</option>
                <option value="Santa Brígida" {% if lead.localidad == 'Santa Brígida' %}selected{% endif %}>Santa Brígida</option>
                <option value="Santa Lucía de Tirajana" {% if lead.localidad == 'Santa Lucía de Tirajana' %}selected{% endif %}>Santa Lucía de Tirajana</option>
                <option value="Santa María de Guía" {% if lead.localidad == 'Santa María de Guía' %}selected{% endif %}>Santa María de Guía</option>
                <option value="Sardina del Norte" {% if lead.localidad == 'Sardina del Norte' %}selected{% endif %}>Sardina del Norte</option>
                <option value="Tafira" {% if lead.localidad == 'Tafira' %}selected{% endif %}>Tafira</option>
                <option value="Tejeda" {% if lead.localidad == 'Tejeda' %}selected{% endif %}>Tejeda</option>
                <option value="Telde" {% if lead.localidad == 'Telde' %}selected{% endif %}>Telde</option>
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

            <label>Administrador de Fincas:</label><br>
            <input type="text" name="administrador_fincas" value="{{ lead.administrador_fincas }}"><br><br>

            <label>Número de Ascensores:</label><br>
            <select name="numero_ascensores" required>
                <option value="">-- Cuantos ascensores hay? --</option>
                <option value="1" {% if lead.numero_ascensores == '1' %}selected{% endif %}>1 ascensor</option>
                <option value="2" {% if lead.numero_ascensores == '2' %}selected{% endif %}>2 ascensores</option>
                <option value="3" {% if lead.numero_ascensores == '3' %}selected{% endif %}>3 ascensores</option>
                <option value="4" {% if lead.numero_ascensores == '4' %}selected{% endif %}>4 ascensores</option>
                <option value="5" {% if lead.numero_ascensores == '5' %}selected{% endif %}>5 ascensores</option>
                <option value="6" {% if lead.numero_ascensores == '6' %}selected{% endif %}>6 ascensores</option>
                <option value="7" {% if lead.numero_ascensores == '7' %}selected{% endif %}>7 ascensores</option>
                <option value="8" {% if lead.numero_ascensores == '8' %}selected{% endif %}>8 ascensores</option>
                <option value="9" {% if lead.numero_ascensores == '9' %}selected{% endif %}>9 ascensores</option>
                <option value="10" {% if lead.numero_ascensores == '10' %}selected{% endif %}>10 ascensores</option>
                <option value="11" {% if lead.numero_ascensores == '11' %}selected{% endif %}>11 ascensores</option>
                <option value="12" {% if lead.numero_ascensores == '12' %}selected{% endif %}>12 ascensores</option>
                <option value="13" {% if lead.numero_ascensores == '13' %}selected{% endif %}>13 ascensores</option>
                <option value="14" {% if lead.numero_ascensores == '14' %}selected{% endif %}>14 ascensores</option>
                <option value="15" {% if lead.numero_ascensores == '15' %}selected{% endif %}>15 ascensores</option>
                <option value="16" {% if lead.numero_ascensores == '16' %}selected{% endif %}>16 ascensores</option>
                <option value="17" {% if lead.numero_ascensores == '17' %}selected{% endif %}>17 ascensores</option>
                <option value="18" {% if lead.numero_ascensores == '18' %}selected{% endif %}>18 ascensores</option>
                <option value="19" {% if lead.numero_ascensores == '19' %}selected{% endif %}>19 ascensores</option>
                <option value="20" {% if lead.numero_ascensores == '20' %}selected{% endif %}>20 ascensores</option>
                <option value="20+" {% if lead.numero_ascensores == '20+' %}selected{% endif %}>Más de 20 ascensores</option>
            </select><br><br>

            <label>Observaciones:</label><br>
            <textarea name="observaciones">{{ lead.observaciones }}</textarea><br><br>

            <button type="submit" class="button">Actualizar Lead</button>
        </form>
        <a href="/leads_dashboard" class="button">Volver</a>
    </div>
</main>
</body>
</html>
'''

REPORTE_TEMPLATE = '''
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
            <p>Selecciona el mes y año para generar el descargo comercial:</p>
            
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
'''

DASHBOARD_TEMPLATE_WITH_FILTERS = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
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
                <h1>Dashboard</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <h3>Dashboard de Leads</h3>
            <table border="1">
                <tr>
                    <th>Dirección</th>
                    <th>Localidad</th>
                    <th>Equipos</th>
                    <th>Acciones</th>
                </tr>
                {% for row in rows %}
                <tr>
                    <td>{{ row.direccion }}</td>
                    <td>{{ row.localidad }}</td>
                    <td>{{ row.total_equipos }}</td>
                    <td>
                        <a href="/editar_lead/{{ row.lead_id }}">Editar</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
            <br>
            <a href="/home" class="button">Volver</a>
        </div>
    </main>
</body>
</html>
'''

EQUIPO_EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Equipo</title>
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
                <h1>Editar Equipo</h1>
            </div>
        </div>
    </header>
    <main>
        <div class="menu">
            <form method="POST">
                <label>Tipo de Equipo:</label><br>
                <input type="text" name="tipo_equipo" value="{{ equipo.tipo_equipo }}" required><br><br>

                <label>Identificación del Ascensor:</label><br>
                <input type="text" name="identificacion" value="{{ equipo.identificacion }}"><br><br>

                <label>Fecha Vencimiento Contrato:</label><br>
                <input type="date" name="fecha_vencimiento_contrato" value="{{ equipo.fecha_vencimiento_contrato }}"><br><br>

                <label>RAE:</label><br>
                <input type="text" name="rae" value="{{ equipo.rae }}"><br><br>

                <label>Próxima IPO:</label><br>
                <input type="date" name="ipo_proxima" value="{{ equipo.ipo_proxima }}"><br><br>

                <label>Observaciones:</label><br>
                <textarea name="observaciones">{{ equipo.descripcion }}</textarea><br><br>

                <button type="submit" class="button">Actualizar Equipo</button>
            </form>
            <br>
            <a href="/home" class="button">Volver al inicio</a>
        </div>
    </main>
</body>
</html>
'''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)# -*- coding: utf-8 -*-
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

# Lista de administradores para autocompletado
ADMINISTRADORES = [
    "2005 Administraciones VBG, S.L.ADMINISTRACIÓN DE FINCAS",
    "8 FINCAS Manuel Alejo",
    "AAF-Arquitectura",
    "ADMINISTRACION FINCAS REYES",
    "ADMINISTRACIONES S.R.",
    "ADMINISTRADORES DE FINCAS ESPACIO DOS",
    "AIRAM MARTEL - Administrador de Fincas",
    "AL Abogados&Administradores",
    "AMIAT, ADMINISTRACION DE FINCAS",
    "ASESORIA H.F.",
    "Abogados Administradores de Fincas García Grima",
    "Administración Ascanio Asociados Sociedad Limitada Profesional",
    "Administración de Fincas",
    "Administración de Fincas Canarias Isla",
    "Administración de Fincas Don Benito S.A",
    "Administración de Fincas F. Abreu",
    "Administración de Fincas Fefora,s.l.",
    "Administración de Fincas García Camacho, S.L.P.",
    "Administración de Fincas Germán Navarro",
    "Administración de Fincas Leguerin S.L",
    "Administración de Fincas Martín Trujillo",
    "Administración de Fincas Melián",
    "Administración de Fincas Melián y Figueroa SLP",
    "Administración de Fincas Raúl Rodríguez y Asociados",
    "Administración de Fincas Sánchez Delgado & Asociados,S.L.P.",
    "Administración de Fincas Zulima Guerra López",
    "Administración de fincas FUTURAFFIN",
    "Administración de fincas José Alejandro González",
    "Administración de fincas Siverio Medina, SLP",
    "Administrador De Fincas Francisco Manuel Garcia-Camacho",
    "Administrador de Fincas",
    "Administrador de Fincas Elías Monzón",
    "Administrador de Fincas Yván Morales",
    "Administrador de fincas Jesús Jiménez",
    "Administradores de Fincas Feliciano Suárez",
    "Administradores de Fincas Geslain S.L.",
    "Administradores de Fincas González & Lorenzo Cardona",
    "Administradores de Fincas Rogelio José Sánchez Delgado y Asociados,S.L",
    "Baires Administración de Fincas",
    "Bradomin Administración de fincas",
    "Bufete Jurídico Del Castillo",
    "Bufete Pilar Felipe, Abogados",
    "C.A.I. ADMINISTRACION DE FINCAS, SLP",
    "COMUNIADMINISTRA",
    "COMUNIFINCAS",
    "Cabrera Báez Abogados - Administradores de Fincas",
    "Canarias Administración de Fincas S.L",
    "Canarias Administración de Fincas S.L.",
    "Castaño & Monzón Abogados",
    "Cayetano Ojeda. Abogados",
    "Communityfive",
    "Dévora Aranda, Administrador de Fincas",
    "ERA Canarias",
    "El Pilar Consulting",
    "Eslava Administrador De Fincas",
    "Eslava y Asociados, SLP",
    "Estudio Jurídico Francisco Suárez",
    "FINCAS 27",
    "Fincas Alberty SL",
    "Fincas Bermejo",
    "Fincas G. Canarias",
    "Fincas García",
    "Fincas Grupo MGC",
    "Fincas Los Cristianos",
    "Fincas Mederos y Asociados Administradores de fincas",
    "Fincas Monterrey",
    "Fincas Moscú",
    "Fincas Servicio & Gestión",
    "Fincas Tamaraceite",
    "Francisco González, Administrador De Fincas",
    "Francisco Luis Suarez González",
    "Gabriel Fumero Hernández. Administrador de Fincas. API Nº 3.017",
    "Gerardo Ledesma Fernández - Administrador de Fincas",
    "Gestfincas",
    "Gestión Administrativa Global",
    "Grupo Servifincas Canarias, S.L.",
    "Gestión de Fincas Jesús Hernández",
    "Gestión y Administración de Fincas",
    "HERJOTAX",
    "Hernández Delgado Asociados",
    "Interbrok",
    "Interjurídico",
    "Jiménez Ríos - Abogados Administradores de Fincas",
    "José Manuel Navarro Melián - Administrador de Fincas - Abogado",
    "Legiscorp Consultores",
    "Litosa Administración de fincas",
    "López Ballesteros, José Antonio - Administrador De Fincas",
    "Melián Melián Carlos - Administrador De Fincas",
    "Mon & Partners Administradores",
    "PALMAS FINCAS Administración de Fincas",
    "Pérez Rodríguez, Blanco Rodríguez y Asociados",
    "Pérez-Rodríguez, Blanco-Rodríguez y Asociados",
    "Ramón Bolaños Talavera",
    "Reyes Hernández Alicia",
    "SEGAL ASESORÍA y ADMINISTRACIÓN",
    "SHM Administración de fincas",
    "SIE Consulting",
    "Santiago López Mendoza",
    "Siga Administradores",
    "Simply Canaries",
    "Srcomunidades",
    "Surimaspa S.L.",
    "Tomás Padrón Alamo",
    "Zona Residencial Toni Gallardo",
    "fgestiona Administrador de Fincas Las Palmas de Gran Canaria"
]

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

    # Para GET: mostrar formulario con fecha actual por defecto
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template_string(FORM_TEMPLATE, fecha_hoy=fecha_hoy)

# NUEVA RUTA: Visita a Administrador
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
            return """
            <h3>Visita registrada correctamente</h3>
            <a href='/visita_administrador' class='button'>Añadir otra visita</a><br><br>
            <a href='/home' class='button'>Volver al inicio</a>
            """
        else:
            return f"<h3 style='color:red;'>Error al registrar visita</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"
    
    # GET: mostrar formulario
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    return render_template_string(VISITA_ADMIN_TEMPLATE, fecha_hoy=fecha_hoy, administradores=ADMINISTRADORES)

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

        # Limpiar campos vacíos
        for key, value in equipo_data.items():
            if value == "":
                equipo_data[key] = None

        res = requests.post(f"{SUPABASE_URL}/rest/v1/equipos", json=equipo_data, headers=HEADERS)
        if res.status_code in [200, 201]:
            return f"""
            <h3>Equipo registrado correctamente</h3>
            <a href='/nuevo_equipo?cliente_id={cliente_id}' class='button'>Añadir otro equipo</a><br><br>
            <a href='/home' class='button'>Finalizar y volver al inicio</a>
            """
        else:
            return f"<h3 style='color:red;'>Error al registrar equipo</h3><pre>{res.text}</pre><a href='/home'>Volver</a>"

    return render_template_string(EQUIPO_TEMPLATE, cliente=cliente_data)

# DESCARGO COMERCIAL MENSUAL CON 2 HOJAS
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
        response_clientes = requests.get(f"{SUPABASE_URL}/rest/v1/clientes?{query_clientes}&select=*", headers=HEADERS)
        
        # Consultar visitas a administradores del mes
        response_admin = requests.get(f"{SUPABASE_URL}/rest/v1/visitas_administradores?{query_clientes}&select=*", headers=HEADERS)
        
        if response_clientes.status_code != 200:
            return f"Error al obtener datos de instalaciones: {response_clientes.text}"
        
        clientes_mes = response_clientes.json()
        visitas_admin_mes = response_admin.json() if response_admin.status_code == 200 else []
        
        # Generar Excel con 2 hojas
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        
        # HOJA 1: VISITAS A INSTALACIONES
        ws1 = wb.active
        ws1.title = "VISITAS INSTALACIONES"
        
        headers_instalaciones = ['FECHA', 'COMUNIDAD/EMPRESA', 'DIRECCION', 'ZONA', 'OBSERVACIONES']
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'), 
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Encabezados hoja 1
        for col, header in enumerate(headers_instalaciones, 1):
            cell = ws1.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        # Datos de instalaciones
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
        
        # Ajustar anchos de columna hoja 1
        ws1.column_dimensions['A'].width = 12
        ws1.column_dimensions['B'].width = 40
        ws1.column_dimensions['C'].width = 50
        ws1.column_dimensions['D'].width = 20
        ws1.column_dimensions['E'].width = 70
        
        # HOJA 2: VISITAS A ADMINISTRADORES
        ws2 = wb.create_sheet(title="VISITAS ADMINISTRADORES")
        
        headers_admin = ['FECHA', 'ADMINISTRADOR', 'PERSONA CONTACTO', 'OBSERVACIONES']
        
        # Encabezados hoja 2
        for col, header in enumerate(headers_admin, 1):
            cell = ws2.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border
        
        # Datos de visitas a administradores
        row = 2
        for visita in visitas_admin_mes:
            ws2.cell(row=row, column=1, value=visita.get('fecha_visita', ''))
            ws2.cell(row=row, column=2, value=visita.get('administrador_fincas', ''))
            ws2.cell(row=row, column=3, value=visita.get('persona_contacto', ''))
            ws2.cell(row=row, column=4, value=visita.get('observaciones', ''))
            
            for col in range(1, 5):
                ws2.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        # Ajustar anchos de columna hoja 2
        ws2.column_dimensions['A'].width = 12
        ws2.column_dimensions['B'].width = 50
        ws2.column_dimensions['C'].width = 30
        ws2.column_dimensions['D'].width = 70
        
        # Guardar archivo en memoria
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generar respuesta de descarga
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
        return f"<h3 style='color:red;'>Error al obtener leads</h3><pre>{response.text}</pre><a href='/home'>Volver</a>"

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
            
            # Empresa mantenedora ahora viene del cliente
            empresa_mantenedora = lead.get("empresa_mantenedora", "-")
            if empresa_mantenedora:
                empresas_disponibles.add(empresa_mantenedora)

            if equipos:
                for equipo in equipos:
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
                        "empresa_mantenedora": empresa_mantenedora,
                        "fecha_vencimiento_contrato": fecha_vencimiento,
                        "ipo_proxima": ipo_proxima,
                        "ipo_fecha_original": ipo_fecha_original
                    }
                    
                    # Aplicar filtros
                    incluir_fila = True
                    
                    # Filtro por empresa
                    if filtro_empresa and filtro_empresa != empresa_mantenedora:
                        incluir_fila = False
                    
                    # Filtro por localidad
                    if filtro_localidad and filtro_localidad != lead.get("localidad", ""):
                        incluir_fila = False
                    
                    # Filtro por IPO
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
                    "empresa_mantenedora": empresa_mantenedora,
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

    # GET: Consultar el lead
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

        # Limpiar campos vacíos
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

# PLANTILLAS HTML
LOGIN_TEMPLATE = '''

FORM_TEMPLATE = '''
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
            <h1>Visita a Instalación</h1>
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

                <button type="submit" class="button">Registrar Lead</button>
            </form>
            <a href="/home" class="button">Volver</a>
        </div>
    </main>
</body>
</html>
'''
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
                <input type="text" name="administrador_fincas" list="administradores_list" required 
                       placeholder="Escribe o selecciona un administrador"><br>
                <datalist id="administradores_list">
                    {% for admin in administradores %}
                    <option value="{{ admin }}">
                    {% endfor %}
                </datalist><br>

                <label>Persona de Contacto:</label><br>
                <input type="text" name="persona_contacto" placeholder="Opcional"><br><br>

                <label>Resultado de la Visita / Observaciones:</label><br>
                <textarea name="observaciones" rows="8" required></textarea><br><br>

                <button type="submit" class="button">Registrar Visita</button>
            </form>
            <a href="/home" class="button">Volver</a>
        </div>
    </main>
</body>
</html>
'''
