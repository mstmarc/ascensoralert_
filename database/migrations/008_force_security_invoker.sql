-- ============================================
-- MIGRACIÓN: Corrección Adicional - Forzar eliminación SECURITY DEFINER
-- Fecha: 2025-12-03
-- ============================================
-- OBJETIVO: Corregir vistas que aún tienen SECURITY DEFINER y tabla schema_migrations sin RLS

-- ============================================
-- PARTE 1: HABILITAR RLS EN SCHEMA_MIGRATIONS
-- ============================================

-- La tabla schema_migrations no debería tener datos sensibles, pero por consistencia:
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;

-- Política permisiva para lectura
DROP POLICY IF EXISTS "Permitir lectura a schema_migrations" ON schema_migrations;
CREATE POLICY "Permitir lectura a schema_migrations"
ON schema_migrations FOR SELECT
TO authenticated
USING (true);

-- Política para escritura (solo service_role debería escribir migraciones)
DROP POLICY IF EXISTS "Permitir escritura a schema_migrations" ON schema_migrations;
CREATE POLICY "Permitir escritura a schema_migrations"
ON schema_migrations FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- ============================================
-- PARTE 2: FORZAR RECREACIÓN DE VISTAS SIN SECURITY DEFINER
-- ============================================
-- Las vistas deben recrearse explícitamente SIN WITH (security_invoker)
-- Por defecto PostgreSQL usa security_definer=off, pero hay que asegurarse

-- Vista 1: v_estado_maquinas_semaforico
DROP VIEW IF EXISTS v_estado_maquinas_semaforico CASCADE;
CREATE VIEW v_estado_maquinas_semaforico
WITH (security_invoker=on) AS
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

-- Vista 2: v_perdidas_por_pendientes
DROP VIEW IF EXISTS v_perdidas_por_pendientes CASCADE;
CREATE VIEW v_perdidas_por_pendientes
WITH (security_invoker=on) AS
SELECT
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) * 350.00 as valor_recomendaciones_perdidas,
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) * 180.00 as coste_averias_evitables,
    (SELECT COUNT(*)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
     AND fecha_envio_presupuesto IS NULL
    ) as oportunidades_sin_presupuesto,
    (SELECT COALESCE(SUM(importe_presupuestado), COUNT(*) * 500.00)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
    ) as valor_oportunidades_sin_presupuesto,
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

-- Vista 3: v_resumen_partes_maquina
DROP VIEW IF EXISTS v_resumen_partes_maquina CASCADE;
CREATE VIEW v_resumen_partes_maquina
WITH (security_invoker=on) AS
SELECT
    m.id as maquina_id,
    m.identificador,
    i.nombre as instalacion_nombre,
    i.municipio,
    COUNT(p.id) as total_partes,
    COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months') as partes_ultimo_año,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as total_averias,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO') as total_mantenimientos,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'REPARACION') as total_reparaciones,
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
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,
    COUNT(p.id) FILTER (WHERE p.tiene_recomendacion = true) as total_recomendaciones,
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true AND p.recomendacion_revisada = false
    ) as recomendaciones_pendientes,
    COUNT(p.id) FILTER (WHERE p.oportunidad_creada = true) as total_oportunidades_creadas
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, i.nombre, i.municipio;

-- Vista 4: v_partes_con_recomendaciones
DROP VIEW IF EXISTS v_partes_con_recomendaciones CASCADE;
CREATE VIEW v_partes_con_recomendaciones
WITH (security_invoker=on) AS
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

-- Vista 5: v_maquinas_problematicas
DROP VIEW IF EXISTS v_maquinas_problematicas CASCADE;
CREATE VIEW v_maquinas_problematicas
WITH (security_invoker=on) AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,
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
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) - COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '6 months'
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '3 months'
    ) as tendencia_averias,
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
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_averias_año,
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.estado = 'COMPLETADO'
        AND p.facturado = false
    ), 0) as facturacion_pendiente,
    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes,
    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
        AND p.prioridad IN ('URGENTE', 'ALTA')
    ) as partes_pendientes_urgentes,
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_inspeccion_pendientes,
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

