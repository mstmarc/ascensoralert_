-- ============================================
-- AGREGAR CAMPOS DE CIERRE A TAREAS COMERCIALES
-- AscensorAlert - Fedes Ascensores
-- ============================================

-- Agregar columnas para registro de descarte/cierre de tareas
DO $$
BEGIN
    -- Campo para tipo de cierre (descartada_sin_interes, no_contactado, etc.)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'seguimiento_comercial_tareas' AND column_name = 'tipo_cierre'
    ) THEN
        ALTER TABLE seguimiento_comercial_tareas ADD COLUMN tipo_cierre VARCHAR(50);
    END IF;

    -- Campo para motivo detallado del cierre
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'seguimiento_comercial_tareas' AND column_name = 'motivo_cierre'
    ) THEN
        ALTER TABLE seguimiento_comercial_tareas ADD COLUMN motivo_cierre TEXT;
    END IF;

    -- Campo para fecha de cierre
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'seguimiento_comercial_tareas' AND column_name = 'fecha_cierre'
    ) THEN
        ALTER TABLE seguimiento_comercial_tareas ADD COLUMN fecha_cierre TIMESTAMP;
    END IF;
END $$;

-- Crear índice para búsquedas por tipo de cierre
CREATE INDEX IF NOT EXISTS idx_tareas_tipo_cierre ON seguimiento_comercial_tareas(tipo_cierre);

-- Crear índice para búsquedas por fecha de cierre
CREATE INDEX IF NOT EXISTS idx_tareas_fecha_cierre ON seguimiento_comercial_tareas(fecha_cierre);

-- Añadir comentarios para documentación
COMMENT ON COLUMN seguimiento_comercial_tareas.tipo_cierre IS 'Tipo de cierre: descartada_sin_interes, no_contactado, convertida, etc.';
COMMENT ON COLUMN seguimiento_comercial_tareas.motivo_cierre IS 'Motivo detallado del cierre de la tarea';
COMMENT ON COLUMN seguimiento_comercial_tareas.fecha_cierre IS 'Fecha y hora en que se cerró la tarea';

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
