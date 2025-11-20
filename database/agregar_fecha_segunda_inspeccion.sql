-- ============================================
-- AGREGAR: Campo fecha_segunda_inspeccion
-- Fecha: 2025-11-20
-- Descripción: Agrega campo para gestionar la segunda inspección (6 meses después)
-- ============================================

BEGIN;

-- 1. Agregar columna fecha_segunda_inspeccion
ALTER TABLE inspecciones
ADD COLUMN IF NOT EXISTS fecha_segunda_inspeccion DATE;

-- 2. Calcular fecha_segunda_inspeccion para registros existentes
-- (fecha_inspeccion + 6 meses)
UPDATE inspecciones
SET fecha_segunda_inspeccion = fecha_inspeccion + INTERVAL '6 months'
WHERE fecha_segunda_inspeccion IS NULL;

-- 3. Crear índice para mejorar rendimiento en consultas de alertas
CREATE INDEX IF NOT EXISTS idx_inspecciones_fecha_segunda
ON inspecciones(fecha_segunda_inspeccion);

-- 4. Actualizar la vista v_inspecciones_completas para incluir el nuevo campo
DROP VIEW IF EXISTS v_inspecciones_completas;

CREATE VIEW v_inspecciones_completas AS
SELECT
    i.id,
    i.maquina,
    i.fecha_inspeccion,
    i.fecha_segunda_inspeccion,
    i.presupuesto,
    i.estado,
    i.estado_material,
    i.oca_id,
    o.nombre as oca_nombre,
    i.created_at,
    i.updated_at,
    i.created_by,
    -- Calcular días hasta segunda inspección
    CASE
        WHEN i.fecha_segunda_inspeccion IS NOT NULL THEN
            (i.fecha_segunda_inspeccion - CURRENT_DATE)
        ELSE NULL
    END as dias_hasta_segunda_inspeccion,
    -- Calcular urgencia de segunda inspección
    CASE
        WHEN i.fecha_segunda_inspeccion IS NULL THEN 'SIN_FECHA'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE THEN 'VENCIDA'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 30 THEN 'URGENTE'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 60 THEN 'PROXIMA'
        ELSE 'NORMAL'
    END as urgencia_segunda_inspeccion,
    -- Contar defectos pendientes
    (SELECT COUNT(*) FROM defectos_inspeccion d
     WHERE d.inspeccion_id = i.id AND d.estado = 'PENDIENTE') as defectos_pendientes,
    -- Contar materiales especiales pendientes
    (SELECT COUNT(*) FROM materiales_especiales m
     WHERE m.inspeccion_id = i.id AND m.estado != 'INSTALADO') as materiales_pendientes
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

COMMIT;

-- ============================================
-- FIN
-- ============================================

-- Para verificar:
-- SELECT maquina, fecha_inspeccion, fecha_segunda_inspeccion,
--        dias_hasta_segunda_inspeccion, urgencia_segunda_inspeccion
-- FROM v_inspecciones_completas
-- ORDER BY fecha_segunda_inspeccion ASC;
