-- ============================================
-- MIGRACIÓN: Corrección de Warnings de Seguridad
-- Fecha: 2025-12-03
-- ============================================
-- OBJETIVO: Solucionar warnings detectados por Supabase Database Linter:
-- 1. Fijar search_path en 8 funciones (prevenir search_path injection)
-- 2. Mover 2 extensiones de schema public a schema extensions

-- ============================================
-- VERIFICACIONES PREVIAS
-- ============================================

DO $$
BEGIN
    -- Verificar que existen las tablas necesarias
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'componentes_criticos') THEN
        RAISE EXCEPTION 'Tabla componentes_criticos no existe. Ejecuta primero las migraciones anteriores.';
    END IF;
END
$$;

-- ============================================
-- PARTE 1: CREAR SCHEMA PARA EXTENSIONES
-- ============================================

-- Crear schema dedicado para extensiones (si no existe)
CREATE SCHEMA IF NOT EXISTS extensions;

-- Dar permisos apropiados
GRANT USAGE ON SCHEMA extensions TO postgres, authenticated, anon, service_role;

-- ============================================
-- PARTE 2: MOVER EXTENSIONES A SCHEMA DEDICADO
-- ============================================

-- Mover extensión pg_trgm
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension
        WHERE extname = 'pg_trgm'
        AND extnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) THEN
        ALTER EXTENSION pg_trgm SET SCHEMA extensions;
        RAISE NOTICE '✓ Extensión pg_trgm movida a schema extensions';
    ELSE
        RAISE NOTICE 'ℹ Extensión pg_trgm no encontrada en public o ya está en extensions';
    END IF;
END
$$;

-- Mover extensión unaccent
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension
        WHERE extname = 'unaccent'
        AND extnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) THEN
        ALTER EXTENSION unaccent SET SCHEMA extensions;
        RAISE NOTICE '✓ Extensión unaccent movida a schema extensions';
    ELSE
        RAISE NOTICE 'ℹ Extensión unaccent no encontrada en public o ya está en extensions';
    END IF;
END
$$;

-- ============================================
-- PARTE 3: RECREAR FUNCIONES CON SEARCH_PATH FIJO
-- ============================================

-- Función 1: update_updated_at_column
-- Usada en triggers para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function para actualizar columna updated_at automáticamente';

-- Función 2: detectar_componente_critico
-- Detecta componente crítico en texto de resolución
CREATE OR REPLACE FUNCTION detectar_componente_critico(texto_resolucion TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
SET search_path = public, pg_catalog
AS $$
DECLARE
    componente_record RECORD;
    texto_upper TEXT;
    keyword TEXT;
BEGIN
    IF texto_resolucion IS NULL OR texto_resolucion = '' THEN
        RETURN NULL;
    END IF;

    texto_upper := UPPER(texto_resolucion);

    -- Buscar cada componente crítico
    FOR componente_record IN
        SELECT id, keywords FROM componentes_criticos WHERE activo = true
    LOOP
        -- Revisar cada keyword del componente
        FOREACH keyword IN ARRAY componente_record.keywords
        LOOP
            IF texto_upper LIKE '%' || UPPER(keyword) || '%' THEN
                RETURN componente_record.id;
            END IF;
        END LOOP;
    END LOOP;

    RETURN NULL;
END;
$$;

COMMENT ON FUNCTION detectar_componente_critico(TEXT) IS 'Detecta componente crítico en un texto de resolución basándose en keywords';

-- Función 3: update_configuracion_avisos_timestamp
-- Actualizar timestamp en configuracion_avisos
CREATE OR REPLACE FUNCTION update_configuracion_avisos_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION update_configuracion_avisos_timestamp() IS 'Trigger function para actualizar timestamp en configuracion_avisos';

-- Recrear trigger si existe
DROP TRIGGER IF EXISTS trigger_update_configuracion_avisos_timestamp ON configuracion_avisos;
CREATE TRIGGER trigger_update_configuracion_avisos_timestamp
    BEFORE UPDATE ON configuracion_avisos
    FOR EACH ROW
    EXECUTE FUNCTION update_configuracion_avisos_timestamp();

-- Función 4: update_administradores_updated_at
-- Actualizar timestamp en administradores
CREATE OR REPLACE FUNCTION update_administradores_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION update_administradores_updated_at() IS 'Trigger function para actualizar timestamp en administradores';

-- Recrear trigger si existe la tabla administradores
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'administradores') THEN
        DROP TRIGGER IF EXISTS trigger_update_administradores_updated_at ON administradores;
        CREATE TRIGGER trigger_update_administradores_updated_at
            BEFORE UPDATE ON administradores
            FOR EACH ROW
            EXECUTE FUNCTION update_administradores_updated_at();
        RAISE NOTICE '✓ Trigger update_administradores_updated_at recreado';
    END IF;
END
$$;

