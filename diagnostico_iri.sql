-- ============================================
-- SCRIPT DE DIAGNÓSTICO DEL IRI
-- Verificar por qué no aparecen máquinas en el IRI
-- ============================================

\echo '=========================================='
\echo 'DIAGNÓSTICO 1: Estado de Instalaciones'
\echo '=========================================='

SELECT
    'Total instalaciones' as metrica,
    COUNT(*) as cantidad
FROM instalaciones
UNION ALL
SELECT
    'Instalaciones EN cartera (en_cartera = TRUE)',
    COUNT(*)
FROM instalaciones
WHERE en_cartera = true
UNION ALL
SELECT
    'Instalaciones FUERA de cartera (en_cartera = FALSE)',
    COUNT(*)
FROM instalaciones
WHERE en_cartera = false OR en_cartera IS NULL;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 2: Estado de Máquinas'
\echo '=========================================='

SELECT
    'Total máquinas' as metrica,
    COUNT(*) as cantidad
FROM maquinas_cartera
UNION ALL
SELECT
    'Máquinas EN cartera (en_cartera = TRUE)',
    COUNT(*)
FROM maquinas_cartera
WHERE en_cartera = true
UNION ALL
SELECT
    'Máquinas FUERA de cartera (en_cartera = FALSE)',
    COUNT(*)
FROM maquinas_cartera
WHERE en_cartera = false OR en_cartera IS NULL;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 3: Máquinas EN cartera por instalación'
\echo '=========================================='

SELECT
    i.id,
    i.nombre,
    i.municipio,
    i.en_cartera as instalacion_en_cartera,
    COUNT(m.id) as total_maquinas,
    COUNT(m.id) FILTER (WHERE m.en_cartera = true) as maquinas_en_cartera,
    COUNT(m.id) FILTER (WHERE m.en_cartera = false OR m.en_cartera IS NULL) as maquinas_fuera_cartera
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id
GROUP BY i.id, i.nombre, i.municipio, i.en_cartera
ORDER BY total_maquinas DESC
LIMIT 20;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 4: Verificar Vista v_riesgo_instalaciones'
\echo '=========================================='

SELECT
    COUNT(*) as total_instalaciones_con_iri
FROM v_riesgo_instalaciones;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 5: Top 10 Instalaciones por IRI (actual)'
\echo '=========================================='

SELECT
    instalacion_nombre,
    municipio,
    total_maquinas,
    maquinas_criticas,
    maquinas_inestables,
    promedio_indice_problema,
    alertas_activas,
    pendientes_urgentes,
    indice_riesgo_instalacion as iri,
    nivel_riesgo_instalacion
FROM v_riesgo_instalaciones
ORDER BY indice_riesgo_instalacion DESC
LIMIT 10;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 6: Distribución de IRI'
\echo '=========================================='

SELECT
    nivel_riesgo_instalacion,
    COUNT(*) as cantidad,
    ROUND(AVG(indice_riesgo_instalacion), 2) as iri_promedio,
    MIN(indice_riesgo_instalacion) as iri_min,
    MAX(indice_riesgo_instalacion) as iri_max
FROM v_riesgo_instalaciones
GROUP BY nivel_riesgo_instalacion
ORDER BY
    CASE nivel_riesgo_instalacion
        WHEN 'CRITICO' THEN 1
        WHEN 'ALTO' THEN 2
        WHEN 'MEDIO' THEN 3
        WHEN 'BAJO' THEN 4
    END;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 7: Estadísticas de Averías Recientes'
\echo '=========================================='

SELECT
    'Máquinas con averías en último mes' as metrica,
    COUNT(DISTINCT m.id) as cantidad
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
INNER JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true
AND i.en_cartera = true
AND p.tipo_parte_normalizado = 'AVERIA'
AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
UNION ALL
SELECT
    'Máquinas con averías en último trimestre',
    COUNT(DISTINCT m.id)
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
INNER JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true
AND i.en_cartera = true
AND p.tipo_parte_normalizado = 'AVERIA'
AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
UNION ALL
SELECT
    'Máquinas sin averías registradas (último año)',
    COUNT(DISTINCT m.id)
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
    AND p.tipo_parte_normalizado = 'AVERIA'
    AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
WHERE m.en_cartera = true
AND i.en_cartera = true
AND p.id IS NULL;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 8: Estado Semafórico de Máquinas'
\echo '=========================================='

SELECT
    estado_semaforico,
    COUNT(*) as cantidad_maquinas
FROM v_estado_maquinas_semaforico
GROUP BY estado_semaforico
ORDER BY
    CASE estado_semaforico
        WHEN 'CRITICO' THEN 1
        WHEN 'INESTABLE' THEN 2
        WHEN 'SEGUIMIENTO' THEN 3
        WHEN 'ESTABLE' THEN 4
    END;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 9: Alertas Activas'
\echo '=========================================='

SELECT
    'Total alertas activas' as metrica,
    COUNT(*) as cantidad
