#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: Analizador de Ascensores con IA
===============================================================================
Descripción: Sistema de análisis predictivo que usa IA (Claude) para analizar
             partes de trabajo de ascensores y predecir futuras averías con
             conocimiento técnico especializado.

Capacidades:
    - Análisis semántico profundo de partes de trabajo
    - Predicción de averías futuras basada en patrones históricos
    - Generación de alertas predictivas inteligentes
    - Extracción de información técnica (componentes, causas, recomendaciones)
    - Aprendizaje continuo del sistema

Autor: AscensorAlert IA System
Fecha: 2025-12-04
===============================================================================
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from anthropic import Anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
MODELO_IA = "claude-3-5-sonnet-20241022"  # Modelo más reciente
MAX_TOKENS = 4096
TEMPERATURA = 0.3  # Baja temperatura para respuestas más técnicas y precisas

# Inicializar cliente de Anthropic
client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# ============================================================================
# PROMPTS ESPECIALIZADOS
# ============================================================================

PROMPT_ANALISIS_PARTE = """Eres un experto técnico en ascensores con más de 20 años de experiencia en mantenimiento, reparación y diagnóstico de averías. Tu especialidad es analizar partes de trabajo y extraer información técnica precisa.

Analiza el siguiente parte de trabajo de ascensor y extrae la siguiente información en formato JSON:

PARTE DE TRABAJO:
Número: {numero_parte}
Tipo: {tipo_parte}
Fecha: {fecha_parte}
Máquina: {maquina}
Descripción del trabajo: {resolucion}

Proporciona un análisis JSON con esta estructura exacta:
{{
  "componente_principal": "Nombre del componente principal afectado",
  "componentes_secundarios": ["Otros componentes relacionados"],
  "tipo_fallo": "Clasificación técnica del fallo (desgaste, ruptura, desajuste, obstrucción, etc.)",
  "causa_raiz": "Explicación técnica de la causa raíz del problema",
  "gravedad_tecnica": "LEVE|MODERADA|GRAVE|CRITICA",
  "es_fallo_recurrente": true/false,
  "indicadores_deterioro": ["Señales de desgaste o deterioro identificadas"],
  "probabilidad_recurrencia": 0-100,
  "tiempo_estimado_proxima_falla": días estimados hasta próxima falla (null si no aplica),
  "recomendacion_ia": "Recomendación técnica detallada",
  "acciones_preventivas": ["Lista de acciones preventivas sugeridas"],
  "urgencia_ia": "BAJA|MEDIA|ALTA|URGENTE",
  "coste_estimado_preventivo": valor numérico en euros,
  "coste_estimado_correctivo": valor numérico en euros,
  "contexto_tecnico": "Análisis contextual completo del problema",
  "confianza_analisis": 0-100
}}

IMPORTANTE:
- Sé preciso y técnico en tu análisis
- Usa nomenclatura técnica estándar de ascensores
- Si no hay suficiente información para algún campo, usa null
- La probabilidad_recurrencia debe reflejar la probabilidad real de que vuelva a ocurrir
- Los costes deben ser realistas según estándares del sector
- La confianza_analisis refleja cuán seguro estás del análisis (baja si la descripción es vaga)

Responde SOLO con el JSON, sin explicaciones adicionales."""

