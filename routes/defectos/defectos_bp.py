"""
Blueprint de Defectos

Gestión de defectos de inspecciones con funcionalidades de:
- Dashboard con estadísticas y filtros operativos
- Exportación a PDF agrupado por máquina
- CRUD completo de defectos
- Subsanación y reversión de estado
- Gestión operativa (técnicos, materiales, stock)
- Actualización AJAX para campos de gestión
"""

from flask import Blueprint, render_template, request, redirect, flash, make_response, jsonify
from datetime import datetime, date
import os
import requests
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import helpers

# Configuración de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Crear Blueprint
defectos_bp = Blueprint('defectos', __name__, url_prefix='/defectos')


@defectos_bp.route('')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def dashboard():
    """Dashboard principal de defectos con estadísticas y filtros"""
    
    # Obtener todos los defectos con información de urgencia usando la vista
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_defectos_con_urgencia?select=*&order=fecha_limite.asc",
        headers=HEADERS
    )
    
    todos_defectos = []
    if response.status_code == 200:
        todos_defectos = response.json()
    
    # Calcular estadísticas generales
    total_defectos = len(todos_defectos)
    defectos_pendientes = [d for d in todos_defectos if d.get('estado') == 'PENDIENTE']
    defectos_subsanados = [d for d in todos_defectos if d.get('estado') == 'SUBSANADO']
    
    # Aplicar filtros
    filtro_tecnico = request.args.get('tecnico', '')
    filtro_material = request.args.get('material', '')
    filtro_stock = request.args.get('stock', '')
    
    if filtro_tecnico:
        if filtro_tecnico == 'sin_asignar':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('tecnico_asignado')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('tecnico_asignado') == filtro_tecnico]
    
    if filtro_material:
        if filtro_material == 'sin_definir':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('gestion_material')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('gestion_material') == filtro_material]
    
    if filtro_stock:
        if filtro_stock == 'sin_definir':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('estado_stock')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('estado_stock') == filtro_stock]
    
    # Clasificar por urgencia
    defectos_vencidos = [d for d in defectos_pendientes if d.get('nivel_urgencia') == 'VENCIDO']
    defectos_urgentes = [d for d in defectos_pendientes if d.get('nivel_urgencia') == 'URGENTE']
    defectos_proximos = [d for d in defectos_pendientes if d.get('nivel_urgencia') == 'PROXIMO']
    defectos_normales = [d for d in defectos_pendientes if d.get('nivel_urgencia') == 'NORMAL']
    
    # Estadísticas por calificación (solo pendientes)
    defectos_dl = [d for d in defectos_pendientes if d.get('calificacion') == 'DL']  # Defecto Leve
    defectos_dg = [d for d in defectos_pendientes if d.get('calificacion') == 'DG']  # Defecto Grave
    defectos_dmg = [d for d in defectos_pendientes if d.get('calificacion') == 'DMG']  # Defecto Muy Grave
    
    # Obtener información adicional de inspecciones para enriquecer datos
    response_insp = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?select=id,maquina,direccion,poblacion,fecha_inspeccion,oca_id,oca:ocas(nombre)",
        headers=HEADERS
    )
    
    inspecciones_dict = {}
    if response_insp.status_code == 200:
        inspecciones = response_insp.json()
        for insp in inspecciones:
            inspecciones_dict[insp['id']] = insp
    
    # Enriquecer defectos con información de inspección
    for defecto in todos_defectos:
        insp_id = defecto.get('inspeccion_id')
        if insp_id and insp_id in inspecciones_dict:
            insp = inspecciones_dict[insp_id]
            defecto['direccion'] = insp.get('direccion')
            defecto['poblacion'] = insp.get('poblacion')
            defecto['fecha_inspeccion'] = insp.get('fecha_inspeccion')
            defecto['oca_nombre'] = insp.get('oca', {}).get('nombre') if insp.get('oca') else None
    
    return render_template(
        "defectos_dashboard.html",
        total_defectos=total_defectos,
        total_pendientes=len(defectos_pendientes),
        total_subsanados=len(defectos_subsanados),
        defectos_vencidos=defectos_vencidos,
        defectos_urgentes=defectos_urgentes,
        defectos_proximos=defectos_proximos,
        defectos_normales=defectos_normales,
        defectos_subsanados=defectos_subsanados,
        defectos_dl=len(defectos_dl),
        defectos_dg=len(defectos_dg),
        defectos_dmg=len(defectos_dmg),
        todos_defectos=todos_defectos
    )