FROM alertas_automaticas a
INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE a.estado IN ('PENDIENTE', 'EN_REVISION')
AND m.en_cartera = true
AND i.en_cartera = true
UNION ALL
SELECT
    'Alertas URGENTES activas',
    COUNT(*)
FROM alertas_automaticas a
INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE a.estado IN ('PENDIENTE', 'EN_REVISION')
AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
AND m.en_cartera = true
AND i.en_cartera = true
UNION ALL
SELECT
    'Alertas de FALLA_REPETIDA activas',
    COUNT(*)
FROM alertas_automaticas a
INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE a.estado IN ('PENDIENTE', 'EN_REVISION')
AND a.tipo_alerta = 'FALLA_REPETIDA'
AND m.en_cartera = true
AND i.en_cartera = true;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 10: Pendientes Técnicos'
\echo '=========================================='

SELECT
    nivel_urgencia,
    estado,
    COUNT(*) as cantidad
FROM pendientes_tecnicos
WHERE estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
GROUP BY nivel_urgencia, estado
ORDER BY
    CASE nivel_urgencia
        WHEN 'URGENTE' THEN 1
        WHEN 'ALTA' THEN 2
        WHEN 'MEDIA' THEN 3
        WHEN 'BAJA' THEN 4
    END;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 11: Índice de Problema por Máquina (Top 20)'
\echo '=========================================='

SELECT
    identificador,
    instalacion_nombre,
    averias_ultimo_mes,
    averias_ultimo_trimestre,
    partes_pendientes_urgentes,
    defectos_inspeccion_pendientes,
    indice_problema,
    nivel_riesgo
FROM v_maquinas_problematicas
ORDER BY indice_problema DESC
LIMIT 20;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 12: Instalaciones SIN datos (IRI = 0 o muy bajo)'
\echo '=========================================='

SELECT
    instalacion_nombre,
    municipio,
    total_maquinas,
    promedio_indice_problema,
    maquinas_criticas,
    maquinas_inestables,
    alertas_activas,
    pendientes_urgentes,
    indice_riesgo_instalacion as iri
FROM v_riesgo_instalaciones
WHERE indice_riesgo_instalacion < 5
ORDER BY total_maquinas DESC
LIMIT 10;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 13: Componentes del IRI - Desglose Detallado'
\echo '=========================================='

SELECT
    instalacion_nombre,
    municipio,
    -- Componente 1: Promedio índice (30%)
    ROUND((COALESCE(promedio_indice_problema, 0) * 2) * 0.30, 2) as componente_indice,
    -- Componente 2: Máquinas críticas (40%)
    ROUND((maquinas_criticas * 20 + maquinas_inestables * 10) * 0.40, 2) as componente_maquinas,
    -- Componente 3: Alertas y pendientes (30%)
    ROUND((pendientes_urgentes * 8 + alertas_activas * 5) * 0.30, 2) as componente_alertas,
    -- Total
    indice_riesgo_instalacion as iri_total,
    nivel_riesgo_instalacion
FROM v_riesgo_instalaciones
ORDER BY indice_riesgo_instalacion DESC
LIMIT 10;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO 14: Simulación IRI con Umbrales Ajustados'
\echo '=========================================='

SELECT
    instalacion_nombre,
    indice_riesgo_instalacion as iri,
    nivel_riesgo_instalacion as clasificacion_actual,
    CASE
        WHEN indice_riesgo_instalacion >= 40 THEN 'CRÍTICO'
        WHEN indice_riesgo_instalacion >= 15 THEN 'ALTO'
        WHEN indice_riesgo_instalacion >= 5 THEN 'MEDIO'
        ELSE 'BAJO'
    END as clasificacion_propuesta,
    CASE
        WHEN nivel_riesgo_instalacion != CASE
            WHEN indice_riesgo_instalacion >= 40 THEN 'CRÍTICO'
            WHEN indice_riesgo_instalacion >= 15 THEN 'ALTO'
            WHEN indice_riesgo_instalacion >= 5 THEN 'MEDIO'
            ELSE 'BAJO'
        END THEN '✅ CAMBIARÍA'
        ELSE 'Sin cambio'
    END as impacto
FROM v_riesgo_instalaciones
ORDER BY indice_riesgo_instalacion DESC
LIMIT 20;

\echo ''
\echo '=========================================='
\echo 'DIAGNÓSTICO COMPLETADO'
\echo '=========================================='
\echo ''
\echo 'CONCLUSIONES:'
\echo '1. Si "Total instalaciones EN cartera" = 0 → REACTIVAR INSTALACIONES'
\echo '2. Si "Total máquinas EN cartera" = 0 → REACTIVAR MÁQUINAS'
\echo '3. Si IRI máximo < 25 → AJUSTAR UMBRALES (bajar de 25 a 15 para ALTO)'
\echo '4. Si no hay alertas activas → EJECUTAR DETECTORES'
\echo '5. Si no hay averías recientes → VERIFICAR IMPORTACIÓN DE DATOS'
\echo ''
