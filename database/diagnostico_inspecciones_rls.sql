-- ============================================
-- DIAGNÓSTICO: Tabla inspecciones
-- ============================================

-- 1. Verificar que las columnas existen
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'inspecciones'
  AND column_name IN ('acta_pdf_url', 'presupuesto_pdf_url');

-- 2. Verificar si RLS está habilitado en la tabla
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'inspecciones';

-- 3. Listar políticas RLS de la tabla inspecciones (si existen)
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'inspecciones';

-- 4. Ver estructura completa de la tabla
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'inspecciones'
ORDER BY ordinal_position;
