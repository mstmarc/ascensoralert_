#!/usr/bin/env python3
"""
Script para importar partes de trabajo desde Excel

Columnas esperadas:
- PARTE (número de parte)
- TIPO PARTE (CONSERVACIÓN, AVERÍA, etc.)
- CÓD. MÁQUINA (informativo)
- MÁQUINA (identificador principal)
- FECHA (fecha y hora)
- CODIFICACIÓN ADICIONAL
- RESOLUCIÓN (descripción del trabajo + recomendaciones)

Proceso:
1. Leer Excel de partes
2. Mapear máquina con maquinas_cartera por identificador
3. Mapear tipo de parte con tipos_parte_mapeo
4. Detectar recomendaciones en campo RESOLUCIÓN
5. Insertar partes_trabajo con toda la información
"""

import os
import sys
import pandas as pd
import requests
import re
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
    "Prefer": "return=representation,resolution=ignore-duplicates"
}

# Palabras clave para detectar recomendaciones
PALABRAS_CLAVE_RECOMENDACION = [
    'RECOMENDACIÓN', 'RECOMENDACION', 'RECOMIENDO', 'RECOMENDAMOS',
    'CONVENDRÍA', 'CONVIENE', 'SERÍA CONVENIENTE', 'SE RECOMIENDA',
    'IMPORTANTE', 'URGENTE', 'NECESARIO', 'CAMBIAR', 'SUSTITUIR',
    'MODERNIZAR', 'REVISAR', 'PRÓXIMAMENTE', 'PROXIMAMENTE'
]

def detectar_recomendacion(texto_resolucion):
    """
    Detecta si el texto contiene recomendaciones técnicas

    Returns:
        tuple: (tiene_recomendacion: bool, texto_extraido: str or None)
    """
    if not texto_resolucion or pd.isna(texto_resolucion):
        return False, None

    texto_upper = texto_resolucion.upper()

    # Buscar palabras clave
    for palabra in PALABRAS_CLAVE_RECOMENDACION:
        if palabra in texto_upper:
            # Intentar extraer el texto de la recomendación
            # Buscar desde la palabra clave hasta el final
            patron = re.compile(f"{palabra}:?(.*)", re.IGNORECASE | re.DOTALL)
            match = patron.search(texto_resolucion)

            if match:
                recomendacion = match.group(1).strip()
                return True, recomendacion

            # Si no hay match del patrón, retornar el texto completo
            return True, texto_resolucion

    return False, None

def parsear_fecha(fecha_str):
    """
    Parsea fecha desde el Excel (puede venir en varios formatos)

    Ejemplos:
        "01/01/2024 21:27" → datetime
        "2024-01-01 21:27:00" → datetime
    """
    if pd.isna(fecha_str):
        return None

    # Si ya es datetime
    if isinstance(fecha_str, datetime):
        return fecha_str

    # Intentar parsear diferentes formatos
    formatos = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(str(fecha_str), formato)
        except ValueError:
            continue

    print(f"   ⚠️  No se pudo parsear fecha: {fecha_str}")
    return None

def cargar_mapeo_tipos():
    """Carga el mapeo de tipos de parte desde la BD"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/tipos_parte_mapeo?select=*",
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"❌ ERROR cargando mapeo de tipos: {response.text}")
        return {}

    mapeo = {}
    for row in response.json():
        mapeo[row['tipo_original'].upper()] = row['tipo_normalizado']

    return mapeo

def cargar_maquinas():
    """Carga todas las máquinas para mapeo rápido"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/maquinas_cartera?select=id,identificador",
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"❌ ERROR cargando máquinas: {response.text}")
        return {}

    maquinas_map = {}
    for row in response.json():
        maquinas_map[row['identificador']] = row['id']

    return maquinas_map

