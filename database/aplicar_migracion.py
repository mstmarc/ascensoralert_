#!/usr/bin/env python3
"""
Script para aplicar migraciones SQL a Supabase
"""

import os
import sys
import argparse

def aplicar_migracion(archivo_sql):
    """Aplica una migración SQL a Supabase usando psycopg2"""

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

    print(f"📋 Aplicando migración: {os.path.basename(archivo_sql)}")
    print(f"   Servidor: {supabase_url}")

    try:
        # Conectar
        print("\n🔌 Conectando a Supabase...")
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Leer SQL
        print(f"📄 Leyendo {archivo_sql}...")

        with open(archivo_sql, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Ejecutar
        print("⚙️  Ejecutando migración...")
        cur.execute(migration_sql)
        conn.commit()

        print("\n✅ ¡Migración aplicada correctamente!")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\n❌ ERROR de base de datos:")
        print(f"   {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ ERROR: No se encontró el archivo {archivo_sql}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR inesperado:")
        print(f"   {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aplicar migración SQL a Supabase')
    parser.add_argument('archivo', help='Ruta al archivo SQL de migración')
    args = parser.parse_args()

    aplicar_migracion(args.archivo)
