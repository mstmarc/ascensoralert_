# Refactorización de AscensorAlert

## Resumen de Cambios

Se ha realizado una refactorización importante del archivo `app.py` (8,567 líneas) para mejorar la mantenibilidad y organización del código.

## Antes vs Después

### Antes
- **app.py**: 8,567 líneas con 177 rutas mezcladas
- Configuración, caché, rutas y utilidades en un solo archivo
- Difícil de mantener y navegar

### Después
- **app.py**: 316 líneas, limpio y organizado
- **app_legacy.py**: Archivo original como respaldo
- Código modularizado en servicios y utilidades separadas

## Nueva Estructura

```
ascensoralert_/
├── app.py                          # Aplicación principal (316 líneas) ✨ NUEVO
├── app_legacy.py                   # Código original (8,567 líneas)
├── config.py                       # Configuración centralizada ✨ NUEVO
│
├── services/                       # ✨ NUEVO
│   ├── __init__.py
│   ├── cache_service.py           # Sistema de caché centralizado
│   ├── supabase_client.py         # Cliente para operaciones BD
│   └── email_service.py           # Servicio de envío de emails
│
├── middleware/                     # ✨ NUEVO
│   └── __init__.py
│
├── utils/                          # ✨ NUEVO
│   ├── __init__.py
│   └── formatters.py              # Funciones de formateo
│
├── routes/                         # ✨ NUEVO (preparado para futura migración)
│   ├── __init__.py
│   ├── inspecciones/
│   ├── administracion/
│   ├── cartera/
│   └── ia/
│
└── helpers.py                      # Existente (sin cambios)
```

## Archivos Nuevos

### 1. `config.py`
Centraliza toda la configuración de la aplicación:
- Variables de entorno (SECRET_KEY, SUPABASE_KEY, etc.)
- Configuración de headers para API
- Constantes de caché (TTL)

### 2. `services/cache_service.py`
Sistema de caché optimizado:
- `get_administradores_cached()` - TTL 5 min
- `get_metricas_home_cached()` - TTL 5 min
- `get_filtros_cached()` - TTL 30 min
- `get_ultimas_instalaciones_cached()` - TTL 10 min
- `get_ultimas_oportunidades_cached()` - TTL 10 min
- `clear_all_caches()` - Limpia todas las cachés

### 3. `services/supabase_client.py`
Cliente simplificado para operaciones con Supabase:
- `get(table, select, filters, order, limit)` - Consultas GET
- `get_by_id(table, record_id)` - Obtener por ID
- `post(table, data)` - Crear registros
- `patch(table, record_id, data)` - Actualizar registros
- `delete(table, record_id)` - Eliminar registros
- `count(table, filters)` - Contar registros

### 4. `services/email_service.py`
Servicio para envío de emails con Resend:
- `enviar_avisos_email(config)` - Envía avisos de IPOs y contratos

### 5. `utils/formatters.py`
Funciones de formateo y transformación:
- `limpiar_none(data)` - Convierte None a strings vacíos
- `format_fecha_filter(fecha_str)` - Formato dd/mm/yyyy
- `calcular_color_ipo(fecha_ipo_str)` - Color según urgencia IPO
- `calcular_color_contrato(fecha_contrato_str)` - Color según vencimiento

## Nuevo `app.py` (316 líneas)

El nuevo app.py está organizado en secciones claras:

1. **Imports y configuración** (líneas 1-26)
2. **Filtros Jinja2** (líneas 28-58)
3. **Import de rutas desde app_legacy** (líneas 60-153)
4. **Registro de rutas** (líneas 155-308)
5. **Punto de entrada** (líneas 310-315)

## Ventajas de la Refactorización

### Mantenibilidad
- Código organizado en módulos lógicos
- Fácil de navegar y encontrar funciones
- Separación de responsabilidades

### Reutilización
- Servicios independientes pueden usarse en cualquier parte
- Cliente de Supabase facilita operaciones de BD
- Sistema de caché centralizado

### Escalabilidad
- Preparado para migración a Blueprints de Flask
- Estructura de carpetas `routes/` lista para módulos
- Fácil agregar nuevos servicios

### Performance
- Sistema de caché optimizado y centralizado
- Reduce consultas redundantes a Supabase

## Compatibilidad

✅ **100% Compatible**: La aplicación mantiene toda la funcionalidad original
- Todas las 177 rutas funcionan igual
- Mismo comportamiento para usuarios
- No se requieren cambios en templates

## Próximos Pasos Recomendados

### Fase 2: Migración a Blueprints
1. Extraer rutas de autenticación a `routes/auth.py`
2. Extraer rutas de leads a `routes/leads.py`
3. Extraer rutas de inspecciones a `routes/inspecciones/`
4. Continuar módulo por módulo

### Fase 3: Optimizaciones
1. Implementar decoradores de caché automáticos
2. Crear middleware de paginación
3. Unificar manejo de errores
4. Agregar tests unitarios

## Uso del Nuevo Código

### Importar servicios:
```python
from config import config
from services.cache_service import get_administradores_cached, clear_all_caches
from services.supabase_client import db
from services.email_service import enviar_avisos_email
from utils.formatters import format_fecha_filter, limpiar_none
```

### Usar el cliente de Supabase:
```python
from services.supabase_client import db

# GET
clientes = db.get('clientes', select='id,nombre', filters={'activo': 'eq.true'})

# GET por ID
cliente = db.get_by_id('clientes', 123)

# POST
nuevo = db.post('clientes', {'nombre': 'Test', 'email': 'test@example.com'})

# PATCH
actualizado = db.patch('clientes', 123, {'nombre': 'Actualizado'})

# DELETE
db.delete('clientes', 123)
```

### Usar el sistema de caché:
```python
from services.cache_service import get_administradores_cached, clear_all_caches

# Obtener datos con caché
admins = get_administradores_cached()  # Se cachea por 5 minutos

# Limpiar cachés si es necesario
clear_all_caches()
```

## Archivos Modificados

- ✅ `app.py` - Refactorizado completamente
- ✅ `app_legacy.py` - Creado (respaldo del original)
- ✅ Nuevos archivos de servicios y utilidades

## Archivos Sin Modificar

- ✅ `helpers.py` - Sistema de permisos existente
- ✅ `analizador_ia.py` - Módulo de IA
- ✅ `catastro_service.py` - Servicio de catastro
- ✅ `templates/` - Sin cambios
- ✅ `static/` - Sin cambios

## Verificación

Para verificar que todo funciona:

```bash
# Verificar sintaxis
python3 -m py_compile app.py config.py services/*.py utils/*.py

# Ejecutar la aplicación
python3 app.py
```

## Notas

- El archivo `app_legacy.py` se mantiene como referencia y respaldo
- Toda la funcionalidad original está preservada
- La refactorización es incremental y permite iteraciones futuras
- El código está documentado con docstrings

## Contacto

Para preguntas o sugerencias sobre esta refactorización, consulta la documentación del proyecto.
