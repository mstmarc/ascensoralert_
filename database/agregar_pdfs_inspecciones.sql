-- Migración: Añadir campos para PDFs en inspecciones
-- Fecha: 2025-11-21
-- Permite subir y almacenar URLs de acta y presupuesto en PDF

-- Añadir columnas para URLs de PDFs
ALTER TABLE inspecciones
ADD COLUMN IF NOT EXISTS acta_pdf_url TEXT,
ADD COLUMN IF NOT EXISTS presupuesto_pdf_url TEXT;

-- Comentarios
COMMENT ON COLUMN inspecciones.acta_pdf_url IS 'URL del PDF del acta de inspección en Supabase Storage';
COMMENT ON COLUMN inspecciones.presupuesto_pdf_url IS 'URL del PDF del presupuesto en Supabase Storage';

-- Verificar
SELECT
    id,
    maquina,
    fecha_inspeccion,
    acta_pdf_url,
    presupuesto_pdf_url
FROM inspecciones
LIMIT 5;
