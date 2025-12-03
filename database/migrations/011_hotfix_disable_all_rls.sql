-- ============================================
-- MIGRACIÓN 011: HOTFIX - Deshabilitar RLS en TODAS las tablas
-- ============================================
-- Fecha: 2025-12-03
-- Descripción: Deshabilitar temporalmente RLS en todas las tablas
--              para restaurar acceso completo a los datos
--
-- ⚠️  ADVERTENCIA: Esta es una solución TEMPORAL
--     RLS proporciona seguridad a nivel de fila
--     Después de restaurar el acceso, se debe configurar RLS correctamente
-- ============================================

-- Verificar que hay datos en las tablas principales
DO $$
DECLARE
    tabla_count RECORD;
BEGIN
    RAISE NOTICE '🔍 VERIFICANDO EXISTENCIA DE DATOS...';

    FOR tabla_count IN
        SELECT
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        AND n_live_tup > 0
        ORDER BY n_live_tup DESC
        LIMIT 10
    LOOP
        RAISE NOTICE '   ✓ %.%: % filas', tabla_count.schemaname, tabla_count.tablename, tabla_count.row_count;
    END LOOP;
END
$$;

-- ============================================
-- DESHABILITAR RLS EN TODAS LAS TABLAS
-- ============================================

DO $$
DECLARE
    tabla RECORD;
    contador INT := 0;
BEGIN
    RAISE NOTICE '🔓 DESHABILITANDO RLS EN TODAS LAS TABLAS...';

    FOR tabla IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT LIKE 'pg_%'
    LOOP
        EXECUTE format('ALTER TABLE %I.%I DISABLE ROW LEVEL SECURITY',
                      tabla.schemaname, tabla.tablename);
        contador := contador + 1;
        RAISE NOTICE '   ✓ RLS deshabilitado en: %.%', tabla.schemaname, tabla.tablename;
    END LOOP;

    RAISE NOTICE '✅ RLS deshabilitado en % tablas', contador;
END
$$;

-- ============================================
-- RECREAR VISTAS SIN security_invoker
-- ============================================

-- Vista: v_estado_maquinas_semaforico
DROP VIEW IF EXISTS v_estado_maquinas_semaforico CASCADE;

CREATE VIEW v_estado_maquinas_semaforico AS
SELECT
    mc.id,
    mc.num_serie,
    mc.num_fabricacion,
    mc.modelo,
    mc.ubicacion,
    mc.edificio,
    mc.codigo_cliente,
    c.nombre as nombre_cliente,
    mc.estado_maquina,
    mc.fecha_proxima_revision,
    mc.fecha_ultima_revision,
    mc.observaciones,
    mc.activo,
    CASE
        WHEN mc.fecha_proxima_revision IS NULL THEN 'SIN_FECHA'
        WHEN mc.fecha_proxima_revision < CURRENT_DATE THEN 'VENCIDA'
        WHEN mc.fecha_proxima_revision <= CURRENT_DATE + INTERVAL '30 days' THEN 'PROXIMA'
        ELSE 'VIGENTE'
    END as estado_semaforico,
    CASE
        WHEN mc.fecha_proxima_revision IS NULL THEN 999999
        WHEN mc.fecha_proxima_revision < CURRENT_DATE THEN
            EXTRACT(DAY FROM CURRENT_DATE - mc.fecha_proxima_revision)
        ELSE
            -EXTRACT(DAY FROM mc.fecha_proxima_revision - CURRENT_DATE)
    END as dias_diferencia
FROM maquinas_cartera mc
LEFT JOIN clientes c ON mc.codigo_cliente = c.codigo_cliente
WHERE mc.activo = true;

-- Vista: v_inspecciones_completas
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;

CREATE VIEW v_inspecciones_completas AS
SELECT
    i.id,
    i.codigo_inspeccion,
    i.num_serie,
    i.fecha_inspeccion,
    i.tipo_inspeccion,
    i.id_inspector,
    i.observaciones_generales,
    i.estado,
    i.created_at,
    i.updated_at,
    mc.codigo_cliente,
    c.nombre as nombre_cliente,
    mc.ubicacion,
    mc.edificio,
    mc.modelo,
    insp.nombre as nombre_inspector,
    insp.apellido as apellido_inspector,
    COUNT(di.id) as total_defectos,
    COUNT(CASE WHEN di.es_grave THEN 1 END) as defectos_graves
FROM inspecciones i
LEFT JOIN maquinas_cartera mc ON i.num_serie = mc.num_serie
LEFT JOIN clientes c ON mc.codigo_cliente = c.codigo_cliente
LEFT JOIN inspectores insp ON i.id_inspector = insp.id
LEFT JOIN defectos_inspeccion di ON i.id = di.id_inspeccion
GROUP BY
    i.id, i.codigo_inspeccion, i.num_serie, i.fecha_inspeccion,
    i.tipo_inspeccion, i.id_inspector, i.observaciones_generales,
    i.estado, i.created_at, i.updated_at,
    mc.codigo_cliente, c.nombre, mc.ubicacion, mc.edificio, mc.modelo,
    insp.nombre, insp.apellido;

