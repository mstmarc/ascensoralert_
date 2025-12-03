-- ============================================
-- VERIFICACIÓN DE DATOS PARA DETECTORES V2
-- ============================================

-- 1. Verificar componentes críticos (debe mostrar 12)
SELECT COUNT(*) as total_componentes FROM componentes_criticos;
SELECT nombre, familia FROM componentes_criticos LIMIT 5;

-- 2. Verificar si hay recomendaciones detectadas
SELECT COUNT(*) as total_recomendaciones
FROM partes_trabajo
WHERE tiene_recomendacion = true;

SELECT COUNT(*) as recomendaciones_pendientes
FROM partes_trabajo
WHERE tiene_recomendacion = true
AND recomendacion_revisada = false;

-- 3. Ver ejemplos de textos de resolución (para ver si coinciden con keywords)
SELECT
    id,
    numero_parte,
    LEFT(resolucion, 100) as resolucion_inicio,
    tipo_parte_normalizado
FROM partes_trabajo
WHERE tipo_parte_normalizado = 'AVERIA'
AND fecha_parte >= CURRENT_DATE - INTERVAL '90 days'
LIMIT 10;

-- 4. Verificar si hay máquinas en estado CRITICO
SELECT COUNT(*) as maquinas_criticas
FROM v_estado_maquinas_semaforico
WHERE estado_semaforico = 'CRITICO';

SELECT
    identificador,
    estado_semaforico,
    averias_mes,
    averias_trimestre
FROM v_estado_maquinas_semaforico
WHERE estado_semaforico IN ('CRITICO', 'INESTABLE')
LIMIT 10;

-- 5. Verificar mantenimientos recientes por máquina
SELECT
    m.identificador,
    MAX(p.fecha_parte) as ultimo_mantenimiento,
    CURRENT_DATE - MAX(p.fecha_parte)::date as dias_sin_mantenimiento
FROM maquinas_cartera m
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
    AND p.tipo_parte_normalizado = 'MANTENIMIENTO'
WHERE m.en_cartera = true
GROUP BY m.id, m.identificador
ORDER BY dias_sin_mantenimiento DESC NULLS FIRST
LIMIT 10;

-- 6. Ver si hay instalaciones con múltiples averías
SELECT
    i.nombre as instalacion,
    COUNT(p.id) as averias_ultimo_mes
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id
INNER JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE p.tipo_parte_normalizado = 'AVERIA'
AND p.fecha_parte >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY i.id, i.nombre
HAVING COUNT(p.id) >= 5
ORDER BY averias_ultimo_mes DESC;

-- 7. Buscar posibles fallas repetidas manualmente
-- (agrupar averías por máquina para ver si hay componentes que se repiten)
SELECT
    m.identificador,
    COUNT(*) as total_averias,
    STRING_AGG(LEFT(p.resolucion, 50), ' | ') as resoluciones
FROM maquinas_cartera m
INNER JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE p.tipo_parte_normalizado = 'AVERIA'
AND p.fecha_parte >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY m.id, m.identificador
HAVING COUNT(*) >= 2
ORDER BY total_averias DESC
LIMIT 10;