@defectos_bp.route('/exportar_pdf')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def exportar_pdf():
    """Exporta defectos a PDF en formato horizontal, agrupados por máquina"""
    
    # Obtener todos los defectos con información de urgencia usando la vista
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/v_defectos_con_urgencia?select=*&order=fecha_limite.asc",
        headers=HEADERS
    )
    
    todos_defectos = []
    if response.status_code == 200:
        todos_defectos = response.json()
    
    # Aplicar filtros (mismo código que el dashboard)
    defectos_pendientes = [d for d in todos_defectos if d.get('estado') == 'PENDIENTE']
    
    filtro_tecnico = request.args.get('tecnico', '')
    filtro_material = request.args.get('material', '')
    filtro_stock = request.args.get('stock', '')
    
    if filtro_tecnico:
        if filtro_tecnico == 'sin_asignar':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('tecnico_asignado')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('tecnico_asignado') == filtro_tecnico]
    
    if filtro_material:
        if filtro_material == 'sin_definir':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('gestion_material')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('gestion_material') == filtro_material]
    
    if filtro_stock:
        if filtro_stock == 'sin_definir':
            defectos_pendientes = [d for d in defectos_pendientes if not d.get('estado_stock')]
        else:
            defectos_pendientes = [d for d in defectos_pendientes if d.get('estado_stock') == filtro_stock]
    
    # Obtener información adicional de inspecciones para enriquecer datos
    response_insp = requests.get(
        f"{SUPABASE_URL}/rest/v1/inspecciones?select=id,maquina,direccion,poblacion,fecha_inspeccion,oca_id,oca:ocas(nombre)",
        headers=HEADERS
    )
    
    inspecciones_dict = {}
    if response_insp.status_code == 200:
        inspecciones = response_insp.json()
        for insp in inspecciones:
            inspecciones_dict[insp['id']] = insp
    
    # Enriquecer defectos con información de inspección
    for defecto in defectos_pendientes:
        insp_id = defecto.get('inspeccion_id')
        if insp_id and insp_id in inspecciones_dict:
            insp = inspecciones_dict[insp_id]
            defecto['direccion'] = insp.get('direccion')
            defecto['poblacion'] = insp.get('poblacion')
            defecto['fecha_inspeccion'] = insp.get('fecha_inspeccion')
            defecto['oca_nombre'] = insp.get('oca', {}).get('nombre') if insp.get('oca') else None
    
    # Agrupar defectos por máquina
    defectos_por_maquina = {}
    for defecto in defectos_pendientes:
        maquina = defecto.get('maquina', 'Sin especificar')
        if maquina not in defectos_por_maquina:
            defectos_por_maquina[maquina] = []
        defectos_por_maquina[maquina].append(defecto)
    
    # Generar PDF
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    # Elementos del PDF
    elementos = []
    
    # Logo
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo-fedes-ascensores.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=4*cm, height=1.6*cm)
        elementos.append(logo)
        elementos.append(Spacer(1, 0.3*cm))
    
    # Título
    styles = getSampleStyleSheet()
    titulo = Paragraph("<b>LISTADO DE DEFECTOS PENDIENTES</b>", styles['Title'])
    elementos.append(titulo)
    
    # Fecha de generación
    fecha_hoy = datetime.now().strftime('%d/%m/%Y %H:%M')
    fecha_texto = Paragraph(f"<i>Generado el: {fecha_hoy}</i>", styles['Normal'])
    elementos.append(fecha_texto)
    elementos.append(Spacer(1, 0.5*cm))
    
    # Crear tabla para cada máquina
    for maquina, defectos in defectos_por_maquina.items():
        # Título de la máquina
        maquina_titulo = Paragraph(f"<b>MÁQUINA: {maquina}</b>", styles['Heading2'])
        elementos.append(maquina_titulo)
        elementos.append(Spacer(1, 0.2*cm))
        
        # Datos de la tabla
        datos_tabla = [['Defecto', 'Calif.', 'Plazo', 'Límite', 'Días', 'Dirección', 'Población']]
        
        for defecto in defectos:
            datos_tabla.append([
                Paragraph(defecto.get('descripcion', ''), styles['Normal']),
                defecto.get('calificacion', ''),
                f"{defecto.get('plazo_meses', '')}m",
                defecto.get('fecha_limite', '')[:10] if defecto.get('fecha_limite') else '',
                str(defecto.get('dias_restantes', '')),
                Paragraph(defecto.get('direccion', ''), styles['Normal']),
                defecto.get('poblacion', '')
            ])
        
        # Crear tabla
        tabla = Table(datos_tabla, colWidths=[7*cm, 1.5*cm, 1.5*cm, 2*cm, 1.5*cm, 5*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.5*cm))
    
    # Construir PDF
    doc.build(elementos)
    
    # Preparar respuesta
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=defectos_pendientes_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response


