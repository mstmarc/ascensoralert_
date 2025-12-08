#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple para ejecutar análisis desde la web
Ejecutar: python scripts/ejecutar_analisis_web.py
"""

import os
import sys

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
import threading

app = Flask(__name__)

# Variable global para tracking
estado_analisis = {
    'en_progreso': False,
    'completado': 0,
    'total': 0,
    'errores': 0,
    'mensajes': []
}

def ejecutar_analisis_background():
    """Ejecuta el análisis en background"""
    import psycopg2
    import analizador_ia
    from datetime import datetime

    global estado_analisis

    try:
        # Obtener DATABASE_URL del entorno
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            estado_analisis['mensajes'].append("ERROR: DATABASE_URL no configurada")
            estado_analisis['en_progreso'] = False
            return

        # Conectar a BD
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Obtener partes de 2025 sin analizar
        cursor.execute("""
            SELECT p.id, p.numero_parte, p.tipo_parte_original,
                   p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
                   p.resolucion, p.maquina_id
            FROM partes_trabajo p
            LEFT JOIN analisis_partes_ia a ON p.id = a.parte_id
            WHERE a.id IS NULL
              AND p.resolucion IS NOT NULL
              AND p.resolucion != ''
              AND EXTRACT(YEAR FROM p.fecha_parte) = 2025
              AND p.tipo_parte_normalizado IN (
                  'AVERIA', 'GUARDIA AVISO', 'RESOL. AVERIAS', 'REPARACION', 'RESCATE'
              )
            ORDER BY p.fecha_parte DESC
        """)

        partes = cursor.fetchall()
        estado_analisis['total'] = len(partes)
        estado_analisis['mensajes'].append(f"Encontrados {len(partes)} partes de 2025 para analizar")

        # Procesar cada parte
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

            try:
                resultado = analizador_ia.analizar_parte_con_ia(parte, conn)

                if resultado:
                    estado_analisis['completado'] += 1
                    estado_analisis['mensajes'].append(
                        f"[{idx}/{len(partes)}] ✅ Parte #{parte['numero_parte']} analizado"
                    )
                else:
                    estado_analisis['errores'] += 1
                    estado_analisis['mensajes'].append(
                        f"[{idx}/{len(partes)}] ❌ Error en parte #{parte['numero_parte']}"
                    )

            except Exception as e:
                estado_analisis['errores'] += 1
                estado_analisis['mensajes'].append(
                    f"[{idx}/{len(partes)}] ❌ Excepción: {str(e)}"
                )

        conn.close()

        estado_analisis['mensajes'].append(
            f"✅ COMPLETADO: {estado_analisis['completado']} exitosos, {estado_analisis['errores']} errores"
        )
        estado_analisis['en_progreso'] = False

    except Exception as e:
        estado_analisis['mensajes'].append(f"ERROR FATAL: {str(e)}")
        estado_analisis['en_progreso'] = False


@app.route('/analizar-2025')
def analizar_2025():
    """Inicia el análisis de partes de 2025"""
    global estado_analisis

    if estado_analisis['en_progreso']:
        return jsonify({
            'error': 'Ya hay un análisis en progreso',
            'estado': estado_analisis
        })

    # Verificar API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        return jsonify({
            'error': 'ANTHROPIC_API_KEY no configurada en las variables de entorno'
        }), 500

    # Resetear estado
    estado_analisis = {
        'en_progreso': True,
        'completado': 0,
        'total': 0,
        'errores': 0,
        'mensajes': ['🚀 Iniciando análisis...']
    }

    # Ejecutar en thread separado
    thread = threading.Thread(target=ejecutar_analisis_background)
    thread.daemon = True
    thread.start()

    return jsonify({
        'mensaje': 'Análisis iniciado. Consulta /estado para ver el progreso.',
        'estado': estado_analisis
    })


@app.route('/estado')
def ver_estado():
    """Ver el estado del análisis"""
    return jsonify(estado_analisis)


@app.route('/mensajes')
def ver_mensajes():
    """Ver los mensajes del análisis (HTML)"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Estado Análisis IA</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: monospace; padding: 20px; background: #1e1e1e; color: #00ff00; }
            .completado { color: #00ff00; }
            .error { color: #ff0000; }
            .info { color: #00ffff; }
            h1 { color: #ffffff; }
            .progreso { background: #333; padding: 10px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>📊 Estado del Análisis IA - 2025</h1>
        <div class="progreso">
            <p><strong>Estado:</strong> {estado}</p>
            <p><strong>Progreso:</strong> {completado} / {total}</p>
            <p><strong>Errores:</strong> {errores}</p>
        </div>
        <h2>Mensajes:</h2>
        <div style="background: #000; padding: 10px; border-radius: 5px; max-height: 500px; overflow-y: scroll;">
            {mensajes}
        </div>
        <p><em>Esta página se actualiza automáticamente cada 5 segundos</em></p>
    </body>
    </html>
    """.format(
        estado='🟢 En progreso' if estado_analisis['en_progreso'] else '✅ Completado',
        completado=estado_analisis['completado'],
        total=estado_analisis['total'],
        errores=estado_analisis['errores'],
        mensajes='<br>'.join(estado_analisis['mensajes'][-50:])  # Últimos 50 mensajes
    )

    return html


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"""
    ╔════════════════════════════════════════════════════════╗
    ║  SERVIDOR DE ANÁLISIS IA - 2025                        ║
    ╚════════════════════════════════════════════════════════╝

    Endpoints disponibles:

    1. Iniciar análisis:
       http://localhost:{port}/analizar-2025

    2. Ver estado (JSON):
       http://localhost:{port}/estado

    3. Ver mensajes (HTML):
       http://localhost:{port}/mensajes

    Presiona Ctrl+C para detener
    """)

    app.run(host='0.0.0.0', port=port, debug=False)
