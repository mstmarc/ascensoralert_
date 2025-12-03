-- ============================================
-- MIGRACIÓN: Corrección Final - Funciones de Búsqueda
-- Fecha: 2025-12-03
-- ============================================
-- OBJETIVO: Eliminar todas las versiones de funciones de búsqueda y recrearlas con search_path fijo

-- ============================================
-- PARTE 1: ELIMINAR TODAS LAS VERSIONES DE LAS FUNCIONES
-- ============================================

-- Eliminar función buscar_clientes_sin_acentos con cualquier firma
DO $$
DECLARE
    func_record RECORD;
BEGIN
    FOR func_record IN
        SELECT proname, oidvectortypes(proargtypes) as argtypes
        FROM pg_proc
        WHERE proname = 'buscar_clientes_sin_acentos'
        AND pronamespace = 'public'::regnamespace
    LOOP
        EXECUTE format('DROP FUNCTION IF EXISTS public.%I(%s) CASCADE',
                      func_record.proname,
                      func_record.argtypes);
        RAISE NOTICE 'Eliminada función: % con argumentos: %', func_record.proname, func_record.argtypes;
    END LOOP;
END
$$;

-- Eliminar función buscar_administradores_sin_acentos con cualquier firma
DO $$
DECLARE
    func_record RECORD;
BEGIN
    FOR func_record IN
        SELECT proname, oidvectortypes(proargtypes) as argtypes
        FROM pg_proc
        WHERE proname = 'buscar_administradores_sin_acentos'
        AND pronamespace = 'public'::regnamespace
    LOOP
        EXECUTE format('DROP FUNCTION IF EXISTS public.%I(%s) CASCADE',
                      func_record.proname,
                      func_record.argtypes);
        RAISE NOTICE 'Eliminada función: % con argumentos: %', func_record.proname, func_record.argtypes;
    END LOOP;
END
$$;

-- ============================================
-- PARTE 2: RECREAR FUNCIONES CON SEARCH_PATH FIJO
-- ============================================

-- Función: buscar_clientes_sin_acentos
CREATE OR REPLACE FUNCTION buscar_clientes_sin_acentos(termino TEXT)
RETURNS TABLE (
    id INTEGER,
    nombre TEXT,
    municipio TEXT,
    relevancia REAL
)
LANGUAGE plpgsql
STABLE
SET search_path TO public, extensions, pg_catalog
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

COMMENT ON FUNCTION buscar_clientes_sin_acentos(TEXT) IS
'Busca clientes ignorando acentos usando pg_trgm. SET search_path fijo para seguridad.';

-- Función: buscar_administradores_sin_acentos
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
SET search_path TO public, extensions, pg_catalog
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

COMMENT ON FUNCTION buscar_administradores_sin_acentos(TEXT) IS
'Busca administradores ignorando acentos usando pg_trgm. SET search_path fijo para seguridad.';

-- ============================================
-- PARTE 3: VERIFICAR QUE SEARCH_PATH ESTÁ CONFIGURADO
-- ============================================

DO $$
DECLARE
    func_config TEXT[];
    func_name TEXT;
BEGIN
    -- Verificar buscar_clientes_sin_acentos
    SELECT proconfig INTO func_config
    FROM pg_proc
    WHERE proname = 'buscar_clientes_sin_acentos'
    AND pronamespace = 'public'::regnamespace;

    IF func_config IS NULL OR NOT (func_config::text LIKE '%search_path%') THEN
        RAISE EXCEPTION 'ERROR: buscar_clientes_sin_acentos no tiene search_path configurado!';
    ELSE
        RAISE NOTICE '✓ buscar_clientes_sin_acentos tiene search_path: %', func_config;
    END IF;

    -- Verificar buscar_administradores_sin_acentos
    SELECT proconfig INTO func_config
    FROM pg_proc
    WHERE proname = 'buscar_administradores_sin_acentos'
    AND pronamespace = 'public'::regnamespace;

    IF func_config IS NULL OR NOT (func_config::text LIKE '%search_path%') THEN
        RAISE EXCEPTION 'ERROR: buscar_administradores_sin_acentos no tiene search_path configurado!';
    ELSE
        RAISE NOTICE '✓ buscar_administradores_sin_acentos tiene search_path: %', func_config;
    END IF;
END
$$;

-- ============================================
-- PARTE 4: REGISTRAR MIGRACIÓN
-- ============================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) VALUES
    ('009', 'Corrección Final - Eliminar y recrear funciones de búsqueda con search_path fijo verificado')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migración 009 completada exitosamente';
    RAISE NOTICE '🔒 CORRECCIONES APLICADAS:';
    RAISE NOTICE '   ✓ Eliminadas todas las versiones anteriores de funciones de búsqueda';
    RAISE NOTICE '   ✓ Recreadas 2 funciones con SET search_path TO (sintaxis explícita)';
    RAISE NOTICE '   ✓ Verificado que search_path está configurado correctamente';
    RAISE NOTICE '🔧 FUNCIONES CORREGIDAS:';
    RAISE NOTICE '   1. buscar_clientes_sin_acentos';
    RAISE NOTICE '   2. buscar_administradores_sin_acentos';
    RAISE NOTICE '⚠️  SIGUIENTE PASO:';
    RAISE NOTICE '   Ejecutar el linter de Supabase - debería mostrar 0 warnings';
    RAISE NOTICE '✨ Si aún aparecen warnings:';
    RAISE NOTICE '   Las funciones pueden estar en otro schema o tener firma diferente';
    RAISE NOTICE '   Ejecutar: SELECT proname, nspname, proconfig FROM pg_proc p';
    RAISE NOTICE '             JOIN pg_namespace n ON p.pronamespace = n.oid';
    RAISE NOTICE '             WHERE proname LIKE ''buscar_%sin_acentos'';';
END
$$;
