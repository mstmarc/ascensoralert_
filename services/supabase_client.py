"""
Cliente simplificado para operaciones con Supabase
"""
import requests
from config import config


class SupabaseClient:
    """Cliente para interactuar con Supabase"""

    def __init__(self):
        self.url = config.SUPABASE_URL
        self.headers = config.HEADERS
        self.storage_headers = config.STORAGE_HEADERS

    def get(self, table, select="*", filters=None, order=None, limit=None, timeout=10):
        """
        Realiza una consulta GET a una tabla

        Args:
            table: Nombre de la tabla
            select: Campos a seleccionar (default: *)
            filters: Diccionario de filtros {campo: valor}
            order: Ordenamiento (ej: "created_at.desc")
            limit: Límite de resultados
            timeout: Timeout en segundos

        Returns:
            Lista de resultados o None si hay error
        """
        url = f"{self.url}/rest/v1/{table}?select={select}"

        if filters:
            for key, value in filters.items():
                url += f"&{key}={value}"

        if order:
            url += f"&order={order}"

        if limit:
            url += f"&limit={limit}"

        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            if response.ok:
                return response.json()
            else:
                print(f"⚠️ Error en GET {table}: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Excepción en GET {table}: {type(e).__name__}: {str(e)}")
            return None

    def get_by_id(self, table, record_id, select="*"):
        """
        Obtiene un registro por ID

        Args:
            table: Nombre de la tabla
            record_id: ID del registro
            select: Campos a seleccionar

        Returns:
            Diccionario con el registro o None si no existe
        """
        result = self.get(table, select=select, filters={"id": f"eq.{record_id}"})
        if result and len(result) > 0:
            return result[0]
        return None

    def post(self, table, data, timeout=10):
        """
        Crea un nuevo registro

        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a insertar
            timeout: Timeout en segundos

        Returns:
            Registro creado o None si hay error
        """
        url = f"{self.url}/rest/v1/{table}"

        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=timeout)
            if response.ok:
                result = response.json()
                return result[0] if result else None
            else:
                print(f"⚠️ Error en POST {table}: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Excepción en POST {table}: {type(e).__name__}: {str(e)}")
            return None

    def patch(self, table, record_id, data, timeout=10):
        """
        Actualiza un registro existente

        Args:
            table: Nombre de la tabla
            record_id: ID del registro a actualizar
            data: Diccionario con los campos a actualizar
            timeout: Timeout en segundos

        Returns:
            Registro actualizado o None si hay error
        """
        url = f"{self.url}/rest/v1/{table}?id=eq.{record_id}"

        try:
            response = requests.patch(url, json=data, headers=self.headers, timeout=timeout)
            if response.ok:
                result = response.json()
                return result[0] if result else None
            else:
                print(f"⚠️ Error en PATCH {table}: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Excepción en PATCH {table}: {type(e).__name__}: {str(e)}")
            return None

    def delete(self, table, record_id, timeout=10):
        """
        Elimina un registro

        Args:
            table: Nombre de la tabla
            record_id: ID del registro a eliminar
            timeout: Timeout en segundos

        Returns:
            True si se eliminó correctamente, False si hubo error
        """
        url = f"{self.url}/rest/v1/{table}?id=eq.{record_id}"

        try:
            response = requests.delete(url, headers=self.headers, timeout=timeout)
            if response.ok:
                return True
            else:
                print(f"⚠️ Error en DELETE {table}: {response.status_code}")
                print(f"📄 Respuesta: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Excepción en DELETE {table}: {type(e).__name__}: {str(e)}")
            return False

    def count(self, table, filters=None, timeout=10):
        """
        Cuenta registros en una tabla

        Args:
            table: Nombre de la tabla
            filters: Diccionario de filtros opcionales
            timeout: Timeout en segundos

        Returns:
            Número de registros o 0 si hay error
        """
        result = self.get(table, select="id", filters=filters, timeout=timeout)
        return len(result) if result else 0


# Instancia global del cliente
db = SupabaseClient()
