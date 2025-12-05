#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SCRIPT: Test del Sistema de IA Predictiva
===============================================================================
Descripción: Script para probar el sistema de análisis predictivo con IA.
             Permite analizar partes y generar predicciones de ejemplo.

Uso:
    python scripts/test_ia_predictiva.py [opciones]

Opciones:
    --analizar-partes N     Analizar N partes recientes (default: 10)
    --generar-prediccion ID Generar predicción para máquina específica
    --analizar-todo        Analizar todos los partes sin análisis
    --predicciones-todas   Generar predicciones para todas las máquinas

Requisitos:
    - ANTHROPIC_API_KEY configurada en .env
    - Credenciales de PostgreSQL (DATABASE_URL o variables individuales)

===============================================================================
"""

import sys
import os
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analizador_ia

# Cargar variables de entorno
load_dotenv()

def conectar_bd():
    """Conectar a la base de datos PostgreSQL"""
    # Intentar con DATABASE_URL primero
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        print(f"✓ Conectando con DATABASE_URL...")
        conn = psycopg2.connect(database_url)
    else:
        # Usar variables individuales
        print(f"✓ Conectando con variables individuales...")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'ascensoralert'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

    print("✅ Conexión a base de datos establecida")
    return conn

def verificar_schema(conn):
    """Verificar que las tablas de IA existan"""
    cursor = conn.cursor()

    tablas_requeridas = [
        'analisis_partes_ia',
        'predicciones_maquina',
        'alertas_predictivas_ia',
        'conocimiento_tecnico_ia'
    ]

    print("\n📋 Verificando schema de IA predictiva...")

    for tabla in tablas_requeridas:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            )
        """, (tabla,))

        existe = cursor.fetchone()[0]

        if existe:
            print(f"  ✓ Tabla {tabla} existe")
        else:
            print(f"  ✗ Tabla {tabla} NO existe")
            print(f"\n⚠️  ERROR: Falta ejecutar el schema de IA predictiva")
            print(f"    Ejecuta: psql -d <database> -f database/ia_predictiva_schema.sql")
            return False

    print("✅ Schema verificado correctamente\n")
    return True

def analizar_partes_test(conn, limite=10):
    """Analizar partes de prueba"""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: Análisis de {limite} partes con IA")
    print(f"{'='*80}\n")

    cursor = conn.cursor()

    # Obtener partes sin analizar
    cursor.execute("""
        SELECT p.id, p.numero_parte, p.tipo_parte_original,
               p.tipo_parte_normalizado, p.fecha_parte, p.maquina_texto,
               p.resolucion, p.maquina_id
        FROM partes_trabajo p
        LEFT JOIN analisis_partes_ia a ON p.id = a.parte_id
        WHERE a.id IS NULL
          AND p.resolucion IS NOT NULL
          AND p.resolucion != ''
          AND p.tipo_parte_normalizado IN ('AVERIA', 'REPARACION')
        ORDER BY p.fecha_parte DESC
        LIMIT %s
    """, (limite,))

    partes = cursor.fetchall()

    if not partes:
        print("⚠️  No hay partes sin analizar (o todos ya tienen análisis)")
        return

    print(f"📝 Encontrados {len(partes)} partes para analizar\n")

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

        print(f"\n[{idx}/{len(partes)}] Analizando parte #{parte['numero_parte']}")
        print(f"    Tipo: {parte['tipo_parte_normalizado']}")
        print(f"    Máquina: {parte['maquina_texto']}")
        print(f"    Resolución: {parte['resolucion'][:100]}...")

        analisis_id = analizador_ia.analizar_parte_con_ia(parte, conn)

        if analisis_id:
            # Mostrar resultado
            cursor.execute("""
                SELECT componente_principal, gravedad_tecnica,
                       probabilidad_recurrencia, urgencia_ia,
                       coste_estimado_correctivo, confianza_analisis
                FROM analisis_partes_ia
                WHERE id = %s
            """, (analisis_id,))

            resultado = cursor.fetchone()
            if resultado:
                print(f"\n    ✅ ANÁLISIS COMPLETADO:")
                print(f"       Componente: {resultado[0]}")
                print(f"       Gravedad: {resultado[1]}")
                print(f"       Prob. Recurrencia: {resultado[2]}%")
                print(f"       Urgencia: {resultado[3]}")
                print(f"       Coste Estimado: {resultado[4]}€")
                print(f"       Confianza: {resultado[5]}%")
        else:
            print(f"    ❌ Error en el análisis")

        print()

    print(f"{'='*80}")
    print(f"✅ Test de análisis completado")
    print(f"{'='*80}\n")