PROMPT_PREDICCION_MAQUINA = """Eres un experto en mantenimiento predictivo de ascensores. Analiza el historial completo de una máquina y genera una predicción sobre su estado de salud y posibles averías futuras.

DATOS DE LA MÁQUINA:
Identificador: {maquina}
Instalación: {instalacion}

HISTORIAL DE PARTES (últimos {dias_historico} días):
{historial_partes}

ANÁLISIS PREVIOS CON IA:
{analisis_previos}

ESTADÍSTICAS:
- Total de partes: {total_partes}
- Averías: {total_averias}
- Conservaciones: {total_conservaciones}
- Días desde última avería: {dias_sin_averias}
- Componentes con problemas recurrentes: {componentes_recurrentes}

Genera una predicción detallada en formato JSON:
{{
  "estado_salud_ia": "EXCELENTE|BUENA|REGULAR|MALA|CRITICA",
  "puntuacion_salud": 0-100,
  "tendencia": "MEJORANDO|ESTABLE|DETERIORANDO|CRITICA",
  "componente_riesgo_1": "Componente con mayor riesgo",
  "probabilidad_fallo_1": 0-100,
  "dias_estimados_fallo_1": días estimados,
  "componente_riesgo_2": "Segundo componente en riesgo",
  "probabilidad_fallo_2": 0-100,
  "dias_estimados_fallo_2": días estimados,
  "componente_riesgo_3": "Tercer componente en riesgo",
  "probabilidad_fallo_3": 0-100,
  "dias_estimados_fallo_3": días estimados,
  "patron_detectado": "Descripción del patrón (ej: DESGASTE_PROGRESIVO)",
  "descripcion_patron": "Explicación detallada del patrón detectado",
  "componentes_criticos": ["Lista de componentes que necesitan atención"],
  "proxima_intervencion_sugerida": "YYYY-MM-DD",
  "tipo_intervencion_sugerida": "Descripción de la intervención",
  "prioridad_intervencion": "BAJA|MEDIA|ALTA|URGENTE",
  "coste_mantenimiento_preventivo": valor en euros,
  "coste_estimado_si_no_actua": valor en euros si no se interviene,
  "ahorro_potencial": diferencia entre correctivo y preventivo,
  "roi_intervencion": ROI porcentual,
  "factores_riesgo": ["Lista de factores de riesgo identificados"],
  "justificacion_prediccion": "Explicación técnica detallada de por qué esta predicción",
  "confianza_prediccion": 0-100
}}

Sé preciso, usa datos históricos reales y genera predicciones técnicamente fundamentadas.
Responde SOLO con el JSON, sin explicaciones adicionales."""

PROMPT_DETECTAR_ALERTAS = """Eres un sistema de alerta temprana para ascensores. Analiza la predicción de una máquina y los análisis recientes para determinar si se deben generar alertas predictivas.

PREDICCIÓN ACTUAL:
{prediccion}

ANÁLISIS RECIENTES:
{analisis_recientes}

DATOS CONTEXTUALES:
{datos_contexto}

Genera alertas SOLO si hay riesgos reales que requieran atención. Responde en formato JSON:
{{
  "alertas": [
    {{
      "tipo_alerta": "FALLO_INMINENTE|DETERIORO_PROGRESIVO|PATRON_ANOMALO|MANTENIMIENTO_URGENTE",
      "nivel_urgencia": "BAJA|MEDIA|ALTA|URGENTE|CRITICA",
      "titulo": "Título breve de la alerta",
      "descripcion": "Descripción técnica detallada",
      "componente_afectado": "Componente",
      "probabilidad_fallo": 0-100,
      "dias_estimados_fallo": días,
      "impacto_estimado": "BAJO|MEDIO|ALTO|CRITICO",
      "accion_recomendada": "Acción específica a tomar",
      "fecha_limite_accion": "YYYY-MM-DD",
      "alternativas": ["Alternativas de acción"],
      "coste_intervencion": valor en euros,
      "coste_si_no_actua": valor en euros,
      "ahorro_estimado": diferencia,
      "confianza": 0-100,
      "explicacion_ia": "Por qué se genera esta alerta"
    }}
  ]
}}

Si NO hay alertas necesarias, devuelve {{"alertas": []}}.
Sé conservador: solo genera alertas cuando haya riesgos reales.
Responde SOLO con el JSON."""

# ============================================================================
# FUNCIÓN PRINCIPAL: Analizar Parte de Trabajo
# ============================================================================

