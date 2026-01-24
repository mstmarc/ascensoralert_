"""
Módulo de gestión de Inspecciones

Incluye funcionalidades para:
- Dashboard con alertas por urgencia
- Creación y edición de inspecciones
- Upload de actas y presupuestos (PDFs)
- Gestión de estados y segunda inspección
- Extracción de defectos desde PDFs
"""

from .inspecciones_bp import inspecciones_bp

__all__ = ['inspecciones_bp']
