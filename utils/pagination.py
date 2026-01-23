"""
Helper para paginación consistente en toda la aplicación
"""
from flask import request


class Pagination:
    """Clase para manejar paginación de forma consistente"""

    def __init__(self, page=1, per_page=25, total=0):
        """
        Inicializa objeto de paginación

        Args:
            page: Número de página actual (base 1)
            per_page: Elementos por página
            total: Total de elementos (opcional)
        """
        self.page = max(1, page)  # Asegurar que page >= 1
        self.per_page = max(1, per_page)  # Asegurar que per_page >= 1
        self.total = max(0, total)

    @property
    def offset(self):
        """Calcula el offset para la query (base 0)"""
        return (self.page - 1) * self.per_page

    @property
    def limit(self):
        """Alias de per_page para consistencia con SQL"""
        return self.per_page

    @property
    def total_pages(self):
        """Calcula el total de páginas"""
        if self.total == 0:
            return 1
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self):
        """Verifica si hay página anterior"""
        return self.page > 1

    @property
    def has_next(self):
        """Verifica si hay página siguiente"""
        return self.page < self.total_pages

    @property
    def prev_page(self):
        """Número de página anterior (o None)"""
        return self.page - 1 if self.has_prev else None

    @property
    def next_page(self):
        """Número de página siguiente (o None)"""
        return self.page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """
        Genera números de página para mostrar en UI

        Args:
            left_edge: Páginas a mostrar al inicio
            left_current: Páginas a mostrar antes de la actual
            right_current: Páginas a mostrar después de la actual
            right_edge: Páginas a mostrar al final

        Yields:
            int o None: Número de página o None para indicar "..."
        """
        last = 0
        for num in range(1, self.total_pages + 1):
            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.total_pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def to_dict(self):
        """Retorna diccionario con toda la info de paginación"""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'total_pages': self.total_pages,
            'offset': self.offset,
            'limit': self.limit,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_page': self.prev_page,
            'next_page': self.next_page
        }


def get_pagination(per_page_default=25):
    """
    Obtiene paginación desde request.args

    Args:
        per_page_default: Valor por defecto para elementos por página

    Returns:
        Pagination: Objeto de paginación (sin total, debe establecerse después)

    Ejemplo:
        pagination = get_pagination(per_page_default=20)
        # Hacer query con pagination.offset y pagination.limit
        # Luego establecer el total:
        pagination.total = total_count
    """
    try:
        page = int(request.args.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get('per_page', per_page_default))
    except (ValueError, TypeError):
        per_page = per_page_default

    return Pagination(page=page, per_page=per_page)


def paginate_query(query_url, headers, per_page_default=25, filters=None):
    """
    Helper completo para paginar queries de Supabase

    Args:
        query_url: URL base de Supabase (sin parámetros de paginación)
        headers: Headers para la request
        per_page_default: Elementos por página por defecto
        filters: Filtros adicionales para la query (dict)

    Returns:
        tuple: (pagination, data) donde pagination es Pagination y data es lista de resultados

    Ejemplo:
        pagination, leads = paginate_query(
            f"{SUPABASE_URL}/rest/v1/clientes?select=*",
            HEADERS,
            per_page_default=25,
            filters={'activo': 'eq.true'}
        )
    """
    import requests

    # Obtener paginación de request
    pagination = get_pagination(per_page_default)

    # Construir URL con filtros
    url = query_url
    if filters:
        for key, value in filters.items():
            separator = '&' if '?' in url else '?'
            url += f"{separator}{key}={value}"

    # Agregar paginación
    separator = '&' if '?' in url else '?'
    url += f"{separator}limit={pagination.limit}&offset={pagination.offset}"

    # Hacer query
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # Obtener total (si está disponible en headers)
        content_range = response.headers.get('Content-Range')
        if content_range:
            # Format: "0-24/100" o "*/100"
            try:
                total_str = content_range.split('/')[-1]
                pagination.total = int(total_str)
            except (ValueError, IndexError):
                pagination.total = len(data)
        else:
            # Si no hay Content-Range, el total es al menos el número de resultados
            pagination.total = len(data)

        return pagination, data
    else:
        return pagination, []
