-- ============================================
-- AGREGAR: Campo fecha_segunda_realizada
-- Fecha: 2025-11-20
-- Descripción: Registra cuándo se realizó la segunda inspección
--              Permite distinguir entre pendiente y realizada-esperando-materiales
-- ============================================

BEGIN;

-- 1. Agregar columna fecha_segunda_realizada
ALTER TABLE inspecciones
ADD COLUMN IF NOT EXISTS fecha_segunda_realizada DATE;

-- 2. Crear índice
CREATE INDEX IF NOT EXISTS idx_inspecciones_fecha_segunda_realizada
ON inspecciones(fecha_segunda_realizada);

-- 3. Actualizar la vista v_inspecciones_completas
DROP VIEW IF EXISTS v_inspecciones_completas;

CREATE VIEW v_inspecciones_completas AS
SELECT
    i.*,
    o.nombre as oca_nombre,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id) as total_defectos,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'SUBSANADO') as defectos_subsanados,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as defectos_pendientes,
    (SELECT MIN(fecha_limite) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as fecha_limite_proxima,
    -- Información de segunda inspección
    CASE
        WHEN i.fecha_segunda_inspeccion IS NOT NULL THEN
            (i.fecha_segunda_inspeccion - CURRENT_DATE)
        ELSE NULL
    END as dias_hasta_segunda_inspeccion,
    -- Urgencia de segunda inspección (solo si NO se ha realizado)
    CASE
        WHEN i.fecha_segunda_realizada IS NOT NULL THEN 'REALIZADA'
        WHEN i.fecha_segunda_inspeccion IS NULL THEN 'SIN_FECHA'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE THEN 'VENCIDA'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 30 THEN 'URGENTE'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 60 THEN 'PROXIMA'
        ELSE 'NORMAL'
    END as urgencia_segunda_inspeccion,
    -- Contar materiales especiales pendientes (cortinas/pesacargas con 12 meses)
    (SELECT COUNT(*) FROM materiales_especiales m
     WHERE m.inspeccion_id = i.id AND m.estado != 'INSTALADO') as materiales_pendientes,
    -- Estado general de la inspección
    CASE
        WHEN i.fecha_segunda_realizada IS NOT NULL AND
             NOT EXISTS (SELECT 1 FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') AND
             NOT EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'CERRADA'
        WHEN i.fecha_segunda_realizada IS NOT NULL AND
             EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'ESPERANDO_MATERIALES'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE AND i.fecha_segunda_realizada IS NULL
        THEN 'SEGUNDA_VENCIDA'
        WHEN i.fecha_segunda_inspeccion IS NOT NULL AND i.fecha_segunda_realizada IS NULL
        THEN 'SEGUNDA_PENDIENTE'
        ELSE 'ABIERTA'
    END as estado_inspeccion
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

COMMIT;

-- ============================================
-- FIN
-- ============================================

-- Para verificar estados:
-- SELECT maquina, fecha_inspeccion, fecha_segunda_inspeccion, fecha_segunda_realizada,
--        defectos_pendientes, materiales_pendientes, estado_inspeccion,
--        urgencia_segunda_inspeccion
-- FROM v_inspecciones_completas
-- ORDER BY estado_inspeccion, fecha_segunda_inspeccion ASC;