def importar_partes(excel_path, batch_size=100):
    """
    Importa partes de trabajo desde Excel

    Args:
        excel_path: Ruta al archivo Excel
        batch_size: Número de registros a procesar por lote
    """

    print("="*70)
    print("📋 IMPORTAR PARTES DE TRABAJO")
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

    # 2. Cargar mapeos
    print("\n🔄 Cargando mapeos...")
    mapeo_tipos = cargar_mapeo_tipos()
    print(f"   ✓ {len(mapeo_tipos)} tipos de parte mapeados")

    maquinas_map = cargar_maquinas()
    print(f"   ✓ {len(maquinas_map)} máquinas cargadas")

    if len(maquinas_map) == 0:
        print("   ⚠️  No hay máquinas en la base de datos")
        print("   📌 Ejecutar primero: python scripts/importar_cartera.py")
        sys.exit(1)

    # 3. Procesar partes
    print("\n⚙️  Procesando partes...")

    stats = {
        "total": len(df),
        "insertados": 0,
        "duplicados": 0,
        "sin_maquina": 0,
        "errores": 0,
        "recomendaciones_detectadas": 0
    }

    partes_batch = []

    for idx, row in df.iterrows():
        # Mostrar progreso cada 100 registros
        if (idx + 1) % 100 == 0:
            print(f"   Procesados: {idx + 1}/{len(df)}")

        # Validar columnas requeridas
        if pd.isna(row.get('PARTE')) or pd.isna(row.get('MÁQUINA')):
            stats["errores"] += 1
            continue

        # Mapear máquina
        identificador_maquina = str(row['MÁQUINA']).strip()
        maquina_id = maquinas_map.get(identificador_maquina)

        if not maquina_id:
            stats["sin_maquina"] += 1
            # print(f"   ⚠️  Máquina no encontrada: {identificador_maquina}")
            # Aún así insertamos el parte (con maquina_id = NULL)
            pass

        # Mapear tipo de parte
        tipo_original = str(row.get('TIPO PARTE', '')).strip().upper()
        tipo_normalizado = mapeo_tipos.get(tipo_original, 'OTRO')

        # Parsear fecha
        fecha_parte = parsear_fecha(row.get('FECHA'))
        if not fecha_parte:
            stats["errores"] += 1
            continue

        # Detectar recomendaciones
        resolucion = row.get('RESOLUCIÓN', '')
        tiene_recomendacion, recomendacion_extraida = detectar_recomendacion(resolucion)

        if tiene_recomendacion:
            stats["recomendaciones_detectadas"] += 1

        # Preparar datos para inserción
        parte_data = {
            "numero_parte": str(row['PARTE']),
            "tipo_parte_original": str(row.get('TIPO PARTE', '')).strip(),
            "codigo_maquina": str(row.get('CÓD. MÁQUINA', '')) if pd.notna(row.get('CÓD. MÁQUINA')) else None,
            "maquina_texto": identificador_maquina,
            "fecha_parte": fecha_parte.isoformat(),
            "codificacion_adicional": str(row.get('CODIFICACIÓN ADICIONAL', '')) if pd.notna(row.get('CODIFICACIÓN ADICIONAL')) else None,
            "resolucion": str(resolucion) if pd.notna(resolucion) else None,
            "maquina_id": maquina_id,
            "tipo_parte_normalizado": tipo_normalizado,
            "tiene_recomendacion": tiene_recomendacion,
            "recomendaciones_extraidas": recomendacion_extraida if tiene_recomendacion else None,
            "estado": "COMPLETADO",  # Por defecto al importar
            "importado": True
        }

        partes_batch.append(parte_data)

        # Insertar por lotes
        if len(partes_batch) >= batch_size:
            resultado = insertar_batch(partes_batch, stats)
            partes_batch = []

    # Insertar lote final
    if partes_batch:
        insertar_batch(partes_batch, stats)

    # 4. Resumen final
    print("\n" + "="*70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*70)
    print(f"\n📊 RESUMEN:")
    print(f"   Total procesados:        {stats['total']}")
    print(f"   Insertados correctamente: {stats['insertados']}")
    print(f"   Duplicados (omitidos):   {stats['duplicados']}")
    print(f"   Sin máquina asignada:    {stats['sin_maquina']}")
    print(f"   Errores:                 {stats['errores']}")
    print(f"\n💡 RECOMENDACIONES:")
    print(f"   Detectadas automáticamente: {stats['recomendaciones_detectadas']}")
    print(f"   Pendientes de revisar:      {stats['recomendaciones_detectadas']}")

    print("\n📌 Próximos pasos:")
    print("   1. Revisar recomendaciones detectadas en la interfaz web")
    print("   2. Crear oportunidades de facturación desde recomendaciones")
    print("   3. Ver análisis de datos en Dashboard")

    return stats

def insertar_batch(partes_batch, stats):
    """Inserta un lote de partes"""
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/partes_trabajo",
        json=partes_batch,
        headers=HEADERS
    )

    if response.status_code == 201:
        insertados = len(response.json())
        stats["insertados"] += insertados
    elif response.status_code == 200:
        # Algunos ya existían (ignore-duplicates)
        stats["insertados"] += len(partes_batch)
        # Los duplicados ya están manejados por Supabase
    else:
        # Error
        print(f"\n   ✗ ERROR insertando lote: {response.text}")
        stats["errores"] += len(partes_batch)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/importar_partes.py <archivo_excel>")
        print("\nEjemplo:")
        print("  python scripts/importar_partes.py partes_2024_2025.xlsx")
        print("\n📌 Nota: Ejecutar primero importar_cartera.py para crear las máquinas")
        sys.exit(1)

    excel_path = sys.argv[1]
    resultado = importar_partes(excel_path)