def generar_prediccion_test(conn, maquina_id):
    """Generar predicción de prueba para una máquina"""
    print(f"\n{'='*80}")
    print(f"🔮 TEST: Generación de predicción para máquina ID={maquina_id}")
    print(f"{'='*80}\n")

    cursor = conn.cursor()

    # Verificar que la máquina existe
    cursor.execute("""
        SELECT m.id, m.identificador, i.nombre as instalacion
        FROM maquinas_cartera m
        LEFT JOIN instalaciones i ON m.instalacion_id = i.id
        WHERE m.id = %s
    """, (maquina_id,))

    maquina = cursor.fetchone()

    if not maquina:
        print(f"❌ Máquina con ID {maquina_id} no encontrada")
        return

    print(f"📌 Máquina: {maquina[1]}")
    print(f"📍 Instalación: {maquina[2] or 'N/A'}\n")

    # Generar predicción
    prediccion_id = analizador_ia.generar_prediccion_maquina(maquina_id, conn)

    if prediccion_id:
        # Mostrar resultado
        cursor.execute("""
            SELECT estado_salud_ia, puntuacion_salud, tendencia,
                   componente_riesgo_1, probabilidad_fallo_1, dias_estimados_fallo_1,
                   prioridad_intervencion, ahorro_potencial, confianza_prediccion
            FROM predicciones_maquina
            WHERE id = %s
        """, (prediccion_id,))

        pred = cursor.fetchone()
        if pred:
            print(f"\n✅ PREDICCIÓN GENERADA:")
            print(f"   Estado de Salud: {pred[0]}")
            print(f"   Puntuación: {pred[1]}/100")
            print(f"   Tendencia: {pred[2]}")
            print(f"   Componente en Mayor Riesgo: {pred[3]}")
            print(f"   Probabilidad de Fallo: {pred[4]}%")
            print(f"   Días Estimados: {pred[5]}")
            print(f"   Prioridad de Intervención: {pred[6]}")
            print(f"   Ahorro Potencial: {pred[7]}€")
            print(f"   Confianza: {pred[8]}%")

        # Generar alertas
        print(f"\n🚨 Generando alertas predictivas...")
        alertas = analizador_ia.generar_alertas_predictivas(prediccion_id, conn)

        if alertas > 0:
            print(f"✅ {alertas} alerta(s) generada(s)")
        else:
            print(f"✅ No se detectaron alertas necesarias")
    else:
        print(f"❌ Error generando predicción")

    print(f"\n{'='*80}")
    print(f"✅ Test de predicción completado")
    print(f"{'='*80}\n")