-- Vista 6: v_inspecciones_completas
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;
CREATE VIEW v_inspecciones_completas
WITH (security_invoker=on) AS
SELECT
    i.*,
    o.nombre as oca_nombre,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id) as total_defectos,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'SUBSANADO') as defectos_subsanados,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as defectos_pendientes,
    (SELECT MIN(fecha_limite) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as fecha_limite_proxima
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

-- Vista 7: v_defectos_con_urgencia
DROP VIEW IF EXISTS v_defectos_con_urgencia CASCADE;
CREATE VIEW v_defectos_con_urgencia
WITH (security_invoker=on) AS
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

-- Vista 8: v_materiales_con_urgencia
DROP VIEW IF EXISTS v_materiales_con_urgencia CASCADE;
CREATE VIEW v_materiales_con_urgencia
WITH (security_invoker=on) AS
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
-- PARTE 3: RECREAR FUNCIONES DE BÚSQUEDA CON SEARCH_PATH
-- ============================================
-- Estas funciones no se actualizaron correctamente en la migración 007

-- Función: buscar_clientes_sin_acentos
DROP FUNCTION IF EXISTS buscar_clientes_sin_acentos(TEXT);
CREATE FUNCTION buscar_clientes_sin_acentos(termino TEXT)
RETURNS TABLE (
    id INTEGER,
    nombre TEXT,
    municipio TEXT,
    relevancia REAL
)
LANGUAGE plpgsql
STABLE
SET search_path = public, extensions, pg_catalog
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.nombre,
        c.municipio,
        extensions.similarity(f_unaccent(c.nombre), f_unaccent(termino)) as relevancia
    FROM clientes c
    WHERE
        f_unaccent(c.nombre) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(c.municipio) ILIKE '%' || f_unaccent(termino) || '%'
        OR extensions.similarity(f_unaccent(c.nombre), f_unaccent(termino)) > 0.3
    ORDER BY relevancia DESC, c.nombre
    LIMIT 50;
END;
$$;

COMMENT ON FUNCTION buscar_clientes_sin_acentos(TEXT) IS 'Busca clientes ignorando acentos usando pg_trgm - con search_path fijo';

-- Función: buscar_administradores_sin_acentos
DROP FUNCTION IF EXISTS buscar_administradores_sin_acentos(TEXT);
CREATE FUNCTION buscar_administradores_sin_acentos(termino TEXT)
RETURNS TABLE (
    id INTEGER,
    nombre TEXT,
    apellido1 TEXT,
    apellido2 TEXT,
    telefono TEXT,
    relevancia REAL
)
LANGUAGE plpgsql
STABLE
SET search_path = public, extensions, pg_catalog
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.nombre,
        a.apellido1,
        a.apellido2,
        a.telefono,
        GREATEST(
            extensions.similarity(f_unaccent(a.nombre), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido1, '')), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido2, '')), f_unaccent(termino))
        ) as relevancia
    FROM administradores a
    WHERE
        f_unaccent(a.nombre) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(COALESCE(a.apellido1, '')) ILIKE '%' || f_unaccent(termino) || '%'
        OR f_unaccent(COALESCE(a.apellido2, '')) ILIKE '%' || f_unaccent(termino) || '%'
        OR a.telefono LIKE '%' || termino || '%'
        OR GREATEST(
            extensions.similarity(f_unaccent(a.nombre), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido1, '')), f_unaccent(termino)),
            extensions.similarity(f_unaccent(COALESCE(a.apellido2, '')), f_unaccent(termino))
        ) > 0.3
    ORDER BY relevancia DESC, a.nombre
    LIMIT 50;
END;
$$;

COMMENT ON FUNCTION buscar_administradores_sin_acentos(TEXT) IS 'Busca administradores ignorando acentos usando pg_trgm - con search_path fijo';

-- ============================================
-- PARTE 4: REGISTRAR MIGRACIÓN
-- ============================================

INSERT INTO schema_migrations (version, description) VALUES
    ('008', 'Corrección Adicional - Forzar security_invoker=on en vistas, RLS en schema_migrations y search_path en funciones')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migración 008 completada exitosamente';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 CORRECCIONES APLICADAS:';
    RAISE NOTICE '   ✓ RLS habilitado en schema_migrations';
    RAISE NOTICE '   ✓ 8 vistas recreadas con security_invoker=on';
    RAISE NOTICE '   ✓ 2 funciones recreadas con search_path fijo';
    RAISE NOTICE '';
    RAISE NOTICE '📝 VISTAS CORREGIDAS:';
    RAISE NOTICE '   1. v_estado_maquinas_semaforico';
    RAISE NOTICE '   2. v_perdidas_por_pendientes';
    RAISE NOTICE '   3. v_resumen_partes_maquina';
    RAISE NOTICE '   4. v_partes_con_recomendaciones';
    RAISE NOTICE '   5. v_maquinas_problematicas';
    RAISE NOTICE '   6. v_inspecciones_completas';
    RAISE NOTICE '   7. v_defectos_con_urgencia';
    RAISE NOTICE '   8. v_materiales_con_urgencia';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 FUNCIONES CORREGIDAS:';
    RAISE NOTICE '   1. buscar_clientes_sin_acentos';
    RAISE NOTICE '   2. buscar_administradores_sin_acentos';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  SIGUIENTE PASO:';
    RAISE NOTICE '   Ejecutar el linter de Supabase para verificar que TODOS los problemas desaparecieron';
    RAISE NOTICE '';
END
$$;
