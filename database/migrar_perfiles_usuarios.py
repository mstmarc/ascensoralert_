#!/usr/bin/env python3
"""
Script de migración para configurar perfiles de usuarios
Ejecuta el schema SQL y configura los perfiles iniciales
"""
import os
import requests

# Configuración de Supabase
SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ Error: SUPABASE_KEY no está configurada")
    print("   Ejecuta: export SUPABASE_KEY='tu_clave'")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def obtener_usuarios():
    """Obtiene lista de usuarios actuales"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/usuarios?select=id,nombre_usuario,email,perfil",
        headers=HEADERS
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error al obtener usuarios: {response.status_code}")
        print(response.text)
        return []

def actualizar_perfil(usuario_id, perfil):
    """Actualiza el perfil de un usuario"""
    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{usuario_id}",
        json={"perfil": perfil},
        headers=HEADERS
    )

    if response.status_code == 200:
        return True
    else:
        print(f"❌ Error al actualizar usuario {usuario_id}: {response.status_code}")
        print(response.text)
        return False

def main():
    """Proceso principal de migración"""
    print("=" * 60)
    print("MIGRACIÓN: Configuración de Perfiles de Usuario")
    print("=" * 60)
    print()

    print("📋 Paso 1: Obteniendo usuarios actuales...")
    usuarios = obtener_usuarios()

    if not usuarios:
        print("⚠️  No se encontraron usuarios. Asegúrate de que:")
        print("   1. La tabla 'usuarios' existe en Supabase")
        print("   2. El campo 'perfil' se añadió correctamente")
        print("   3. La clave SUPABASE_KEY es correcta")
        return

    print(f"✅ Se encontraron {len(usuarios)} usuarios\n")

    print("=" * 60)
    print("USUARIOS ACTUALES:")
    print("=" * 60)
    for i, user in enumerate(usuarios, 1):
        perfil_actual = user.get('perfil', 'Sin perfil')
        print(f"{i}. {user['nombre_usuario']:20} | Perfil: {perfil_actual:15} | Email: {user.get('email', 'N/A')}")
    print()

    print("=" * 60)
    print("CONFIGURACIÓN DE PERFILES")
    print("=" * 60)
    print()

    print("Por favor, configura los perfiles de los usuarios:")
    print()
    print("Perfiles disponibles:")
    print("  1. admin       - Acceso total (incluyendo Inspecciones)")
    print("  2. gestor      - Acceso a todo EXCEPTO Inspecciones")
    print("  3. visualizador - Solo lectura en todos los módulos")
    print()

    configuracion = []

    for user in usuarios:
        nombre = user['nombre_usuario']
        email = user.get('email', 'N/A')
        perfil_actual = user.get('perfil', 'visualizador')

        print(f"\n👤 Usuario: {nombre} ({email})")
        print(f"   Perfil actual: {perfil_actual}")

        # Sugerencias automáticas
        if perfil_actual and perfil_actual != 'visualizador':
            sugerencia = perfil_actual
            print(f"   Sugerencia: Mantener '{perfil_actual}' (presiona Enter)")
        elif 'julio' in nombre.lower():
            sugerencia = 'gestor'
            print(f"   Sugerencia: 'gestor' (acceso a todo excepto inspecciones)")
        else:
            sugerencia = 'visualizador'
            print(f"   Sugerencia: 'visualizador' (solo lectura)")

        nuevo_perfil = input(f"   Nuevo perfil [{sugerencia}]: ").strip().lower()

        if not nuevo_perfil:
            nuevo_perfil = sugerencia

        if nuevo_perfil not in ['admin', 'gestor', 'visualizador']:
            print(f"   ⚠️  Perfil inválido. Usando '{sugerencia}'")
            nuevo_perfil = sugerencia

        configuracion.append({
            'id': user['id'],
            'nombre': nombre,
            'perfil_anterior': perfil_actual,
            'perfil_nuevo': nuevo_perfil
        })

    print()
    print("=" * 60)
    print("RESUMEN DE CAMBIOS")
    print("=" * 60)
    for config in configuracion:
        cambio = "sin cambios" if config['perfil_anterior'] == config['perfil_nuevo'] else "CAMBIO"
        print(f"{config['nombre']:20} | {config['perfil_anterior']:15} → {config['perfil_nuevo']:15} | {cambio}")

    print()
    confirmacion = input("¿Aplicar estos cambios? (s/N): ").strip().lower()

    if confirmacion != 's':
        print("\n❌ Migración cancelada")
        return

    print()
    print("=" * 60)
    print("APLICANDO CAMBIOS...")
    print("=" * 60)

    exitosos = 0
    for config in configuracion:
        if config['perfil_anterior'] == config['perfil_nuevo']:
            print(f"⏭  {config['nombre']:20} - sin cambios")
            exitosos += 1
            continue

        print(f"🔄 Actualizando {config['nombre']}...", end=" ")
        if actualizar_perfil(config['id'], config['perfil_nuevo']):
            print(f"✅ {config['perfil_nuevo']}")
            exitosos += 1
        else:
            print(f"❌ ERROR")

    print()
    print("=" * 60)
    print(f"✅ Migración completada: {exitosos}/{len(configuracion)} usuarios actualizados")
    print("=" * 60)

    # Mostrar usuarios finales
    print("\n📋 Verificando configuración final...")
    usuarios_finales = obtener_usuarios()

    print("\n" + "=" * 60)
    print("USUARIOS CONFIGURADOS:")
    print("=" * 60)
    for user in usuarios_finales:
        perfil = user.get('perfil', 'Sin perfil')
        icono = "👑" if perfil == 'admin' else "🔧" if perfil == 'gestor' else "👁️"
        print(f"{icono} {user['nombre_usuario']:20} | {perfil:15}")
    print("=" * 60)

if __name__ == "__main__":
    main()
