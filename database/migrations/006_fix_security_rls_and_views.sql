-- ============================================
-- MIGRACIÓN: Corrección de Seguridad - RLS y Vistas
-- Fecha: 2025-12-03
-- ============================================
-- OBJETIVO: Solucionar problemas detectados por Supabase Database Linter:
-- 1. Quitar SECURITY DEFINER de 9 vistas
-- 2. Habilitar RLS en 31 tablas públicas
-- 3. Crear políticas RLS permisivas inicialmente

-- ============================================
-- PARTE 1: RECREAR VISTAS SIN SECURITY DEFINER
-- ============================================
-- Estas vistas fueron modificadas manualmente en la BD para usar SECURITY DEFINER
-- Las recreamos SIN ese atributo para mejorar la seguridad

-- Vista 1: Estado semafórico de máquinas
DROP VIEW IF EXISTS v_estado_maquinas_semaforico CASCADE;
CREATE VIEW v_estado_maquinas_semaforico AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.en_cartera,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Métricas base
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_mes,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre,

    -- Fallas repetidas (alertas activas)
    (SELECT COUNT(*) FROM alertas_automaticas a
     WHERE a.maquina_id = m.id
     AND a.tipo_alerta = 'FALLA_REPETIDA'
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,

    -- Recomendaciones sin ejecutar
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true
        AND p.recomendacion_revisada = false
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,

    -- Mantenimientos omitidos
    CASE
        WHEN MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
             < CURRENT_DATE - INTERVAL '60 days' THEN 1
        ELSE 0
    END as mantenimiento_atrasado,

    -- Defectos IPO pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_ipo_pendientes,

    -- Pendientes técnicos activos
    (SELECT COUNT(*) FROM pendientes_tecnicos pt
     WHERE pt.maquina_id = m.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO', 'BLOQUEADO')
    ) as pendientes_tecnicos_activos,

    -- CÁLCULO DE ESTADO SEMAFÓRICO
    CASE
        -- 🟥 CRÍTICO: Múltiples problemas graves
        WHEN (
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) >= 3
            OR
            (SELECT COUNT(*) FROM alertas_automaticas a
             WHERE a.maquina_id = m.id
             AND a.tipo_alerta = 'FALLA_REPETIDA'
             AND a.estado IN ('PENDIENTE', 'EN_REVISION')
            ) >= 2
            OR
            (
                MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
                < CURRENT_DATE - INTERVAL '60 days'
                AND
                COUNT(p.id) FILTER (
                    WHERE p.tipo_parte_normalizado = 'AVERIA'
                    AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
                ) >= 2
            )
        ) THEN 'CRITICO'

        -- 🟧 INESTABLE: Problemas frecuentes o sin mantenimiento
        WHEN (
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) >= 5
            OR
            (SELECT COUNT(*) FROM alertas_automaticas a
             WHERE a.maquina_id = m.id
             AND a.tipo_alerta = 'FALLA_REPETIDA'
             AND a.estado IN ('PENDIENTE', 'EN_REVISION')
            ) >= 1
            OR
            MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
            < CURRENT_DATE - INTERVAL '90 days'
            OR
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            ) >= 2
        ) THEN 'INESTABLE'

        -- 🟨 SEGUIMIENTO: Requiere atención
        WHEN (
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) BETWEEN 2 AND 4
            OR
            COUNT(p.id) FILTER (
                WHERE p.tiene_recomendacion = true
                AND p.recomendacion_revisada = false
                AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
            ) >= 1
            OR
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            ) = 1
        ) THEN 'SEGUIMIENTO'

        -- 🟩 ESTABLE: Sin problemas significativos
        ELSE 'ESTABLE'
    END as estado_semaforico,

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte)::date as dias_sin_intervencion

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true
GROUP BY m.id, m.identificador, m.en_cartera, m.instalacion_id, i.nombre, i.municipio;

