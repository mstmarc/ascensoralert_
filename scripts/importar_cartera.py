#!/usr/bin/env python3
"""
Script para importar cartera de instalaciones y máquinas desde Excel

Columnas esperadas en el Excel:
- Cód. instalación
- Instalación
- Cód. máquina
- Máquina
- Técnico (opcional)

Proceso:
1. Agrupar por instalación → crear instalaciones únicas
2. Crear máquinas para cada instalación
3. Extraer municipio del campo "Instalación"
"""

import os
import sys
import pandas as pd
import requests
from datetime import datetime

# Configuración
SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ ERROR: Variable de entorno SUPABASE_KEY no está configurada")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Mapeo de nombres de columnas (por si vienen diferentes)
COLUMN_MAPPING = {
    'Cód. instalación': 'cod_instalacion',
    'Instalación': 'instalacion',
    'Cód. máquina': 'cod_maquina',
    'Máquina': 'maquina',
    'Técnico': 'tecnico'
}

# Municipios de Gran Canaria (para extracción)
MUNICIPIOS_GC = [
    'LAS PALMAS', 'TELDE', 'SANTA LUCIA', 'AGÜIMES', 'INGENIO',
    'MOGAN', 'SAN BARTOLOME', 'SANTA BRIGIDA', 'ARUCAS', 'TEROR',
    'GALDAR', 'AGAETE', 'VALLESECO', 'FIRGAS', 'MOYA',
    'SANTA MARIA DE GUIA', 'VALSEQUILLO', 'VEGA DE SAN MATEO',
    'TEJEDA', 'ALDEA DE SAN NICOLAS'
]

def extraer_municipio(instalacion_texto):
    """
    Extrae el municipio del texto de instalación

    Ejemplo:
    "PELICAN MOTOR, S.L. - C/ DIEGO VEGA SARMIENTO 56" → "LAS PALMAS" (default)
    "ED. MIRADOR DE VEGUETA - C/ MENDIZABAL, Nº 31-33" → "LAS PALMAS"
    """
    texto_upper = instalacion_texto.upper()

    # Buscar municipios conocidos
    for municipio in MUNICIPIOS_GC:
        if municipio in texto_upper:
            return municipio.title()

    # Si no se encuentra, asumir Las Palmas (capital, más probable)
    return "Las Palmas de Gran Canaria"

def limpiar_nombre_instalacion(instalacion_texto):
    """
    Limpia el nombre de la instalación para consistencia

    Ejemplo:
    "PELICAN MOTOR, S.L. (CONCESIONARIO JAGUAR) - C/ DIEGO VEGA SARMIENTO 56"
    → "PELICAN MOTOR, S.L. (CONCESIONARIO JAGUAR)"
    """
    # Eliminar dirección (después del guion)
    if ' - ' in instalacion_texto:
        return instalacion_texto.split(' - ')[0].strip()
    return instalacion_texto.strip()

