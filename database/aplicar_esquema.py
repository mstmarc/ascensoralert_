#!/usr/bin/env python3
"""
Script para aplicar el esquema de Cartera a Supabase
"""

import os
import sys

def aplicar_esquema():
    """Aplica el esquema SQL a Supabase usando psycopg2"""

    # Intentar importar psycopg2
    try:
        import psycopg2
    except ImportError:
        print("❌ ERROR: psycopg2 no está instalado")
        print("\nInstalar con:")
        print("  pip install psycopg2-binary")
        sys.exit(1)

    # Obtener credenciales
    supabase_url = "hvkifqguxsgegzaxwcmj.supabase.co"
    supabase_password = os.environ.get("SUPABASE_DB_PASSWORD")

    if not supabase_password:
        print("❌ ERROR: Variable de entorno SUPABASE_DB_PASSWORD no está configurada")
        print("\nConfigurar con:")
        print("  export SUPABASE_DB_PASSWORD='tu_password'")
        print("\nEncuentra el password en:")
        print("  Supabase Dashboard → Settings → Database → Connection String")
        sys.exit(1)

    # Construir connection string
    conn_string = f"postgresql://postgres:{supabase_password}@{supabase_url}:5432/postgres"

    print("📋 Aplicando esquema de Cartera a Supabase...")
    print(f"   Servidor: {supabase_url}")

    try:
        # Conectar
        print("\n🔌 Conectando a Supabase...")
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Leer schema SQL
        schema_path = os.path.join(os.path.dirname(__file__), "cartera_schema.sql")
        print(f"📄 Leyendo {schema_path}...")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Ejecutar
        print("⚙️  Ejecutando SQL...")
        cur.execute(schema_sql)
        conn.commit()

        print("\n✅ ¡Esquema aplicado correctamente!")

        # Verificar
        print("\n📊 Verificando tablas creadas...")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE '%cartera%'
                 OR table_name LIKE '%oportunidades%'
                 OR table_name LIKE '%tipos_parte%'
                 OR table_name = 'instalaciones'
                 OR table_name = 'partes_trabajo')
            ORDER BY table_name;
        """)

        tables = cur.fetchall()
        print(f"\n   Tablas creadas ({len(tables)}):")
        for table in tables:
            print(f"   ✓ {table[0]}")

        # Verificar tipos_parte_mapeo
        cur.execute("SELECT COUNT(*) FROM tipos_parte_mapeo;")
        count = cur.fetchone()[0]
        print(f"\n   ✓ tipos_parte_mapeo: {count} registros")

        # Verificar vistas
        cur.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            AND table_name LIKE 'v_%'
            AND (table_name LIKE '%maquina%'
                 OR table_name LIKE '%parte%'
                 OR table_name LIKE '%mantenimiento%')
            ORDER BY table_name;
        """)

        views = cur.fetchall()
        print(f"\n   Vistas creadas ({len(views)}):")
        for view in views:
            print(f"   ✓ {view[0]}")

        print("\n" + "="*60)
        print("🎉 ¡Esquema de Cartera aplicado exitosamente!")
        print("="*60)
        print("\n📌 Próximos pasos:")
        print("   1. Importar Excel de cartera (instalaciones + máquinas)")
        print("   2. Importar Excel de partes (2024 + 2025 YTD)")
        print("   3. Revisar recomendaciones detectadas")
        print("   4. Crear oportunidades de facturación")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\n❌ ERROR de base de datos:")
        print(f"   {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERROR: No se encontró el archivo cartera_schema.sql")
        print(f"   Ruta esperada: {schema_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR inesperado:")
        print(f"   {e}")
        sys.exit(1)

if __name__ == "__main__":
    aplicar_esquema()
