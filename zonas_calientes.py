"""
Módulo de detección de zonas calientes para modernización de ascensores
Utiliza antigüedad de edificios del Catastro como proxy de oportunidades
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
import math

from catastro_service import CatastroService
from geocoding_service import GeocodingService

logger = logging.getLogger(__name__)


@dataclass
class EdificioCandidato:
    """Representa un edificio candidato a modernización"""
    referencia_catastral: str
    direccion: str
    latitud: float
    longitud: float
    anio_construccion: Optional[int]
    antiguedad: Optional[int]
    uso: str
    superficie: float
    score_modernizacion: float = 0.0
    categoria_antiguedad: str = ""


@dataclass
class ZonaCaliente:
    """Representa una zona identificada como caliente para modernización"""
    nombre: str
    latitud_centro: float
    longitud_centro: float
    radio_metros: int
    edificios: List[EdificioCandidato] = field(default_factory=list)
    total_edificios: int = 0
    edificios_muy_antiguos: int = 0
    edificios_antiguos: int = 0
    edificios_modernos: int = 0
    densidad_oportunidades: float = 0.0
    score_total: float = 0.0
    stats_por_decada: Dict[str, int] = field(default_factory=dict)


class DetectorZonasCalientes:
    """
    Detector de zonas con alta concentración de edificios candidatos
    a modernización de ascensores basándose en antigüedad.
    """

    # Rangos de antigüedad para clasificación
    ANIO_ACTUAL = datetime.now().year
    UMBRAL_MUY_ANTIGUO = 50  # Más de 50 años
    UMBRAL_ANTIGUO = 30      # Entre 30-50 años
    UMBRAL_MODERNO = 30      # Menos de 30 años

    # Pesos para scoring
    PESO_MUY_ANTIGUO = 3.0
    PESO_ANTIGUO = 2.0
    PESO_MODERNO = 0.5

    def __init__(
        self,
        catastro_service: Optional[CatastroService] = None,
        geocoding_service: Optional[GeocodingService] = None
    ):
        """
        Inicializa el detector de zonas calientes.

        Args:
            catastro_service: Servicio de Catastro (se crea uno nuevo si no se proporciona)
            geocoding_service: Servicio de geocodificación (se crea uno nuevo si no se proporciona)
        """
        self.catastro = catastro_service or CatastroService()
        self.geocoding = geocoding_service or GeocodingService()

    def analizar_zona_por_direcciones(
        self,
        direcciones_semilla: List[str],
        ciudad: str = "Las Palmas de Gran Canaria",
        radio_metros: int = 500,
        grid_size: int = 5,
        solo_residencial: bool = True
    ) -> ZonaCaliente:
        """
        Analiza una zona a partir de direcciones semilla.

        Args:
            direcciones_semilla: Lista de direcciones de referencia en la zona
            ciudad: Ciudad donde se encuentran
            radio_metros: Radio de búsqueda alrededor de cada dirección
            grid_size: Tamaño de la cuadrícula de muestreo
            solo_residencial: Si True, filtra solo inmuebles residenciales

        Returns:
            ZonaCaliente con el análisis completo
        """
        logger.info(f"Iniciando análisis de zona con {len(direcciones_semilla)} direcciones semilla")

        # 1. Geocodificar direcciones semilla
        coordenadas = self.geocoding.geocodificar_multiple(direcciones_semilla, ciudad=ciudad)

        if not coordenadas:
            logger.error("No se pudo geocodificar ninguna dirección semilla")
            return self._crear_zona_vacia("Zona sin datos", 0, 0, radio_metros)

        # 2. Calcular centro de la zona (promedio de coordenadas)
        lat_centro = sum(c['latitud'] for c in coordenadas) / len(coordenadas)
        lon_centro = sum(c['longitud'] for c in coordenadas) / len(coordenadas)

        logger.info(f"Centro de zona calculado: ({lat_centro}, {lon_centro})")

        # 3. Obtener datos de Catastro en el área
        todos_inmuebles = []
        for coords in coordenadas:
            inmuebles = self.catastro.obtener_datos_area(
                lat_centro=coords['latitud'],
                lon_centro=coords['longitud'],
                radio_metros=radio_metros,
                grid_size=grid_size
            )
            todos_inmuebles.extend(inmuebles)

        # Eliminar duplicados por referencia catastral
        inmuebles_unicos = {
            inm['referencia_catastral']: inm
            for inm in todos_inmuebles
            if inm.get('referencia_catastral')
        }

        logger.info(f"Total de inmuebles únicos encontrados: {len(inmuebles_unicos)}")

        # 4. Filtrar y clasificar edificios
        edificios_candidatos = []
        for datos in inmuebles_unicos.values():
            # Filtrar residenciales si se requiere
            if solo_residencial and not self._es_residencial(datos.get('uso', '')):
                continue

            # Calcular antigüedad
            anio_construccion = datos.get('anio_construccion')
            if anio_construccion:
                antiguedad = self.ANIO_ACTUAL - anio_construccion
                categoria = self._clasificar_antiguedad(antiguedad)
                score = self._calcular_score_modernizacion(antiguedad)
            else:
                antiguedad = None
                categoria = "Sin datos"
                score = 0.0

            edificio = EdificioCandidato(
                referencia_catastral=datos.get('referencia_catastral', ''),
                direccion=datos.get('direccion', ''),
                latitud=datos.get('latitud', 0),
                longitud=datos.get('longitud', 0),
                anio_construccion=anio_construccion,
                antiguedad=antiguedad,
                uso=datos.get('uso', ''),
                superficie=datos.get('superficie', 0),
                score_modernizacion=score,
                categoria_antiguedad=categoria
            )
            edificios_candidatos.append(edificio)

        # 5. Generar estadísticas
        zona = self._crear_zona_caliente(
            nombre=f"Zona {ciudad}",
            lat_centro=lat_centro,
            lon_centro=lon_centro,
            radio_metros=radio_metros,
            edificios=edificios_candidatos
        )

        logger.info(f"Análisis completado: {zona.total_edificios} edificios, "
                   f"densidad de oportunidades: {zona.densidad_oportunidades:.2f}")

        return zona

    def analizar_zona_por_nombre(
        self,
        nombre_zona: str,
        ciudad: str = "Las Palmas de Gran Canaria",
        grid_size: int = 7,
        solo_residencial: bool = True
    ) -> ZonaCaliente:
        """
        Analiza una zona por su nombre (barrio, distrito, etc.).

        Args:
            nombre_zona: Nombre de la zona (ej: "Casablanca III")
            ciudad: Ciudad
            grid_size: Tamaño de cuadrícula de muestreo
            solo_residencial: Si True, filtra solo inmuebles residenciales

        Returns:
            ZonaCaliente con el análisis
        """
        logger.info(f"Analizando zona por nombre: {nombre_zona}, {ciudad}")

        # Geocodificar zona para obtener bbox
        zona_data = self.geocoding.geocodificar_zona(nombre_zona, ciudad=ciudad)

        if not zona_data:
            logger.error(f"No se pudo geocodificar la zona: {nombre_zona}")
            return self._crear_zona_vacia(nombre_zona, 0, 0, 0)

        # Calcular radio aproximado del bbox
        bbox = zona_data['bbox']  # [lat_min, lat_max, lon_min, lon_max]
        lat_min, lat_max, lon_min, lon_max = [float(x) for x in bbox]

        # Radio en metros (mitad del lado mayor del bbox)
        lat_diff_km = (lat_max - lat_min) * 111
        lon_diff_km = (lon_max - lon_min) * 111 * math.cos(math.radians(zona_data['latitud']))
        radio_metros = int(max(lat_diff_km, lon_diff_km) * 1000 / 2)

        logger.info(f"Área de zona: {zona_data['area_km2']:.2f} km², radio aproximado: {radio_metros}m")

        # Obtener datos del área
        inmuebles = self.catastro.obtener_datos_area(
            lat_centro=zona_data['latitud'],
            lon_centro=zona_data['longitud'],
            radio_metros=radio_metros,
            grid_size=grid_size
        )

        # Procesar edificios
        edificios_candidatos = []
        for datos in inmuebles:
            if solo_residencial and not self._es_residencial(datos.get('uso', '')):
                continue

            anio_construccion = datos.get('anio_construccion')
            if anio_construccion:
                antiguedad = self.ANIO_ACTUAL - anio_construccion
                categoria = self._clasificar_antiguedad(antiguedad)
                score = self._calcular_score_modernizacion(antiguedad)
            else:
                antiguedad = None
                categoria = "Sin datos"
                score = 0.0

            edificio = EdificioCandidato(
                referencia_catastral=datos.get('referencia_catastral', ''),
                direccion=datos.get('direccion', ''),
                latitud=datos.get('latitud', 0),
                longitud=datos.get('longitud', 0),
                anio_construccion=anio_construccion,
                antiguedad=antiguedad,
                uso=datos.get('uso', ''),
                superficie=datos.get('superficie', 0),
                score_modernizacion=score,
                categoria_antiguedad=categoria
            )
            edificios_candidatos.append(edificio)

        # Generar zona caliente
        zona = self._crear_zona_caliente(
            nombre=nombre_zona,
            lat_centro=zona_data['latitud'],
            lon_centro=zona_data['longitud'],
            radio_metros=radio_metros,
            edificios=edificios_candidatos
        )

        return zona

    def comparar_zonas(self, zonas: List[ZonaCaliente]) -> List[ZonaCaliente]:
        """
        Compara y ordena zonas por potencial de modernización.

        Args:
            zonas: Lista de zonas analizadas

        Returns:
            Lista de zonas ordenadas por score (mayor a menor)
        """
        return sorted(zonas, key=lambda z: z.score_total, reverse=True)

    def _clasificar_antiguedad(self, antiguedad: int) -> str:
        """Clasifica un edificio según su antigüedad"""
        if antiguedad >= self.UMBRAL_MUY_ANTIGUO:
            return "Muy antiguo (>50 años)"
        elif antiguedad >= self.UMBRAL_ANTIGUO:
            return "Antiguo (30-50 años)"
        else:
            return "Moderno (<30 años)"

    def _calcular_score_modernizacion(self, antiguedad: int) -> float:
        """
        Calcula score de oportunidad de modernización.
        Más antiguo = mayor score.
        """
        if antiguedad >= self.UMBRAL_MUY_ANTIGUO:
            return self.PESO_MUY_ANTIGUO
        elif antiguedad >= self.UMBRAL_ANTIGUO:
            return self.PESO_ANTIGUO
        else:
            return self.PESO_MODERNO

    def _es_residencial(self, uso: str) -> bool:
        """Determina si un inmueble es residencial"""
        uso_lower = uso.lower()
        residencial_keywords = ['resid', 'viviend', 'almacen', '1-', '2-']
        return any(kw in uso_lower for kw in residencial_keywords)

    def _crear_zona_caliente(
        self,
        nombre: str,
        lat_centro: float,
        lon_centro: float,
        radio_metros: int,
        edificios: List[EdificioCandidato]
    ) -> ZonaCaliente:
        """Crea objeto ZonaCaliente con todas las estadísticas calculadas"""

        # Contar por categoría
        muy_antiguos = sum(1 for e in edificios if e.antiguedad and e.antiguedad >= self.UMBRAL_MUY_ANTIGUO)
        antiguos = sum(1 for e in edificios if e.antiguedad and self.UMBRAL_ANTIGUO <= e.antiguedad < self.UMBRAL_MUY_ANTIGUO)
        modernos = sum(1 for e in edificios if e.antiguedad and e.antiguedad < self.UMBRAL_ANTIGUO)

        # Score total de la zona
        score_total = sum(e.score_modernizacion for e in edificios)

        # Densidad de oportunidades (score promedio por edificio)
        densidad = score_total / len(edificios) if edificios else 0.0

        # Estadísticas por década
        stats_decada = defaultdict(int)
        for e in edificios:
            if e.anio_construccion:
                decada = (e.anio_construccion // 10) * 10
                stats_decada[f"{decada}s"] += 1

        zona = ZonaCaliente(
            nombre=nombre,
            latitud_centro=lat_centro,
            longitud_centro=lon_centro,
            radio_metros=radio_metros,
            edificios=edificios,
            total_edificios=len(edificios),
            edificios_muy_antiguos=muy_antiguos,
            edificios_antiguos=antiguos,
            edificios_modernos=modernos,
            densidad_oportunidades=densidad,
            score_total=score_total,
            stats_por_decada=dict(sorted(stats_decada.items()))
        )

        return zona

    def _crear_zona_vacia(self, nombre: str, lat: float, lon: float, radio: int) -> ZonaCaliente:
        """Crea una zona vacía (sin datos)"""
        return ZonaCaliente(
            nombre=nombre,
            latitud_centro=lat,
            longitud_centro=lon,
            radio_metros=radio,
            edificios=[],
            total_edificios=0,
            edificios_muy_antiguos=0,
            edificios_antiguos=0,
            edificios_modernos=0,
            densidad_oportunidades=0.0,
            score_total=0.0,
            stats_por_decada={}
        )

    def exportar_zona_json(self, zona: ZonaCaliente, ruta_archivo: str):
        """
        Exporta una zona caliente a formato JSON.

        Args:
            zona: ZonaCaliente a exportar
            ruta_archivo: Ruta del archivo de salida
        """
        data = {
            'nombre': zona.nombre,
            'centro': {
                'latitud': zona.latitud_centro,
                'longitud': zona.longitud_centro
            },
            'radio_metros': zona.radio_metros,
            'resumen': {
                'total_edificios': zona.total_edificios,
                'edificios_muy_antiguos': zona.edificios_muy_antiguos,
                'edificios_antiguos': zona.edificios_antiguos,
                'edificios_modernos': zona.edificios_modernos,
                'densidad_oportunidades': round(zona.densidad_oportunidades, 2),
                'score_total': round(zona.score_total, 2),
                'stats_por_decada': zona.stats_por_decada
            },
            'edificios': [
                {
                    'referencia_catastral': e.referencia_catastral,
                    'direccion': e.direccion,
                    'latitud': e.latitud,
                    'longitud': e.longitud,
                    'anio_construccion': e.anio_construccion,
                    'antiguedad': e.antiguedad,
                    'categoria': e.categoria_antiguedad,
                    'score': round(e.score_modernizacion, 2),
                    'uso': e.uso,
                    'superficie': e.superficie
                }
                for e in zona.edificios
            ],
            'fecha_analisis': datetime.now().isoformat()
        }

        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Zona exportada a: {ruta_archivo}")

    def exportar_zona_csv(self, zona: ZonaCaliente, ruta_archivo: str):
        """
        Exporta edificios de una zona a CSV.

        Args:
            zona: ZonaCaliente a exportar
            ruta_archivo: Ruta del archivo CSV de salida
        """
        import csv

        with open(ruta_archivo, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)

            # Cabeceras
            writer.writerow([
                'Referencia Catastral',
                'Dirección',
                'Latitud',
                'Longitud',
                'Año Construcción',
                'Antigüedad (años)',
                'Categoría',
                'Score Modernización',
                'Uso',
                'Superficie (m²)'
            ])

            # Datos
            for e in zona.edificios:
                writer.writerow([
                    e.referencia_catastral,
                    e.direccion,
                    e.latitud,
                    e.longitud,
                    e.anio_construccion or 'N/A',
                    e.antiguedad or 'N/A',
                    e.categoria_antiguedad,
                    round(e.score_modernizacion, 2),
                    e.uso,
                    e.superficie
                ])

        logger.info(f"Datos exportados a CSV: {ruta_archivo}")

    def generar_reporte_texto(self, zona: ZonaCaliente) -> str:
        """
        Genera un reporte de texto legible de la zona.

        Args:
            zona: ZonaCaliente a reportar

        Returns:
            String con el reporte formateado
        """
        linea = "=" * 70

        reporte = f"""
{linea}
ANÁLISIS DE ZONA CALIENTE - MODERNIZACIÓN DE ASCENSORES
{linea}

