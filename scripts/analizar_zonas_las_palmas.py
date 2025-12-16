#!/usr/bin/env python3
"""
Script de ejemplo para analizar zonas calientes de modernización en Las Palmas de Gran Canaria

Uso:
    python scripts/analizar_zonas_las_palmas.py
"""

import sys
import os
import logging

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zonas_calientes import DetectorZonasCalientes, ZonaCaliente
from catastro_service import CatastroService
from geocoding_service import GeocodingService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analizar_casablanca_iii():
    """
    Analiza el barrio Casablanca III en Las Palmas
    Zona de ejemplo con direcciones semilla
    """
    logger.info("=" * 70)
    logger.info("ANÁLISIS: CASABLANCA III - LAS PALMAS DE GRAN CANARIA")
    logger.info("=" * 70)

    # Inicializar servicios
    detector = DetectorZonasCalientes()

    # Direcciones semilla en Casablanca III
    direcciones_semilla = [
        "Calle Aconcagua",
        "Calle Amazonas",
        "Calle Himalaya"
    ]

    # Analizar zona
    zona = detector.analizar_zona_por_direcciones(
        direcciones_semilla=direcciones_semilla,
        ciudad="Las Palmas de Gran Canaria",
        radio_metros=400,
        grid_size=5,
        solo_residencial=True
    )

    # Generar reporte
    reporte = detector.generar_reporte_texto(zona)
    print(reporte)

    # Exportar resultados
    os.makedirs('resultados', exist_ok=True)

    detector.exportar_zona_json(
        zona,
        'resultados/casablanca_iii_analisis.json'
    )

    detector.exportar_zona_csv(
        zona,
        'resultados/casablanca_iii_edificios.csv'
    )

    logger.info("Resultados exportados a carpeta 'resultados/'")

    return zona


def analizar_vegueta():
    """
    Analiza el barrio histórico de Vegueta
    Zona antigua con alto potencial de modernización
    """
    logger.info("=" * 70)
    logger.info("ANÁLISIS: VEGUETA - LAS PALMAS DE GRAN CANARIA")
    logger.info("=" * 70)

    detector = DetectorZonasCalientes()

    # Analizar por nombre de zona
    zona = detector.analizar_zona_por_nombre(
        nombre_zona="Vegueta",
        ciudad="Las Palmas de Gran Canaria",
        grid_size=6,
        solo_residencial=True
    )

    # Generar reporte
    reporte = detector.generar_reporte_texto(zona)
    print(reporte)

    # Exportar
    os.makedirs('resultados', exist_ok=True)

    detector.exportar_zona_json(
        zona,
        'resultados/vegueta_analisis.json'
    )

    detector.exportar_zona_csv(
        zona,
        'resultados/vegueta_edificios.csv'
    )

    return zona


def analizar_triana():
    """
    Analiza el barrio de Triana
    Zona comercial y residencial céntrica
    """
    logger.info("=" * 70)
    logger.info("ANÁLISIS: TRIANA - LAS PALMAS DE GRAN CANARIA")
    logger.info("=" * 70)

    detector = DetectorZonasCalientes()

    direcciones_semilla = [
        "Calle Mayor de Triana",
        "Calle Domingo Rivero",
        "Calle Pérez Galdós"
    ]

    zona = detector.analizar_zona_por_direcciones(
        direcciones_semilla=direcciones_semilla,
        ciudad="Las Palmas de Gran Canaria",
        radio_metros=300,
        grid_size=5,
        solo_residencial=True
    )

    reporte = detector.generar_reporte_texto(zona)
    print(reporte)

    os.makedirs('resultados', exist_ok=True)

    detector.exportar_zona_json(
        zona,
        'resultados/triana_analisis.json'
    )

    detector.exportar_zona_csv(
        zona,
        'resultados/triana_edificios.csv'
    )

    return zona


