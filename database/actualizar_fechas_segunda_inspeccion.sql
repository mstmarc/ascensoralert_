-- Actualizar fecha_segunda_inspeccion para TODAS las inspecciones existentes
-- Calcula automáticamente: fecha_inspeccion + 6 meses
-- Fecha: 2025-11-21

-- Actualizar todas las inspecciones que NO tienen fecha_segunda_inspeccion
UPDATE inspecciones
SET fecha_segunda_inspeccion = fecha_inspeccion + INTERVAL '6 months'
WHERE fecha_segunda_inspeccion IS NULL
  AND fecha_inspeccion IS NOT NULL;

-- Verificar resultados
SELECT
    id,
    maquina,
    fecha_inspeccion,
    fecha_segunda_inspeccion,
    (fecha_segunda_inspeccion - CURRENT_DATE) as dias_hasta_limite
FROM inspecciones
ORDER BY fecha_segunda_inspeccion ASC;

-- Resumen
SELECT
    COUNT(*) as total_inspecciones,
    COUNT(fecha_segunda_inspeccion) as con_fecha_limite,
    COUNT(*) - COUNT(fecha_segunda_inspeccion) as sin_fecha_limite
FROM inspecciones;
