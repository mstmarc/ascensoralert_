-- Migración: Agregar IDs a vistas para permitir enlaces a vistas detalladas
-- Fecha: 2025-11-30

-- Eliminar vistas existentes antes de recrearlas
DROP VIEW IF EXISTS v_maquinas_problematicas;
DROP VIEW IF EXISTS v_partes_con_recomendaciones;

-- Actualizar vista de máquinas problemáticas para incluir instalacion_id
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
    -- Fórmula: (averías_trimestre * 3) + (averías_mes * 5) + (partes_pendientes_urgentes * 2) + defectos_pendientes
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
GROUP BY m.id, m.identificador, m.instalacion_id, i.nombre, i.municipio;


-- Actualizar vista de partes con recomendaciones para incluir IDs
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
ORDER BY p.fecha_parte DESC;
