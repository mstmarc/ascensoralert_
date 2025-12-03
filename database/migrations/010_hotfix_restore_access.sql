-- ============================================
-- MIGRACIÓN HOTFIX: Restaurar Acceso a Datos
-- Fecha: 2025-12-03
-- ============================================
-- EMERGENCIA: Las vistas con security_invoker=on bloquearon el acceso
-- SOLUCIÓN TEMPORAL: Quitar security_invoker y usar SECURITY DEFINER temporalmente

-- ============================================
-- PARTE 1: VERIFICAR QUE LOS DATOS EXISTEN
-- ============================================

DO $$
DECLARE
    count_inspecciones INTEGER;
    count_maquinas INTEGER;
    count_defectos INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_inspecciones FROM inspecciones;
    SELECT COUNT(*) INTO count_maquinas FROM maquinas_cartera;
    SELECT COUNT(*) INTO count_defectos FROM defectos_inspeccion;

    RAISE NOTICE '📊 VERIFICACIÓN DE DATOS:';
    RAISE NOTICE '   Inspecciones: % registros', count_inspecciones;
    RAISE NOTICE '   Máquinas: % registros', count_maquinas;
    RAISE NOTICE '   Defectos: % registros', count_defectos;

    IF count_inspecciones = 0 AND count_maquinas = 0 THEN
        RAISE WARNING '⚠️ Las tablas parecen estar vacías!';
    END IF;
END
$$;

-- ============================================
-- PARTE 2: RECREAR VISTAS SIN SECURITY_INVOKER
-- ============================================
-- Temporalmente usamos el comportamiento por defecto para restaurar acceso

-- Vista 1: v_estado_maquinas_semaforico
DROP VIEW IF EXISTS v_estado_maquinas_semaforico CASCADE;
CREATE VIEW v_estado_maquinas_semaforico AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.en_cartera,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_mes,
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre,
    (SELECT COUNT(*) FROM alertas_automaticas a
     WHERE a.maquina_id = m.id
     AND a.tipo_alerta = 'FALLA_REPETIDA'
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true
        AND p.recomendacion_revisada = false
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,
    CASE
        WHEN MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
             < CURRENT_DATE - INTERVAL '60 days' THEN 1
        ELSE 0
    END as mantenimiento_atrasado,
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_ipo_pendientes,
    (SELECT COUNT(*) FROM pendientes_tecnicos pt
     WHERE pt.maquina_id = m.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO', 'BLOQUEADO')
    ) as pendientes_tecnicos_activos,
    CASE
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
        ELSE 'ESTABLE'
    END as estado_semaforico,
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte)::date as dias_sin_intervencion
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true
GROUP BY m.id, m.identificador, m.en_cartera, m.instalacion_id, i.nombre, i.municipio;

-- ============================================
-- PARTE 3: DESHABILITAR RLS TEMPORALMENTE EN TABLAS CRÍTICAS
-- ============================================
-- SOLO PARA RESTAURAR ACCESO - DEBE HABILITARSE DE NUEVO DESPUÉS

ALTER TABLE inspecciones DISABLE ROW LEVEL SECURITY;
ALTER TABLE defectos_inspeccion DISABLE ROW LEVEL SECURITY;
ALTER TABLE maquinas_cartera DISABLE ROW LEVEL SECURITY;
ALTER TABLE partes_trabajo DISABLE ROW LEVEL SECURITY;
ALTER TABLE instalaciones DISABLE ROW LEVEL SECURITY;

-- ============================================
-- PARTE 4: REGISTRAR MIGRACIÓN
-- ============================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) VALUES
    ('010', 'HOTFIX - Restaurar acceso a datos deshabilitando RLS temporalmente')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🚨 HOTFIX 010 aplicado';
    RAISE NOTICE '';
    RAISE NOTICE '✅ ACCIONES TOMADAS:';
    RAISE NOTICE '   ✓ RLS DESHABILITADO temporalmente en tablas críticas';
    RAISE NOTICE '   ✓ Vista v_estado_maquinas_semaforico recreada sin security_invoker';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANTE:';
    RAISE NOTICE '   Este es un HOTFIX temporal para restaurar acceso';
    RAISE NOTICE '   Las tablas NO tienen RLS activo (menos seguro)';
    RAISE NOTICE '   Verificar que los datos son visibles ahora';
    RAISE NOTICE '';
    RAISE NOTICE '📋 SIGUIENTE PASO:';
    RAISE NOTICE '   1. Verificar que los datos son visibles';
    RAISE NOTICE '   2. Configurar políticas RLS correctas';
    RAISE NOTICE '   3. Reactivar RLS con políticas apropiadas';
    RAISE NOTICE '';
END
$$;