@defectos_bp.route('/<int:defecto_id>')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def ver(defecto_id):
    """Ver detalle completo de un defecto"""
    
    # Obtener el defecto con información de inspección
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}&select=*",
        headers=HEADERS
    )
    
    if response.status_code != 200 or not response.json():
        flash("Defecto no encontrado", "error")
        return redirect('/defectos')
    
    defecto = response.json()[0]
    
    # Obtener información de la inspección asociada
    if defecto.get('inspeccion_id'):
        response_insp = requests.get(
            f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{defecto['inspeccion_id']}&select=*",
            headers=HEADERS
        )
        
        if response_insp.status_code == 200 and response_insp.json():
            inspeccion = response_insp.json()[0]
            
            # Obtener información del OCA si existe
            if inspeccion.get('oca_id'):
                response_oca = requests.get(
                    f"{SUPABASE_URL}/rest/v1/ocas?id=eq.{inspeccion['oca_id']}&select=nombre",
                    headers=HEADERS
                )
                if response_oca.status_code == 200 and response_oca.json():
                    inspeccion['oca_nombre'] = response_oca.json()[0].get('nombre')
                else:
                    inspeccion['oca_nombre'] = None
            else:
                inspeccion['oca_nombre'] = None
            
            defecto['inspeccion'] = inspeccion
        else:
            defecto['inspeccion'] = None
    else:
        defecto['inspeccion'] = None
    
    # Calcular días restantes
    if defecto.get('fecha_limite') and defecto.get('estado') == 'PENDIENTE':
        try:
            fecha_limite = datetime.strptime(defecto['fecha_limite'].split('T')[0], '%Y-%m-%d').date()
            hoy = date.today()
            dias_restantes = (fecha_limite - hoy).days
            defecto['dias_restantes'] = dias_restantes
            
            if dias_restantes < 0:
                defecto['nivel_urgencia'] = 'VENCIDO'
            elif dias_restantes <= 15:
                defecto['nivel_urgencia'] = 'URGENTE'
            elif dias_restantes <= 30:
                defecto['nivel_urgencia'] = 'PROXIMO'
            else:
                defecto['nivel_urgencia'] = 'NORMAL'
        except:
            defecto['nivel_urgencia'] = 'NORMAL'
    else:
        defecto['nivel_urgencia'] = 'COMPLETADO'
    
    return render_template(
        "ver_defecto.html",
        defecto=defecto
    )


