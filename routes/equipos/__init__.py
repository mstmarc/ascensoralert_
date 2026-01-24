"""
Módulo de gestión de Equipos

Incluye funcionalidades para:
- Creación de equipos vinculados a clientes
- CRUD completo de equipos (ver, editar, eliminar)
- Sistema de acciones/tareas para seguimiento
"""

from .equipos_bp import equipos_bp

__all__ = ['equipos_bp']
