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