@defectos_bp.route('/<int:defecto_id>/editar', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def editar(defecto_id):
    """Editar un defecto existente"""
    
    if request.method == "POST":
        # Obtener datos del formulario
        descripcion = request.form.get("descripcion")
        calificacion = request.form.get("calificacion")
        plazo_meses = request.form.get("plazo_meses", type=int)
        fecha_limite_str = request.form.get("fecha_limite")
        estado = request.form.get("estado")
        fecha_subsanacion_str = request.form.get("fecha_subsanacion")
        es_cortina = request.form.get("es_cortina") == "on"
        es_pesacarga = request.form.get("es_pesacarga") == "on"
        observaciones = request.form.get("observaciones")
        
        # Nuevos campos de gestión operativa
        tecnico_asignado = request.form.get("tecnico_asignado") or None
        gestion_material = request.form.get("gestion_material") or None
        estado_stock = request.form.get("estado_stock") or None
        
        # Validaciones
        if not descripcion or not calificacion:
            flash("Descripción y calificación son obligatorios", "error")
            return redirect(f"/defectos/{defecto_id}/editar")
        
        # Obtener el defecto actual para verificar si cambió el plazo
        response_defecto = requests.get(
            f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}&select=plazo_meses,inspeccion_id",
            headers=HEADERS
        )
        
        if response_defecto.status_code == 200 and response_defecto.json():
            defecto_actual = response_defecto.json()[0]
            plazo_anterior = defecto_actual.get('plazo_meses')
            inspeccion_id = defecto_actual.get('inspeccion_id')
            
            # Si cambió el plazo, recalcular la fecha límite
            if plazo_meses != plazo_anterior and inspeccion_id:
                # Obtener fecha de inspección
                response_insp = requests.get(
                    f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{inspeccion_id}&select=fecha_inspeccion",
                    headers=HEADERS
                )
                
                if response_insp.status_code == 200 and response_insp.json():
                    fecha_inspeccion = response_insp.json()[0].get('fecha_inspeccion')
                    
                    if fecha_inspeccion:
                        try:
                            fecha_insp_dt = datetime.strptime(fecha_inspeccion.split('T')[0], '%Y-%m-%d')
                            # Sumar plazo en meses
                            mes_limite = fecha_insp_dt.month + plazo_meses
                            anio_limite = fecha_insp_dt.year + (mes_limite - 1) // 12
                            mes_limite = ((mes_limite - 1) % 12) + 1
                            
                            fecha_limite_dt = fecha_insp_dt.replace(year=anio_limite, month=mes_limite)
                            fecha_limite_str = fecha_limite_dt.strftime('%Y-%m-%d')
                        except Exception as e:
                            flash(f"Error al calcular fecha límite: {str(e)}", "error")
        
        # Preparar datos para actualizar
        datos_actualizacion = {
            "descripcion": descripcion,
            "calificacion": calificacion,
            "plazo_meses": plazo_meses,
            "fecha_limite": fecha_limite_str,
            "estado": estado,
            "es_cortina": es_cortina,
            "es_pesacarga": es_pesacarga,
            "observaciones": observaciones,
            "tecnico_asignado": tecnico_asignado,
            "gestion_material": gestion_material,
            "estado_stock": estado_stock
        }
        
        # Si el estado es subsanado y hay fecha, incluirla
        if estado == "SUBSANADO" and fecha_subsanacion_str:
            datos_actualizacion["fecha_subsanacion"] = fecha_subsanacion_str
        elif estado == "PENDIENTE":
            datos_actualizacion["fecha_subsanacion"] = None
        
        # Actualizar en la base de datos
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}",
            headers=HEADERS,
            json=datos_actualizacion
        )
        
        if response.status_code in [200, 204]:
            flash("Defecto actualizado correctamente", "success")
            return redirect(f"/defectos/{defecto_id}")
        else:
            flash(f"Error al actualizar defecto: {response.text}", "error")
            return redirect(f"/defectos/{defecto_id}/editar")
    
    # GET: Mostrar formulario de edición
    # Obtener el defecto
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}&select=*",
        headers=HEADERS
    )
    
    if response.status_code != 200 or not response.json():
        flash("Defecto no encontrado", "error")
        return redirect('/defectos')
    
    defecto = response.json()[0]
    
    # Obtener información de la inspección asociada
    if defecto.get('inspeccion_id'):
        response_insp = requests.get(
            f"{SUPABASE_URL}/rest/v1/inspecciones?id=eq.{defecto['inspeccion_id']}&select=id,rae,maquina,direccion,fecha_inspeccion",
            headers=HEADERS
        )
        
        if response_insp.status_code == 200 and response_insp.json():
            defecto['inspeccion'] = response_insp.json()[0]
        else:
            defecto['inspeccion'] = {'maquina': 'N/A', 'direccion': 'N/A'}
    else:
        defecto['inspeccion'] = {'maquina': 'N/A', 'direccion': 'N/A'}
    
    return render_template(
        "editar_defecto.html",
        defecto=defecto
    )


