#!/usr/bin/env python3
"""
Análisis de zonas calientes por CALLES específicas
Ideal para analizar calles comerciales principales y áreas alrededor

Uso:
    python ejemplo_analisis_por_calle.py
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
print("ANÁLISIS DE ZONAS CALIENTES POR CALLE")
print("Las Palmas de Gran Canaria")
print("="*70 + "\n")

# Inicializar detector
detector = DetectorZonasCalientes()

# Calles principales de Las Palmas de Gran Canaria
CALLES_PRINCIPALES = {
    "comerciales": [
        "Calle Mayor de Triana",
        "Calle Cano",
        "Calle Mesa y López"
    ],
    "historicas": [
        "Calle Pelota",
        "Calle Obispo Codina",
        "Calle Los Balcones"
    ],
    "principales": [
        "Calle León y Castillo",
        "Avenida Marítima del Norte",
        "Calle Juan de Quesada"
    ]
}

print("📋 CALLES DISPONIBLES:\n")
print("🛍️  COMERCIALES:")
for calle in CALLES_PRINCIPALES["comerciales"]:
    print(f"   • {calle}")

print("\n🏛️  HISTÓRICAS (Vegueta/Triana):")
for calle in CALLES_PRINCIPALES["historicas"]:
    print(f"   • {calle}")

print("\n🚗 PRINCIPALES:")
for calle in CALLES_PRINCIPALES["principales"]:
    print(f"   • {calle}")

print("\n" + "="*70)
print("EJEMPLO 1: Análisis de calle única")
print("="*70 + "\n")

# Analizar Calle Mayor de Triana (emblemática calle comercial)
print("Analizando Calle Mayor de Triana...\n")

zona_triana = detector.analizar_zona_por_calle(
    nombre_calle="Calle Mayor de Triana",
    ciudad="Las Palmas de Gran Canaria",
    radio_metros=300,  # 300m alrededor de la calle
    solo_residencial=True
)

# Mostrar reporte
print(detector.generar_reporte_texto(zona_triana))

# Exportar
os.makedirs('resultados', exist_ok=True)
detector.exportar_zona_json(zona_triana, 'resultados/calle_triana_analisis.json')
detector.exportar_zona_csv(zona_triana, 'resultados/calle_triana_edificios.csv')

print("\n" + "="*70)
print("EJEMPLO 2: Comparación de calles comerciales")
print("="*70 + "\n")

# Comparar 3 calles comerciales principales
calles_comerciales = [
    "Calle Mayor de Triana",
    "Calle Mesa y López",
    "Calle León y Castillo"
]

print(f"Analizando {len(calles_comerciales)} calles comerciales...\n")

zonas = []
for i, calle in enumerate(calles_comerciales, 1):
    print(f"[{i}/{len(calles_comerciales)}] Analizando {calle}...")

    zona = detector.analizar_zona_por_calle(
        nombre_calle=calle,
        ciudad="Las Palmas de Gran Canaria",
        radio_metros=250,
        grid_size=4  # Más rápido para comparación
    )
    zonas.append(zona)
    print(f"    ✓ Encontrados {zona.total_edificios} edificios\n")

# Comparar y rankear
zonas_ordenadas = detector.comparar_zonas(zonas)

print("\n" + "="*70)
print("🏆 RANKING DE CALLES POR POTENCIAL")
print("="*70 + "\n")

for i, zona in enumerate(zonas_ordenadas, 1):
    pct_muy_antiguos = zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0

    print(f"{i}. {zona.nombre}")
    print(f"   Score Total:        {zona.score_total:.2f}")
    print(f"   Densidad:           {zona.densidad_oportunidades:.2f}")
    print(f"   Total edificios:    {zona.total_edificios}")
    print(f"   Muy antiguos:       {zona.edificios_muy_antiguos} ({pct_muy_antiguos:.1f}%)")
    print(f"   Antiguos:           {zona.edificios_antiguos}")
    print()

# Exportar comparación
import json
from datetime import datetime

comparacion = {
    'fecha_analisis': datetime.now().isoformat(),
    'criterio': 'Calle',
    'ciudad': 'Las Palmas de Gran Canaria',
    'calles_analizadas': len(zonas_ordenadas),
    'ranking': [
        {
            'posicion': i,
            'calle': z.nombre,
            'metricas': {
                'score_total': round(z.score_total, 2),
                'densidad_oportunidades': round(z.densidad_oportunidades, 2),
                'total_edificios': z.total_edificios,
                'edificios_muy_antiguos': z.edificios_muy_antiguos,
                'edificios_antiguos': z.edificios_antiguos,
                'porcentaje_muy_antiguos': round(pct_muy_antiguos, 1)
            },
            'centro': {
                'latitud': z.latitud_centro,
                'longitud': z.longitud_centro
            }
        }
        for i, z in enumerate(zonas_ordenadas, 1)
        for pct_muy_antiguos in [z.edificios_muy_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0]
    ]
}

with open('resultados/ranking_calles.json', 'w', encoding='utf-8') as f:
    json.dump(comparacion, f, ensure_ascii=False, indent=2)

print("="*70)
print("✅ ANÁLISIS COMPLETADO")
print("="*70)
print("\nArchivos generados en carpeta 'resultados/':")
print("  • calle_triana_analisis.json - Análisis detallado Calle Triana")
print("  • calle_triana_edificios.csv - Listado de edificios Calle Triana")
print("  • ranking_calles.json - Comparación de calles comerciales")
print()

print("\n💡 CASOS DE USO:\n")
print("1. Análisis de calles comerciales principales")
print("2. Identificar edificios antiguos en calles específicas")
print("3. Prospección comercial calle por calle")
print("4. Comparar diferentes calles para priorizar campañas")
print()

print("="*70)
print("CALLES ADICIONALES SUGERIDAS PARA ANALIZAR:")
print("="*70)
print("\n🛍️  Comerciales:")
print("   • Calle Cano")
print("   • Calle Domingo Rivero")
print("   • Calle Galicia")
print("\n🏛️  Históricas:")
print("   • Calle Los Balcones (Vegueta)")
print("   • Calle Obispo Codina")
print("   • Calle Pelota")
print("\n🏢 Residenciales principales:")
print("   • Calle Aconcagua (Casablanca)")
print("   • Calle Amazonas (Casablanca)")
print("   • Calle Doctor Grau Bassas")
print()
