-- ============================================
-- CORRECCIÓN: Permitir UPDATE en tabla inspecciones
-- ============================================
-- Este script soluciona el error "Archivo subido pero error al guardar en base de datos"

-- OPCIÓN 1: Deshabilitar RLS en la tabla inspecciones
-- (Recomendado si tu aplicación maneja los permisos a nivel de código)
-- ============================================

ALTER TABLE inspecciones DISABLE ROW LEVEL SECURITY;

-- ============================================
-- FIN OPCIÓN 1
-- ============================================


-- ============================================
-- OPCIÓN 2: Mantener RLS pero crear políticas permisivas
-- (Usa esto solo si prefieres mantener RLS habilitado)
-- Comenta la OPCIÓN 1 y descomenta esto:
-- ============================================

-- -- Eliminar políticas existentes de inspecciones (si existen)
-- DROP POLICY IF EXISTS "Permitir lectura de inspecciones" ON inspecciones;
-- DROP POLICY IF EXISTS "Permitir escritura de inspecciones" ON inspecciones;
-- DROP POLICY IF EXISTS "Permitir actualización de inspecciones" ON inspecciones;
-- DROP POLICY IF EXISTS "Permitir eliminación de inspecciones" ON inspecciones;
--
-- -- Crear políticas permisivas para todos los roles
-- CREATE POLICY "Permitir lectura de inspecciones"
-- ON inspecciones FOR SELECT
-- TO public
-- USING (true);
--
-- CREATE POLICY "Permitir escritura de inspecciones"
-- ON inspecciones FOR INSERT
-- TO public
-- WITH CHECK (true);
--
-- CREATE POLICY "Permitir actualización de inspecciones"
-- ON inspecciones FOR UPDATE
-- TO public
-- USING (true)
-- WITH CHECK (true);
--
-- CREATE POLICY "Permitir eliminación de inspecciones"
-- ON inspecciones FOR DELETE
-- TO public
-- USING (true);

-- ============================================
-- FIN OPCIÓN 2
-- ============================================


-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Verificar que RLS está deshabilitado
SELECT
    tablename,
    rowsecurity AS "RLS Habilitado"
FROM pg_tables
WHERE tablename = 'inspecciones';

-- Verificar columnas de PDFs
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'inspecciones'
  AND column_name IN ('acta_pdf_url', 'presupuesto_pdf_url');

-- Si ves que las columnas no existen, ejecuta también:
-- ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS acta_pdf_url TEXT;
-- ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS presupuesto_pdf_url TEXT;
