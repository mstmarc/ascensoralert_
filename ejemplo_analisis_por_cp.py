#!/usr/bin/env python3
"""
Ejemplo de análisis de zonas calientes usando CÓDIGOS POSTALES
Ideal para segmentación comercial y análisis masivo de mercado

Uso:
    python ejemplo_analisis_por_cp.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zonas_calientes import DetectorZonasCalientes
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("\n" + "="*70)
print("ANÁLISIS DE ZONAS CALIENTES POR CÓDIGO POSTAL")
print("Las Palmas de Gran Canaria")
print("="*70 + "\n")

# Inicializar detector
detector = DetectorZonasCalientes()

# Códigos postales principales de Las Palmas de Gran Canaria
CODIGOS_POSTALES_LPGC = {
    "35001": "Triana - Centro",
    "35002": "Vegueta - Casco Antiguo",
    "35003": "Arenales - Ciudad Jardín",
    "35004": "Altavista - Escaleritas",
    "35005": "Vegueta (zona baja)",
    "35006": "Puerto - La Luz",
    "35007": "Zona Portuaria",
    "35008": "Schamann - La Paterna",
    "35009": "Tafira",
    "35010": "Guanarteme - Alcaravaneras",
    "35011": "Santa Catalina - Tomás Morales",
    "35012": "Ciudad Alta - Miller",
    "35013": "Escaleritas - Altavista Sur",
    "35014": "San José - El Lasso",
    "35015": "Jinámar - Polígonos",
    "35016": "Tamaraceite",
    "35017": "San Lorenzo - Tenoya",
    "35018": "Hoya de la Plata - Casa Ayala",
    "35019": "Siete Palmas"
}

print("📋 CÓDIGOS POSTALES DISPONIBLES:\n")
for cp, zona in sorted(CODIGOS_POSTALES_LPGC.items()):
    print(f"   {cp} - {zona}")

print("\n" + "="*70)
print("EJEMPLO 1: Análisis de código postal único")
print("="*70 + "\n")

# Analizar CP 35001 (Triana - Centro histórico comercial)
print("Analizando CP 35001 (Triana - Centro)...\n")

zona_triana = detector.analizar_zona_por_codigo_postal(
    codigo_postal="35001",
    ciudad="Las Palmas de Gran Canaria",
    grid_size=5,
    solo_residencial=True
)

# Mostrar reporte
print(detector.generar_reporte_texto(zona_triana))

# Exportar
os.makedirs('resultados', exist_ok=True)
detector.exportar_zona_json(zona_triana, 'resultados/cp_35001_analisis.json')
detector.exportar_zona_csv(zona_triana, 'resultados/cp_35001_edificios.csv')

print("\n" + "="*70)
print("EJEMPLO 2: Comparación de múltiples códigos postales")
print("="*70 + "\n")

# Seleccionar CPs de zonas clave para análisis
cps_prioritarios = [
    "35001",  # Triana (centro comercial)
    "35002",  # Vegueta (casco antiguo)
    "35010",  # Guanarteme (residencial)
    "35012",  # Miller (residencial antiguo)
]

print(f"Analizando {len(cps_prioritarios)} códigos postales...\n")

zonas = []
for i, cp in enumerate(cps_prioritarios, 1):
    nombre_zona = CODIGOS_POSTALES_LPGC.get(cp, "Desconocida")
    print(f"[{i}/{len(cps_prioritarios)}] Analizando CP {cp} ({nombre_zona})...")

    zona = detector.analizar_zona_por_codigo_postal(
        codigo_postal=cp,
        ciudad="Las Palmas de Gran Canaria",
        grid_size=4  # Más rápido para análisis múltiple
    )
    zonas.append(zona)
    print(f"    ✓ Encontrados {zona.total_edificios} edificios\n")

# Comparar y rankear
zonas_ordenadas = detector.comparar_zonas(zonas)

print("\n" + "="*70)
print("🏆 RANKING DE CÓDIGOS POSTALES POR POTENCIAL")
print("="*70 + "\n")

for i, zona in enumerate(zonas_ordenadas, 1):
    cp = zona.nombre.replace("CP ", "")
    nombre = CODIGOS_POSTALES_LPGC.get(cp, "Desconocida")

    print(f"{i}. {zona.nombre} - {nombre}")
    print(f"   Score Total:        {zona.score_total:.2f}")
    print(f"   Densidad:           {zona.densidad_oportunidades:.2f}")
    print(f"   Total edificios:    {zona.total_edificios}")
    print(f"   Muy antiguos:       {zona.edificios_muy_antiguos} ({zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)")
    print(f"   Antiguos:           {zona.edificios_antiguos} ({zona.edificios_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)")
    print()

# Exportar comparación
import json
from datetime import datetime

comparacion = {
    'fecha_analisis': datetime.now().isoformat(),
    'criterio': 'Código Postal',
    'ciudad': 'Las Palmas de Gran Canaria',
    'zonas_analizadas': len(zonas_ordenadas),
    'ranking': [
        {
            'posicion': i,
            'codigo_postal': z.nombre.replace("CP ", ""),
            'nombre_zona': CODIGOS_POSTALES_LPGC.get(z.nombre.replace("CP ", ""), "Desconocida"),
            'score_total': round(z.score_total, 2),
            'densidad_oportunidades': round(z.densidad_oportunidades, 2),
            'total_edificios': z.total_edificios,
            'edificios_muy_antiguos': z.edificios_muy_antiguos,
            'edificios_antiguos': z.edificios_antiguos,
            'porcentaje_muy_antiguos': round(z.edificios_muy_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0, 1),
            'centro': {
                'latitud': z.latitud_centro,
                'longitud': z.longitud_centro
            }
        }
        for i, z in enumerate(zonas_ordenadas, 1)
    ]
}

with open('resultados/ranking_codigos_postales.json', 'w', encoding='utf-8') as f:
    json.dump(comparacion, f, ensure_ascii=False, indent=2)

print("="*70)
print("✅ ANÁLISIS COMPLETADO")
print("="*70)
print("\nArchivos generados en carpeta 'resultados/':")
print("  • cp_35001_analisis.json - Análisis detallado CP 35001")
print("  • cp_35001_edificios.csv - Listado de edificios CP 35001")
print("  • ranking_codigos_postales.json - Comparación de todos los CPs")
print()

print("\n💡 PRÓXIMOS PASOS SUGERIDOS:\n")
print("1. Revisar el ranking para identificar CPs con mayor potencial")
print("2. Analizar CPs adicionales con el mismo método")
print("3. Exportar edificios prioritarios a CRM/base de datos")
print("4. Planificar campañas comerciales por zonas calientes")
print()

print("="*70)
print("¿Quieres analizar todos los CPs de Las Palmas?")
print("Ejecuta: python scripts/analisis_masivo_codigos_postales.py")
print("="*70 + "\n")
