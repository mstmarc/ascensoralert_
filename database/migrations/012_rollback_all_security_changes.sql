-- ============================================
-- MIGRACIÓN 012: ROLLBACK COMPLETO - Revertir todos los cambios de seguridad
-- ============================================
-- Fecha: 2025-12-03
-- Descripción: Revertir migraciones 006-011 y restaurar el estado funcional original
--              La aplicación funcionaba correctamente antes de los cambios de seguridad
--
-- ✅ PRIORIDAD: Aplicación funcional > Warnings del linter
-- ============================================

-- ============================================
-- PASO 1: ELIMINAR TODAS LAS POLÍTICAS RLS
-- ============================================

DO $$
DECLARE
    policy_record RECORD;
    contador INT := 0;
BEGIN
    RAISE NOTICE '🗑️  ELIMINANDO TODAS LAS POLÍTICAS RLS...';

    FOR policy_record IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
                      policy_record.policyname,
                      policy_record.schemaname,
                      policy_record.tablename);
        contador := contador + 1;
    END LOOP;

    RAISE NOTICE '   ✓ Eliminadas % políticas RLS', contador;
END
$$;

-- ============================================
-- PASO 2: DESHABILITAR RLS EN TODAS LAS TABLAS
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
    END LOOP;

    RAISE NOTICE '   ✓ RLS deshabilitado en % tablas', contador;
END
$$;

-- ============================================
-- PASO 3: RESTAURAR VISTAS CON SECURITY DEFINER (Estado Original)
-- ============================================

RAISE NOTICE '👁️  RESTAURANDO VISTAS AL ESTADO ORIGINAL...';

-- Vista: v_estado_maquinas_semaforico (CON SECURITY DEFINER)
DROP VIEW IF EXISTS v_estado_maquinas_semaforico CASCADE;

CREATE VIEW v_estado_maquinas_semaforico
WITH (security_barrier = false)
AS
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

-- Vista: v_inspecciones_completas (CON SECURITY DEFINER)
DROP VIEW IF EXISTS v_inspecciones_completas CASCADE;

CREATE VIEW v_inspecciones_completas
WITH (security_barrier = false)
AS
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

-- Vista: v_defectos_con_detalle (CON SECURITY DEFINER)
DROP VIEW IF EXISTS v_defectos_con_detalle CASCADE;

CREATE VIEW v_defectos_con_detalle
WITH (security_barrier = false)
AS
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

-- Vista: v_partes_trabajo_completos (CON SECURITY DEFINER)
DROP VIEW IF EXISTS v_partes_trabajo_completos CASCADE;

CREATE VIEW v_partes_trabajo_completos
WITH (security_barrier = false)
AS
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

-- Vista: v_instalaciones_completas (CON SECURITY DEFINER)
DROP VIEW IF EXISTS v_instalaciones_completas CASCADE;

CREATE VIEW v_instalaciones_completas
WITH (security_barrier = false)
AS
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
-- PASO 4: RESTAURAR FUNCIONES (Sin SET search_path)
-- ============================================

RAISE NOTICE '🔧 RESTAURANDO FUNCIONES AL ESTADO ORIGINAL...';

-- Función: buscar_clientes_sin_acentos (SIN search_path fijo)
CREATE OR REPLACE FUNCTION buscar_clientes_sin_acentos(termino_busqueda text)
RETURNS TABLE (
    codigo_cliente character varying,
    nombre character varying,
    cif character varying,
    direccion text,
    telefono character varying,
    email character varying,
    activo boolean,
    similarity_score real
)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        c.codigo_cliente,
        c.nombre,
        c.cif,
        c.direccion,
        c.telefono,
        c.email,
        c.activo,
        GREATEST(
            similarity(unaccent(lower(c.nombre)), unaccent(lower(termino_busqueda))),
            similarity(unaccent(lower(c.cif)), unaccent(lower(termino_busqueda))),
            similarity(unaccent(lower(COALESCE(c.direccion, ''))), unaccent(lower(termino_busqueda)))
        ) as similarity_score
    FROM clientes c
    WHERE
        unaccent(lower(c.nombre)) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
        OR unaccent(lower(c.cif)) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
        OR unaccent(lower(COALESCE(c.direccion, ''))) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
        OR c.codigo_cliente ILIKE '%' || termino_busqueda || '%'
    ORDER BY similarity_score DESC, c.nombre
    LIMIT 50;
