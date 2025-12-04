-- ============================================
-- MIGRACIÓN: Actualizar vistas para excluir instalaciones y máquinas dadas de baja
-- Fecha: 2025-12-04
-- Descripción: Las vistas ahora filtran solo máquinas e instalaciones con en_cartera = TRUE
-- ============================================

-- Vista: Partes con recomendaciones pendientes de revisar
-- Ahora excluye máquinas e instalaciones fuera de cartera
CREATE OR REPLACE VIEW v_partes_con_recomendaciones AS
SELECT
    p.id,
    p.numero_parte,
    p.tipo_parte_original,
    p.fecha_parte,
    p.resolucion,
    p.recomendaciones_extraidas,
    p.maquina_id,
    m.identificador as maquina_identificador,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio
FROM partes_trabajo p
INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE p.tiene_recomendacion = true
AND p.recomendacion_revisada = false
AND p.oportunidad_creada = false
AND m.en_cartera = true  -- Solo máquinas en cartera
AND i.en_cartera = true  -- Solo instalaciones en cartera
ORDER BY p.fecha_parte DESC;

-- Vista: Índice de Problemas por Máquina
-- Ahora excluye máquinas e instalaciones fuera de cartera
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
        ) * 2)
        +
        (SELECT COUNT(d.id)
         FROM inspecciones insp
         INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
         WHERE insp.maquina = m.identificador
         AND d.estado = 'PENDIENTE'
        )
    ) as indice_problema,

    -- Clasificación de riesgo
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
            ) * 2)
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
            ) * 2)
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
            ) * 2)
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

-- Vista: Resumen de partes por máquina
-- Ahora excluye máquinas e instalaciones fuera de cartera
CREATE OR REPLACE VIEW v_resumen_partes_maquina AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,
    COUNT(p.id) as total_partes,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as total_averias,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO') as total_mantenimientos,
    COUNT(p.id) FILTER (WHERE p.tiene_recomendacion = true) as total_recomendaciones,
    MAX(p.fecha_parte) as ultimo_parte
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true  -- Solo máquinas en cartera
AND i.en_cartera = true    -- Solo instalaciones en cartera
GROUP BY m.id, m.identificador, m.instalacion_id, i.nombre, i.municipio;

-- ============================================
-- VISTAS DEL MÓDULO V2
-- ============================================

-- Vista: Índice de Riesgo de Instalación
-- Actualizar para filtrar instalaciones fuera de cartera
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
     AND mc.en_cartera = true  -- Solo alertas de máquinas en cartera
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
                     AND mc.en_cartera = true  -- Solo alertas de máquinas en cartera
                     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                     AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 5
                ) * 0.30
            )
        )
    , 2) as indice_riesgo_instalacion,
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
                         AND mc.en_cartera = true  -- Solo alertas de máquinas en cartera
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 25 THEN 'ALTO'
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
                         AND mc.en_cartera = true  -- Solo alertas de máquinas en cartera
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 10 THEN 'MEDIO'
        ELSE 'BAJO'
    END as nivel_riesgo_instalacion
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id AND m.en_cartera = true
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
LEFT JOIN v_maquinas_problematicas vmp ON m.id = vmp.maquina_id
LEFT JOIN v_estado_maquinas_semaforico esm ON m.id = esm.maquina_id
WHERE i.en_cartera = true  -- Solo instalaciones en cartera
GROUP BY i.id, i.nombre, i.municipio;

-- Vista: Resumen de Pérdidas por Pendientes
-- Actualizar para filtrar solo máquinas en cartera
CREATE OR REPLACE VIEW v_perdidas_por_pendientes AS
SELECT
    (SELECT COUNT(*)
     FROM partes_trabajo p
     INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE p.tiene_recomendacion = true
     AND p.recomendacion_revisada = false
     AND p.oportunidad_creada = false
     AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) as recomendaciones_vencidas,

    (SELECT COUNT(*)
     FROM partes_trabajo p
     INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE p.tiene_recomendacion = true
     AND p.recomendacion_revisada = false
     AND p.oportunidad_creada = false
     AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) * 350.00 as valor_recomendaciones_perdidas,

    (SELECT COUNT(*)
     FROM alertas_automaticas a
     INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE a.tipo_alerta = 'FALLA_REPETIDA'
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) as fallas_repetidas_activas,

    (SELECT COUNT(*)
     FROM alertas_automaticas a
     INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE a.tipo_alerta = 'FALLA_REPETIDA'
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) * 180.00 as coste_averias_evitables,

    (SELECT COUNT(*)
     FROM oportunidades_facturacion o
     INNER JOIN maquinas_cartera m ON o.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE o.estado = 'DETECTADA'
     AND o.fecha_envio_presupuesto IS NULL
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) as oportunidades_sin_presupuesto,

    (SELECT COALESCE(SUM(o.importe_presupuestado), COUNT(*) * 500.00)
     FROM oportunidades_facturacion o
     INNER JOIN maquinas_cartera m ON o.maquina_id = m.id
     INNER JOIN instalaciones i ON m.instalacion_id = i.id
     WHERE o.estado = 'DETECTADA'
     AND m.en_cartera = true
     AND i.en_cartera = true
    ) as valor_oportunidades_sin_presupuesto,

    (
        (SELECT COUNT(*)
         FROM partes_trabajo p
         INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
         INNER JOIN instalaciones i ON m.instalacion_id = i.id
         WHERE p.tiene_recomendacion = true
         AND p.recomendacion_revisada = false
         AND p.oportunidad_creada = false
         AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
         AND m.en_cartera = true
         AND i.en_cartera = true
        ) * 350.00
        +
        (SELECT COUNT(*)
         FROM alertas_automaticas a
         INNER JOIN maquinas_cartera m ON a.maquina_id = m.id
         INNER JOIN instalaciones i ON m.instalacion_id = i.id
         WHERE a.tipo_alerta = 'FALLA_REPETIDA'
         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
         AND m.en_cartera = true
         AND i.en_cartera = true
        ) * 180.00
        +
        (SELECT COALESCE(SUM(o.importe_presupuestado), COUNT(*) * 500.00)
         FROM oportunidades_facturacion o
         INNER JOIN maquinas_cartera m ON o.maquina_id = m.id
         INNER JOIN instalaciones i ON m.instalacion_id = i.id
         WHERE o.estado = 'DETECTADA'
         AND m.en_cartera = true
         AND i.en_cartera = true
        )
    ) as perdida_total_estimada;
