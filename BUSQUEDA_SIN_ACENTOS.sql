-- ============================================
-- CONFIGURACIÓN DE BÚSQUEDA SIN ACENTOS
-- ============================================
-- Este script configura PostgreSQL/Supabase para realizar búsquedas
-- sin distinción de acentos (e.g., "Ramon" encontrará "Ramón")

-- PASO 1: Habilitar extensiones necesarias
-- Estas extensiones vienen incluidas en PostgreSQL/Supabase
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- PASO 2: Crear función personalizada para búsqueda sin acentos
-- Esta función normaliza el texto removiendo acentos para las comparaciones
CREATE OR REPLACE FUNCTION f_unaccent(text)
  RETURNS text AS
$func$
SELECT public.unaccent('public.unaccent', $1)
$func$ LANGUAGE sql IMMUTABLE;

-- PASO 3: Crear índices GIN con unaccent para búsquedas rápidas
-- Estos índices permiten búsquedas muy rápidas sin distinción de acentos

-- Índice para dirección en clientes
CREATE INDEX IF NOT EXISTS idx_clientes_direccion_unaccent
ON clientes USING gin(f_unaccent(direccion) gin_trgm_ops);

-- Índice para nombre_cliente en clientes
CREATE INDEX IF NOT EXISTS idx_clientes_nombre_unaccent
ON clientes USING gin(f_unaccent(nombre_cliente) gin_trgm_ops);

-- Índice para localidad en clientes
CREATE INDEX IF NOT EXISTS idx_clientes_localidad_unaccent
ON clientes USING gin(f_unaccent(localidad) gin_trgm_ops);

-- Índice para nombre_empresa en administradores
CREATE INDEX IF NOT EXISTS idx_administradores_nombre_unaccent
ON administradores USING gin(f_unaccent(nombre_empresa) gin_trgm_ops);

-- ============================================
-- CÓMO USAR EN LAS QUERIES
-- ============================================
-- En lugar de: direccion.ilike.*ramon*
-- Usar: f_unaccent(direccion).ilike.*ramon*
-- Esto hará que "ramon" encuentre "Ramón", "RAMON", "ramón", etc.

-- EJEMPLO:
-- SELECT * FROM clientes
-- WHERE f_unaccent(direccion) ILIKE '%ramon%'
--    OR f_unaccent(nombre_cliente) ILIKE '%ramon%'
--    OR f_unaccent(localidad) ILIKE '%ramon%';

-- ============================================
-- INSTRUCCIONES PARA EJECUTAR EN SUPABASE
-- ============================================
-- 1. Abre tu proyecto en https://app.supabase.com
-- 2. Ve a "SQL Editor" en el menú lateral
-- 3. Crea un nuevo query
-- 4. Copia y pega todo este archivo
-- 5. Haz clic en "Run" para ejecutar
-- 6. Verifica que no haya errores

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Para verificar que la extensión está instalada:
-- SELECT * FROM pg_extension WHERE extname = 'unaccent';

-- Para verificar que la función existe:
-- SELECT f_unaccent('Ramón García') AS resultado;
-- Debería devolver: "Ramon Garcia"

-- Para verificar que los índices existen:
-- SELECT indexname FROM pg_indexes
-- WHERE schemaname = 'public'
-- AND indexname LIKE '%unaccent%';

-- ============================================
-- PASO 4: Crear función RPC para búsqueda de clientes sin acentos
-- ============================================
-- Esta función permite buscar clientes desde la API usando búsqueda sin acentos

CREATE OR REPLACE FUNCTION buscar_clientes_sin_acentos(
    termino_busqueda text DEFAULT '',
    filtro_localidad text DEFAULT '',
    filtro_empresa text DEFAULT '',
    limite int DEFAULT 25,
    desplazamiento int DEFAULT 0
)
RETURNS TABLE (
    id int,
    direccion text,
    nombre_cliente text,
    localidad text,
    empresa_mantenedora text,
    numero_ascensores int,
    total_count bigint
)
LANGUAGE sql
STABLE
AS $$
    WITH filtered_data AS (
        SELECT
            c.id,
            c.direccion,
            c.nombre_cliente,
            c.localidad,
            c.empresa_mantenedora,
            c.numero_ascensores,
            COUNT(*) OVER() as total_count
        FROM clientes c
        WHERE
            -- Filtro de búsqueda sin acentos
            (
                termino_busqueda = ''
                OR f_unaccent(COALESCE(c.direccion, '')) ILIKE '%' || f_unaccent(termino_busqueda) || '%'
                OR f_unaccent(COALESCE(c.nombre_cliente, '')) ILIKE '%' || f_unaccent(termino_busqueda) || '%'
                OR f_unaccent(COALESCE(c.localidad, '')) ILIKE '%' || f_unaccent(termino_busqueda) || '%'
            )
            -- Filtro de localidad
            AND (filtro_localidad = '' OR c.localidad = filtro_localidad)
            -- Filtro de empresa
            AND (filtro_empresa = '' OR c.empresa_mantenedora = filtro_empresa)
    )
    SELECT
        id,
        direccion,
        nombre_cliente,
        localidad,
        empresa_mantenedora,
        numero_ascensores,
        total_count
    FROM filtered_data
    ORDER BY id
    LIMIT limite
    OFFSET desplazamiento;
$$;

-- ============================================
-- PASO 5: Crear función RPC para búsqueda de administradores sin acentos
-- ============================================

CREATE OR REPLACE FUNCTION buscar_administradores_sin_acentos(
    termino_busqueda text DEFAULT '',
    limite int DEFAULT 10,
    desplazamiento int DEFAULT 0
)
RETURNS TABLE (
    id int,
    nombre_empresa text,
    localidad text,
    telefono text,
    email text,
    direccion text,
    observaciones text,
    total_count bigint
)
LANGUAGE sql
STABLE
AS $$
    WITH filtered_data AS (
        SELECT
            a.id,
            a.nombre_empresa,
            a.localidad,
            a.telefono,
            a.email,
            a.direccion,
            a.observaciones,
            COUNT(*) OVER() as total_count
        FROM administradores a
        WHERE
            termino_busqueda = ''
            OR f_unaccent(COALESCE(a.nombre_empresa, '')) ILIKE '%' || f_unaccent(termino_busqueda) || '%'
            OR f_unaccent(COALESCE(a.localidad, '')) ILIKE '%' || f_unaccent(termino_busqueda) || '%'
            OR COALESCE(a.email, '') ILIKE '%' || termino_busqueda || '%'
    )
    SELECT
        id,
        nombre_empresa,
        localidad,
        telefono,
        email,
        direccion,
        observaciones,
        total_count
    FROM filtered_data
    ORDER BY nombre_empresa ASC
    LIMIT limite
    OFFSET desplazamiento;
$$;
