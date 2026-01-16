#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Documentación PDF - AscensorAlert CRM
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

def generar_documentacion_pdf():
    """Genera el PDF con la documentación completa"""

    # Crear el PDF
    filename = f"AscensorAlert_Documentacion_Completa_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#c7254e'),
        fontName='Courier',
        leftIndent=20,
        spaceAfter=6
    )

    # Contenido del PDF
    story = []

    # Portada
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("DOCUMENTACIÓN COMPLETA", title_style))
    story.append(Paragraph("ASCENSORALERT CRM", title_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Análisis Exhaustivo de la Aplicación", h2_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%d de %B de %Y')}", body_style))
    story.append(PageBreak())

    # 1. ESTRUCTURA DEL PROYECTO
    story.append(Paragraph("1. ESTRUCTURA DEL PROYECTO", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Organización de Carpetas", h2_style))
    story.append(Paragraph(
        "AscensorAlert es una aplicación Flask de 8,567 líneas con 115 rutas distribuidas en los siguientes módulos:",
        body_style
    ))

    estructura_folders = [
        ["Carpeta/Archivo", "Descripción"],
        ["app.py", "Aplicación principal Flask (8,567 líneas, 115 rutas)"],
        ["helpers.py", "Funciones auxiliares y sistema de permisos"],
        ["database/", "Schemas SQL y migraciones (14 migraciones)"],
        ["templates/", "Frontend HTML/Jinja2 (45+ templates)"],
        ["static/", "Archivos estáticos (CSS, JS, imágenes)"],
        ["scripts/", "Scripts de importación y utilidad"],
        ["analizador_ia.py", "Motor de IA con Claude"],
        ["detectores_alertas.py", "Sistema de alertas automáticas"],
    ]

    t = Table(estructura_folders, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Tecnologías Principales", h2_style))

    tech_data = [
        ["Capa", "Tecnología", "Propósito"],
        ["Backend", "Flask 2.3.3", "Framework web Python"],
        ["Base de Datos", "PostgreSQL (Supabase)", "Base de datos relacional"],
        ["Almacenamiento", "Supabase Storage", "PDFs, documentos, archivos"],
        ["IA/ML", "Anthropic Claude 3.5 Sonnet", "Análisis predictivo"],
        ["Frontend", "HTML5, Jinja2, CSS3, JS", "Interfaz responsiva"],
        ["Reportes", "ReportLab, openpyxl, pandas", "Exportación PDF/Excel"],
        ["Email", "Resend API", "Notificaciones por correo"],
    ]

    t2 = Table(tech_data, colWidths=[3.5*cm, 5.5*cm, 7*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t2)

    story.append(PageBreak())

    # 2. MODELOS DE DATOS
    story.append(Paragraph("2. MODELOS DE DATOS", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Base de Datos Principal", h2_style))
    story.append(Paragraph(
        "La aplicación utiliza PostgreSQL alojado en Supabase con más de 15 tablas relacionales y vistas SQL para reportes.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    # Tabla instalaciones
    story.append(Paragraph("Tabla: <b>instalaciones</b> (Edificios/Comunidades)", h3_style))
    instalaciones_fields = [
        ["Campo", "Tipo", "Descripción"],
        ["id", "PK", "Identificador único"],
        ["nombre", "TEXT", "Identificación del edificio/comunidad"],
        ["municipio", "TEXT", "Para agrupación y análisis"],
        ["en_cartera", "BOOLEAN", "Estado activo/inactivo"],
        ["fecha_salida_cartera", "TIMESTAMP", "Cuándo se desactivó"],
        ["motivo_salida", "TEXT", "Razón de baja"],
    ]

    t3 = Table(instalaciones_fields, colWidths=[4*cm, 3*cm, 9*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.3*cm))

    # Tabla máquinas
    story.append(Paragraph("Tabla: <b>maquinas_cartera</b> (Ascensores/Equipos)", h3_style))
    maquinas_fields = [
        ["Campo", "Tipo", "Descripción"],
        ["id", "PK", "Identificador único"],
        ["instalacion_id", "FK", "Referencia a instalaciones"],
        ["identificador", "TEXT", "Nombre único (ej: MONTACOCHES JAGUAR)"],
        ["codigo_maquina", "TEXT", "Código técnico (ej: V301F8817)"],
        ["en_cartera", "BOOLEAN", "Estado activo/inactivo"],
    ]

    t4 = Table(maquinas_fields, colWidths=[4*cm, 3*cm, 9*cm])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t4)
    story.append(Spacer(1, 0.3*cm))

    # Tabla partes_trabajo
    story.append(Paragraph("Tabla: <b>partes_trabajo</b> (Historial de Intervenciones)", h3_style))
    story.append(Paragraph(
        "Registro completo de todas las intervenciones técnicas realizadas en las máquinas. "
        "Incluye: número de parte, tipo (normalizado), fecha, máquina afectada, resolución, "
        "recomendaciones técnicas, estado, prioridad, costes y facturación.",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    partes_fields = [
        ["Campo Clave", "Descripción"],
        ["numero_parte", "Identificador único (ej: 2024000022)"],
        ["tipo_parte_normalizado", "MANTENIMIENTO, AVERIA, REPARACION, etc."],
        ["resolucion", "Descripción completa del trabajo realizado"],
        ["tiene_recomendacion", "Boolean si tiene recomendación técnica"],
        ["estado", "COMPLETADO, PENDIENTE, EN_PROCESO, CANCELADO"],
        ["prioridad", "BAJA, NORMAL, ALTA, URGENTE"],
    ]

    t5 = Table(partes_fields, colWidths=[5*cm, 11*cm])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t5)

    story.append(PageBreak())

    # Módulo de Inspecciones
    story.append(Paragraph("Módulo de Inspecciones (IPOs)", h2_style))
    story.append(Paragraph(
        "Sistema completo para gestión de inspecciones periódicas obligatorias (IPOs), "
        "defectos encontrados, materiales especiales (cortinas y pesacargas según ITC-AEM1), "
        "y seguimiento de OCAs (Organismos de Control Autorizados).",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>inspecciones</b> (Actas de Inspección)", h3_style))
    inspecciones_fields = [
        ["Campo", "Descripción"],
        ["numero_certificado", "Referencia del OCA"],
        ["oca_id", "FK a tabla OCAs"],
        ["fecha_inspeccion", "Fecha del acta"],
        ["estado_presupuesto", "PENDIENTE, PREPARANDO, ENVIADO, ACEPTADO, RECHAZADO"],
        ["estado_trabajo", "PENDIENTE, EN_EJECUCION, COMPLETADO"],
    ]

    t6 = Table(inspecciones_fields, colWidths=[5*cm, 11*cm])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t6)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>defectos_inspeccion</b> (Defectos Encontrados)", h3_style))
    defectos_fields = [
        ["Campo", "Descripción"],
        ["codigo_defecto", "Código oficial del defecto"],
        ["calificacion", "DL (leve), DG (grave), DMG (muy grave)"],
        ["plazo_meses", "Meses para reparar según calificación"],
        ["fecha_limite", "Calculada automáticamente"],
        ["es_cortina / es_pesacarga", "Marcas especiales (ITC-AEM1 julio 2024)"],
        ["estado_subsanacion", "PENDIENTE / SUBSANADO"],
    ]

    t7 = Table(defectos_fields, colWidths=[5*cm, 11*cm])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t7)

    story.append(PageBreak())

    # Módulo de Alertas V2
    story.append(Paragraph("Módulo de Alertas Automáticas V2", h2_style))
    story.append(Paragraph(
        "Sistema inteligente de detección automática de patrones críticos en el mantenimiento. "
        "Incluye 3 detectores que analizan el historial de partes y generan alertas cuando "
        "detectan situaciones de riesgo.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>componentes_criticos</b> (Base de Conocimiento)", h3_style))
    componentes_fields = [
        ["Campo", "Descripción"],
        ["nombre", "Componente (Puerta automática, Cerradero, etc.)"],
        ["familia", "PUERTAS, MANIOBRA, SEGURIDAD, COMUNICACION, etc."],
        ["keywords[]", "Array de palabras clave para detección automática"],
        ["nivel_critico", "ALTO, MEDIO, BAJO"],
        ["coste_reparacion_promedio", "Coste medio de reparación"],
    ]

    t8 = Table(componentes_fields, colWidths=[5*cm, 11*cm])
    t8.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1abc9c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t8)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Detectores Automáticos", h3_style))
    story.append(Paragraph(
        "<b>Detector 1 - FALLAS_REPETIDAS:</b> Detecta 2+ fallos en 30 días del mismo componente → ALERTA ALTA",
        body_style
    ))
    story.append(Paragraph(
        "<b>Detector 2 - RECOMENDACIONES_IGNORADAS:</b> Recomendación no ejecutada + 2 averías posteriores → ALERTA MEDIA",
        body_style
    ))
    story.append(Paragraph(
        "<b>Detector 3 - MANTENIMIENTOS_OMITIDOS:</b> 60+ días sin conservación + averías recientes → ALERTA ALTA",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>alertas_automaticas</b> (Alertas Generadas)", h3_style))
    alertas_fields = [
        ["Campo", "Valores"],
        ["tipo_alerta", "FALLA_REPETIDA, RECOMENDACION_IGNORADA, MANTENIMIENTO_OMITIDO"],
        ["nivel_urgencia", "URGENTE, ALTA, MEDIA, BAJA"],
        ["estado", "PENDIENTE, EN_REVISION, OPORTUNIDAD_CREADA, RESUELTA, DESCARTADA"],
        ["datos_deteccion", "JSON con detalles del patrón detectado"],
        ["notificacion_enviada", "Boolean - si se envió email"],
    ]

    t9 = Table(alertas_fields, colWidths=[5*cm, 11*cm])
    t9.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t9)

    story.append(PageBreak())

    # Módulo de IA Predictiva
    story.append(Paragraph("Módulo de IA Predictiva", h2_style))
    story.append(Paragraph(
        "Integración con Anthropic Claude 3.5 Sonnet para análisis técnico inteligente. "
        "La IA analiza cada parte de trabajo, identifica patrones, predice fallos futuros "
        "y calcula el ROI de intervenciones preventivas.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>analisis_partes_ia</b> (Análisis por Claude)", h3_style))
    analisis_fields = [
        ["Campo", "Descripción"],
        ["componente_principal", "Componente afectado identificado por IA"],
        ["tipo_fallo", "Desgaste, ruptura, desajuste, obstrucción, etc."],
        ["causa_raiz", "Explicación técnica de la causa"],
        ["probabilidad_recurrencia", "0-100% de que vuelva a fallar"],
        ["tiempo_estimado_proxima_falla", "Días estimados hasta próxima falla"],
        ["gravedad_tecnica", "LEVE, MODERADA, GRAVE, CRITICA"],
        ["recomendacion_ia", "Recomendación técnica generada por IA"],
        ["coste_estimado_preventivo", "Coste si se actúa preventivamente"],
        ["coste_estimado_correctivo", "Coste si se espera a que falle"],
    ]

    t10 = Table(analisis_fields, colWidths=[5.5*cm, 10.5*cm])
    t10.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t10)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Tabla: <b>predicciones_maquina</b> (Predicciones Agregadas)", h3_style))
    predicciones_fields = [
        ["Campo", "Descripción"],
        ["estado_salud_ia", "EXCELENTE, BUENA, REGULAR, MALA, CRITICA"],
        ["puntuacion_salud", "0-100 puntos de salud"],
        ["tendencia", "MEJORANDO, ESTABLE, DETERIORANDO, CRITICA"],
        ["componente_riesgo_1/2/3", "Top 3 componentes en riesgo"],
        ["probabilidad_fallo_1/2/3", "Probabilidades de fallo de cada componente"],
        ["patron_detectado", "DESGASTE_PROGRESIVO, etc."],
        ["proxima_intervencion_sugerida", "Fecha recomendada para intervenir"],
        ["ahorro_potencial", "€ ahorrados al intervenir preventivamente"],
        ["roi_intervencion", "% ROI de la intervención"],
    ]

    t11 = Table(predicciones_fields, colWidths=[5.5*cm, 10.5*cm])
    t11.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t11)

    story.append(PageBreak())

    # 3. FUNCIONALIDADES PRINCIPALES
    story.append(Paragraph("3. FUNCIONALIDADES PRINCIPALES", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("A. Módulo CRM - Gestión Comercial", h2_style))
    funcionalidades_crm = [
        ["Funcionalidad", "Descripción"],
        ["Dashboard Principal", "KPIs: clientes, equipos, oportunidades, IPOs próximas, contratos por vencer"],
        ["Gestión de Leads", "Crear, editar, buscar leads. Exportar a Excel"],
        ["Gestión de Equipos", "Registro de ascensores con datos técnicos, IPO, contratos"],
        ["Oportunidades", "Estados: Activa, ganada, perdida. Seguimiento de acciones"],
        ["Visitas", "Registro de visitas a fincas, agenda de eventos"],
        ["Administradores", "Catálogo de administradores de fincas"],
    ]

    t12 = Table(funcionalidades_crm, colWidths=[5*cm, 11*cm])
    t12.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t12)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("B. Módulo de Inspecciones (IPOs)", h2_style))
    funcionalidades_ipos = [
        ["Funcionalidad", "Descripción"],
        ["Dashboard IPOs", "Alertas por urgencia: VENCIDO, URGENTE, PRÓXIMO. Filtros y búsquedas"],
        ["Gestión Inspecciones", "Crear actas, registrar OCA, características técnicas, estados"],
        ["Gestión Defectos", "Registrar DL/DG/DMG, cálculo automático de fechas límite"],
        ["Materiales Especiales", "Seguimiento cortinas y pesacargas (ITC-AEM1 julio 2024)"],
        ["OCAs", "Catálogo de Organismos de Control Autorizados"],
    ]

    t13 = Table(funcionalidades_ipos, colWidths=[5*cm, 11*cm])
    t13.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t13)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("C. Módulo de Cartera (Análisis Técnico)", h2_style))
    funcionalidades_cartera = [
        ["Funcionalidad", "Descripción"],
        ["Dashboard Cartera", "Vista de máquinas, estados por municipio, análisis de partes"],
        ["Importación Datos", "Importar Excel con equipos y partes de trabajo históricos"],
        ["Oportunidades Facturación", "Estados: DETECTADA → PRESUPUESTO → ACEPTADO → COMPLETADO → FACTURADO"],
    ]

    t14 = Table(funcionalidades_cartera, colWidths=[5*cm, 11*cm])
    t14.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t14)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("D. Módulo de Alertas Automáticas V2", h2_style))
    funcionalidades_alertas = [
        ["Funcionalidad", "Descripción"],
        ["Dashboard V2", "KPIs de alertas, máquinas por estado semafórico, pérdidas estimadas"],
        ["Detectores Automáticos", "3 detectores: fallas repetidas, recomendaciones ignoradas, mantenimientos omitidos"],
        ["Alertas Automáticas", "Ver por estado, crear trabajos técnicos u oportunidades"],
        ["Pendientes Técnicos", "Backlog del técnico con seguimiento de repuestos y tiempos"],
    ]

    t15 = Table(funcionalidades_alertas, colWidths=[5*cm, 11*cm])
    t15.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t15)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("E. Módulo de IA Predictiva", h2_style))
    funcionalidades_ia = [
        ["Funcionalidad", "Descripción"],
        ["Dashboard de IA", "Estado de salud, puntuación 0-100, componentes en riesgo, ahorro potencial"],
        ["Análisis de Partes", "Claude analiza cada parte: componente, fallo, causa raíz, probabilidad"],
        ["Predicciones Máquina", "Predicción agregada: salud, tendencia, intervención sugerida, ROI"],
        ["Patrones y ROI", "Detección de patrones, cálculo de ahorro, ranking por prioridad"],
        ["Alertas Predictivas", "Tipos: FALLO_INMINENTE, DETERIORO_PROGRESIVO, PATRON_ANOMALO"],
    ]

    t16 = Table(funcionalidades_ia, colWidths=[5*cm, 11*cm])
    t16.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t16)

    story.append(PageBreak())

    # 4. ARQUITECTURA TÉCNICA
    story.append(Paragraph("4. ARQUITECTURA TÉCNICA", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Flujo de Comunicación", h2_style))
    story.append(Paragraph(
        "La aplicación sigue una arquitectura de 3 capas:",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    arquitectura_capas = [
        ["Capa", "Tecnología", "Responsabilidad"],
        ["Frontend", "HTML/Jinja2 + JavaScript + CSS", "Interfaz de usuario, validaciones cliente"],
        ["Backend", "Flask 2.3.3 (Python)", "Lógica de negocio, autenticación, APIs"],
        ["Base de Datos", "PostgreSQL (Supabase)", "Persistencia, consultas, vistas SQL"],
        ["Servicios Externos", "Claude AI, Resend, Storage", "IA, email, almacenamiento"],
    ]

    t17 = Table(arquitectura_capas, colWidths=[3.5*cm, 5.5*cm, 7*cm])
    t17.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t17)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Sistema de Autenticación", h2_style))
    story.append(Paragraph(
        "La autenticación se basa en sesiones Flask con decoradores personalizados:",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph(
        "<b>@login_required</b>: Verifica que el usuario esté autenticado",
        code_style
    ))
    story.append(Paragraph(
        "<b>@requiere_permiso('modulo', 'accion')</b>: Verifica permisos específicos por perfil",
        code_style
    ))
    story.append(Paragraph(
        "<b>@solo_admin</b>: Restringe acceso solo a administradores",
        code_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Integración con Claude AI", h2_style))
    story.append(Paragraph(
        "La aplicación utiliza Anthropic Claude 3.5 Sonnet para análisis técnico:",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    claude_specs = [
        ["Parámetro", "Valor"],
        ["Modelo", "claude-3-5-sonnet-20241022"],
        ["Temperatura", "0.3 (respuestas técnicas precisas)"],
        ["Max Tokens", "4096"],
        ["Coste por Análisis Parte", "~$0.003"],
        ["Coste por Predicción Máquina", "~$0.015"],
    ]

    t18 = Table(claude_specs, colWidths=[8*cm, 8*cm])
    t18.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(t18)

    story.append(PageBreak())

    # 5. ROLES Y PERMISOS
    story.append(Paragraph("5. ROLES Y PERMISOS", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Sistema RBAC (Role Based Access Control)", h2_style))
    story.append(Paragraph(
        "La aplicación implementa control de acceso basado en roles con 3 perfiles principales:",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Perfil: ADMIN", h3_style))
    admin_permisos = [
        ["Módulo", "Permisos"],
        ["Clientes/Instalaciones", "CRUD completo"],
        ["Equipos/Ascensores", "CRUD completo"],
        ["Administradores de Fincas", "CRUD completo"],
        ["Oportunidades Comerciales", "CRUD completo"],
        ["Visitas", "CRUD completo"],
        ["Inspecciones (IPOs)", "CRUD completo - ACCESO EXCLUSIVO"],
        ["Materiales Especiales", "CRUD completo"],
        ["OCAs", "CRUD completo"],
        ["Cartera & IA", "Acceso total, análisis, detectores"],
        ["Gestión de Usuarios", "Crear, editar, eliminar usuarios"],
        ["Configuración", "Acceso a todas las configuraciones"],
    ]

    t19 = Table(admin_permisos, colWidths=[8*cm, 8*cm])
    t19.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t19)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Perfil: GESTOR", h3_style))
    gestor_permisos = [
        ["Módulo", "Permisos"],
        ["Clientes/Instalaciones", "CRUD completo"],
        ["Equipos/Ascensores", "CRUD completo"],
        ["Administradores de Fincas", "CRUD completo"],
        ["Oportunidades Comerciales", "CRUD completo"],
        ["Visitas", "CRUD completo"],
        ["Inspecciones (IPOs)", "SIN ACCESO - BLOQUEADO"],
        ["Materiales Especiales", "SIN ACCESO - BLOQUEADO"],
        ["OCAs", "SIN ACCESO - BLOQUEADO"],
        ["Cartera", "Solo lectura y análisis"],
        ["Mi Agenda", "CRUD de su agenda personal"],
    ]

    t20 = Table(gestor_permisos, colWidths=[8*cm, 8*cm])
    t20.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t20)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Perfil: VISUALIZADOR", h3_style))
    visualizador_permisos = [
        ["Módulo", "Permisos"],
        ["Clientes/Instalaciones", "Solo lectura"],
        ["Equipos/Ascensores", "Solo lectura"],
        ["Administradores de Fincas", "Solo lectura"],
        ["Oportunidades Comerciales", "Solo lectura"],
        ["Visitas", "SIN ACCESO"],
        ["Inspecciones (IPOs)", "SIN ACCESO - BLOQUEADO"],
        ["Cartera", "Solo lectura"],
        ["Crear/Editar/Eliminar", "SIN PERMISOS en ningún módulo"],
    ]

    t21 = Table(visualizador_permisos, colWidths=[8*cm, 8*cm])
    t21.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t21)

    story.append(PageBreak())

    # 6. RESUMEN EJECUTIVO
    story.append(Paragraph("6. RESUMEN EJECUTIVO", h1_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "<b>AscensorAlert</b> es un <b>CRM empresarial especializado en gestión de ascensores</b> "
        "con capacidades avanzadas de análisis predictivo mediante IA.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Características Clave", h2_style))
    caracteristicas = [
        "Gestión CRM completa: Leads, oportunidades, visitas, administradores",
        "Módulo de Inspecciones: IPOs, defectos, materiales especiales (ITC-AEM1)",
        "IA Predictiva: Claude analiza máquinas y predice averías",
        "Alertas Automáticas: 3 detectores de patrones críticos",
        "Analítica Avanzada: Índice de riesgo (IRI), zonas calientes, ROI",
        "Control de Acceso: 3 perfiles (Admin, Gestor, Visualizador)",
        "Backend Robusto: Flask + PostgreSQL/Supabase",
        "Responsive Design: Desktop y móvil",
    ]

    for caracteristica in caracteristicas:
        story.append(Paragraph(f"• {caracteristica}", body_style))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Stack Tecnológico", h2_style))
    stack_resumen = [
        ["Componente", "Tecnología"],
        ["Backend", "Flask 2.3.3 (Python)"],
        ["Base de Datos", "PostgreSQL (Supabase)"],
        ["IA", "Anthropic Claude 3.5 Sonnet"],
        ["Email", "Resend API"],
        ["Frontend", "HTML5, Jinja2, CSS3, JavaScript vanilla"],
        ["Reportes", "ReportLab, openpyxl, pandas"],
    ]

    t22 = Table(stack_resumen, colWidths=[6*cm, 10*cm])
    t22.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(t22)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Métricas del Proyecto", h2_style))
    metricas = [
        ["Métrica", "Valor"],
        ["Rutas Flask", "115 rutas"],
        ["Módulos Principales", "8 módulos"],
        ["Tablas de Base de Datos", "15+ tablas relacionales"],
        ["Templates Frontend", "45+ templates HTML"],
        ["Líneas de Código (app.py)", "8,567 líneas"],
        ["Migraciones SQL", "14 migraciones"],
    ]

    t23 = Table(metricas, colWidths=[8*cm, 8*cm])
    t23.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(t23)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Puntos Fuertes de la Arquitectura", h2_style))
    puntos_fuertes = [
        "Separación clara entre módulos (CRM, Inspecciones, Cartera, IA)",
        "Sistema de permisos granular por perfil",
        "Análisis predictivo con IA para mantenimiento preventivo",
        "Alertas automáticas basadas en patrones detectados",
        "Trazabilidad completa de estados y transiciones",
        "Exportación flexible a múltiples formatos (PDF, Excel)",
        "API REST bien estructurada con Supabase",
        "Frontend responsive sin dependencias pesadas",
    ]

    for punto in puntos_fuertes:
        story.append(Paragraph(f"• {punto}", body_style))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Oportunidades de Adaptación a Otros Sectores", h2_style))
    story.append(Paragraph(
        "La arquitectura modular y flexible de AscensorAlert permite su adaptación "
        "a múltiples sectores industriales:",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    oportunidades = [
        "El sistema de alertas automáticas es agnóstico al dominio",
        "El motor de IA puede adaptarse a cualquier tipo de mantenimiento industrial",
        "La estructura CRM es genérica (leads → oportunidades → clientes)",
        "El sistema de inspecciones puede aplicarse a cualquier activo regulado",
        "Los detectores de patrones pueden configurarse para cualquier industria",
        "El análisis predictivo funciona con cualquier historial de intervenciones",
        "El sistema de roles y permisos es reutilizable en cualquier contexto",
        "La integración con IA permite análisis técnico en cualquier sector",
    ]

    for oportunidad in oportunidades:
        story.append(Paragraph(f"• {oportunidad}", body_style))

    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("Sectores Objetivo Potenciales", h2_style))
    sectores = [
        ["Sector", "Aplicabilidad"],
        ["HVAC (Climatización)", "Mantenimiento de equipos de aire acondicionado y calefacción"],
        ["Equipos Médicos", "Gestión de mantenimiento hospitalario y calibraciones"],
        ["Vehículos de Flota", "Mantenimiento preventivo de flotas de transporte"],
        ["Maquinaria Industrial", "Gestión de equipos de producción y manufactura"],
        ["Energía Renovable", "Mantenimiento de paneles solares, aerogeneradores"],
        ["Instalaciones Hoteleras", "Gestión de equipos de hostelería (cocinas, lavanderías)"],
        ["Edificios Inteligentes", "Mantenimiento integral de sistemas smart building"],
        ["Infraestructura Pública", "Gestión de activos municipales (semáforos, alumbrado)"],
    ]

    t24 = Table(sectores, colWidths=[5*cm, 11*cm])
    t24.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t24)

    story.append(PageBreak())

    # Página final
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("FIN DEL DOCUMENTO", h1_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Para más información sobre el proyecto, consulte los archivos de código fuente "
        "y documentación técnica en el repositorio.",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Documento generado automáticamente el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}",
        body_style
    ))

    # Construir el PDF
    doc.build(story)
    print(f"✅ PDF generado exitosamente: {filename}")
    return filename

if __name__ == "__main__":
    generar_documentacion_pdf()
