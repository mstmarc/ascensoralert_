"""
Módulo de gestión de Defectos

Incluye funcionalidades para:
- Dashboard con estadísticas y filtros operativos
- Exportación a PDF agrupado por máquina
- CRUD completo de defectos
- Subsanación y reversión de estado
- Gestión operativa (técnicos, materiales, stock)
"""

from .defectos_bp import defectos_bp

__all__ = ['defectos_bp']
