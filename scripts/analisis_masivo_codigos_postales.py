#!/usr/bin/env python3
"""
Script de análisis masivo de TODOS los códigos postales de Las Palmas de Gran Canaria
Genera un ranking completo de zonas por potencial de modernización

ADVERTENCIA: Este script puede tardar 30-60 minutos en completarse debido a:
- Rate limiting de APIs públicas (Nominatim, Catastro)
- Análisis de 19 códigos postales diferentes
- Consultas extensivas a servicios externos

Uso:
    python scripts/analisis_masivo_codigos_postales.py

    # Para análisis más rápido (menor precisión):
    python scripts/analisis_masivo_codigos_postales.py --rapido
"""

import sys
import os
import argparse
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zonas_calientes import DetectorZonasCalientes
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Todos los códigos postales de Las Palmas de Gran Canaria
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


def analisis_masivo(modo_rapido: bool = False):
    """
    Ejecuta análisis de todos los códigos postales de Las Palmas.

    Args:
        modo_rapido: Si True, usa grid_size menor para análisis más rápido
    """
    print("\n" + "="*80)
    print("ANÁLISIS MASIVO DE CÓDIGOS POSTALES - LAS PALMAS DE GRAN CANARIA")
    print("="*80)

    grid_size = 3 if modo_rapido else 5
    modo = "RÁPIDO (menor precisión)" if modo_rapido else "COMPLETO (mayor precisión)"

    print(f"\nModo: {modo}")
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Códigos postales a analizar: {len(CODIGOS_POSTALES_LPGC)}")
    print(f"Tiempo estimado: {'15-25 minutos' if modo_rapido else '30-60 minutos'}")

    # Confirmar ejecución
    print("\n⚠️  Este proceso realizará múltiples consultas a APIs públicas.")
    print("    Por favor, respeta los términos de uso de los servicios.")

    respuesta = input("\n¿Desea continuar? (s/n): ").strip().lower()
    if respuesta != 's':
        print("\nAnálisis cancelado.")
        return

    print("\n" + "="*80)
    print("INICIANDO ANÁLISIS...")
    print("="*80 + "\n")

    inicio = datetime.now()
    detector = DetectorZonasCalientes()

    zonas = []
    errores = []

    for i, (cp, nombre) in enumerate(sorted(CODIGOS_POSTALES_LPGC.items()), 1):
        print(f"\n[{i}/{len(CODIGOS_POSTALES_LPGC)}] Analizando CP {cp} - {nombre}")
        print("-" * 80)

        try:
            zona = detector.analizar_zona_por_codigo_postal(
                codigo_postal=cp,
                ciudad="Las Palmas de Gran Canaria",
                grid_size=grid_size,
                solo_residencial=True
            )

            zonas.append(zona)

            # Mostrar resumen
            print(f"    ✓ Edificios encontrados: {zona.total_edificios}")
            print(f"    ✓ Muy antiguos (>50 años): {zona.edificios_muy_antiguos}")
            print(f"    ✓ Score total: {zona.score_total:.2f}")
            print(f"    ✓ Densidad: {zona.densidad_oportunidades:.2f}")

        except Exception as e:
            logger.error(f"Error analizando CP {cp}: {e}")
            errores.append({'cp': cp, 'nombre': nombre, 'error': str(e)})
            print(f"    ✗ ERROR: {e}")

    fin = datetime.now()
    duracion = (fin - inicio).total_seconds() / 60

    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO")
    print("="*80)
    print(f"\nDuración: {duracion:.1f} minutos")
    print(f"Zonas analizadas: {len(zonas)}/{len(CODIGOS_POSTALES_LPGC)}")
    print(f"Errores: {len(errores)}")

    if errores:
        print("\n⚠️  Códigos postales con errores:")
        for error in errores:
            print(f"   • CP {error['cp']} ({error['nombre']}): {error['error']}")

    # Generar ranking
    print("\n" + "="*80)
    print("🏆 RANKING DE CÓDIGOS POSTALES")
    print("="*80 + "\n")

    zonas_ordenadas = detector.comparar_zonas(zonas)

    # Mostrar top 10
    print("TOP 10 ZONAS CON MAYOR POTENCIAL:\n")
    for i, zona in enumerate(zonas_ordenadas[:10], 1):
        cp = zona.nombre.replace("CP ", "")
        nombre = CODIGOS_POSTALES_LPGC.get(cp, "Desconocida")

        pct_muy_antiguos = zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0

        print(f"{i:2}. CP {cp} - {nombre}")
        print(f"    Score: {zona.score_total:6.2f} | Densidad: {zona.densidad_oportunidades:4.2f} | "
              f"Edificios: {zona.total_edificios:3} | Muy antiguos: {pct_muy_antiguos:5.1f}%")

    # Exportar resultados completos
    print("\n" + "="*80)
    print("EXPORTANDO RESULTADOS...")
    print("="*80 + "\n")

    os.makedirs('resultados', exist_ok=True)

    # Generar JSON completo
    resultado_completo = {
        'metadata': {
            'fecha_analisis': inicio.isoformat(),
            'duracion_minutos': round(duracion, 2),
            'modo': 'rapido' if modo_rapido else 'completo',
            'grid_size': grid_size,
            'ciudad': 'Las Palmas de Gran Canaria',
            'total_cps_analizados': len(zonas),
            'total_cps_errores': len(errores)
        },
        'ranking': [
            {
                'posicion': i,
                'codigo_postal': z.nombre.replace("CP ", ""),
                'nombre_zona': CODIGOS_POSTALES_LPGC.get(z.nombre.replace("CP ", ""), "Desconocida"),
                'metricas': {
                    'score_total': round(z.score_total, 2),
                    'densidad_oportunidades': round(z.densidad_oportunidades, 2),
                    'total_edificios': z.total_edificios,
                    'edificios_muy_antiguos': z.edificios_muy_antiguos,
                    'edificios_antiguos': z.edificios_antiguos,
                    'edificios_modernos': z.edificios_modernos,
                    'porcentaje_muy_antiguos': round(z.edificios_muy_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0, 1),
                    'porcentaje_antiguos': round(z.edificios_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0, 1)
                },
                'ubicacion': {
                    'latitud': z.latitud_centro,
                    'longitud': z.longitud_centro,
                    'radio_metros': z.radio_metros
                },
                'estadisticas_decada': z.stats_por_decada
            }
            for i, z in enumerate(zonas_ordenadas, 1)
        ],
        'errores': errores if errores else []
    }

    # Guardar JSON principal
    with open('resultados/analisis_masivo_cps_lpgc.json', 'w', encoding='utf-8') as f:
        json.dump(resultado_completo, f, ensure_ascii=False, indent=2)
    print("✓ JSON completo: resultados/analisis_masivo_cps_lpgc.json")

    # Generar CSV resumen
    import csv
    with open('resultados/ranking_cps_resumen.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Posición',
            'Código Postal',
            'Nombre Zona',
            'Score Total',
            'Densidad',
            'Total Edificios',
            'Muy Antiguos',
            '% Muy Antiguos',
            'Antiguos',
            '% Antiguos',
            'Modernos',
            'Latitud',
            'Longitud'
        ])

        for i, z in enumerate(zonas_ordenadas, 1):
            cp = z.nombre.replace("CP ", "")
            nombre = CODIGOS_POSTALES_LPGC.get(cp, "Desconocida")
            pct_muy_antiguos = z.edificios_muy_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0
            pct_antiguos = z.edificios_antiguos/z.total_edificios*100 if z.total_edificios > 0 else 0

            writer.writerow([
                i,
                cp,
                nombre,
                round(z.score_total, 2),
                round(z.densidad_oportunidades, 2),
                z.total_edificios,
                z.edificios_muy_antiguos,
                round(pct_muy_antiguos, 1),
                z.edificios_antiguos,
                round(pct_antiguos, 1),
                z.edificios_modernos,
                z.latitud_centro,
                z.longitud_centro
            ])

    print("✓ CSV resumen: resultados/ranking_cps_resumen.csv")

    # Exportar detalle de cada zona
    for zona in zonas:
        cp = zona.nombre.replace("CP ", "")
        detector.exportar_zona_json(zona, f'resultados/detalle_cp_{cp}.json')
        detector.exportar_zona_csv(zona, f'resultados/edificios_cp_{cp}.csv')

    print(f"✓ Exportados {len(zonas)} archivos JSON detallados")
    print(f"✓ Exportados {len(zonas)} archivos CSV con edificios")

    # Generar reporte de texto
    with open('resultados/reporte_analisis_masivo.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ANÁLISIS MASIVO DE CÓDIGOS POSTALES\n")
        f.write("Las Palmas de Gran Canaria\n")
        f.write("="*80 + "\n\n")
        f.write(f"Fecha: {inicio.strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"Duración: {duracion:.1f} minutos\n")
        f.write(f"Modo: {modo}\n")
        f.write(f"Códigos postales analizados: {len(zonas)}\n\n")

        f.write("="*80 + "\n")
        f.write("RANKING COMPLETO\n")
        f.write("="*80 + "\n\n")

        for i, zona in enumerate(zonas_ordenadas, 1):
            cp = zona.nombre.replace("CP ", "")
            nombre = CODIGOS_POSTALES_LPGC.get(cp, "Desconocida")
            pct_muy_antiguos = zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0

            f.write(f"{i:2}. CP {cp} - {nombre}\n")
            f.write(f"    Score Total: {zona.score_total:6.2f}\n")
            f.write(f"    Densidad de Oportunidades: {zona.densidad_oportunidades:4.2f}\n")
            f.write(f"    Total Edificios: {zona.total_edificios}\n")
            f.write(f"    Muy Antiguos (>50 años): {zona.edificios_muy_antiguos} ({pct_muy_antiguos:.1f}%)\n")
            f.write(f"    Antiguos (30-50 años): {zona.edificios_antiguos}\n")
            f.write(f"    Modernos (<30 años): {zona.edificios_modernos}\n")
            f.write("\n")

    print("✓ Reporte de texto: resultados/reporte_analisis_masivo.txt")

    print("\n" + "="*80)
    print("✅ ANÁLISIS MASIVO COMPLETADO EXITOSAMENTE")
    print("="*80)
    print("\nTodos los resultados están disponibles en la carpeta 'resultados/'")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Análisis masivo de códigos postales de Las Palmas de Gran Canaria"
    )
    parser.add_argument(
        '--rapido',
        action='store_true',
        help='Modo rápido (menor precisión, grid_size=3)'
    )

    args = parser.parse_args()

    try:
        analisis_masivo(modo_rapido=args.rapido)
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario.\n")
        sys.exit(1)
