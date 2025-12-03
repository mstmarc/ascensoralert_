# Migración 007: Corrección de Warnings de Seguridad

**Fecha:** 2025-12-03
**Archivo:** `database/migrations/007_fix_security_warnings.sql`

## 📋 Resumen

Esta migración soluciona los **warnings de seguridad** detectados por el **Supabase Database Linter**:

- ✅ **8 funciones** con search_path mutable → Recreadas con search_path fijo
- ✅ **2 extensiones** en schema public → Movidas a schema `extensions`

## 🔍 Problemas Detectados

### 1. Function Search Path Mutable (WARN)

Las siguientes 8 funciones no tenían un `search_path` fijo, haciéndolas vulnerables a **search path injection attacks**:

1. `update_updated_at_column` - Trigger para actualizar timestamps
2. `detectar_componente_critico` - Detecta componentes en texto
3. `update_configuracion_avisos_timestamp` - Trigger para configuracion_avisos
4. `update_administradores_updated_at` - Trigger para administradores
5. `f_unaccent` - Wrapper para quitar acentos
6. `buscar_clientes_sin_acentos` - Búsqueda de clientes sin acentos
7. `buscar_administradores_sin_acentos` - Búsqueda de administradores sin acentos
8. `actualizar_fecha_actualizacion_tarea` - Trigger para tareas comerciales

**Problema:** Sin un search_path fijo, un atacante podría crear objetos (tablas, funciones) en un schema que esté antes en el search_path y hacer que la función los use en lugar de los objetos legítimos.

**Ejemplo de vulnerabilidad:**

```sql
-- ❌ Función vulnerable (sin search_path fijo)
CREATE FUNCTION mi_funcion()
RETURNS void AS $$
BEGIN
    -- Si alguien crea una tabla "usuarios" en otro schema,
    -- esta query podría usar esa tabla en lugar de la legítima
    SELECT * FROM usuarios;
END;
$$ LANGUAGE plpgsql;

-- ✅ Función segura (con search_path fijo)
CREATE FUNCTION mi_funcion()
RETURNS void
SET search_path = public, pg_catalog  -- Search path fijo
AS $$
BEGIN
    -- Ahora siempre usará public.usuarios
    SELECT * FROM usuarios;
END;
$$ LANGUAGE plpgsql;
```

### 2. Extension in Public (WARN)

Dos extensiones estaban instaladas en el schema `public`:

1. **pg_trgm** - Extensión para búsquedas de similaridad de texto (trigrams)
2. **unaccent** - Extensión para quitar acentos de texto

**Problema:** Las extensiones deberían estar en un schema dedicado (no en `public`) para evitar conflictos de nombres y mejorar la organización.

## 🔧 Soluciones Implementadas

### Parte 1: Schema Dedicado para Extensiones

Se creó el schema `extensions`:

```sql
CREATE SCHEMA IF NOT EXISTS extensions;
GRANT USAGE ON SCHEMA extensions TO postgres, authenticated, anon, service_role;
```

### Parte 2: Mover Extensiones

```sql
ALTER EXTENSION pg_trgm SET SCHEMA extensions;
ALTER EXTENSION unaccent SET SCHEMA extensions;
```

### Parte 3: Recrear Funciones con Search_Path Fijo

Todas las funciones fueron recreadas con `SET search_path`:

**Ejemplo - Función de Trigger:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog  -- ✅ Search path fijo
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;
```

**Ejemplo - Función con Extensión:**
```sql
CREATE OR REPLACE FUNCTION f_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
SET search_path = extensions, public, pg_catalog  -- ✅ Incluye schema extensions
AS $$
    SELECT extensions.unaccent('extensions.unaccent', $1)