-- Función 5: f_unaccent
-- Función para quitar acentos de texto (depende de extensión unaccent)
CREATE OR REPLACE FUNCTION f_unaccent(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
SET search_path = extensions, public, pg_catalog
AS $$
    SELECT extensions.unaccent('extensions.unaccent', $1)
$$;

COMMENT ON FUNCTION f_unaccent(TEXT) IS 'Wrapper para unaccent - quita acentos de texto';

-- Función 6: buscar_clientes_sin_acentos
-- Buscar clientes ignorando acentos
CREATE OR REPLACE FUNCTION buscar_clientes_sin_acentos(termino TEXT)
RETURNS TABLE (
    id INTEGER,
    nombre TEXT,
    municipio TEXT,
    relevancia REAL
)
LANGUAGE plpgsql
STABLE
SET search_path = public, extensions, pg_catalog
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.nombre,
        c.municipio,
        extensions.similarity(f_unaccent(c.nombre), f_unaccent(termino)) as relevancia
    FROM clientes c
    WHERE
        f_unaccent(c.nombre) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(c.municipio) ILIKE '%' || f_unaccent(termino) || '%'
        OR extensions.similarity(f_unaccent(c.nombre), f_unaccent(termino)) > 0.3
    ORDER BY relevancia DESC, c.nombre
    LIMIT 50;
END;
$$;

COMMENT ON FUNCTION buscar_clientes_sin_acentos(TEXT) IS 'Busca clientes ignorando acentos usando pg_trgm';

-- Función 7: buscar_administradores_sin_acentos
-- Buscar administradores ignorando acentos
CREATE OR REPLACE FUNCTION buscar_administradores_sin_acentos(termino TEXT)
RETURNS TABLE (
    id INTEGER,
    nombre TEXT,
    apellido1 TEXT,
    apellido2 TEXT,
    telefono TEXT,
    relevancia REAL
)
LANGUAGE plpgsql
STABLE
SET search_path = public, extensions, pg_catalog
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.nombre,
        a.apellido1,
        a.apellido2,
        a.telefono,
        GREATEST(
            extensions.similarity(f_unaccent(a.nombre), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido1, '')), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido2, '')), f_unaccent(termino))
        ) as relevancia
    FROM administradores a
    WHERE
        f_unaccent(a.nombre) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(COALESCE(a.apellido1, '')) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(COALESCE(a.apellido2, '')) ILIKE '%' || f_unaccent(termino) || '%'
        OR a.telefono LIKE '%' || termino || '%'
        OR GREATEST(
            extensions.similarity(f_unaccent(a.nombre), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido1, '')), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido2, '')), f_unaccent(termino))
        ) > 0.3
    ORDER BY relevancia DESC, a.nombre
    LIMIT 50;
END;
$$;

COMMENT ON FUNCTION buscar_administradores_sin_acentos(TEXT) IS 'Busca administradores ignorando acentos usando pg_trgm';

-- Función 8: actualizar_fecha_actualizacion_tarea
-- Actualizar timestamp en seguimiento_comercial_tareas
CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion_tarea()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_catalog
AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION actualizar_fecha_actualizacion_tarea() IS 'Trigger function para actualizar fecha_actualizacion en seguimiento_comercial_tareas';

-- Recrear trigger si existe la tabla seguimiento_comercial_tareas
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'seguimiento_comercial_tareas') THEN
        DROP TRIGGER IF EXISTS trigger_actualizar_fecha_actualizacion_tarea ON seguimiento_comercial_tareas;
        CREATE TRIGGER trigger_actualizar_fecha_actualizacion_tarea
            BEFORE UPDATE ON seguimiento_comercial_tareas
            FOR EACH ROW
            EXECUTE FUNCTION actualizar_fecha_actualizacion_tarea();
        RAISE NOTICE '✓ Trigger actualizar_fecha_actualizacion_tarea recreado';
    END IF;
END
$$;

-- ============================================
-- PARTE 4: ACTUALIZAR SEARCH_PATH DEL ROL authenticated
-- ============================================
-- Asegurar que el search_path incluya extensions para usuarios autenticados

DO $$
BEGIN
    -- Configurar search_path para el rol authenticated
    ALTER ROLE authenticated SET search_path TO public, extensions, pg_catalog;
    RAISE NOTICE '✓ Search path actualizado para rol authenticated';
EXCEPTION
    WHEN insufficient_privilege THEN
        RAISE NOTICE '⚠ No se pudo actualizar search_path para authenticated (permisos insuficientes)';
    WHEN undefined_object THEN
        RAISE NOTICE 'ℹ Rol authenticated no existe en este entorno';
END
$$;

-- ============================================
-- PARTE 5: REGISTRAR MIGRACIÓN
-- ============================================

INSERT INTO schema_migrations (version, description) VALUES
    ('007', 'Corrección de Warnings - search_path en funciones y mover extensiones a schema dedicado')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migración 007 completada exitosamente';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 WARNINGS DE SEGURIDAD CORREGIDOS:';
    RAISE NOTICE '   ✓ 8 funciones recreadas con search_path fijo';
    RAISE NOTICE '   ✓ 2 extensiones movidas a schema extensions';
    RAISE NOTICE '';
    RAISE NOTICE '📦 EXTENSIONES MOVIDAS:';
    RAISE NOTICE '   - pg_trgm: public → extensions';
    RAISE NOTICE '   - unaccent: public → extensions';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 FUNCIONES ACTUALIZADAS:';
    RAISE NOTICE '   1. update_updated_at_column';
    RAISE NOTICE '   2. detectar_componente_critico';
    RAISE NOTICE '   3. update_configuracion_avisos_timestamp';
    RAISE NOTICE '   4. update_administradores_updated_at';
    RAISE NOTICE '   5. f_unaccent';
    RAISE NOTICE '   6. buscar_clientes_sin_acentos';
    RAISE NOTICE '   7. buscar_administradores_sin_acentos';
    RAISE NOTICE '   8. actualizar_fecha_actualizacion_tarea';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  SIGUIENTE PASO:';
    RAISE NOTICE '   Ejecutar el linter de Supabase para verificar que los warnings desaparecieron';
    RAISE NOTICE '';
END
$$;
