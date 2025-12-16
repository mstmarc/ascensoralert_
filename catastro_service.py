"""
Servicio de integración con la API de Catastro español
Permite consultar datos catastrales por coordenadas y referencia catastral
"""

import requests
import xmltodict
import logging
from typing import Dict, Optional, List
from time import sleep
from datetime import datetime

logger = logging.getLogger(__name__)


class CatastroService:
    """
    Cliente para interactuar con los servicios web del Catastro español.
    Utiliza el servicio OVC (Oficina Virtual del Catastro) para consultas por coordenadas.
    """

    BASE_URL = "http://ovc.catastro.meh.es/ovcservweb"
    COORD_ENDPOINT = f"{BASE_URL}/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_CPMRC"
    DNPRC_ENDPOINT = f"{BASE_URL}/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"

    # Sistema de referencia: EPSG:4326 (WGS84) - Lat/Lon estándar GPS
    SRS = "EPSG:4326"

    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Inicializa el servicio de Catastro.

        Args:
            max_retries: Número máximo de reintentos en caso de error
            retry_delay: Tiempo de espera entre reintentos (segundos)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AscensorAlert/1.0 (Modernization Analysis System)'
        })

    def obtener_datos_por_coordenadas(self, latitud: float, longitud: float) -> Optional[Dict]:
        """
        Obtiene datos catastrales de un inmueble a partir de coordenadas GPS.

        Args:
            latitud: Latitud en formato WGS84 (ej: 28.124167)
            longitud: Longitud en formato WGS84 (ej: -15.437778)

        Returns:
            Dict con datos del inmueble o None si no se encuentra
            {
                'referencia_catastral': str,
                'direccion': str,
                'codigo_postal': str,
                'uso': str,
                'anio_construccion': int,
                'superficie': float,
                'latitud': float,
                'longitud': float
            }
        """
        params = {
            'SRS': self.SRS,
            'Coordenada_X': str(longitud),  # OVC usa X=longitud, Y=latitud
            'Coordenada_Y': str(latitud)
        }

        for intento in range(self.max_retries):
            try:
                logger.info(f"Consultando Catastro: lat={latitud}, lon={longitud} (intento {intento + 1})")

                response = self.session.get(
                    self.COORD_ENDPOINT,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()

                # Parsear XML a diccionario
                data = xmltodict.parse(response.content)

                # Extraer datos del inmueble
                resultado = self._parsear_respuesta_coordenadas(data)

                if resultado:
                    logger.info(f"Datos obtenidos: {resultado.get('direccion', 'N/A')}, "
                               f"año {resultado.get('anio_construccion', 'N/A')}")
                    return resultado
                else:
                    logger.warning(f"No se encontraron datos para coordenadas: {latitud}, {longitud}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.warning(f"Error en consulta (intento {intento + 1}/{self.max_retries}): {e}")
                if intento < self.max_retries - 1:
                    sleep(self.retry_delay * (2 ** intento))  # Exponential backoff
                else:
                    logger.error(f"Error final consultando Catastro: {e}")
                    return None
            except Exception as e:
                logger.error(f"Error parseando respuesta de Catastro: {e}")
                return None

        return None

    def obtener_datos_por_referencia(self, referencia_catastral: str) -> Optional[Dict]:
        """
        Obtiene datos detallados de un inmueble por su referencia catastral.

        Args:
            referencia_catastral: Referencia catastral del inmueble (14 o 20 caracteres)

        Returns:
            Dict con datos detallados del inmueble o None si no se encuentra
        """
        params = {
            'Provincia': '',
            'Municipio': '',
            'RC': referencia_catastral
        }

        try:
            logger.info(f"Consultando Catastro por referencia: {referencia_catastral}")

            response = self.session.get(
                self.DNPRC_ENDPOINT,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = xmltodict.parse(response.content)
            return self._parsear_respuesta_referencia(data)

        except Exception as e:
            logger.error(f"Error consultando referencia catastral: {e}")
            return None

    def _parsear_respuesta_coordenadas(self, data: Dict) -> Optional[Dict]:
        """
        Parsea la respuesta XML del servicio de coordenadas.

        Args:
            data: Diccionario con el XML parseado

        Returns:
            Dict con datos normalizados o None
        """
        try:
            # Navegar por la estructura XML del Catastro
            consulta = data.get('consulta_coordenadas', {})

            # Verificar si hay error
            if 'err' in consulta or 'lerr' in consulta:
                return None

            coordenadas = consulta.get('coordenadas', {})
            coord = coordenadas.get('coord', {})

            # Datos del inmueble
            pc = coord.get('pc', {})
            if not pc:
                return None

            pc1 = pc.get('pc1', {}) if isinstance(pc.get('pc1'), dict) else {}
            pc2 = pc.get('pc2', {}) if isinstance(pc.get('pc2'), dict) else {}

            # Dirección
            ldt = coord.get('ldt', '')
            direccion = ldt if ldt else "Dirección no disponible"

            # Referencia catastral
            referencia = pc1.get('@rc', '') or pc2.get('@rc', '')

            # Año de construcción (puede estar en diferentes campos)
            anio = None
            if 'bi' in coord:
                bi = coord['bi']
                if isinstance(bi, dict):
                    anio = bi.get('@ant', None)

            # Intentar obtener de pc1 o pc2
            if not anio:
                anio = pc1.get('@ant', None) or pc2.get('@ant', None)

            # Convertir año a entero
            try:
                anio_construccion = int(anio) if anio else None
            except (ValueError, TypeError):
                anio_construccion = None

            # Uso del inmueble
            uso = pc1.get('@use', '') or pc2.get('@use', 'Desconocido')

            # Superficie
            superficie_str = pc1.get('@sfc', '0') or pc2.get('@sfc', '0')
            try:
                superficie = float(superficie_str)
            except (ValueError, TypeError):
                superficie = 0.0

            # Coordenadas
            geo = coord.get('geo', {})
            xcen = geo.get('xcen', '')
            ycen = geo.get('ycen', '')

            try:
                longitud = float(xcen) if xcen else None
                latitud = float(ycen) if ycen else None
            except (ValueError, TypeError):
                longitud = None
                latitud = None

            return {
                'referencia_catastral': referencia,
                'direccion': direccion,
                'codigo_postal': '',  # No siempre disponible en respuesta de coordenadas
                'uso': uso,
                'anio_construccion': anio_construccion,
                'superficie': superficie,
                'latitud': latitud,
                'longitud': longitud,
                'fecha_consulta': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parseando respuesta de coordenadas: {e}")
            return None

    def _parsear_respuesta_referencia(self, data: Dict) -> Optional[Dict]:
        """
        Parsea la respuesta XML del servicio de referencia catastral (más detallado).

        Args:
            data: Diccionario con el XML parseado

        Returns:
            Dict con datos normalizados o None
        """
        try:
            # Implementación similar a _parsear_respuesta_coordenadas
            # pero con estructura de respuesta DNPRC
            consulta = data.get('consulta_dnp', {})

            if 'err' in consulta:
                return None

            bico = consulta.get('bico', {})
            if not bico:
                return None

            bi = bico.get('bi', {})
            if isinstance(bi, list):
                bi = bi[0] if bi else {}

            # Extraer datos
            idbi = bi.get('idbi', {})
            rc = idbi.get('rc', '')

            dt = bi.get('dt', {})
            locs = dt.get('locs', {})
            lors = locs.get('lors', {})

            # Dirección
            if isinstance(lors, dict):
                lorus = lors.get('lorus', {})
                direccion = f"{lorus.get('loint', {}).get('nv', '')} {lorus.get('loint', {}).get('nm', '')}"
            else:
                direccion = "Dirección no disponible"

            # Año de construcción
            anio = bi.get('@ant', None)
            try:
                anio_construccion = int(anio) if anio else None
            except (ValueError, TypeError):
                anio_construccion = None

            return {
                'referencia_catastral': rc,
                'direccion': direccion.strip(),
                'anio_construccion': anio_construccion,
                'fecha_consulta': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parseando respuesta de referencia: {e}")
            return None

    def obtener_datos_area(
        self,
        lat_centro: float,
        lon_centro: float,
        radio_metros: int = 500,
        grid_size: int = 5
    ) -> List[Dict]:
        """
        Obtiene datos de múltiples inmuebles en un área alrededor de un punto central.
        Utiliza una cuadrícula para muestrear el área.

        Args:
            lat_centro: Latitud del centro
            lon_centro: Longitud del centro
            radio_metros: Radio del área a consultar en metros
            grid_size: Número de puntos por lado de la cuadrícula (total = grid_size²)

        Returns:
            Lista de diccionarios con datos de inmuebles encontrados
        """
        # Conversión aproximada de metros a grados (válido para latitudes medias)
        # 1 grado de latitud ≈ 111 km
        # 1 grado de longitud ≈ 111 km * cos(latitud)
        import math

        delta_lat = (radio_metros / 111000)  # grados de latitud
        delta_lon = (radio_metros / (111000 * math.cos(math.radians(lat_centro))))  # grados de longitud

        inmuebles = []
        inmuebles_unicos = set()  # Para evitar duplicados por referencia catastral

        logger.info(f"Escaneando área: centro ({lat_centro}, {lon_centro}), radio {radio_metros}m, grid {grid_size}x{grid_size}")

        # Generar cuadrícula de puntos
        for i in range(grid_size):
            for j in range(grid_size):
                # Calcular coordenadas del punto de la cuadrícula
                lat_offset = delta_lat * (i - grid_size / 2) * 2 / grid_size
                lon_offset = delta_lon * (j - grid_size / 2) * 2 / grid_size

                lat_punto = lat_centro + lat_offset
                lon_punto = lon_centro + lon_offset

                # Consultar Catastro en este punto
                datos = self.obtener_datos_por_coordenadas(lat_punto, lon_punto)

                if datos and datos.get('referencia_catastral'):
                    ref = datos['referencia_catastral']
                    if ref not in inmuebles_unicos:
                        inmuebles_unicos.add(ref)
                        inmuebles.append(datos)
                        logger.debug(f"Inmueble encontrado: {datos['direccion']} ({datos.get('anio_construccion', 'N/A')})")

                # Pequeña pausa para no saturar el servicio
                sleep(0.5)

        logger.info(f"Total de inmuebles únicos encontrados: {len(inmuebles)}")
        return inmuebles
