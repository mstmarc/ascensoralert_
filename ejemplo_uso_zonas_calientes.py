#!/usr/bin/env python3
"""
Ejemplo rápido de uso del módulo de zonas calientes
Ejecutar: python ejemplo_uso_zonas_calientes.py
"""

from zonas_calientes import DetectorZonasCalientes

# Inicializar detector
detector = DetectorZonasCalientes()

print("\n" + "="*70)
print("EJEMPLO: Análisis de zona en Las Palmas de Gran Canaria")
print("="*70 + "\n")

# Caso de uso 1: Analizar zona por direcciones semilla
print("📍 Analizando zona Casablanca III por direcciones semilla...\n")

zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=[
        "Calle Aconcagua",
        "Calle Amazonas"
    ],
    ciudad="Las Palmas de Gran Canaria",
    radio_metros=400,
    grid_size=5,
    solo_residencial=True
)

# Mostrar reporte
print(detector.generar_reporte_texto(zona))

# Exportar resultados
import os
os.makedirs('resultados', exist_ok=True)

detector.exportar_zona_json(zona, 'resultados/ejemplo_analisis.json')
detector.exportar_zona_csv(zona, 'resultados/ejemplo_edificios.csv')

print("\n✅ Resultados exportados a carpeta 'resultados/'")
print("   - ejemplo_analisis.json (datos completos)")
print("   - ejemplo_edificios.csv (tabla de edificios)\n")
