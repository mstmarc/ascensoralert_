"""
Servicio de geocodificación de direcciones
Convierte direcciones a coordenadas geográficas usando Nominatim (OpenStreetMap)
"""

import requests
import logging
from typing import Optional, Dict, List
from time import sleep

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Cliente para geocodificar direcciones usando Nominatim (OpenStreetMap).
    Servicio gratuito que no requiere API key.
    """

    BASE_URL = "https://nominatim.openstreetmap.org/search"
    REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

    def __init__(self, user_agent: str = "AscensorAlert/1.0"):
        """
        Inicializa el servicio de geocodificación.

        Args:
            user_agent: Identificador de la aplicación (requerido por Nominatim)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })
        # Nominatim requiere máximo 1 petición por segundo
        self.min_delay = 1.0

    def geocodificar_direccion(
        self,
        direccion: str,
        ciudad: str = "Las Palmas de Gran Canaria",
        pais: str = "España"
    ) -> Optional[Dict]:
        """
        Convierte una dirección en coordenadas GPS.

        Args:
            direccion: Dirección a geocodificar (calle y número)
            ciudad: Ciudad donde se encuentra la dirección
            pais: País (por defecto España)

        Returns:
            Dict con coordenadas y datos o None si no se encuentra
            {
                'latitud': float,
                'longitud': float,
                'direccion_completa': str,
                'tipo': str,
                'importancia': float
            }
        """
        # Construir query completa
        query = f"{direccion}, {ciudad}, {pais}"

        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }

        try:
            logger.info(f"Geocodificando: {query}")

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if not results or len(results) == 0:
                logger.warning(f"No se encontraron resultados para: {query}")
                return None

            # Tomar el primer resultado
            result = results[0]

            coords = {
                'latitud': float(result['lat']),
                'longitud': float(result['lon']),
                'direccion_completa': result.get('display_name', query),
                'tipo': result.get('type', 'unknown'),
                'importancia': float(result.get('importance', 0)),
                'bbox': result.get('boundingbox', [])  # [lat_min, lat_max, lon_min, lon_max]
            }

            logger.info(f"Geocodificado: {direccion} -> ({coords['latitud']}, {coords['longitud']})")

            # Respetar rate limit
            sleep(self.min_delay)

            return coords

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en geocodificación: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando respuesta de geocodificación: {e}")
            return None

    def geocodificar_multiple(
        self,
        direcciones: List[str],
        ciudad: str = "Las Palmas de Gran Canaria"
    ) -> List[Dict]:
        """
        Geocodifica múltiples direcciones.

        Args:
            direcciones: Lista de direcciones a geocodificar
            ciudad: Ciudad donde se encuentran las direcciones

        Returns:
            Lista de diccionarios con coordenadas (None para direcciones no encontradas)
        """
        resultados = []

        for direccion in direcciones:
            coords = self.geocodificar_direccion(direccion, ciudad=ciudad)
            if coords:
                coords['direccion_original'] = direccion
                resultados.append(coords)
            else:
                logger.warning(f"No se pudo geocodificar: {direccion}")

        logger.info(f"Geocodificadas {len(resultados)} de {len(direcciones)} direcciones")
        return resultados

    def geocodificar_zona(
        self,
        zona: str,
        ciudad: str = "Las Palmas de Gran Canaria"
    ) -> Optional[Dict]:
        """
        Obtiene coordenadas y bounding box de una zona (barrio, distrito, etc.).

        Args:
            zona: Nombre de la zona (ej: "Casablanca III", "Vegueta")
            ciudad: Ciudad

        Returns:
            Dict con coordenadas del centro y bounding box
            {
                'latitud': float,
                'longitud': float,
                'bbox': [lat_min, lat_max, lon_min, lon_max],
                'area_km2': float
            }
        """
        query = f"{zona}, {ciudad}, España"

        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }

        try:
            logger.info(f"Geocodificando zona: {query}")

            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                logger.warning(f"No se encontró la zona: {query}")
                return None

            result = results[0]
            bbox = result.get('boundingbox', [])

            if len(bbox) != 4:
                logger.warning(f"Bounding box inválido para zona: {zona}")
                return None

            # bbox formato: [lat_min, lat_max, lon_min, lon_max]
            lat_min, lat_max, lon_min, lon_max = [float(x) for x in bbox]

            # Calcular centro
            lat_centro = (lat_min + lat_max) / 2
            lon_centro = (lon_min + lon_max) / 2

            # Calcular área aproximada en km²
            # Fórmula aproximada para latitudes medias
            import math
            lat_diff = lat_max - lat_min
            lon_diff = lon_max - lon_min
            lat_km = lat_diff * 111  # 1 grado latitud ≈ 111 km
            lon_km = lon_diff * 111 * math.cos(math.radians(lat_centro))
            area_km2 = lat_km * lon_km

            zona_data = {
                'latitud': lat_centro,
                'longitud': lon_centro,
                'bbox': bbox,
                'area_km2': area_km2,
                'nombre': result.get('display_name', zona)
            }

            logger.info(f"Zona geocodificada: {zona} -> centro ({lat_centro}, {lon_centro}), área {area_km2:.2f} km²")

            sleep(self.min_delay)
            return zona_data

        except Exception as e:
            logger.error(f"Error geocodificando zona: {e}")
            return None

    def obtener_direccion_por_coordenadas(
        self,
        latitud: float,
        longitud: float
    ) -> Optional[str]:
        """
        Geocodificación inversa: obtiene dirección a partir de coordenadas.

        Args:
            latitud: Latitud en WGS84
            longitud: Longitud en WGS84

        Returns:
            Dirección completa como string o None
        """
        params = {
            'lat': str(latitud),
            'lon': str(longitud),
            'format': 'json',
            'addressdetails': 1
        }

        try:
            response = self.session.get(
                self.REVERSE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            direccion = result.get('display_name', '')

            sleep(self.min_delay)
            return direccion

        except Exception as e:
            logger.error(f"Error en geocodificación inversa: {e}")
            return None
