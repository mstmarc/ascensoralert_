import pandas as pd
import requests
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================

SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ ERROR: Variable de entorno SUPABASE_KEY no configurada")
    print("Configúrala con: export SUPABASE_KEY='tu_clave_aqui'")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def validar_fecha(fecha_str):
    """Convierte fecha a formato correcto o devuelve None"""
    if pd.isna(fecha_str) or fecha_str == "" or fecha_str == "-":
        return None
    
    try:
        if isinstance(fecha_str, datetime):
            return fecha_str.strftime('%Y-%m-%d')
        
        fecha_str = str(fecha_str).strip()
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        
        for formato in formatos:
            try:
                fecha_obj = datetime.strptime(fecha_str, formato)
                return fecha_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        return None
    except:
        return None


def verificar_comunidad_existe(cliente_id):
    """Verifica si existe la comunidad en la base de datos"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/clientes?id=eq.{cliente_id}&select=id,nombre_cliente",
        headers=HEADERS
    )
    
    if response.status_code == 200 and response.json():
        return True, response.json()[0].get('nombre_cliente', 'Sin nombre')
    return False, None


# ============================================
# EXPORTAR EQUIPOS
# ============================================

def exportar_equipos():
    """Descarga todos los equipos existentes y los guarda en Excel"""
    
    print("=" * 60)
    print("📥 EXPORTANDO EQUIPOS DESDE SUPABASE")
    print("=" * 60)
    print()
    
    # Obtener todos los equipos con información de la comunidad
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/equipos?select=*,clientes(nombre_cliente,direccion,localidad)",
            headers=HEADERS
        )
        
        if response.status_code != 200:
            print(f"❌ Error al obtener equipos: {response.status_code}")
            print(response.text)
            return
        
        equipos = response.json()
        print(f"✅ {len(equipos)} equipos encontrados")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    # Preparar datos para Excel
    datos_excel = []
    
    for equipo in equipos:
        # Obtener nombre de la comunidad
        cliente_info = equipo.get('clientes', {})
        if isinstance(cliente_info, list) and cliente_info:
            cliente_info = cliente_info[0]
        
        nombre_cliente = cliente_info.get('nombre_cliente', 'Sin nombre') if cliente_info else 'Sin nombre'
        direccion = cliente_info.get('direccion', '') if cliente_info else ''
        localidad = cliente_info.get('localidad', '') if cliente_info else ''
        
        # Formatear fechas
        ipo_proxima = equipo.get('ipo_proxima', '')
        fecha_contrato = equipo.get('fecha_vencimiento_contrato', '')
        
        datos_excel.append({
            'id_equipo': equipo.get('id'),  # IMPORTANTE: ID para actualizar
            'id_comunidad': equipo.get('cliente_id'),
            'nombre_comunidad': nombre_cliente,
            'direccion': direccion,
            'localidad': localidad,
            'tipo_equipo': equipo.get('tipo_equipo', ''),
            'identificacion': equipo.get('identificacion', ''),
            'rae': equipo.get('rae', ''),
            'ipo_proxima': ipo_proxima if ipo_proxima else '',
            'fecha_vencimiento_contrato': fecha_contrato if fecha_contrato else '',
            'observaciones': equipo.get('descripcion', '')
        })
    
    # Crear DataFrame y guardar en Excel
    df = pd.DataFrame(datos_excel)
    
    # Ordenar por comunidad y tipo de equipo
    df = df.sort_values(['nombre_comunidad', 'tipo_equipo'])
    
    nombre_archivo = f"equipos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    try:
        df.to_excel(nombre_archivo, index=False, sheet_name='Equipos')
        print(f"✅ Archivo creado: {nombre_archivo}")
        print()
        print("📝 INSTRUCCIONES:")
        print("  1. Abre el archivo Excel")
        print("  2. Completa o modifica los datos que necesites")
        print("  3. Para AÑADIR equipos nuevos: añade filas dejando 'id_equipo' vacío")
        print("  4. Para MODIFICAR equipos: mantén el 'id_equipo' existente")
        print("  5. Guarda el archivo")
        print("  6. Ejecuta: python gestionar_ascensores.py importar <nombre_archivo.xlsx>")
        print()
        print("⚠️  IMPORTANTE: NO borres la columna 'id_equipo'")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error al crear archivo Excel: {e}")


# ============================================
# IMPORTAR EQUIPOS
# ============================================

def importar_equipos(archivo_excel):
    """Lee el Excel e importa/actualiza los equipos en Supabase"""
    
    print("=" * 60)
    print("📤 IMPORTANDO EQUIPOS A SUPABASE")
    print("=" * 60)
    print()
    
    # Leer Excel
    try:
        df = pd.read_excel(archivo_excel)
        print(f"✅ Archivo Excel leído correctamente")
        print(f"📊 Total de filas encontradas: {len(df)}")
        print()
    except FileNotFoundError:
        print(f"❌ ERROR: No se encuentra el archivo '{archivo_excel}'")
        return
    except Exception as e:
        print(f"❌ ERROR al leer Excel: {e}")
        return
    
    # Validar columnas requeridas
    columnas_requeridas = ['id_comunidad', 'tipo_equipo']
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if columnas_faltantes:
        print(f"❌ ERROR: Faltan columnas requeridas: {', '.join(columnas_faltantes)}")
        return
    
    # Procesar cada fila
    insertados = 0
    actualizados = 0
    errores = 0
    errores_detalle = []
    
    for idx, row in df.iterrows():
        fila_num = idx + 2  # +2 porque Excel empieza en 1 y tiene encabezado
        
        # Determinar si es actualización o inserción
        id_equipo = row.get('id_equipo')
        es_actualizacion = not pd.isna(id_equipo) and str(id_equipo).strip() != ''
        
        # Validar cliente_id
        cliente_id = row.get('id_comunidad')
        
        if pd.isna(cliente_id):
            errores += 1
            errores_detalle.append(f"Fila {fila_num}: ID de comunidad vacío")
            continue
        
        try:
            cliente_id = int(cliente_id)
        except:
            errores += 1
            errores_detalle.append(f"Fila {fila_num}: ID de comunidad inválido ({cliente_id})")
            continue
        
        # Verificar que la comunidad existe
        existe, nombre_comunidad = verificar_comunidad_existe(cliente_id)
        if not existe:
            errores += 1
            errores_detalle.append(f"Fila {fila_num}: Comunidad ID {cliente_id} no existe")
            continue
        
        # Validar tipo_equipo
        tipo_equipo = row.get('tipo_equipo')
        if pd.isna(tipo_equipo) or str(tipo_equipo).strip() == "":
            errores += 1
            errores_detalle.append(f"Fila {fila_num}: Tipo de equipo vacío")
            continue
        
        # Preparar datos del equipo
        equipo_data = {
            "cliente_id": cliente_id,
            "tipo_equipo": str(tipo_equipo).strip(),
            "identificacion": str(row.get('identificacion', '')).strip() if not pd.isna(row.get('identificacion')) else None,
            "rae": str(row.get('rae', '')).strip() if not pd.isna(row.get('rae')) else None,
            "descripcion": str(row.get('observaciones', '')).strip() if not pd.isna(row.get('observaciones')) else None,
            "ipo_proxima": validar_fecha(row.get('ipo_proxima')),
            "fecha_vencimiento_contrato": validar_fecha(row.get('fecha_vencimiento_contrato'))
        }
        
        # Limpiar valores vacíos pero mantener None explícitos para fechas
        equipo_data_limpio = {}
        for k, v in equipo_data.items():
            if k in ['ipo_proxima', 'fecha_vencimiento_contrato']:
                # Para fechas, siempre incluir (puede ser None para borrar)
                equipo_data_limpio[k] = v
            elif v not in ['', 'nan']:
                # Para otros campos, solo incluir si tienen valor
                equipo_data_limpio[k] = v
        
        # Insertar o actualizar en Supabase
        try:
            if es_actualizacion:
                # ACTUALIZAR equipo existente
                try:
                    id_equipo_int = int(id_equipo)
                except:
                    errores += 1
                    errores_detalle.append(f"Fila {fila_num}: ID de equipo inválido ({id_equipo})")
                    continue
                
                response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/equipos?id=eq.{id_equipo_int}",
                    json=equipo_data_limpio,
                    headers=HEADERS
                )
                
                if response.status_code in [200, 204]:
                    actualizados += 1
                    print(f"🔄 Fila {fila_num}: Equipo ID {id_equipo_int} actualizado en '{nombre_comunidad}'")
                else:
                    errores += 1
                    errores_detalle.append(f"Fila {fila_num}: Error API UPDATE - {response.text[:100]}")
                    print(f"❌ Fila {fila_num}: Error al actualizar equipo ID {id_equipo_int}")
            
            else:
                # INSERTAR equipo nuevo
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/equipos",
                    json=equipo_data_limpio,
                    headers=HEADERS
                )
                
                if response.status_code in [200, 201]:
                    insertados += 1
                    print(f"✅ Fila {fila_num}: Equipo nuevo añadido a '{nombre_comunidad}'")
                else:
                    errores += 1
                    errores_detalle.append(f"Fila {fila_num}: Error API INSERT - {response.text[:100]}")
                    print(f"❌ Fila {fila_num}: Error al insertar equipo")
        
        except Exception as e:
            errores += 1
            errores_detalle.append(f"Fila {fila_num}: Excepción - {str(e)}")
            print(f"❌ Fila {fila_num}: Error de conexión")
    
    # Resumen final
    print()
    print("=" * 60)
    print("📊 RESUMEN DE IMPORTACIÓN")
    print("=" * 60)
    print(f"✅ Equipos nuevos insertados: {insertados}")
    print(f"🔄 Equipos actualizados: {actualizados}")
    print(f"❌ Errores: {errores}")
    print()
    
    if errores > 0:
        print("⚠️  DETALLE DE ERRORES:")
        print("-" * 60)
        for error in errores_detalle[:10]:  # Mostrar máximo 10 errores
            print(f"  • {error}")
        if len(errores_detalle) > 10:
            print(f"  ... y {len(errores_detalle) - 10} errores más")
        print()
    
    print("✨ Importación completada")
    print("=" * 60)


# ============================================
# MENÚ PRINCIPAL
# ============================================

def mostrar_ayuda():
    print("=" * 60)
    print("🔧 GESTOR DE ASCENSORES - AscensorAlert")
    print("=" * 60)
    print()
    print("USO:")
    print("  python gestionar_ascensores.py exportar")
    print("      → Descarga todos los equipos a Excel")
    print()
    print("  python gestionar_ascensores.py importar <archivo.xlsx>")
    print("      → Importa/actualiza equipos desde Excel")
    print()
    print("EJEMPLOS:")
    print("  python gestionar_ascensores.py exportar")
    print("  python gestionar_ascensores.py importar equipos_export_20251013_120000.xlsx")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        mostrar_ayuda()
        exit(0)
    
    comando = sys.argv[1].lower()
    
    if comando == "exportar":
        exportar_equipos()
    
    elif comando == "importar":
        if len(sys.argv) < 3:
            print("❌ ERROR: Falta el nombre del archivo Excel")
            print("Uso: python gestionar_ascensores.py importar <archivo.xlsx>")
            exit(1)
        
        archivo = sys.argv[2]
        importar_equipos(archivo)
    
    else:
        print(f"❌ Comando desconocido: {comando}")
        print()
        mostrar_ayuda()
