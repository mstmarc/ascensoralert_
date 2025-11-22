-- Recalcular fecha_segunda_inspeccion para TODAS las inspecciones existentes
-- Este script actualiza TODAS las inspecciones (incluso las que ya tienen fecha_segunda_inspeccion)
-- para asegurar que la fecha límite esté correctamente calculada como fecha_inspeccion + 6 meses
-- Fecha: 2025-11-22

-- IMPORTANTE: Solo actualiza las inspecciones que NO han sido verificadas aún
-- (donde fecha_segunda_realizada es NULL)

-- Actualizar TODAS las inspecciones pendientes de verificación
UPDATE inspecciones
SET fecha_segunda_inspeccion = fecha_inspeccion + INTERVAL '6 months'
WHERE fecha_inspeccion IS NOT NULL
  AND fecha_segunda_realizada IS NULL;

-- Verificar resultados
SELECT
    id,
    maquina,
    fecha_inspeccion,
    fecha_segunda_inspeccion,
    fecha_segunda_realizada,
    (fecha_segunda_inspeccion - CURRENT_DATE) as dias_hasta_limite,
    CASE
        WHEN fecha_segunda_realizada IS NOT NULL THEN 'COMPLETADA'
        WHEN fecha_segunda_inspeccion < CURRENT_DATE THEN 'VENCIDA'
        WHEN (fecha_segunda_inspeccion - CURRENT_DATE) <= 30 THEN 'URGENTE'
        WHEN (fecha_segunda_inspeccion - CURRENT_DATE) <= 60 THEN 'PRÓXIMA'
        ELSE 'NORMAL'
    END as categoria
FROM inspecciones
ORDER BY fecha_segunda_inspeccion ASC NULLS LAST;

-- Resumen de actualización
SELECT
    COUNT(*) as total_inspecciones,
    COUNT(fecha_segunda_inspeccion) as con_fecha_limite,
    COUNT(fecha_segunda_realizada) as completadas,
    COUNT(*) FILTER (WHERE fecha_segunda_inspeccion < CURRENT_DATE AND fecha_segunda_realizada IS NULL) as vencidas,
    COUNT(*) FILTER (WHERE (fecha_segunda_inspeccion - CURRENT_DATE) <= 30 AND fecha_segunda_realizada IS NULL) as urgentes
FROM inspecciones;
