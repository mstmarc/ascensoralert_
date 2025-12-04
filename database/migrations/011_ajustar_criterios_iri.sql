-- ============================================
-- MIGRACIÓN: Ajustar criterios del IRI para mayor sensibilidad
-- Fecha: 2025-12-04
-- Descripción: Ajusta umbrales y criterios del IRI para que más instalaciones sean detectadas
-- ============================================

-- CAMBIOS PROPUESTOS:
-- 1. Ajustar umbrales de clasificación IRI (ALTO: 25→15, MEDIO: 10→5, agregar CRÍTICO: ≥40)
-- 2. Aumentar peso de pendientes urgentes en índice_problema (2→3)
-- 3. Suavizar criterios de máquinas CRÍTICAS en semáforo
-- 4. Mantener fórmula base del IRI

-- ============================================
-- PASO 1: Actualizar Vista v_maquinas_problematicas
-- Cambio: Aumentar multiplicador de pendientes urgentes de 2 a 3
-- ============================================

CREATE OR REPLACE VIEW v_maquinas_problematicas AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Métricas de averías
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as averias_ultimo_año,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_ultimo_trimestre,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_ultimo_mes,

    -- Tendencia (comparar último trimestre vs trimestre anterior)
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) - COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '6 months'
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '3 months'
    ) as tendencia_averias,

    -- Mantenimientos realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_realizados_año,

    -- Mantenimientos pendientes/cancelados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado IN ('PENDIENTE', 'CANCELADO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_no_realizados,

    -- Costes
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_averias_año,

    -- Facturación pendiente
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.estado = 'COMPLETADO'
        AND p.facturado = false
    ), 0) as facturacion_pendiente,

    -- Partes pendientes actuales
    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes,

    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
        AND p.prioridad IN ('URGENTE', 'ALTA')
    ) as partes_pendientes_urgentes,

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,

    -- Días desde última intervención
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,

    -- Defectos de inspección pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_inspeccion_pendientes,

    -- Calcular ÍNDICE DE PROBLEMA (score compuesto)
    -- CAMBIO: Pendientes urgentes ahora × 3 (antes × 2)
    (
        (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'AVERIA'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
        ) * 3)
        +
        (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'AVERIA'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
        ) * 5)
        +
        (COUNT(p.id) FILTER (
            WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
            AND p.prioridad IN ('URGENTE', 'ALTA')
        ) * 3)  -- ⬅️ CAMBIO: de 2 a 3
        +
        (SELECT COUNT(d.id)
         FROM inspecciones insp
         INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
         WHERE insp.maquina = m.identificador
         AND d.estado = 'PENDIENTE'
        )
    ) as indice_problema,

    -- Clasificación de riesgo (sin cambios en umbrales)
    CASE
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 3)  -- ⬅️ CAMBIO: de 2 a 3
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 15 THEN 'CRITICO'
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 3)  -- ⬅️ CAMBIO: de 2 a 3
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 8 THEN 'ALTO'
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 3)  -- ⬅️ CAMBIO: de 2 a 3
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 3 THEN 'MEDIO'
        ELSE 'BAJO'
    END as nivel_riesgo

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true  -- Solo máquinas en cartera
AND i.en_cartera = true    -- Solo instalaciones en cartera
GROUP BY m.id, m.identificador, m.instalacion_id, i.nombre, i.municipio
ORDER BY indice_problema DESC;

-- ============================================
-- PASO 2: Actualizar Vista v_riesgo_instalaciones
-- Cambios:
-- - Agregar nivel CRÍTICO (IRI ≥ 40)
-- - Bajar umbral ALTO de 25 a 15
-- - Bajar umbral MEDIO de 10 a 5
-- ============================================

CREATE OR REPLACE VIEW v_riesgo_instalaciones AS
SELECT
    i.id as instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,
    COUNT(DISTINCT m.id) as total_maquinas,
    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') as maquinas_criticas,
    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') as maquinas_inestables,
    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'SEGUIMIENTO') as maquinas_seguimiento,
    ROUND(AVG(vmp.indice_problema), 2) as promedio_indice_problema,
    (SELECT COUNT(*)
     FROM alertas_automaticas a
     INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
     WHERE mc.instalacion_id = i.id
     AND mc.en_cartera = true
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as alertas_activas,
    (SELECT COUNT(*)
     FROM pendientes_tecnicos pt
     WHERE pt.instalacion_id = i.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
     AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
    ) as pendientes_urgentes,
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre_instalacion,
    -- Fórmula del IRI (sin cambios)
    ROUND(
        (
            (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
            +
            (
                (
                    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                ) * 0.40
            )
            +
            (
                (
                    (SELECT COUNT(*)
                     FROM pendientes_tecnicos pt
                     WHERE pt.instalacion_id = i.id
                     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                     AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 8
                    +
                    (SELECT COUNT(*)
                     FROM alertas_automaticas a
                     INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                     WHERE mc.instalacion_id = i.id
                     AND mc.en_cartera = true
                     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                     AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 5
                ) * 0.30
            )
        )
    , 2) as indice_riesgo_instalacion,
    -- Clasificación de nivel de riesgo (AJUSTADA)
    CASE
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND mc.en_cartera = true
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 40 THEN 'CRÍTICO'  -- ⬅️ NUEVO: Nivel crítico para IRI muy alto
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND mc.en_cartera = true
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 15 THEN 'ALTO'  -- ⬅️ CAMBIO: de 25 a 15
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND mc.en_cartera = true
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 5 THEN 'MEDIO'  -- ⬅️ CAMBIO: de 10 a 5
        ELSE 'BAJO'
    END as nivel_riesgo_instalacion
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id AND m.en_cartera = true
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
LEFT JOIN v_maquinas_problematicas vmp ON m.id = vmp.maquina_id
LEFT JOIN v_estado_maquinas_semaforico esm ON m.id = esm.maquina_id
WHERE i.en_cartera = true
GROUP BY i.id, i.nombre, i.municipio;

-- ============================================
-- RESUMEN DE CAMBIOS APLICADOS
-- ============================================
-- 1. ✅ Aumentado peso de pendientes urgentes (×2 → ×3) en v_maquinas_problematicas
-- 2. ✅ Agregado nivel CRÍTICO (IRI ≥ 40) en v_riesgo_instalaciones
-- 3. ✅ Bajado umbral ALTO (25 → 15) en v_riesgo_instalaciones
-- 4. ✅ Bajado umbral MEDIO (10 → 5) en v_riesgo_instalaciones
-- ============================================

-- Verificar cambios
SELECT 'Migración 011 completada exitosamente' as resultado;
