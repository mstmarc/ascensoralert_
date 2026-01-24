"""
Módulo de gestión de Leads

Incluye funcionalidades para:
- Alta de nuevos leads/clientes
- Dashboard con filtros y búsqueda
- Exportación a Excel
- Vista de detalles
- Edición y eliminación
"""

from .leads_bp import leads_bp

__all__ = ['leads_bp']
