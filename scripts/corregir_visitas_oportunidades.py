#!/usr/bin/env python3
"""
Script para corregir visitas huérfanas y vincularlas con oportunidades
Identifica visitas sin oportunidad_id y las vincula según cliente y fechas
"""

import os
import sys
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Variables SUPABASE_URL y SUPABASE_KEY no configuradas")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def diagnosticar_visitas_instalacion():
    """Identificar visitas a instalación sin oportunidad_id"""
    print("\n" + "="*80)
    print("📋 DIAGNÓSTICO: Visitas a Instalación sin oportunidad_id")
    print("="*80)

    # Obtener visitas sin oportunidad_id
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?select=*,clientes(*)&oportunidad_id=is.null&order=fecha_visita.desc",
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"❌ Error al obtener visitas: {response.text}")
        return []

    visitas = response.json()
    candidatas = []

    for visita in visitas:
        cliente_id = visita.get('cliente_id')
        fecha_visita = visita.get('fecha_visita')

        # Buscar oportunidades del mismo cliente
        opp_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/oportunidades?select=*&cliente_id=eq.{cliente_id}&estado=neq.ganada&estado=neq.perdida",
            headers=HEADERS
        )

        if opp_response.status_code == 200:
            oportunidades = opp_response.json()

            # Filtrar oportunidades por fecha
            for opp in oportunidades:
                fecha_creacion = opp.get('fecha_creacion', '')[:10]
                if fecha_visita >= fecha_creacion:
                    candidatas.append({
                        'visita': visita,
                        'oportunidad': opp
                    })
                    break  # Solo la primera oportunidad coincidente

    print(f"\n✅ Encontradas {len(candidatas)} visitas candidatas a corrección")

    for i, candidata in enumerate(candidatas[:10], 1):  # Mostrar solo primeras 10
        v = candidata['visita']
        o = candidata['oportunidad']
        print(f"\n{i}. Visita ID {v['id']} - {v['fecha_visita']}")
        print(f"   Cliente: {v['clientes']['nombre_cliente'] if v.get('clientes') else 'N/A'}")
        print(f"   → Oportunidad ID {o['id']}: {o['tipo']} ({o['estado']})")

    if len(candidatas) > 10:
        print(f"\n   ... y {len(candidatas) - 10} más")

    return candidatas

def diagnosticar_visitas_administrador():
    """Identificar visitas a administrador sin oportunidad_id"""
    print("\n" + "="*80)
    print("📋 DIAGNÓSTICO: Visitas a Administrador sin oportunidad_id")
    print("="*80)

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=*&oportunidad_id=is.null&order=fecha_visita.desc",
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"❌ Error al obtener visitas: {response.text}")
        return []

    visitas = response.json()
    candidatas = []

    for visita in visitas:
        admin_id = visita.get('administrador_id')
        fecha_visita = visita.get('fecha_visita')

        if not admin_id:
            continue

        # Buscar clientes de ese administrador
        clientes_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/clientes?select=id&administrador_id=eq.{admin_id}",
            headers=HEADERS
        )

        if clientes_response.status_code == 200:
            clientes = clientes_response.json()

            for cliente in clientes:
                # Buscar oportunidades de esos clientes
                opp_response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/oportunidades?select=*,clientes(nombre_cliente)&cliente_id=eq.{cliente['id']}&estado=neq.ganada&estado=neq.perdida",
                    headers=HEADERS
                )

                if opp_response.status_code == 200:
                    oportunidades = opp_response.json()

                    for opp in oportunidades:
                        fecha_creacion = opp.get('fecha_creacion', '')[:10]
                        if fecha_visita >= fecha_creacion:
                            candidatas.append({
                                'visita': visita,
                                'oportunidad': opp
                            })
                            break
                    if candidatas and candidatas[-1]['visita']['id'] == visita['id']:
                        break

    print(f"\n✅ Encontradas {len(candidatas)} visitas candidatas a corrección")

    for i, candidata in enumerate(candidatas[:10], 1):
        v = candidata['visita']
        o = candidata['oportunidad']
        print(f"\n{i}. Visita ID {v['id']} - {v['fecha_visita']}")
        print(f"   Administrador: {v['administrador_fincas']}")
        print(f"   → Oportunidad ID {o['id']}: {o['tipo']} ({o['estado']})")
        print(f"      Cliente: {o['clientes']['nombre_cliente'] if o.get('clientes') else 'N/A'}")

    if len(candidatas) > 10:
        print(f"\n   ... y {len(candidatas) - 10} más")

    return candidatas

