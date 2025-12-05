#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar SOLO partes de 2025
Ultra-optimizado: Mínimo coste, máximo valor predictivo
"""

import sys
import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analizador_ia

load_dotenv()

def analizar_solo_2025(solo_averias=True):
    """
    Analiza solo partes de 2025 (año en curso)

    Args:
        solo_averias: Si True, solo analiza averías. Si False, analiza todo.
    """

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL no configurada en .env")
        return

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Query base
    query = """
        SELECT p.id, p.numero_parte, p.tipo_parte_original,
               p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
               p.resolucion, p.maquina_id
        FROM partes_trabajo p
        LEFT JOIN analisis_partes_ia a ON p.id = a.parte_id
        WHERE a.id IS NULL
          AND p.resolucion IS NOT NULL
          AND p.resolucion != ''
          AND EXTRACT(YEAR FROM p.fecha_parte) = 2025
    """

    if solo_averias:
        query += """
          AND p.tipo_parte_normalizado IN (
              'AVERIA',
              'GUARDIA AVISO',
              'RESOL. AVERIAS',
              'REPARACION',
              'RESCATE'
          )
        """

    query += " ORDER BY p.fecha_parte DESC"

    cursor.execute(query)
    partes = cursor.fetchall()

    tipo_analisis = "SOLO AVERÍAS" if solo_averias else "TODOS LOS TIPOS"
    coste_estimado = len(partes) * 0.003
    tiempo_estimado = len(partes) * 2 / 60

    print(f"\n{'='*80}")
    print(f"🎯 ANÁLISIS 2025 - {tipo_analisis}")
    print(f"{'='*80}")
    print(f"📅 Año: 2025")
    print(f"📊 Partes encontrados: {len(partes)}")
    print(f"💰 Coste estimado: ${coste_estimado:.2f} (~{coste_estimado:.2f}€)")
    print(f"⏱️  Tiempo estimado: ~{tiempo_estimado:.0f} minutos")
    print(f"{'='*80}\n")

    if not partes:
        print("✅ No hay partes de 2025 pendientes de analizar")
        conn.close()
        return

    # Mostrar distribución por tipo
    from collections import Counter
    tipos = Counter([p[3] for p in partes])
    print("Distribución por tipo:")
    for tipo, count in tipos.most_common():
        print(f"  • {tipo}: {count}")
    print()

    respuesta = input(f"¿Continuar con el análisis? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Cancelado")
        conn.close()
        return

    print(f"\n🚀 Iniciando análisis...\n")

    # Procesar
    exitosos = 0
    errores = 0

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

        print(f"[{idx}/{len(partes)}] #{parte['numero_parte']} ({parte['tipo_parte_normalizado']}) - {parte['fecha_parte'].strftime('%Y-%m-%d')}...")

        resultado = analizador_ia.analizar_parte_con_ia(parte, conn)

        if resultado:
            exitosos += 1
        else:
            errores += 1
            print(f"  ⚠️  Error en este parte")

        # Pausa cada 50 para rate limits
        if idx % 50 == 0:
            print(f"\n⏸️  Pausa de 3 segundos (rate limit)...\n")
            import time
            time.sleep(3)

    conn.close()

    print(f"\n{'='*80}")
    print(f"✅ ANÁLISIS 2025 COMPLETADO")
    print(f"{'='*80}")
    print(f"✓ Exitosos: {exitosos}")
    print(f"✗ Errores: {errores}")
    print(f"💰 Coste real: ${exitosos * 0.003:.2f}")
    print(f"{'='*80}\n")

    if exitosos > 0:
        print("📋 PRÓXIMOS PASOS:")
        print("1. Generar predicciones para las máquinas:")
        print("   python scripts/test_ia_predictiva.py --predicciones-todas")
        print()
        print("2. Ver el dashboard:")
        print("   http://localhost:5000/cartera/ia")
        print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analizar solo partes de 2025')
    parser.add_argument('--todo', action='store_true',
                       help='Analizar TODO 2025 (no solo averías)')

    args = parser.parse_args()

    solo_averias = not args.todo

    analizar_solo_2025(solo_averias=solo_averias)
