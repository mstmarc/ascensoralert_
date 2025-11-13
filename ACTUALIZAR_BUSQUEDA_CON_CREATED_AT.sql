-- ============================================
-- ACTUALIZACIÓN: Agregar created_at a la función de búsqueda
-- ============================================
-- Esta actualización modifica la función buscar_clientes_sin_acentos
-- para incluir el campo created_at y ordenar por fecha de creación

-- Primero eliminar la función existente
DROP FUNCTION IF EXISTS buscar_clientes_sin_acentos(text,text,text,integer,integer);

-- Crear la función con el nuevo esquema
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
    numero_ascensores text,
    created_at timestamp with time zone,
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
            c.created_at,
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
        created_at,
        total_count
    FROM filtered_data
    ORDER BY created_at DESC NULLS LAST
    LIMIT limite
    OFFSET desplazamiento;
$$;

-- ============================================
-- INSTRUCCIONES
-- ============================================
-- 1. Abre tu proyecto Supabase en https://app.supabase.com
-- 2. Ve a "SQL Editor" en el menú lateral
-- 3. Copia y pega este archivo
-- 4. Haz clic en "Run" para ejecutar
-- 5. Verifica que el resultado sea "Success. No rows returned"