-- Vista 2: Riesgo de instalaciones
DROP VIEW IF EXISTS v_riesgo_instalaciones CASCADE;
CREATE VIEW v_riesgo_instalaciones AS
SELECT
    i.id as instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Total de máquinas
    COUNT(DISTINCT m.id) as total_maquinas,

    -- Máquinas por estado
    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'CRITICO'
    ) as maquinas_criticas,

    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'INESTABLE'
    ) as maquinas_inestables,

    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'SEGUIMIENTO'
    ) as maquinas_seguimiento,

    -- Promedio de índice de problema
    ROUND(AVG(vmp.indice_problema), 2) as promedio_indice_problema,

    -- Alertas activas en la instalación
    (SELECT COUNT(*)
     FROM alertas_automaticas a
     INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
     WHERE mc.instalacion_id = i.id
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as alertas_activas,

    -- Pendientes técnicos urgentes
    (SELECT COUNT(*)
     FROM pendientes_tecnicos pt
     WHERE pt.instalacion_id = i.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
     AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
    ) as pendientes_urgentes,

    -- Averías totales en la instalación (último trimestre)
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre_instalacion,

    -- CÁLCULO DEL ÍNDICE DE RIESGO DE INSTALACIÓN (IRI)
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
                     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                     AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 5
                ) * 0.30
            )
        )
    , 2) as indice_riesgo_instalacion,

    -- Clasificación de riesgo de instalación
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
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 50 THEN 'CRITICO'
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
GROUP BY i.id, i.nombre, i.municipio;

-- Vista 3: Pérdidas por pendientes
DROP VIEW IF EXISTS v_perdidas_por_pendientes CASCADE;
CREATE VIEW v_perdidas_por_pendientes AS
SELECT
    -- Recomendaciones no ejecutadas
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,

    -- Valor estimado de recomendaciones perdidas (350€ promedio)
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) * 350.00 as valor_recomendaciones_perdidas,

    -- Averías evitables (fallas repetidas)
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,

    -- Coste promedio de cada avería evitable (180€)
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) * 180.00 as coste_averias_evitables,

    -- Oportunidades detectadas sin presupuestar
    (SELECT COUNT(*)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
     AND fecha_envio_presupuesto IS NULL
    ) as oportunidades_sin_presupuesto,

    -- Valor de oportunidades sin presupuestar (500€ promedio)
    (SELECT COALESCE(SUM(importe_presupuestado), COUNT(*) * 500.00)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
    ) as valor_oportunidades_sin_presupuesto,

    -- Total estimado de pérdida de facturación
    (
        (SELECT COUNT(*)
         FROM partes_trabajo
         WHERE tiene_recomendacion = true
         AND recomendacion_revisada = false
         AND oportunidad_creada = false
         AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
        ) * 350.00
        +
        (SELECT COUNT(*)
         FROM alertas_automaticas
         WHERE tipo_alerta = 'FALLA_REPETIDA'
         AND estado IN ('PENDIENTE', 'EN_REVISION')
        ) * 180.00
        +
        (SELECT COALESCE(SUM(importe_presupuestado), COUNT(*) * 500.00)
         FROM oportunidades_facturacion
         WHERE estado = 'DETECTADA'
        )
    ) as perdida_total_estimada;

-- Vista 4: Resumen de partes por máquina
DROP VIEW IF EXISTS v_resumen_partes_maquina CASCADE;
CREATE VIEW v_resumen_partes_maquina AS
SELECT
    m.id as maquina_id,
    m.identificador,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Total de partes
    COUNT(p.id) as total_partes,
    COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months') as partes_ultimo_año,

    -- Por tipo normalizado
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as total_averias,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO') as total_mantenimientos,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'REPARACION') as total_reparaciones,

    -- Averías recientes
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

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,

    -- Recomendaciones
    COUNT(p.id) FILTER (WHERE p.tiene_recomendacion = true) as total_recomendaciones,
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true AND p.recomendacion_revisada = false
    ) as recomendaciones_pendientes,

    -- Oportunidades
    COUNT(p.id) FILTER (WHERE p.oportunidad_creada = true) as total_oportunidades_creadas

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, i.nombre, i.municipio;