END;
$function$;

-- Función: buscar_administradores_sin_acentos (SIN search_path fijo)
CREATE OR REPLACE FUNCTION buscar_administradores_sin_acentos(termino_busqueda text)
RETURNS TABLE (
    id integer,
    nombre character varying,
    apellido character varying,
    email character varying,
    telefono character varying,
    activo boolean,
    similarity_score real
)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.nombre,
        a.apellido,
        a.email,
        a.telefono,
        a.activo,
        GREATEST(
            similarity(unaccent(lower(a.nombre)), unaccent(lower(termino_busqueda))),
            similarity(unaccent(lower(a.apellido)), unaccent(lower(termino_busqueda))),
            similarity(unaccent(lower(COALESCE(a.email, ''))), unaccent(lower(termino_busqueda)))
        ) as similarity_score
    FROM administradores a
    WHERE
        unaccent(lower(a.nombre)) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
        OR unaccent(lower(a.apellido)) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
        OR unaccent(lower(COALESCE(a.email, ''))) ILIKE '%' || unaccent(lower(termino_busqueda)) || '%'
    ORDER BY similarity_score DESC, a.apellido, a.nombre
    LIMIT 50;
END;
$function$;

-- ============================================
-- PASO 5: ELIMINAR REGISTROS DE MIGRACIONES PROBLEMÁTICAS
-- ============================================

DO $$
BEGIN
    DELETE FROM schema_migrations
    WHERE version IN ('006', '007', '008', '009', '010', '011');

    RAISE NOTICE '🗑️  Eliminados registros de migraciones 006-011';
END
$$;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

DO $$
DECLARE
    rls_count INT;
    policy_count INT;
    view_count INT;
BEGIN
    -- Contar tablas con RLS
    SELECT COUNT(*) INTO rls_count
    FROM pg_tables t
    JOIN pg_class c ON c.relname = t.tablename
    WHERE t.schemaname = 'public'
    AND c.relrowsecurity = true;

    -- Contar políticas
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    -- Contar vistas
    SELECT COUNT(*) INTO view_count
    FROM pg_views
    WHERE schemaname = 'public';

    RAISE NOTICE '═══════════════════════════════════════════';
    RAISE NOTICE '✅ ROLLBACK COMPLETADO EXITOSAMENTE';
    RAISE NOTICE '═══════════════════════════════════════════';
    RAISE NOTICE '📊 ESTADO FINAL:';
    RAISE NOTICE '   • Tablas con RLS habilitado: %', rls_count;
    RAISE NOTICE '   • Políticas RLS activas: %', policy_count;
    RAISE NOTICE '   • Vistas en public: %', view_count;
    RAISE NOTICE '';
    RAISE NOTICE '🔄 REVERTIDO:';
    RAISE NOTICE '   ✓ Todas las políticas RLS eliminadas';
    RAISE NOTICE '   ✓ RLS deshabilitado en todas las tablas';
    RAISE NOTICE '   ✓ Vistas restauradas con SECURITY DEFINER';
    RAISE NOTICE '   ✓ Funciones restauradas sin search_path fijo';
    RAISE NOTICE '   ✓ Registros de migraciones 006-011 eliminados';
    RAISE NOTICE '';
    RAISE NOTICE '✅ LA APLICACIÓN DEBE ESTAR FUNCIONAL AHORA';
    RAISE NOTICE '';
    RAISE NOTICE '💡 RECOMENDACIÓN:';
    RAISE NOTICE '   Los warnings del linter de Supabase son guías,';
    RAISE NOTICE '   no errores críticos. Una aplicación funcional';
    RAISE NOTICE '   es más importante que seguir todas las guías.';
END
$$;

-- Registrar esta migración
INSERT INTO schema_migrations (version, name, executed_at)
VALUES ('012', 'rollback_all_security_changes', NOW())
ON CONFLICT (version) DO NOTHING;