@defectos_bp.route('/<int:defecto_id>/subsanar', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def subsanar(defecto_id):
    """Marcar un defecto como subsanado"""
    
    data = {
        "estado": "SUBSANADO",
        "fecha_subsanacion": date.today().isoformat()
    }
    
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}",
        json=data,
        headers=HEADERS
    )
    
    if response.status_code in [200, 204]:
        flash("Defecto marcado como subsanado", "success")
    else:
        flash("Error al actualizar defecto", "error")
    
    return redirect(request.referrer)


@defectos_bp.route('/<int:defecto_id>/revertir', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def revertir(defecto_id):
    """Revertir un defecto subsanado a estado pendiente"""
    
    data = {
        "estado": "PENDIENTE",
        "fecha_subsanacion": None
    }
    
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}",
        json=data,
        headers=HEADERS
    )
    
    if response.status_code in [200, 204]:
        flash("Defecto revertido a pendiente", "success")
    else:
        flash("Error al revertir defecto", "error")
    
    return redirect(request.referrer)


@defectos_bp.route('/<int:defecto_id>/eliminar')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'delete')
def eliminar(defecto_id):
    """Eliminar un defecto"""
    
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}",
        headers=HEADERS
    )
    
    if response.status_code in [200, 204]:
        flash("Defecto eliminado correctamente", "success")
    else:
        flash("Error al eliminar defecto", "error")
    
    return redirect(request.referrer)


@defectos_bp.route('/<int:defecto_id>/actualizar_gestion', methods=["POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def actualizar_gestion(defecto_id):
    """Endpoint para actualización rápida de campos de gestión operativa desde el dashboard"""
    try:
        data = request.json
        campo = data.get("campo")
        valor = data.get("valor")
        
        if not campo:
            return {"error": "Campo requerido"}, 400
        
        # Mapear campos del frontend a campos de base de datos
        campos_map = {
            "tecnico": "tecnico_asignado",
            "material": "gestion_material",
            "stock": "estado_stock"
        }
        
        if campo not in campos_map:
            return {"error": "Campo no válido"}, 400
        
        campo_db = campos_map[campo]
        
        # Preparar datos para actualizar
        datos_actualizacion = {
            campo_db: valor if valor else None
        }
        
        # Actualizar en la base de datos
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/defectos_inspeccion?id=eq.{defecto_id}",
            headers=HEADERS,
            json=datos_actualizacion
        )
        
        if response.status_code in [200, 204]:
            return {"success": True, "campo": campo, "valor": valor}, 200
        else:
            return {"error": f"Error al actualizar: {response.text}"}, 500
    except Exception as e:
        return {"error": str(e)}, 500
