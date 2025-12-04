-- ============================================
-- DIAGNÓSTICO SIMPLE DEL IRI
-- Solo usa tablas base (no requiere vistas)
-- ============================================

-- DIAGNÓSTICO 1: Verificar que existen las tablas necesarias
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 1: Verificar Tablas Base' as info;
SELECT '========================================' as info;

SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_tables WHERE tablename = 'instalaciones') THEN '✅ Tabla instalaciones existe'
        ELSE '❌ Tabla instalaciones NO EXISTE'
    END as verificacion
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_tables WHERE tablename = 'maquinas_cartera') THEN '✅ Tabla maquinas_cartera existe'
        ELSE '❌ Tabla maquinas_cartera NO EXISTE'
    END
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_tables WHERE tablename = 'partes_trabajo') THEN '✅ Tabla partes_trabajo existe'
        ELSE '❌ Tabla partes_trabajo NO EXISTE'
    END
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_tables WHERE tablename = 'alertas_automaticas') THEN '✅ Tabla alertas_automaticas existe'
        ELSE '❌ Tabla alertas_automaticas NO EXISTE'
    END
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_tables WHERE tablename = 'pendientes_tecnicos') THEN '✅ Tabla pendientes_tecnicos existe'
        ELSE '❌ Tabla pendientes_tecnicos NO EXISTE'
    END;

-- DIAGNÓSTICO 2: Verificar que existen las vistas del IRI
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 2: Verificar Vistas del IRI' as info;
SELECT '========================================' as info;

SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_views WHERE viewname = 'v_riesgo_instalaciones') THEN '✅ Vista v_riesgo_instalaciones existe'
        ELSE '❌ Vista v_riesgo_instalaciones NO EXISTE - DEBE EJECUTAR MIGRACIONES'
    END as verificacion
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_views WHERE viewname = 'v_maquinas_problematicas') THEN '✅ Vista v_maquinas_problematicas existe'
        ELSE '❌ Vista v_maquinas_problematicas NO EXISTE - DEBE EJECUTAR MIGRACIONES'
    END
UNION ALL
SELECT
    CASE
        WHEN EXISTS (SELECT FROM pg_views WHERE viewname = 'v_estado_maquinas_semaforico') THEN '✅ Vista v_estado_maquinas_semaforico existe'
        ELSE '❌ Vista v_estado_maquinas_semaforico NO EXISTE - DEBE EJECUTAR MIGRACIONES'
    END;

-- DIAGNÓSTICO 3: Estado de Instalaciones (desde tabla base)
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 3: Estado de Instalaciones' as info;
SELECT '========================================' as info;

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

-- DIAGNÓSTICO 4: Estado de Máquinas (desde tabla base)
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 4: Estado de Máquinas' as info;
SELECT '========================================' as info;

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

-- DIAGNÓSTICO 5: Instalaciones con Máquinas (Top 10)
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 5: Instalaciones con Máquinas' as info;
SELECT '========================================' as info;

SELECT
    i.id,
    i.nombre,
    i.municipio,
    i.en_cartera,
    COUNT(m.id) as total_maquinas,
    COUNT(m.id) FILTER (WHERE m.en_cartera = true) as maquinas_activas
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id
GROUP BY i.id, i.nombre, i.municipio, i.en_cartera
ORDER BY total_maquinas DESC
LIMIT 10;

-- DIAGNÓSTICO 6: Averías por Instalación (últimos 3 meses)
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 6: Averías Recientes por Instalación' as info;
SELECT '========================================' as info;

SELECT
    i.nombre as instalacion,
    i.en_cartera,
    COUNT(DISTINCT m.id) as maquinas_activas,
    COUNT(p.id) as total_averias_3_meses
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id AND m.en_cartera = true
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
    AND p.tipo_parte_normalizado = 'AVERIA'
    AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
WHERE i.en_cartera = true
GROUP BY i.id, i.nombre, i.en_cartera
HAVING COUNT(DISTINCT m.id) > 0
ORDER BY total_averias_3_meses DESC
LIMIT 10;

