-- ============================================
-- MIGRACIÓN: Agregar campos de baja a instalaciones
-- Fecha: 2025-12-04
-- Descripción: Permite gestionar instalaciones dadas de baja
-- ============================================

-- Agregar campos de baja a la tabla instalaciones
ALTER TABLE instalaciones
ADD COLUMN IF NOT EXISTS en_cartera BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS fecha_salida_cartera DATE,
ADD COLUMN IF NOT EXISTS motivo_salida TEXT;

-- Crear índice para búsquedas por estado
CREATE INDEX IF NOT EXISTS idx_instalaciones_en_cartera ON instalaciones(en_cartera);

-- Comentarios para documentación
COMMENT ON COLUMN instalaciones.en_cartera IS 'TRUE = Instalación activa en cartera, FALSE = Dada de baja';
COMMENT ON COLUMN instalaciones.fecha_salida_cartera IS 'Fecha en que la instalación salió de la cartera';
COMMENT ON COLUMN instalaciones.motivo_salida IS 'Razón de la baja: cambio de empresa, fin de contrato, etc.';