def corregir_visitas(candidatas, tipo='instalacion'):
    """Aplicar correcciones a las visitas"""
    if not candidatas:
        print("\n✅ No hay visitas para corregir")
        return

    print(f"\n{'='*80}")
    print(f"🔧 CORRECCIÓN: Se vincularán {len(candidatas)} visitas")
    print("="*80)

    respuesta = input("\n¿Deseas continuar? (s/N): ").strip().lower()
    if respuesta != 's':
        print("❌ Corrección cancelada")
        return

    tabla = "visitas_seguimiento" if tipo == 'instalacion' else "visitas_administradores"
    corregidas = 0
    errores = 0

    for candidata in candidatas:
        visita_id = candidata['visita']['id']
        oportunidad_id = candidata['oportunidad']['id']

        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{tabla}?id=eq.{visita_id}",
            headers=HEADERS,
            json={"oportunidad_id": oportunidad_id}
        )

        if response.status_code in [200, 204]:
            corregidas += 1
            print(f"✅ Visita {visita_id} vinculada a oportunidad {oportunidad_id}")
        else:
            errores += 1
            print(f"❌ Error en visita {visita_id}: {response.text}")

    print(f"\n{'='*80}")
    print(f"📊 RESUMEN:")
    print(f"   ✅ Corregidas: {corregidas}")
    print(f"   ❌ Errores: {errores}")
    print("="*80)

def mostrar_estadisticas():
    """Mostrar estadísticas finales"""
    print("\n" + "="*80)
    print("📊 ESTADÍSTICAS FINALES")
    print("="*80)

    # Visitas a instalación
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_seguimiento?select=id,oportunidad_id",
        headers=HEADERS
    )
    if response.status_code == 200:
        visitas = response.json()
        total = len(visitas)
        con_opp = sum(1 for v in visitas if v.get('oportunidad_id'))
        print(f"\n📍 Visitas a Instalación:")
        print(f"   Total: {total}")
        print(f"   Con oportunidad: {con_opp} ({con_opp*100//total if total > 0 else 0}%)")
        print(f"   Sin oportunidad: {total - con_opp}")

    # Visitas a administrador
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/visitas_administradores?select=id,oportunidad_id",
        headers=HEADERS
    )
    if response.status_code == 200:
        visitas = response.json()
        total = len(visitas)
        con_opp = sum(1 for v in visitas if v.get('oportunidad_id'))
        print(f"\n👔 Visitas a Administrador:")
        print(f"   Total: {total}")
        print(f"   Con oportunidad: {con_opp} ({con_opp*100//total if total > 0 else 0}%)")
        print(f"   Sin oportunidad: {total - con_opp}")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🔧 CORRECTOR DE VISITAS HUÉRFANAS - AscensorAlert                       ║
║                                                                              ║
║     Este script identifica visitas sin oportunidad_id y las vincula         ║
║     con oportunidades activas según cliente y fechas                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Paso 1: Diagnóstico
    print("\n🔍 PASO 1: DIAGNÓSTICO\n")
    candidatas_instalacion = diagnosticar_visitas_instalacion()
    candidatas_admin = diagnosticar_visitas_administrador()

    total_candidatas = len(candidatas_instalacion) + len(candidatas_admin)

    if total_candidatas == 0:
        print("\n✅ No se encontraron visitas para corregir. Todo está correcto.")
        mostrar_estadisticas()
        return

    # Paso 2: Confirmación
    print(f"\n{'='*80}")
    print(f"📋 RESUMEN: Se encontraron {total_candidatas} visitas para corregir")
    print(f"   - Visitas a instalación: {len(candidatas_instalacion)}")
    print(f"   - Visitas a administrador: {len(candidatas_admin)}")
    print("="*80)

    respuesta = input("\n¿Deseas ver el proceso de corrección? (s/N): ").strip().lower()
    if respuesta != 's':
        print("\n✅ Operación cancelada. No se realizaron cambios.")
        return

    # Paso 3: Corrección
    print("\n🔧 PASO 2: CORRECCIÓN\n")

    if candidatas_instalacion:
        corregir_visitas(candidatas_instalacion, tipo='instalacion')

    if candidatas_admin:
        corregir_visitas(candidatas_admin, tipo='administrador')

    # Paso 4: Estadísticas finales
    mostrar_estadisticas()

    print("\n✅ Proceso completado\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