-- DIAGNÓSTICO 7: Alertas Activas por Instalación
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 7: Alertas Activas por Instalación' as info;
SELECT '========================================' as info;

SELECT
    i.nombre as instalacion,
    COUNT(a.id) as alertas_activas,
    COUNT(a.id) FILTER (WHERE a.nivel_urgencia IN ('URGENTE', 'ALTA')) as alertas_urgentes
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id
LEFT JOIN alertas_automaticas a ON m.id = a.maquina_id
    AND a.estado IN ('PENDIENTE', 'EN_REVISION')
WHERE i.en_cartera = true
AND m.en_cartera = true
GROUP BY i.id, i.nombre
HAVING COUNT(a.id) > 0
ORDER BY alertas_urgentes DESC, alertas_activas DESC
LIMIT 10;

-- DIAGNÓSTICO 8: Resumen General
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'DIAGNÓSTICO 8: Resumen General' as info;
SELECT '========================================' as info;

SELECT
    'Instalaciones activas con máquinas' as metrica,
    COUNT(DISTINCT i.id) as cantidad
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id
WHERE i.en_cartera = true AND m.en_cartera = true
UNION ALL
SELECT
    'Instalaciones con averías (últimos 3 meses)',
    COUNT(DISTINCT i.id)
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id
INNER JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE i.en_cartera = true
AND m.en_cartera = true
AND p.tipo_parte_normalizado = 'AVERIA'
AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
UNION ALL
SELECT
    'Instalaciones con alertas activas',
    COUNT(DISTINCT i.id)
FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id
INNER JOIN alertas_automaticas a ON m.id = a.maquina_id
WHERE i.en_cartera = true
AND m.en_cartera = true
AND a.estado IN ('PENDIENTE', 'EN_REVISION');

-- CONCLUSIONES
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'CONCLUSIONES' as info;
SELECT '========================================' as info;
SELECT '' as info;

SELECT
    CASE
        WHEN NOT EXISTS (SELECT FROM pg_views WHERE viewname = 'v_riesgo_instalaciones')
        THEN '❌ PROBLEMA: Las vistas del IRI no existen'
        ELSE '✅ Las vistas del IRI están creadas'
    END as conclusion
UNION ALL
SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM instalaciones WHERE en_cartera = true) = 0
        THEN '❌ PROBLEMA: No hay instalaciones activas (en_cartera = TRUE)'
        ELSE '✅ Hay ' || (SELECT COUNT(*)::text FROM instalaciones WHERE en_cartera = true) || ' instalaciones activas'
    END
UNION ALL
SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM maquinas_cartera WHERE en_cartera = true) = 0
        THEN '❌ PROBLEMA: No hay máquinas activas (en_cartera = TRUE)'
        ELSE '✅ Hay ' || (SELECT COUNT(*)::text FROM maquinas_cartera WHERE en_cartera = true) || ' máquinas activas'
    END;

-- PRÓXIMOS PASOS
SELECT '' as info;
SELECT '========================================' as info;
SELECT 'PRÓXIMOS PASOS' as info;
SELECT '========================================' as info;
SELECT '' as info;

SELECT
    CASE
        WHEN NOT EXISTS (SELECT FROM pg_views WHERE viewname = 'v_riesgo_instalaciones')
        THEN '1️⃣ EJECUTAR MIGRACIONES para crear vistas del IRI'
        WHEN (SELECT COUNT(*) FROM instalaciones WHERE en_cartera = true) = 0
        THEN '1️⃣ REACTIVAR instalaciones: UPDATE instalaciones SET en_cartera = TRUE;'
        WHEN (SELECT COUNT(*) FROM maquinas_cartera WHERE en_cartera = true) = 0
        THEN '1️⃣ REACTIVAR máquinas: UPDATE maquinas_cartera SET en_cartera = TRUE;'
        ELSE '1️⃣ EJECUTAR diagnostico_iri.sql completo para análisis detallado'
    END as paso;
