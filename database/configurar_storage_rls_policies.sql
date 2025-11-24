-- Políticas RLS para Supabase Storage: inspecciones-pdfs
-- Fecha: 2025-11-21
-- IMPORTANTE: Ejecutar DESPUÉS de crear el bucket 'inspecciones-pdfs' en Supabase Storage

-- ============================================
-- ELIMINAR POLÍTICAS EXISTENTES (si existen)
-- ============================================

DROP POLICY IF EXISTS "Permitir lectura pública de PDFs de inspecciones" ON storage.objects;
DROP POLICY IF EXISTS "Permitir subida de PDFs a usuarios autenticados" ON storage.objects;
DROP POLICY IF EXISTS "Permitir actualización de PDFs a usuarios autenticados" ON storage.objects;
DROP POLICY IF EXISTS "Permitir eliminación de PDFs a usuarios autenticados" ON storage.objects;

-- ============================================
-- CREAR POLÍTICAS DE ACCESO
-- ============================================

-- Política de LECTURA (SELECT): Acceso público a todos los PDFs
CREATE POLICY "Permitir lectura pública de PDFs de inspecciones"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'inspecciones-pdfs');

-- Política de ESCRITURA (INSERT): Permite subir con anon, authenticated o service_role
CREATE POLICY "Permitir subida de PDFs a usuarios autenticados"
ON storage.objects FOR INSERT
TO public
WITH CHECK (
    bucket_id = 'inspecciones-pdfs' AND
    (storage.foldername(name))[1] = 'inspecciones'
);

-- Política de ACTUALIZACIÓN (UPDATE): Permite actualizar con anon, authenticated o service_role
CREATE POLICY "Permitir actualización de PDFs a usuarios autenticados"
ON storage.objects FOR UPDATE
TO public
USING (bucket_id = 'inspecciones-pdfs')
WITH CHECK (bucket_id = 'inspecciones-pdfs');

-- Política de ELIMINACIÓN (DELETE): Permite eliminar con anon, authenticated o service_role
CREATE POLICY "Permitir eliminación de PDFs a usuarios autenticados"
ON storage.objects FOR DELETE
TO public
USING (bucket_id = 'inspecciones-pdfs');

-- ============================================
-- VERIFICAR POLÍTICAS
-- ============================================

-- Listar todas las políticas del bucket
SELECT
    policyname,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename = 'objects'
  AND policyname LIKE '%inspecciones%';

-- ============================================
-- NOTAS
-- ============================================

-- 1. El bucket 'inspecciones-pdfs' debe existir ANTES de ejecutar este script
-- 2. El bucket debe estar marcado como PÚBLICO en la configuración de Supabase
-- 3. Los archivos se guardan en la carpeta: inspecciones/inspeccion_{id}_acta.pdf
-- 4. Las URLs públicas tienen el formato:
--    https://{supabase-url}/storage/v1/object/public/inspecciones-pdfs/inspecciones/inspeccion_{id}_acta.pdf
