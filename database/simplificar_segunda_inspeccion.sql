-- ============================================
-- SIMPLIFICAR: Campo segunda_realizada como boolean
-- Fecha: 2025-11-20
-- Descripción: Cambia fecha_segunda_realizada a boolean segunda_realizada
--              Solo interesa saber si ya se hizo o no, no cuándo
-- ============================================

BEGIN;

-- 1. Si existe fecha_segunda_realizada, eliminarla y crear el boolean
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_segunda_realizada CASCADE;

ALTER TABLE inspecciones
ADD COLUMN IF NOT EXISTS segunda_realizada BOOLEAN DEFAULT false;

-- 2. Crear índice
CREATE INDEX IF NOT EXISTS idx_inspecciones_segunda_realizada
ON inspecciones(segunda_realizada) WHERE segunda_realizada = true;

-- 3. Actualizar la vista v_inspecciones_completas
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;

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
        WHEN i.segunda_realizada = true THEN 'REALIZADA'
        WHEN i.fecha_segunda_inspeccion IS NULL THEN 'SIN_FECHA'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE THEN 'VENCIDA'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 30 THEN 'URGENTE'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 60 THEN 'PROXIMA'
        ELSE 'NORMAL'
    END as urgencia_segunda_inspeccion,
    -- Contar materiales especiales pendientes
    (SELECT COUNT(*) FROM materiales_especiales m
     WHERE m.inspeccion_id = i.id AND m.estado != 'INSTALADO') as materiales_pendientes,
    -- Estado general de la inspección
    CASE
        WHEN i.segunda_realizada = true AND
             NOT EXISTS (SELECT 1 FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') AND
             NOT EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'CERRADA'
        WHEN i.segunda_realizada = true AND
             EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'ESPERANDO_MATERIALES'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE AND i.segunda_realizada = false
        THEN 'SEGUNDA_VENCIDA'
        WHEN i.fecha_segunda_inspeccion IS NOT NULL AND i.segunda_realizada = false
        THEN 'SEGUNDA_PENDIENTE'
        ELSE 'ABIERTA'
    END as estado_inspeccion
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

COMMIT;

-- ============================================
-- FIN
-- ============================================

-- Para verificar:
-- SELECT maquina, fecha_segunda_inspeccion, segunda_realizada,
--        materiales_pendientes, estado_inspeccion
-- FROM v_inspecciones_completas
-- ORDER BY estado_inspeccion, fecha_segunda_inspeccion ASC;