Zona: {zona.nombre}
Centro: {zona.latitud_centro:.6f}, {zona.longitud_centro:.6f}
Radio de análisis: {zona.radio_metros} metros

{linea}
RESUMEN EJECUTIVO
{linea}

Total de edificios analizados: {zona.total_edificios}

Distribución por antigüedad:
  • Muy antiguos (>50 años):     {zona.edificios_muy_antiguos:>4} edificios ({zona.edificios_muy_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)
  • Antiguos (30-50 años):       {zona.edificios_antiguos:>4} edificios ({zona.edificios_antiguos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)
  • Modernos (<30 años):         {zona.edificios_modernos:>4} edificios ({zona.edificios_modernos/zona.total_edificios*100 if zona.total_edificios > 0 else 0:.1f}%)

Score total de oportunidades: {zona.score_total:.2f}
Densidad de oportunidades: {zona.densidad_oportunidades:.2f} (promedio por edificio)

{linea}
DISTRIBUCIÓN POR DÉCADA DE CONSTRUCCIÓN
{linea}

"""
        for decada, cantidad in zona.stats_por_decada.items():
            barra = "█" * int(cantidad / max(zona.stats_por_decada.values()) * 40)
            reporte += f"{decada}: {barra} {cantidad}\n"

        reporte += f"""
{linea}
TOP 10 EDIFICIOS PRIORITARIOS
{linea}

"""
        # Ordenar edificios por score
        top_edificios = sorted(zona.edificios, key=lambda e: e.score_modernizacion, reverse=True)[:10]

        for i, edificio in enumerate(top_edificios, 1):
            reporte += f"{i:2}. {edificio.direccion}\n"
            reporte += f"    Año: {edificio.anio_construccion or 'N/A'} | "
            reporte += f"Antigüedad: {edificio.antiguedad or 'N/A'} años | "
            reporte += f"Score: {edificio.score_modernizacion:.2f}\n"
            reporte += f"    Ref. Catastral: {edificio.referencia_catastral}\n\n"

        reporte += f"{linea}\n"
        reporte += f"Fecha de análisis: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        reporte += f"{linea}\n"

        return reporte