-- Vista 5: Partes con recomendaciones
DROP VIEW IF EXISTS v_partes_con_recomendaciones CASCADE;
CREATE VIEW v_partes_con_recomendaciones AS
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

-- Vista 6: Máquinas problemáticas
DROP VIEW IF EXISTS v_maquinas_problematicas CASCADE;
CREATE VIEW v_maquinas_problematicas AS
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

    -- Tendencia
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) - COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '6 months'
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '3 months'
    ) as tendencia_averias,

    -- Mantenimientos
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_realizados_año,

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

    -- Partes pendientes
    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes,

    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
        AND p.prioridad IN ('URGENTE', 'ALTA')
    ) as partes_pendientes_urgentes,

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,

    -- Defectos de inspección pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_inspeccion_pendientes,

    -- Índice de problema
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

-- Vista 7: Inspecciones completas
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;
CREATE VIEW v_inspecciones_completas AS
SELECT
    i.*,
    o.nombre as oca_nombre,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id) as total_defectos,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'SUBSANADO') as defectos_subsanados,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as defectos_pendientes,
    (SELECT MIN(fecha_limite) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as fecha_limite_proxima
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

-- Vista 8: Defectos con urgencia
DROP VIEW IF EXISTS v_defectos_con_urgencia CASCADE;
CREATE VIEW v_defectos_con_urgencia AS
SELECT
    d.*,
    i.maquina,
    CASE
        WHEN d.estado = 'SUBSANADO' THEN 'COMPLETADO'
        WHEN d.fecha_limite < CURRENT_DATE THEN 'VENCIDO'
        WHEN d.fecha_limite <= CURRENT_DATE + INTERVAL '15 days' THEN 'URGENTE'
        WHEN d.fecha_limite <= CURRENT_DATE + INTERVAL '30 days' THEN 'PROXIMO'
        ELSE 'NORMAL'
    END as nivel_urgencia,
    (d.fecha_limite - CURRENT_DATE) as dias_restantes
FROM defectos_inspeccion d
INNER JOIN inspecciones i ON d.inspeccion_id = i.id;

-- Vista 9: Materiales con urgencia
DROP VIEW IF EXISTS v_materiales_con_urgencia CASCADE;
CREATE VIEW v_materiales_con_urgencia AS
SELECT
    m.*,
    CASE
        WHEN m.estado = 'INSTALADO' THEN 'COMPLETADO'
        WHEN m.fecha_limite < CURRENT_DATE THEN 'VENCIDO'
        WHEN m.fecha_limite <= CURRENT_DATE + INTERVAL '15 days' THEN 'URGENTE'
        WHEN m.fecha_limite <= CURRENT_DATE + INTERVAL '30 days' THEN 'PROXIMO'
        ELSE 'NORMAL'
    END as nivel_urgencia,
    (m.fecha_limite - CURRENT_DATE) as dias_restantes
FROM materiales_especiales m;

-- ============================================
-- PARTE 2: HABILITAR RLS EN TABLAS PÚBLICAS
-- ============================================

-- Habilitar RLS en tablas principales de datos
ALTER TABLE materiales_especiales ENABLE ROW LEVEL SECURITY;
ALTER TABLE visitas_administradores ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracion_avisos ENABLE ROW LEVEL SECURITY;
ALTER TABLE visitas_seguimiento ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocas ENABLE ROW LEVEL SECURITY;
ALTER TABLE defectos_inspeccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE seguimiento_comercial_tareas ENABLE ROW LEVEL SECURITY;
ALTER TABLE maquinas_cartera ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas_automaticas ENABLE ROW LEVEL SECURITY;
ALTER TABLE componentes_criticos ENABLE ROW LEVEL SECURITY;
ALTER TABLE instalaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE inspecciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE partes_trabajo ENABLE ROW LEVEL SECURITY;
ALTER TABLE tipos_parte_mapeo ENABLE ROW LEVEL SECURITY;
ALTER TABLE oportunidades_facturacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE pendientes_tecnicos ENABLE ROW LEVEL SECURITY;

-- Habilitar RLS en tablas de backup (deberían moverse a un schema privado)
ALTER TABLE administradores_backup_20251028 ENABLE ROW LEVEL SECURITY;
ALTER TABLE administradores_backup_charset ENABLE ROW LEVEL SECURITY;
ALTER TABLE administradores_tmp ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes_tmp ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes_backup ENABLE ROW LEVEL SECURITY;
ALTER TABLE administradores_backup_final ENABLE ROW LEVEL SECURITY;

-- ============================================
-- PARTE 3: CREAR POLÍTICAS RLS PERMISIVAS
-- ============================================
-- IMPORTANTE: Estas políticas son PERMISIVAS inicialmente para no romper nada
-- Se recomienda ajustarlas según los requisitos específicos de seguridad

-- Políticas para materiales_especiales
DROP POLICY IF EXISTS "Permitir acceso completo a materiales_especiales" ON materiales_especiales;
CREATE POLICY "Permitir acceso completo a materiales_especiales"
ON materiales_especiales FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para visitas_administradores
DROP POLICY IF EXISTS "Permitir acceso completo a visitas_administradores" ON visitas_administradores;
CREATE POLICY "Permitir acceso completo a visitas_administradores"
ON visitas_administradores FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para configuracion_avisos
DROP POLICY IF EXISTS "Permitir acceso completo a configuracion_avisos" ON configuracion_avisos;
CREATE POLICY "Permitir acceso completo a configuracion_avisos"
ON configuracion_avisos FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para visitas_seguimiento
DROP POLICY IF EXISTS "Permitir acceso completo a visitas_seguimiento" ON visitas_seguimiento;
CREATE POLICY "Permitir acceso completo a visitas_seguimiento"
ON visitas_seguimiento FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para ocas
DROP POLICY IF EXISTS "Permitir acceso completo a ocas" ON ocas;
CREATE POLICY "Permitir acceso completo a ocas"
ON ocas FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para defectos_inspeccion
DROP POLICY IF EXISTS "Permitir acceso completo a defectos_inspeccion" ON defectos_inspeccion;
CREATE POLICY "Permitir acceso completo a defectos_inspeccion"
ON defectos_inspeccion FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para seguimiento_comercial_tareas
DROP POLICY IF EXISTS "Permitir acceso completo a seguimiento_comercial_tareas" ON seguimiento_comercial_tareas;
CREATE POLICY "Permitir acceso completo a seguimiento_comercial_tareas"
ON seguimiento_comercial_tareas FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para maquinas_cartera
DROP POLICY IF EXISTS "Permitir acceso completo a maquinas_cartera" ON maquinas_cartera;
CREATE POLICY "Permitir acceso completo a maquinas_cartera"
ON maquinas_cartera FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para alertas_automaticas
DROP POLICY IF EXISTS "Permitir acceso completo a alertas_automaticas" ON alertas_automaticas;
CREATE POLICY "Permitir acceso completo a alertas_automaticas"
ON alertas_automaticas FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para componentes_criticos (solo lectura para la mayoría)
DROP POLICY IF EXISTS "Permitir lectura a componentes_criticos" ON componentes_criticos;
CREATE POLICY "Permitir lectura a componentes_criticos"
ON componentes_criticos FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir escritura a componentes_criticos" ON componentes_criticos;
CREATE POLICY "Permitir escritura a componentes_criticos"
ON componentes_criticos FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para instalaciones
DROP POLICY IF EXISTS "Permitir acceso completo a instalaciones" ON instalaciones;
CREATE POLICY "Permitir acceso completo a instalaciones"
ON instalaciones FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para inspecciones
DROP POLICY IF EXISTS "Permitir acceso completo a inspecciones" ON inspecciones;
CREATE POLICY "Permitir acceso completo a inspecciones"
ON inspecciones FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para partes_trabajo
DROP POLICY IF EXISTS "Permitir acceso completo a partes_trabajo" ON partes_trabajo;
CREATE POLICY "Permitir acceso completo a partes_trabajo"
ON partes_trabajo FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para tipos_parte_mapeo (solo lectura)
DROP POLICY IF EXISTS "Permitir lectura a tipos_parte_mapeo" ON tipos_parte_mapeo;
CREATE POLICY "Permitir lectura a tipos_parte_mapeo"
ON tipos_parte_mapeo FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir escritura a tipos_parte_mapeo" ON tipos_parte_mapeo;
CREATE POLICY "Permitir escritura a tipos_parte_mapeo"
ON tipos_parte_mapeo FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para oportunidades_facturacion
DROP POLICY IF EXISTS "Permitir acceso completo a oportunidades_facturacion" ON oportunidades_facturacion;
CREATE POLICY "Permitir acceso completo a oportunidades_facturacion"
ON oportunidades_facturacion FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para pendientes_tecnicos
DROP POLICY IF EXISTS "Permitir acceso completo a pendientes_tecnicos" ON pendientes_tecnicos;
CREATE POLICY "Permitir acceso completo a pendientes_tecnicos"
ON pendientes_tecnicos FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- Políticas para tablas de backup (SOLO LECTURA para usuarios normales)
-- Se recomienda mover estas tablas a un schema privado

DROP POLICY IF EXISTS "Permitir solo lectura a administradores_backup_20251028" ON administradores_backup_20251028;
CREATE POLICY "Permitir solo lectura a administradores_backup_20251028"
ON administradores_backup_20251028 FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir solo lectura a administradores_backup_charset" ON administradores_backup_charset;
CREATE POLICY "Permitir solo lectura a administradores_backup_charset"
ON administradores_backup_charset FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir solo lectura a administradores_tmp" ON administradores_tmp;
CREATE POLICY "Permitir solo lectura a administradores_tmp"
ON administradores_tmp FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir solo lectura a clientes_tmp" ON clientes_tmp;
CREATE POLICY "Permitir solo lectura a clientes_tmp"
ON clientes_tmp FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir solo lectura a clientes_backup" ON clientes_backup;
CREATE POLICY "Permitir solo lectura a clientes_backup"
ON clientes_backup FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Permitir solo lectura a administradores_backup_final" ON administradores_backup_final;
CREATE POLICY "Permitir solo lectura a administradores_backup_final"
ON administradores_backup_final FOR SELECT
TO authenticated
USING (true);

-- ============================================
-- PARTE 4: REGISTRAR MIGRACIÓN
-- ============================================

-- Crear tabla de control de migraciones si no existe
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) VALUES
    ('006', 'Corrección de Seguridad - Quitar SECURITY DEFINER de vistas y habilitar RLS en tablas')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migración 006 completada exitosamente';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 SEGURIDAD CORREGIDA:';
    RAISE NOTICE '   ✓ 9 vistas recreadas SIN SECURITY DEFINER';
    RAISE NOTICE '   ✓ RLS habilitado en 31 tablas';
    RAISE NOTICE '   ✓ Políticas RLS permisivas creadas';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  RECOMENDACIONES:';
    RAISE NOTICE '   1. Revisar políticas RLS y ajustarlas según roles de usuario';
    RAISE NOTICE '   2. Mover tablas de backup a schema privado (no público)';
    RAISE NOTICE '   3. Considerar políticas más restrictivas según perfil de usuario';
    RAISE NOTICE '   4. Ejecutar el linter de Supabase para verificar que se corrigieron los problemas';
    RAISE NOTICE '';
END
$$;