def importar_cartera(excel_path):
    """Importa cartera desde Excel"""

    print("="*70)
    print("📁 IMPORTAR CARTERA DE INSTALACIONES Y MÁQUINAS")
    print("="*70)

    # 1. Leer Excel
    print(f"\n📄 Leyendo Excel: {excel_path}")

    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo {excel_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR leyendo Excel: {e}")
        sys.exit(1)

    print(f"   ✓ Leídas {len(df)} filas")

    # 2. Renombrar columnas
    df.rename(columns=COLUMN_MAPPING, inplace=True)

    # Verificar columnas requeridas
    required = ['cod_instalacion', 'instalacion', 'cod_maquina', 'maquina']
    missing = [col for col in required if col not in df.columns]

    if missing:
        print(f"❌ ERROR: Faltan columnas requeridas: {missing}")
        print(f"   Columnas encontradas: {list(df.columns)}")
        sys.exit(1)

    # 3. Procesar instalaciones únicas
    print("\n🏢 Procesando instalaciones...")

    instalaciones_unicas = df[['cod_instalacion', 'instalacion']].drop_duplicates('cod_instalacion')
    instalaciones_creadas = []
    instalaciones_map = {}  # cod_instalacion → id

    print(f"   Instalaciones únicas: {len(instalaciones_unicas)}")

    for idx, row in instalaciones_unicas.iterrows():
        nombre = limpiar_nombre_instalacion(row['instalacion'])
        municipio = extraer_municipio(row['instalacion'])

        # Verificar si ya existe
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/instalaciones?nombre=eq.{nombre}",
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            # Ya existe
            instalacion_id = response.json()[0]['id']
            print(f"   ↻ Ya existe: {nombre[:50]}...")
        else:
            # Crear nueva
            data = {
                "nombre": nombre,
                "municipio": municipio
            }

            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/instalaciones",
                json=data,
                headers=HEADERS
            )

            if response.status_code == 201:
                instalacion_id = response.json()[0]['id']
                instalaciones_creadas.append(nombre)
                print(f"   ✓ Creada: {nombre[:50]}... ({municipio})")
            else:
                print(f"   ✗ ERROR creando instalación: {response.text}")
                continue

        # Guardar mapping
        instalaciones_map[row['cod_instalacion']] = instalacion_id

    print(f"\n   📊 Resumen instalaciones:")
    print(f"      Total procesadas: {len(instalaciones_unicas)}")
    print(f"      Nuevas creadas: {len(instalaciones_creadas)}")
    print(f"      Ya existían: {len(instalaciones_unicas) - len(instalaciones_creadas)}")

    # 4. Procesar máquinas
    print("\n🛗 Procesando máquinas...")

    maquinas_creadas = []
    maquinas_existentes = []
    maquinas_error = []

    for idx, row in df.iterrows():
        cod_instalacion = row['cod_instalacion']
        identificador = row['maquina'].strip()
        codigo_maquina = row['cod_maquina'].strip() if pd.notna(row['cod_maquina']) else None

        # Obtener instalacion_id
        instalacion_id = instalaciones_map.get(cod_instalacion)

        if not instalacion_id:
            print(f"   ⚠️  Instalación no encontrada para máquina: {identificador}")
            maquinas_error.append(identificador)
            continue

        # Verificar si la máquina ya existe
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera?identificador=eq.{identificador}",
            headers=HEADERS
        )

        if response.status_code == 200 and len(response.json()) > 0:
            maquinas_existentes.append(identificador)
            print(f"   ↻ Ya existe: {identificador[:50]}...")
            continue

        # Crear nueva máquina
        data = {
            "instalacion_id": instalacion_id,
            "identificador": identificador,
            "codigo_maquina": codigo_maquina
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/maquinas_cartera",
            json=data,
            headers=HEADERS
        )

        if response.status_code == 201:
            maquinas_creadas.append(identificador)
            print(f"   ✓ Creada: {identificador[:50]}...")
        else:
            print(f"   ✗ ERROR creando máquina: {response.text}")
            maquinas_error.append(identificador)

    print(f"\n   📊 Resumen máquinas:")
    print(f"      Total procesadas: {len(df)}")
    print(f"      Nuevas creadas: {len(maquinas_creadas)}")
    print(f"      Ya existían: {len(maquinas_existentes)}")
    print(f"      Errores: {len(maquinas_error)}")

    # 5. Resumen final
    print("\n" + "="*70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*70)
    print(f"\n📊 RESUMEN GENERAL:")
    print(f"   Instalaciones creadas:  {len(instalaciones_creadas)}")
    print(f"   Máquinas creadas:      {len(maquinas_creadas)}")
    print(f"   Total filas procesadas: {len(df)}")

    if maquinas_error:
        print(f"\n⚠️  {len(maquinas_error)} máquinas con errores:")
        for maq in maquinas_error[:10]:  # Mostrar solo las primeras 10
            print(f"      - {maq}")
        if len(maquinas_error) > 10:
            print(f"      ... y {len(maquinas_error) - 10} más")

    print("\n📌 Próximo paso:")
    print("   Importar partes de trabajo (2024 + 2025 YTD)")
    print(f"   Comando: python scripts/importar_partes.py <archivo_partes.xlsx>")

    return {
        "instalaciones_creadas": len(instalaciones_creadas),
        "maquinas_creadas": len(maquinas_creadas),
        "errores": len(maquinas_error)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/importar_cartera.py <archivo_excel>")
        print("\nEjemplo:")
        print("  python scripts/importar_cartera.py cartera_gran_canaria.xlsx")
        sys.exit(1)

    excel_path = sys.argv[1]
    resultado = importar_cartera(excel_path)