$$;
```

### Parte 4: Actualizar Search_Path del Rol

```sql
ALTER ROLE authenticated SET search_path TO public, extensions, pg_catalog;
```

Esto asegura que los usuarios autenticados puedan acceder a las extensiones en el schema `extensions`.

## 📦 Cómo Aplicar la Migración

### Opción 1: Desde Supabase Dashboard (Recomendado)

1. Accede a tu proyecto en [Supabase](https://app.supabase.com)
2. Ve a **SQL Editor**
3. Copia y pega el contenido de `database/migrations/007_fix_security_warnings.sql`
4. Ejecuta el script

### Opción 2: Desde línea de comandos

```bash
psql -U postgres -d ascensoralert -f database/migrations/007_fix_security_warnings.sql
```

### Opción 3: Con Supabase CLI

```bash
supabase db push
```

## ✅ Verificación

Después de aplicar la migración, verifica los cambios:

### 1. Verificar que las extensiones están en el schema extensions

```sql
SELECT
    e.extname,
    n.nspname as schema_name
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname IN ('pg_trgm', 'unaccent');
```

Debería mostrar:
```
extname  | schema_name
---------+-------------
pg_trgm  | extensions
unaccent | extensions
```

### 2. Verificar que las funciones tienen search_path fijo

```sql
SELECT
    p.proname as function_name,
    pg_get_function_identity_arguments(p.oid) as arguments,
    p.proconfig as search_path_config
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.proname IN (
    'update_updated_at_column',
    'detectar_componente_critico',
    'f_unaccent',
    'buscar_clientes_sin_acentos'
)
ORDER BY p.proname;
```

La columna `search_path_config` debería contener valores como:
```
{search_path=public,pg_catalog}
{search_path=extensions,public,pg_catalog}
```

### 3. Probar una función de búsqueda

```sql
-- Probar búsqueda sin acentos
SELECT * FROM buscar_clientes_sin_acentos('Jose');
```

Debería funcionar correctamente y encontrar "José", "jose", etc.

### 4. Ejecutar el Linter de Supabase nuevamente

En el Dashboard de Supabase:
1. Ve a **Database** > **Linter**
2. Ejecuta el linter
3. Verifica que los warnings `function_search_path_mutable` y `extension_in_public` desaparecieron

## 🔍 Detalles Técnicos

### ¿Qué es Search Path Injection?

El **search path** de PostgreSQL determina en qué schemas buscar objetos cuando no se especifica el schema completo.

**Ejemplo de ataque:**

1. Usuario malicioso crea un schema `malicious`
2. Crea una tabla `usuarios` en ese schema con datos falsos
3. Modifica el search_path para poner `malicious` antes que `public`
4. Una función sin search_path fijo usa `malicious.usuarios` en lugar de `public.usuarios`

**Prevención:**

Fijar el search_path en la definición de la función:

```sql
CREATE FUNCTION mi_funcion()
SET search_path = public, pg_catalog  -- ✅ Siempre usa estos schemas
AS $$ ... $$;
```

### ¿Por qué mover extensiones a un schema dedicado?

**Ventajas:**

1. **Organización:** Separa extensiones de datos de aplicación
2. **Seguridad:** Reduce superficie de ataque en schema `public`
3. **Claridad:** Queda claro qué objetos son extensiones vs código de aplicación
4. **Permisos:** Más fácil gestionar permisos granulares

### Orden del Search Path

El orden importa:

```sql
SET search_path = schema1, schema2, pg_catalog;
```

PostgreSQL buscará objetos en este orden:
1. `schema1`
2. `schema2`
3. `pg_catalog` (funciones del sistema)

**Buena práctica:** Siempre incluir `pg_catalog` al final para acceder a funciones del sistema.

## 🎯 Funciones Actualizadas - Detalles

### 1. update_updated_at_column()
**Uso:** Trigger para actualizar `updated_at` automáticamente
**Tablas afectadas:** inspecciones, materiales_especiales, ocas, y otras
```sql
SET search_path = public, pg_catalog
```

### 2. detectar_componente_critico(TEXT)
**Uso:** Detecta componentes críticos en texto de resolución
**Retorna:** ID del componente o NULL
```sql
SET search_path = public, pg_catalog
```

### 3-4. Funciones de Trigger Específicas
- `update_configuracion_avisos_timestamp()`
- `update_administradores_updated_at()`
- `actualizar_fecha_actualizacion_tarea()`

**Uso:** Triggers específicos para actualizar timestamps
```sql
SET search_path = public, pg_catalog
```

### 5. f_unaccent(TEXT)
**Uso:** Wrapper para quitar acentos usando extensión unaccent
**Ejemplo:**
```sql
SELECT f_unaccent('José'); -- Retorna: 'Jose'
```
```sql
SET search_path = extensions, public, pg_catalog
```

### 6-7. Funciones de Búsqueda
- `buscar_clientes_sin_acentos(TEXT)`
- `buscar_administradores_sin_acentos(TEXT)`

**Uso:** Búsquedas inteligentes ignorando acentos usando pg_trgm
**Ejemplo:**
```sql
-- Encuentra "José García", "Jose Garcia", etc.
SELECT * FROM buscar_clientes_sin_acentos('jose garcia');
```
```sql
SET search_path = public, extensions, pg_catalog
```

## ⚠️ Posibles Problemas y Soluciones

### Problema 1: Error "extension does not exist"

**Error:**
```
ERROR: extension "unaccent" does not exist
```

**Solución:**
```sql
-- Instalar extensión si no existe
CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;
```

### Problema 2: Funciones de búsqueda no encuentran resultados

**Causa:** Las funciones de búsqueda dependen de pg_trgm y unaccent

**Solución:**
```sql
-- Verificar que las extensiones están instaladas
SELECT * FROM pg_extension WHERE extname IN ('pg_trgm', 'unaccent');

-- Si no están, instalarlas
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA extensions;
```

### Problema 3: Permisos insuficientes para mover extensiones

**Error:**
```
ERROR: permission denied to alter extension
```

**Solución:**
Ejecuta la migración con un usuario que tenga permisos de superusuario (postgres) o desde el Dashboard de Supabase.

## 🔗 Relación con Migración 006

Esta migración (007) complementa la migración 006:

- **Migración 006:** Corrigió **ERRORES** de seguridad (RLS, SECURITY DEFINER)
- **Migración 007:** Corrige **WARNINGS** de seguridad (search_path, extensiones)

**Recomendación:** Aplica ambas migraciones en orden (006 → 007).

## 📚 Referencias

- [PostgreSQL Search Path](https://www.postgresql.org/docs/current/ddl-schemas.html#DDL-SCHEMAS-PATH)
- [PostgreSQL Security Best Practices](https://www.postgresql.org/docs/current/sql-createfunction.html)
- [Supabase Database Linter](https://supabase.com/docs/guides/database/database-linter)
- [pg_trgm Extension](https://www.postgresql.org/docs/current/pgtrgm.html)
- [unaccent Extension](https://www.postgresql.org/docs/current/unaccent.html)

## 📝 Registro de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-12-03 | 007 | Corrección de warnings - search_path fijo y mover extensiones |

## 🎉 Resultado Esperado

Después de aplicar esta migración:

✅ **0 errores** de seguridad en el linter
✅ **0 warnings** de seguridad en el linter (relacionados con funciones y extensiones)
✅ Base de datos más segura contra search path injection
✅ Mejor organización con extensiones en schema dedicado
✅ Código más mantenible y claro

¡Tu base de datos ahora cumple con todas las mejores prácticas de seguridad de Supabase! 🔒
