#!/usr/bin/env python3
"""
Script de configuración de Supabase Storage para PDFs de Inspecciones
Crea el bucket 'inspecciones-pdfs' y configura las políticas necesarias
"""

import requests
import os
import sys

# Configuración de Supabase
SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ ERROR: La variable de entorno SUPABASE_KEY no está configurada")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def crear_bucket():
    """Crea el bucket inspecciones-pdfs"""
    print("📦 Creando bucket 'inspecciones-pdfs'...")

    # Configuración del bucket
    bucket_data = {
        "id": "inspecciones-pdfs",
        "name": "inspecciones-pdfs",
        "public": True,  # Bucket público para URLs públicas
        "file_size_limit": 52428800,  # 50 MB en bytes
        "allowed_mime_types": ["application/pdf"]
    }

    response = requests.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        json=bucket_data,
        headers=HEADERS
    )

    if response.status_code == 200:
        print("✅ Bucket creado exitosamente")
        return True
    elif response.status_code == 409:
        print("⚠️  El bucket ya existe")
        return True
    else:
        print(f"❌ Error al crear bucket: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return False

def verificar_bucket():
    """Verifica que el bucket existe"""
    print("\n🔍 Verificando bucket...")

    response = requests.get(
        f"{SUPABASE_URL}/storage/v1/bucket",
        headers=HEADERS
    )

    if response.status_code == 200:
        buckets = response.json()
        bucket_exists = any(b.get('id') == 'inspecciones-pdfs' or b.get('name') == 'inspecciones-pdfs' for b in buckets)

        if bucket_exists:
            print("✅ Bucket 'inspecciones-pdfs' existe")
            # Mostrar detalles del bucket
            for bucket in buckets:
                if bucket.get('id') == 'inspecciones-pdfs' or bucket.get('name') == 'inspecciones-pdfs':
                    print(f"   - ID: {bucket.get('id')}")
                    print(f"   - Público: {'Sí' if bucket.get('public') else 'No'}")
                    print(f"   - Tamaño máximo: {bucket.get('file_size_limit', 'N/A')} bytes")
            return True
        else:
            print("❌ Bucket 'inspecciones-pdfs' NO existe")
            return False
    else:
        print(f"❌ Error al verificar buckets: {response.status_code}")
        print(f"   Respuesta: {response.text}")
        return False

def main():
    print("=" * 60)
    print("🚀 Setup de Supabase Storage para PDFs de Inspecciones")
    print("=" * 60)
    print()

    # Verificar si el bucket ya existe
    if verificar_bucket():
        print("\n✅ El bucket ya está configurado correctamente")
        print("\n💡 Puedes probar subir un PDF ahora")
        return

    # Crear bucket
    print("\n" + "=" * 60)
    if crear_bucket():
        # Verificar creación
        print()
        if verificar_bucket():
            print("\n" + "=" * 60)
            print("✅ CONFIGURACIÓN COMPLETADA")
            print("=" * 60)
            print("\n📝 Siguiente paso:")
            print("   Ejecuta las políticas RLS desde el editor SQL de Supabase:")
            print("   database/configurar_storage_rls_policies.sql")
            print("\n💡 Ahora puedes probar subir PDFs a las inspecciones")
        else:
            print("\n❌ Error en la verificación del bucket")
    else:
        print("\n❌ No se pudo crear el bucket")
        print("\n💡 Solución alternativa:")
        print("   1. Ve a Supabase Dashboard → Storage")
        print("   2. Click en 'New bucket'")
        print("   3. Configura:")
        print("      - Name: inspecciones-pdfs")
        print("      - Public: ✅ Activado")
        print("      - File size limit: 50 MB")
        print("      - Allowed MIME types: application/pdf")

if __name__ == "__main__":
    main()
