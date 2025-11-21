-- Migración: Eliminar campos estado y estado_material de inspecciones
-- Fecha: 2025-11-21
-- Razón: Focalizar en gestión de defectos, no en estados generales

-- Eliminar columnas estado y estado_material
ALTER TABLE inspecciones
DROP COLUMN IF EXISTS estado,
DROP COLUMN IF EXISTS estado_material;

-- Actualizar vista v_inspecciones_completas si existe
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;

CREATE OR REPLACE VIEW v_inspecciones_completas AS
SELECT
    i.id,
    i.maquina,
    i.fecha_inspeccion,
    i.fecha_segunda_inspeccion,
    i.fecha_segunda_realizada,
    i.oca_id,
    i.presupuesto,
    i.created_at,
    i.updated_at,
    -- Datos de la OCA
    o.nombre as oca_nombre,
    o.email as oca_email,
    o.telefono as oca_telefono,
    -- Conteo de defectos pendientes
    (SELECT COUNT(*)
     FROM defectos_inspeccion
     WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as defectos_pendientes,
    -- Conteo de materiales especiales pendientes
    (SELECT COUNT(*)
     FROM materiales_especiales
     WHERE inspeccion_id = i.id AND estado != 'INSTALADO') as materiales_pendientes,
    -- Urgencia de segunda inspección (solo si NO se ha realizado)
    CASE
        WHEN i.fecha_segunda_realizada IS NOT NULL THEN 'REALIZADA'
        WHEN i.fecha_segunda_inspeccion IS NULL THEN 'SIN_FECHA'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE THEN 'VENCIDA'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 30 THEN 'URGENTE'
        WHEN (i.fecha_segunda_inspeccion - CURRENT_DATE) <= 60 THEN 'PROXIMA'
        ELSE 'NORMAL'
    END as urgencia_segunda_inspeccion,
    -- Días hasta segunda inspección
    (i.fecha_segunda_inspeccion - CURRENT_DATE) as dias_hasta_segunda,
    -- Estado general de la inspección basado en defectos
    CASE
        WHEN i.fecha_segunda_realizada IS NOT NULL AND
             NOT EXISTS (SELECT 1 FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') AND
             NOT EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'CERRADA'
        WHEN i.fecha_segunda_realizada IS NOT NULL AND
             EXISTS (SELECT 1 FROM materiales_especiales WHERE inspeccion_id = i.id AND estado != 'INSTALADO')
        THEN 'ESPERANDO_MATERIALES'
        WHEN i.fecha_segunda_inspeccion < CURRENT_DATE AND i.fecha_segunda_realizada IS NULL
        THEN 'DEFECTOS_VENCIDOS'
        WHEN i.fecha_segunda_inspeccion IS NOT NULL AND i.fecha_segunda_realizada IS NULL
        THEN 'DEFECTOS_PENDIENTES'
        ELSE 'ABIERTA'
    END as estado_inspeccion
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

-- Comentarios
COMMENT ON VIEW v_inspecciones_completas IS 'Vista completa de inspecciones con información de defectos y materiales pendientes';