def comparar_multiples_zonas():
    """
    Analiza múltiples zonas y las compara
    """
    logger.info("=" * 70)
    logger.info("COMPARACIÓN DE MÚLTIPLES ZONAS")
    logger.info("=" * 70)

    detector = DetectorZonasCalientes()

    # Analizar varias zonas
    zonas = []

    # Zona 1: Barrio Ciudad Jardín
    logger.info("\n[1/4] Analizando Ciudad Jardín...")
    zona1 = detector.analizar_zona_por_nombre(
        "Ciudad Jardín",
        ciudad="Las Palmas de Gran Canaria",
        grid_size=4
    )
    zonas.append(zona1)

    # Zona 2: Miller Bajo
    logger.info("\n[2/4] Analizando Miller Bajo...")
    zona2 = detector.analizar_zona_por_nombre(
        "Miller Bajo",
        ciudad="Las Palmas de Gran Canaria",
        grid_size=4
    )
    zonas.append(zona2)

    # Zona 3: Schamann
    logger.info("\n[3/4] Analizando Schamann...")
    zona3 = detector.analizar_zona_por_nombre(
        "Schamann",
        ciudad="Las Palmas de Gran Canaria",
        grid_size=4
    )
    zonas.append(zona3)

    # Zona 4: Alcaravaneras
    logger.info("\n[4/4] Analizando Alcaravaneras...")
    zona4 = detector.analizar_zona_por_nombre(
        "Alcaravaneras",
        ciudad="Las Palmas de Gran Canaria",
        grid_size=4
    )
    zonas.append(zona4)

    # Comparar y ordenar
    zonas_ordenadas = detector.comparar_zonas(zonas)

    # Generar reporte comparativo
    print("\n")
    print("=" * 70)
    print("RANKING DE ZONAS POR POTENCIAL DE MODERNIZACIÓN")
    print("=" * 70)
    print()

    for i, zona in enumerate(zonas_ordenadas, 1):
        print(f"{i}. {zona.nombre}")
        print(f"   Score Total: {zona.score_total:.2f}")
        print(f"   Densidad: {zona.densidad_oportunidades:.2f}")
        print(f"   Edificios totales: {zona.total_edificios}")
        print(f"   Muy antiguos: {zona.edificios_muy_antiguos} ({zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)")
        print()

    # Exportar comparación
    os.makedirs('resultados', exist_ok=True)
    import json

    comparacion = {
        'fecha_analisis': datetime.now().isoformat(),
        'zonas': [
            {
                'ranking': i,
                'nombre': z.nombre,
                'score_total': round(z.score_total, 2),
                'densidad_oportunidades': round(z.densidad_oportunidades, 2),
                'total_edificios': z.total_edificios,
                'edificios_muy_antiguos': z.edificios_muy_antiguos,
                'edificios_antiguos': z.edificios_antiguos,
                'edificios_modernos': z.edificios_modernos,
                'centro': {
                    'latitud': z.latitud_centro,
                    'longitud': z.longitud_centro
                }
            }
            for i, z in enumerate(zonas_ordenadas, 1)
        ]
    }

    with open('resultados/comparacion_zonas.json', 'w', encoding='utf-8') as f:
        json.dump(comparacion, f, ensure_ascii=False, indent=2)

    logger.info("Comparación exportada a: resultados/comparacion_zonas.json")

    return zonas_ordenadas


def menu_principal():
    """Menú interactivo para seleccionar análisis"""
    print("\n" + "=" * 70)
    print("DETECTOR DE ZONAS CALIENTES - MODERNIZACIÓN DE ASCENSORES")
    print("Las Palmas de Gran Canaria")
    print("=" * 70)
    print("\nSeleccione una opción:\n")
    print("1. Analizar Casablanca III (por direcciones semilla)")
    print("2. Analizar Vegueta (por nombre de zona)")
    print("3. Analizar Triana (por direcciones semilla)")
    print("4. Comparar múltiples zonas")
    print("5. Analizar zona personalizada")
    print("0. Salir")
    print()

    try:
        opcion = input("Opción: ").strip()

        if opcion == "1":
            analizar_casablanca_iii()
        elif opcion == "2":
            analizar_vegueta()
        elif opcion == "3":
            analizar_triana()
        elif opcion == "4":
            comparar_multiples_zonas()
        elif opcion == "5":
            analizar_zona_personalizada()
        elif opcion == "0":
            print("\n¡Hasta pronto!\n")
            sys.exit(0)
        else:
            print("\nOpción no válida. Intente de nuevo.")
            menu_principal()

    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.\n")
        sys.exit(0)


def analizar_zona_personalizada():
    """Permite al usuario definir una zona personalizada"""
    print("\n" + "=" * 70)
    print("ANÁLISIS PERSONALIZADO")
    print("=" * 70)

    nombre_zona = input("\nNombre de la zona o barrio: ").strip()
    if not nombre_zona:
        print("Error: Debe introducir un nombre de zona")
        return

    ciudad = input("Ciudad [Las Palmas de Gran Canaria]: ").strip()
    if not ciudad:
        ciudad = "Las Palmas de Gran Canaria"

    detector = DetectorZonasCalientes()

    zona = detector.analizar_zona_por_nombre(
        nombre_zona=nombre_zona,
        ciudad=ciudad,
        grid_size=5,
        solo_residencial=True
    )

    reporte = detector.generar_reporte_texto(zona)
    print(reporte)

    # Preguntar si desea exportar
    exportar = input("\n¿Desea exportar los resultados? (s/n): ").strip().lower()
    if exportar == 's':
        os.makedirs('resultados', exist_ok=True)
        nombre_archivo = nombre_zona.lower().replace(' ', '_')

        detector.exportar_zona_json(
            zona,
            f'resultados/{nombre_archivo}_analisis.json'
        )

        detector.exportar_zona_csv(
            zona,
            f'resultados/{nombre_archivo}_edificios.csv'
        )

        print(f"\nResultados exportados a carpeta 'resultados/'")


if __name__ == "__main__":
    from datetime import datetime

    # Verificar si se pasa argumento específico
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()

        if comando == "casablanca":
            analizar_casablanca_iii()
        elif comando == "vegueta":
            analizar_vegueta()
        elif comando == "triana":
            analizar_triana()
        elif comando == "comparar":
            comparar_multiples_zonas()
        else:
            print(f"Comando no reconocido: {comando}")
            print("Comandos disponibles: casablanca, vegueta, triana, comparar")
    else:
        # Mostrar menú interactivo
        menu_principal()