def analizar_parte_con_ia(parte: Dict[str, Any], conn) -> Optional[int]:
    """
    Analiza un parte de trabajo usando IA y guarda el resultado en la BD.

    Args:
        parte: Diccionario con datos del parte (id, numero_parte, tipo_parte, etc.)
        conn: Conexión a la base de datos

    Returns:
        ID del análisis creado o None si falla
    """
    if not client:
        print("⚠️  Cliente de Anthropic no inicializado. Configura ANTHROPIC_API_KEY en .env")
        return None

    try:
        # Preparar prompt
        prompt = PROMPT_ANALISIS_PARTE.format(
            numero_parte=parte.get('numero_parte', 'N/A'),
            tipo_parte=parte.get('tipo_parte_normalizado', parte.get('tipo_parte_original', 'N/A')),
            fecha_parte=parte.get('fecha_parte', 'N/A'),
            maquina=parte.get('maquina_texto', 'N/A'),
            resolucion=parte.get('resolucion', '')
        )

        # Medir tiempo de procesamiento
        tiempo_inicio = time.time()

        # Llamar a la API de Claude
        print(f"🤖 Analizando parte #{parte.get('numero_parte')} con IA...")
        response = client.messages.create(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURA,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        tiempo_procesamiento = int((time.time() - tiempo_inicio) * 1000)  # en ms

        # Extraer contenido de respuesta
        contenido = response.content[0].text

        # Parsear JSON
        try:
            analisis = json.loads(contenido)
        except json.JSONDecodeError:
            # Intentar extraer JSON si hay texto extra
            import re
            json_match = re.search(r'\{.*\}', contenido, re.DOTALL)
            if json_match:
                analisis = json.loads(json_match.group())
            else:
                print(f"❌ Error parseando JSON del análisis: {contenido[:200]}")
                return None

        # Guardar en base de datos
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analisis_partes_ia (
                parte_id, componente_principal, componentes_secundarios,
                tipo_fallo, causa_raiz, gravedad_tecnica,
                es_fallo_recurrente, indicadores_deterioro,
                probabilidad_recurrencia, tiempo_estimado_proxima_falla,
                recomendacion_ia, acciones_preventivas, urgencia_ia,
                coste_estimado_preventivo, coste_estimado_correctivo,
                contexto_tecnico, modelo_ia_usado, confianza_analisis,
                tiempo_procesamiento_ms
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            parte['id'],
            analisis.get('componente_principal'),
            analisis.get('componentes_secundarios', []),
            analisis.get('tipo_fallo'),
            analisis.get('causa_raiz'),
            analisis.get('gravedad_tecnica'),
            analisis.get('es_fallo_recurrente', False),
            analisis.get('indicadores_deterioro', []),
            analisis.get('probabilidad_recurrencia'),
            analisis.get('tiempo_estimado_proxima_falla'),
            analisis.get('recomendacion_ia'),
            analisis.get('acciones_preventivas', []),
            analisis.get('urgencia_ia'),
            analisis.get('coste_estimado_preventivo'),
            analisis.get('coste_estimado_correctivo'),
            analisis.get('contexto_tecnico'),
            MODELO_IA,
            analisis.get('confianza_analisis'),
            tiempo_procesamiento
        ))

        analisis_id = cursor.fetchone()[0]
        conn.commit()

        print(f"✅ Análisis completado: Componente={analisis.get('componente_principal')}, "
              f"Gravedad={analisis.get('gravedad_tecnica')}, "
              f"Confianza={analisis.get('confianza_analisis')}%")

        # Actualizar estadísticas de conocimiento técnico
        if analisis.get('componente_principal'):
            actualizar_estadisticas_componente(analisis.get('componente_principal'), conn)

        return analisis_id

    except Exception as e:
        print(f"❌ Error analizando parte: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# FUNCIÓN: Generar Predicción de Máquina
# ============================================================================

def generar_prediccion_maquina(maquina_id: int, conn, dias_historico: int = 180) -> Optional[int]:
    """
    Genera una predicción del estado de salud y averías futuras de una máquina.

    Args:
        maquina_id: ID de la máquina en maquinas_cartera
        conn: Conexión a la base de datos
        dias_historico: Días de histórico a analizar (default: 180)

    Returns:
        ID de la predicción creada o None si falla
    """
    if not client:
        print("⚠️  Cliente de Anthropic no inicializado")
        return None

    try:
        cursor = conn.cursor()

        # Obtener información de la máquina
        cursor.execute("""
            SELECT m.id, m.identificador, i.nombre as instalacion
            FROM maquinas_cartera m
            LEFT JOIN instalaciones i ON m.instalacion_id = i.id
            WHERE m.id = %s
        """, (maquina_id,))

        maquina = cursor.fetchone()
        if not maquina:
            print(f"❌ Máquina {maquina_id} no encontrada")
            return None

        maquina_dict = {
            'id': maquina[0],
            'identificador': maquina[1],
            'instalacion': maquina[2] or 'Sin instalación'
        }

        # Obtener historial de partes
        fecha_limite = datetime.now() - timedelta(days=dias_historico)
        cursor.execute("""
            SELECT numero_parte, tipo_parte_normalizado, fecha_parte, resolucion,
                   coste_total
            FROM partes_trabajo
            WHERE maquina_id = %s AND fecha_parte >= %s
            ORDER BY fecha_parte DESC
        """, (maquina_id, fecha_limite))

        partes = cursor.fetchall()
        historial_texto = "\n".join([
            f"- [{p[1]}] {p[2].strftime('%Y-%m-%d')}: {p[3][:200]}"
            for p in partes[:50]  # Últimos 50 partes
        ])

        # Obtener análisis previos con IA
        cursor.execute("""
            SELECT a.componente_principal, a.gravedad_tecnica, a.probabilidad_recurrencia,
                   a.recomendacion_ia, p.fecha_parte
            FROM analisis_partes_ia a
            JOIN partes_trabajo p ON a.parte_id = p.id
            WHERE p.maquina_id = %s AND p.fecha_parte >= %s
            ORDER BY p.fecha_parte DESC
            LIMIT 20
        """, (maquina_id, fecha_limite))

        analisis = cursor.fetchall()
        analisis_texto = "\n".join([
            f"- {a[4].strftime('%Y-%m-%d')}: {a[0]} ({a[1]}) - Prob. recurrencia: {a[2]}%"
            for a in analisis
        ])

        # Calcular estadísticas
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE tipo_parte_normalizado = 'AVERIA') as averias,
                COUNT(*) FILTER (WHERE tipo_parte_normalizado = 'MANTENIMIENTO') as conservaciones,
                COALESCE(EXTRACT(DAY FROM NOW() - MAX(fecha_parte) FILTER (WHERE tipo_parte_normalizado = 'AVERIA')), 999) as dias_sin_averias
            FROM partes_trabajo
            WHERE maquina_id = %s AND fecha_parte >= %s
        """, (maquina_id, fecha_limite))

        stats = cursor.fetchone()

        # Componentes recurrentes
        cursor.execute("""
            SELECT componente_principal, COUNT(*) as veces
            FROM analisis_partes_ia a
            JOIN partes_trabajo p ON a.parte_id = p.id
            WHERE p.maquina_id = %s AND a.es_fallo_recurrente = TRUE
            GROUP BY componente_principal
            ORDER BY veces DESC
            LIMIT 5
        """, (maquina_id,))

        componentes_rec = cursor.fetchall()
        componentes_rec_texto = ", ".join([f"{c[0]} ({c[1]}x)" for c in componentes_rec]) or "Ninguno"

        # Preparar prompt
        prompt = PROMPT_PREDICCION_MAQUINA.format(
            maquina=maquina_dict['identificador'],
            instalacion=maquina_dict['instalacion'],
            dias_historico=dias_historico,
            historial_partes=historial_texto or "Sin historial reciente",
            analisis_previos=analisis_texto or "Sin análisis previos",
            total_partes=stats[0],
            total_averias=stats[1],
            total_conservaciones=stats[2],
            dias_sin_averias=int(stats[3]),
            componentes_recurrentes=componentes_rec_texto
        )

        # Llamar a IA
        print(f"🔮 Generando predicción para máquina {maquina_dict['identificador']}...")
        tiempo_inicio = time.time()

        response = client.messages.create(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURA,
            messages=[{"role": "user", "content": prompt}]
        )

        tiempo_procesamiento = int((time.time() - tiempo_inicio) * 1000)

        # Parsear respuesta
        contenido = response.content[0].text
        try:
            prediccion = json.loads(contenido)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', contenido, re.DOTALL)
            if json_match:
                prediccion = json.loads(json_match.group())
            else:
                print(f"❌ Error parseando predicción")
                return None

        # Invalidar predicciones antiguas
        cursor.execute("""
            UPDATE predicciones_maquina
            SET estado = 'VENCIDA'
            WHERE maquina_id = %s AND estado = 'ACTIVA'
        """, (maquina_id,))

        # Guardar nueva predicción
        cursor.execute("""
            INSERT INTO predicciones_maquina (
                maquina_id, estado_salud_ia, puntuacion_salud, tendencia,
                componente_riesgo_1, probabilidad_fallo_1, dias_estimados_fallo_1,
                componente_riesgo_2, probabilidad_fallo_2, dias_estimados_fallo_2,
                componente_riesgo_3, probabilidad_fallo_3, dias_estimados_fallo_3,
                patron_detectado, descripcion_patron, componentes_criticos,
                proxima_intervencion_sugerida, tipo_intervencion_sugerida,
                prioridad_intervencion, coste_mantenimiento_preventivo,
                coste_estimado_si_no_actua, ahorro_potencial, roi_intervencion,
                partes_analizados, periodo_analisis_dias, dias_sin_averias,
                factores_riesgo, justificacion_prediccion, modelo_ia_usado,
                confianza_prediccion, valida_hasta, estado
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            maquina_id,
            prediccion.get('estado_salud_ia'),
            prediccion.get('puntuacion_salud'),
            prediccion.get('tendencia'),
            prediccion.get('componente_riesgo_1'),
            prediccion.get('probabilidad_fallo_1'),
            prediccion.get('dias_estimados_fallo_1'),
            prediccion.get('componente_riesgo_2'),
            prediccion.get('probabilidad_fallo_2'),
            prediccion.get('dias_estimado s_fallo_2'),
            prediccion.get('componente_riesgo_3'),
            prediccion.get('probabilidad_fallo_3'),
            prediccion.get('dias_estimados_fallo_3'),
            prediccion.get('patron_detectado'),
            prediccion.get('descripcion_patron'),
            prediccion.get('componentes_criticos', []),
            prediccion.get('proxima_intervencion_sugerida'),
            prediccion.get('tipo_intervencion_sugerida'),
            prediccion.get('prioridad_intervencion'),
            prediccion.get('coste_mantenimiento_preventivo'),
            prediccion.get('coste_estimado_si_no_actua'),
            prediccion.get('ahorro_potencial'),
            prediccion.get('roi_intervencion'),
            stats[0],  # partes_analizados
            dias_historico,
            int(stats[3]),  # dias_sin_averias
            prediccion.get('factores_riesgo', []),
            prediccion.get('justificacion_prediccion'),
            MODELO_IA,
            prediccion.get('confianza_prediccion'),
            datetime.now() + timedelta(days=30),  # válida 30 días
            'ACTIVA'
        ))

        prediccion_id = cursor.fetchone()[0]
        conn.commit()

        print(f"✅ Predicción generada: Estado={prediccion.get('estado_salud_ia')}, "
              f"Salud={prediccion.get('puntuacion_salud')}/100, "
              f"Tendencia={prediccion.get('tendencia')}")

        return prediccion_id

    except Exception as e:
        print(f"❌ Error generando predicción: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# FUNCIÓN: Generar Alertas Predictivas
# ============================================================================

def generar_alertas_predictivas(prediccion_id: int, conn) -> int:
    """
    Genera alertas predictivas basadas en una predicción de máquina.

    Args:
        prediccion_id: ID de la predicción
        conn: Conexión a la base de datos

    Returns:
        Número de alertas generadas
    """
    if not client:
        return 0

    try:
        cursor = conn.cursor()

        # Obtener predicción
        cursor.execute("""
            SELECT p.*, m.identificador as maquina, i.nombre as instalacion
            FROM predicciones_maquina p
            JOIN maquinas_cartera m ON p.maquina_id = m.id
            LEFT JOIN instalaciones i ON m.instalacion_id = i.id
            WHERE p.id = %s
        """, (prediccion_id,))

        pred = cursor.fetchone()
        if not pred:
            return 0

        # Convertir a dict (asumiendo columnas conocidas)
        cols = [desc[0] for desc in cursor.description]
        prediccion = dict(zip(cols, pred))

        # Obtener análisis recientes
        cursor.execute("""
            SELECT a.componente_principal, a.gravedad_tecnica, a.urgencia_ia,
                   a.probabilidad_recurrencia, p.fecha_parte
            FROM analisis_partes_ia a
            JOIN partes_trabajo p ON a.parte_id = p.id
            WHERE p.maquina_id = %s
            ORDER BY p.fecha_parte DESC
            LIMIT 10
        """, (prediccion['maquina_id'],))

        analisis_recientes = cursor.fetchall()
        analisis_texto = json.dumps([
            {
                'componente': a[0],
                'gravedad': a[1],
                'urgencia': a[2],
                'prob_recurrencia': float(a[3]) if a[3] else 0,
                'fecha': a[4].strftime('%Y-%m-%d')
            }
            for a in analisis_recientes
        ], indent=2)

        # Preparar datos contextuales
        datos_contexto = {
            'maquina': prediccion['maquina'],
            'instalacion': prediccion['instalacion'],
            'dias_sin_averias': prediccion['dias_sin_averias'],
            'partes_analizados': prediccion['partes_analizados']
        }

        # Preparar prompt
        prompt = PROMPT_DETECTAR_ALERTAS.format(
            prediccion=json.dumps({
                'estado_salud': prediccion['estado_salud_ia'],
                'puntuacion': prediccion['puntuacion_salud'],
                'tendencia': prediccion['tendencia'],
                'componente_riesgo_1': prediccion['componente_riesgo_1'],
                'probabilidad_fallo_1': float(prediccion['probabilidad_fallo_1']) if prediccion['probabilidad_fallo_1'] else 0,
                'dias_estimados_1': prediccion['dias_estimados_fallo_1'],
                'prioridad_intervencion': prediccion['prioridad_intervencion']
            }, indent=2),
            analisis_recientes=analisis_texto,
            datos_contexto=json.dumps(datos_contexto, indent=2)
        )

        # Llamar a IA
        print(f"🚨 Detectando alertas para predicción #{prediccion_id}...")
        response = client.messages.create(
            model=MODELO_IA,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURA,
            messages=[{"role": "user", "content": prompt}]
        )

        contenido = response.content[0].text
        try:
            resultado = json.loads(contenido)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', contenido, re.DOTALL)
            if json_match:
                resultado = json.loads(json_match.group())
            else:
                print("❌ Error parseando alertas")
                return 0

        alertas = resultado.get('alertas', [])
        alertas_creadas = 0

        # Guardar alertas
        for alerta in alertas:
            cursor.execute("""
                INSERT INTO alertas_predictivas_ia (
                    maquina_id, prediccion_id, tipo_alerta, nivel_urgencia,
                    titulo, descripcion, componente_afectado, probabilidad_fallo,
                    dias_estimados_fallo, impacto_estimado, accion_recomendada,
                    fecha_limite_accion, alternativas, coste_intervencion,
                    coste_si_no_actua, ahorro_estimado, modelo_ia_usado,
                    confianza, explicacion_ia, estado
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                prediccion['maquina_id'],
                prediccion_id,
                alerta.get('tipo_alerta'),
                alerta.get('nivel_urgencia'),
                alerta.get('titulo'),
                alerta.get('descripcion'),
                alerta.get('componente_afectado'),
                alerta.get('probabilidad_fallo'),
                alerta.get('dias_estimados_fallo'),
                alerta.get('impacto_estimado'),
                alerta.get('accion_recomendada'),
                alerta.get('fecha_limite_accion'),
                alerta.get('alternativas', []),
                alerta.get('coste_intervencion'),
                alerta.get('coste_si_no_actua'),
                alerta.get('ahorro_estimado'),
                MODELO_IA,
                alerta.get('confianza'),
                alerta.get('explicacion_ia'),
                'ACTIVA'
            ))

            alerta_id = cursor.fetchone()[0]
            alertas_creadas += 1
            print(f"  ⚠️  Alerta creada: {alerta.get('titulo')} ({alerta.get('nivel_urgencia')})")

        conn.commit()

        if alertas_creadas > 0:
            print(f"✅ {alertas_creadas} alerta(s) generada(s)")
        else:
            print("✅ No se detectaron alertas necesarias")

        return alertas_creadas

    except Exception as e:
        print(f"❌ Error generando alertas: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

# ============================================================================
# FUNCIÓN: Actualizar Estadísticas de Componente
# ============================================================================

def actualizar_estadisticas_componente(componente: str, conn):
    """
    Actualiza las estadísticas de un componente en conocimiento_tecnico_ia.

    Args:
        componente: Nombre del componente
        conn: Conexión a la base de datos
    """
    try:
        cursor = conn.cursor()

        # Verificar si existe el componente
        cursor.execute("""
            SELECT id FROM conocimiento_tecnico_ia WHERE componente = %s
        """, (componente,))

        existe = cursor.fetchone()

        # Calcular estadísticas
        cursor.execute("""
            SELECT
                COUNT(*) as veces,
                AVG(EXTRACT(EPOCH FROM (LEAD(p.fecha_parte) OVER (ORDER BY p.fecha_parte) - p.fecha_parte)) / 86400) as dias_entre_fallos,
                COUNT(*) FILTER (WHERE a.es_fallo_recurrente = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) * 100 as tasa_recurrencia
            FROM analisis_partes_ia a
            JOIN partes_trabajo p ON a.parte_id = p.id
            WHERE a.componente_principal = %s
        """, (componente,))

        stats = cursor.fetchone()

        if existe:
            # Actualizar
            cursor.execute("""
                UPDATE conocimiento_tecnico_ia
                SET veces_aparecido = %s,
                    promedio_dias_entre_fallos = %s,
                    tasa_recurrencia = %s,
                    updated_at = NOW()
                WHERE componente = %s
            """, (stats[0], stats[1], stats[2], componente))
        else:
            # Crear nuevo (si no está en los predefinidos)
            cursor.execute("""
                INSERT INTO conocimiento_tecnico_ia (
                    componente, veces_aparecido, promedio_dias_entre_fallos,
                    tasa_recurrencia, criticidad
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (componente) DO UPDATE
                SET veces_aparecido = EXCLUDED.veces_aparecido,
                    promedio_dias_entre_fallos = EXCLUDED.promedio_dias_entre_fallos,
                    tasa_recurrencia = EXCLUDED.tasa_recurrencia
            """, (componente, stats[0], stats[1], stats[2], 'MEDIA'))

        conn.commit()

    except Exception as e:
        print(f"⚠️  Error actualizando estadísticas de componente: {str(e)}")

# ============================================================================
# FUNCIÓN: Procesar Lote de Partes
# ============================================================================

def procesar_lote_partes(conn, limite: int = 100, solo_sin_analizar: bool = True):
    """
    Procesa un lote de partes de trabajo con IA.

    Args:
        conn: Conexión a la base de datos
        limite: Número máximo de partes a procesar
        solo_sin_analizar: Si True, solo procesa partes sin análisis IA previo
    """
    try:
        cursor = conn.cursor()

        # Obtener partes sin analizar
        if solo_sin_analizar:
            query = """
                SELECT p.id, p.numero_parte, p.tipo_parte_original,
                       p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
                       p.resolucion, p.maquina_id
                FROM partes_trabajo p
                LEFT JOIN analisis_partes_ia a ON p.id = a.parte_id
                WHERE a.id IS NULL AND p.resolucion IS NOT NULL AND p.resolucion != ''
                ORDER BY p.fecha_parte DESC
                LIMIT %s
            """
        else:
            query = """
                SELECT p.id, p.numero_parte, p.tipo_parte_original,
                       p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
                       p.resolucion, p.maquina_id
                FROM partes_trabajo p
                WHERE p.resolucion IS NOT NULL AND p.resolucion != ''
                ORDER BY p.fecha_parte DESC
                LIMIT %s
            """

        cursor.execute(query, (limite,))
        partes = cursor.fetchall()

        print(f"\n{'='*80}")
        print(f"🚀 Procesando {len(partes)} partes con IA...")
        print(f"{'='*80}\n")

        for idx, parte_tuple in enumerate(partes, 1):
            parte = {
                'id': parte_tuple[0],
                'numero_parte': parte_tuple[1],
                'tipo_parte_original': parte_tuple[2],
                'tipo_parte_normalizado': parte_tuple[3],
                'fecha_parte': parte_tuple[4],
                'maquina_texto': parte_tuple[5],
                'resolucion': parte_tuple[6],
                'maquina_id': parte_tuple[7]
            }

            print(f"[{idx}/{len(partes)}] Procesando parte #{parte['numero_parte']}...")
            analizar_parte_con_ia(parte, conn)
            print()

        print(f"{'='*80}")
        print(f"✅ Procesamiento completado: {len(partes)} partes analizados")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌ Error en procesamiento por lotes: {str(e)}")
        import traceback
        traceback.print_exc()

# ============================================================================
# FUNCIÓN: Generar Predicciones para Todas las Máquinas
# ============================================================================

def generar_predicciones_todas_maquinas(conn, limite: int = None):
    """
    Genera predicciones para todas las máquinas en cartera (o un límite).

    Args:
        conn: Conexión a la base de datos
        limite: Número máximo de máquinas a procesar (None = todas)
    """
    try:
        cursor = conn.cursor()

        # Obtener máquinas en cartera
        query = """
            SELECT id, identificador
            FROM maquinas_cartera
            WHERE en_cartera = TRUE
            ORDER BY id
        """

        if limite:
            query += f" LIMIT {limite}"

        cursor.execute(query)
        maquinas = cursor.fetchall()

        print(f"\n{'='*80}")
        print(f"🔮 Generando predicciones para {len(maquinas)} máquinas...")
        print(f"{'='*80}\n")

        predicciones_generadas = 0
        alertas_generadas = 0

        for idx, (maquina_id, identificador) in enumerate(maquinas, 1):
            print(f"[{idx}/{len(maquinas)}] Máquina: {identificador}")

            prediccion_id = generar_prediccion_maquina(maquina_id, conn)

            if prediccion_id:
                predicciones_generadas += 1

                # Generar alertas para esta predicción
                alertas = generar_alertas_predictivas(prediccion_id, conn)
                alertas_generadas += alertas

            print()

        print(f"{'='*80}")
        print(f"✅ Predicciones generadas: {predicciones_generadas}")
        print(f"✅ Alertas generadas: {alertas_generadas}")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌ Error generando predicciones masivas: {str(e)}")
        import traceback
        traceback.print_exc()

# ============================================================================
# MAIN: Ejemplo de uso
# ============================================================================

if __name__ == "__main__":
    import psycopg2
    from psycopg2.extras import RealDictCursor

    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║       SISTEMA DE ANÁLISIS PREDICTIVO CON IA - ASCENSORES      ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    # Ejemplo de uso (requiere configurar conexión a BD)
    print("Para usar este módulo:")
    print("1. Configura ANTHROPIC_API_KEY en tu archivo .env")
    print("2. Importa las funciones desde app.py o crea un script personalizado")
    print("\nFunciones disponibles:")
    print("  - analizar_parte_con_ia(parte, conn)")
    print("  - generar_prediccion_maquina(maquina_id, conn)")
    print("  - generar_alertas_predictivas(prediccion_id, conn)")
    print("  - procesar_lote_partes(conn, limite=100)")
    print("  - generar_predicciones_todas_maquinas(conn, limite=None)")