-- Vista: v_defectos_con_detalle
DROP VIEW IF EXISTS v_defectos_con_detalle CASCADE;

CREATE VIEW v_defectos_con_detalle AS
SELECT
    di.id,
    di.id_inspeccion,
    di.codigo_defecto,
    di.descripcion,
    di.es_grave,
    di.requiere_paro,
    di.created_at,
    i.codigo_inspeccion,
    i.num_serie,
    i.fecha_inspeccion,
    i.tipo_inspeccion,
    mc.codigo_cliente,
    c.nombre as nombre_cliente,
    mc.ubicacion,
    mc.edificio
FROM defectos_inspeccion di
JOIN inspecciones i ON di.id_inspeccion = i.id
LEFT JOIN maquinas_cartera mc ON i.num_serie = mc.num_serie
LEFT JOIN clientes c ON mc.codigo_cliente = c.codigo_cliente;

-- Vista: v_partes_trabajo_completos
DROP VIEW IF EXISTS v_partes_trabajo_completos CASCADE;

CREATE VIEW v_partes_trabajo_completos AS
SELECT
    pt.id,
    pt.codigo_parte,
    pt.num_serie,
    pt.fecha_trabajo,
    pt.tipo_trabajo,
    pt.descripcion_trabajo,
    pt.tiempo_empleado,
    pt.id_tecnico,
    pt.estado,
    pt.observaciones,
    pt.created_at,
    pt.updated_at,
    mc.codigo_cliente,
    c.nombre as nombre_cliente,
    mc.ubicacion,
    mc.edificio,
    mc.modelo,
    t.nombre as nombre_tecnico,
    t.apellido as apellido_tecnico
FROM partes_trabajo pt
LEFT JOIN maquinas_cartera mc ON pt.num_serie = mc.num_serie
LEFT JOIN clientes c ON mc.codigo_cliente = c.codigo_cliente
LEFT JOIN tecnicos t ON pt.id_tecnico = t.id;

-- Vista: v_instalaciones_completas
DROP VIEW IF EXISTS v_instalaciones_completas CASCADE;

CREATE VIEW v_instalaciones_completas AS
SELECT
    inst.id,
    inst.codigo_instalacion,
    inst.codigo_cliente,
    c.nombre as nombre_cliente,
    inst.direccion,
    inst.localidad,
    inst.provincia,
    inst.codigo_postal,
    inst.persona_contacto,
    inst.telefono_contacto,
    inst.email_contacto,
    inst.observaciones,
    inst.activo,
    inst.created_at,
    inst.updated_at,
    COUNT(mc.id) as total_maquinas,
    COUNT(CASE WHEN mc.activo = true THEN 1 END) as maquinas_activas
FROM instalaciones inst
LEFT JOIN clientes c ON inst.codigo_cliente = c.codigo_cliente
LEFT JOIN maquinas_cartera mc ON inst.id = mc.id_instalacion
GROUP BY
    inst.id, inst.codigo_instalacion, inst.codigo_cliente, c.nombre,
    inst.direccion, inst.localidad, inst.provincia, inst.codigo_postal,
    inst.persona_contacto, inst.telefono_contacto, inst.email_contacto,
    inst.observaciones, inst.activo, inst.created_at, inst.updated_at;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

DO $$
DECLARE
    rls_enabled_count INT;
BEGIN
    SELECT COUNT(*) INTO rls_enabled_count
    FROM pg_tables t
    JOIN pg_class c ON c.relname = t.tablename
    WHERE t.schemaname = 'public'
    AND c.relrowsecurity = true;

    IF rls_enabled_count > 0 THEN
        RAISE WARNING '⚠️  Aún hay % tablas con RLS habilitado', rls_enabled_count;
    ELSE
        RAISE NOTICE '✅ Todas las tablas tienen RLS deshabilitado';
    END IF;

    RAISE NOTICE '✅ HOTFIX 011 COMPLETADO';
    RAISE NOTICE '🔓 RLS deshabilitado en todas las tablas';
    RAISE NOTICE '👁️  Todas las vistas recreadas sin security_invoker';
    RAISE NOTICE '⚠️  RECORDATORIO: Esta es una solución TEMPORAL';
    RAISE NOTICE '   Se debe configurar RLS correctamente en el futuro';
END
$$;

-- Registrar migración
INSERT INTO schema_migrations (version, name, executed_at)
VALUES ('011', 'hotfix_disable_all_rls', NOW())
ON CONFLICT (version) DO NOTHING;