def listar_maquinas_disponibles(conn, limite=10):
    """Listar máquinas disponibles para testing"""
    print(f"\n{'='*80}")
    print(f"📋 MÁQUINAS DISPONIBLES PARA TESTING (Top {limite})")
    print(f"{'='*80}\n")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.id,
            m.identificador,
            i.nombre as instalacion,
            COUNT(DISTINCT p.id) as total_partes,
            COUNT(DISTINCT p.id) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as total_averias
        FROM maquinas_cartera m
        LEFT JOIN instalaciones i ON m.instalacion_id = i.id
        LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
        WHERE m.en_cartera = TRUE
        GROUP BY m.id, m.identificador, i.nombre
        HAVING COUNT(DISTINCT p.id) > 5
        ORDER BY COUNT(DISTINCT p.id) DESC
        LIMIT %s
    """, (limite,))

    maquinas = cursor.fetchall()

    print(f"{'ID':<8} {'Identificador':<30} {'Instalación':<40} {'Partes':<10} {'Averías'}")
    print("-" * 120)

    for m in maquinas:
        print(f"{m[0]:<8} {m[1][:30]:<30} {(m[2] or 'N/A')[:40]:<40} {m[3]:<10} {m[4]}")

    print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Test del Sistema de IA Predictiva de AscensorAlert',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Analizar 5 partes de prueba
  python scripts/test_ia_predictiva.py --analizar-partes 5

  # Generar predicción para máquina específica
  python scripts/test_ia_predictiva.py --generar-prediccion 123

  # Listar máquinas disponibles
  python scripts/test_ia_predictiva.py --listar-maquinas

  # Analizar todos los partes sin análisis (máximo 100)
  python scripts/test_ia_predictiva.py --analizar-todo

  # Generar predicciones para todas las máquinas
  python scripts/test_ia_predictiva.py --predicciones-todas
        """
    )

    parser.add_argument('--analizar-partes', type=int, metavar='N',
                      help='Analizar N partes recientes sin análisis')
    parser.add_argument('--generar-prediccion', type=int, metavar='ID',
                      help='Generar predicción para máquina con ID especificado')
    parser.add_argument('--listar-maquinas', action='store_true',
                      help='Listar máquinas disponibles para testing')
    parser.add_argument('--analizar-todo', action='store_true',
                      help='Analizar todos los partes sin análisis (máx 100)')
    parser.add_argument('--predicciones-todas', action='store_true',
                      help='Generar predicciones para todas las máquinas en cartera')

    args = parser.parse_args()

    # Verificar que se especificó al menos una acción
    if not any([args.analizar_partes, args.generar_prediccion, args.listar_maquinas,
                args.analizar_todo, args.predicciones_todas]):
        parser.print_help()
        return

    # Banner
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     SISTEMA DE ANÁLISIS PREDICTIVO CON IA - ASCENSORES        ║
    ║                        MODO TEST                               ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    # Verificar API Key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ERROR: ANTHROPIC_API_KEY no está configurada")
        print("   Configura tu API key en el archivo .env:")
        print("   ANTHROPIC_API_KEY=tu_clave_aqui")
        return

    print("✓ ANTHROPIC_API_KEY configurada")

    # Conectar a BD
    try:
        conn = conectar_bd()
    except Exception as e:
        print(f"❌ ERROR conectando a la base de datos: {str(e)}")
        print("\nAsegúrate de tener configurado DATABASE_URL o las variables:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return

    # Verificar schema
    if not verificar_schema(conn):
        return

    # Ejecutar acciones
    try:
        if args.listar_maquinas:
            listar_maquinas_disponibles(conn, 20)

        if args.analizar_partes:
            analizar_partes_test(conn, args.analizar_partes)

        if args.generar_prediccion:
            generar_prediccion_test(conn, args.generar_prediccion)

        if args.analizar_todo:
            print("\n⚠️  ATENCIÓN: Analizando TODOS los partes sin análisis (máximo 100)")
            print("   Esto puede tardar varios minutos y consumir créditos de API\n")
            respuesta = input("¿Continuar? (s/n): ")
            if respuesta.lower() == 's':
                analizador_ia.procesar_lote_partes(conn, limite=100)

        if args.predicciones_todas:
            print("\n⚠️  ATENCIÓN: Generando predicciones para TODAS las máquinas")
            print("   Esto puede tardar mucho tiempo y consumir créditos de API\n")
            respuesta = input("¿Continuar? (s/n): ")
            if respuesta.lower() == 's':
                analizador_ia.generar_predicciones_todas_maquinas(conn)

    except Exception as e:
        print(f"\n❌ ERROR durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n✓ Conexión a BD cerrada")

    print("\n" + "="*80)
    print("✅ Test completado")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
