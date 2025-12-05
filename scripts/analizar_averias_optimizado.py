#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script optimizado para analizar solo partes relevantes (AVERÍAS)
Ahorra ~65% de costes enfocándose en lo importante
"""

import sys
import os
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analizador_ia

load_dotenv()

def analizar_averias_optimizado(limite=None, meses_recientes=12):
    """
    Analiza solo partes de AVERÍA y tipos relacionados

    Args:
        limite: Máximo de partes a analizar (None = todos)
        meses_recientes: Solo últimos N meses (None = todos)
    """

    # Conectar a BD
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Query optimizada: SOLO averías relevantes
    query = """
        SELECT p.id, p.numero_parte, p.tipo_parte_original,
               p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
               p.resolucion, p.maquina_id
        FROM partes_trabajo p
        LEFT JOIN analisis_partes_ia a ON p.id = a.parte_id
        WHERE a.id IS NULL  -- Sin análisis previo
          AND p.resolucion IS NOT NULL
          AND p.resolucion != ''
          AND p.tipo_parte_normalizado IN (
              'AVERIA',
              'GUARDIA AVISO',
              'RESOL. AVERIAS',
              'REPARACION',
              'RESCATE'
          )
    """

    if meses_recientes:
        query += f" AND p.fecha_parte >= NOW() - INTERVAL '{meses_recientes} months'"

    query += " ORDER BY p.fecha_parte DESC"

    if limite:
        query += f" LIMIT {limite}"

    cursor.execute(query)
    partes = cursor.fetchall()

    print(f"\n{'='*80}")
    print(f"🎯 ANÁLISIS OPTIMIZADO: Solo Averías y Problemas Reales")
    print(f"{'='*80}")
    print(f"Partes a analizar: {len(partes)}")
    print(f"Coste estimado: ${len(partes) * 0.003:.2f}")
    print(f"Tiempo estimado: ~{len(partes) * 2 / 60:.0f} minutos")
    print(f"{'='*80}\n")

    if not partes:
        print("✅ No hay partes pendientes de analizar")
        return

    respuesta = input(f"¿Continuar con el análisis? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Cancelado")
        return

    # Procesar
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

        print(f"[{idx}/{len(partes)}] Analizando parte #{parte['numero_parte']} ({parte['tipo_parte_normalizado']})...")
        analizador_ia.analizar_parte_con_ia(parte, conn)

        # Pausa cada 50 para evitar rate limits
        if idx % 50 == 0:
            print(f"\n⏸️  Pausa de 5 segundos (rate limit)...\n")
            import time
            time.sleep(5)

    conn.close()

    print(f"\n{'='*80}")
    print(f"✅ Análisis completado: {len(partes)} partes procesados")
    print(f"💰 Coste aproximado: ${len(partes) * 0.003:.2f}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Análisis optimizado de averías')
    parser.add_argument('--limite', type=int, help='Límite de partes a analizar')
    parser.add_argument('--meses', type=int, default=12, help='Solo últimos N meses (default: 12)')
    parser.add_argument('--todos', action='store_true', help='Analizar todas las averías históricas')

    args = parser.parse_args()

    meses = None if args.todos else args.meses

    analizar_averias_optimizado(limite=args.limite, meses_recientes=meses)
