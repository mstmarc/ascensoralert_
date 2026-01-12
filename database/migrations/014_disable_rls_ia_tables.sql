-- ============================================
-- MIGRACIÓN 014: Deshabilitar RLS en tablas de IA Predictiva
-- ============================================
-- Fecha: 2026-01-12
-- Descripción: Deshabilitar RLS en todas las tablas del sistema de IA
--              para mantener consistencia con el resto de la base de datos
--              (migraciones 011 y 012 deshabilitaron RLS en todas las tablas)
--
-- ⚠️  NOTA: Esto alinea las tablas de IA con la política actual de la BD
--     que tiene RLS deshabilitado en todas las tablas
-- ============================================

-- ============================================
-- PASO 1: ELIMINAR POLÍTICAS RLS DE TABLAS DE IA
-- ============================================

DO $$
DECLARE
    policy_record RECORD;
    contador INT := 0;
BEGIN
    RAISE NOTICE '🗑️  ELIMINANDO POLÍTICAS RLS DE TABLAS DE IA...';

    FOR policy_record IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename IN (
            'analisis_partes_ia',
            'predicciones_maquina',
            'alertas_predictivas_ia',
            'conocimiento_tecnico_ia',
            'metricas_precision_ia',
            'aprendizaje_ia'
        )
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I',
                      policy_record.policyname,
                      policy_record.schemaname,
                      policy_record.tablename);
        contador := contador + 1;
        RAISE NOTICE '   ✓ Eliminada política: % en tabla %', policy_record.policyname, policy_record.tablename;
    END LOOP;

    RAISE NOTICE '   ✓ Total políticas eliminadas: %', contador;
END
$$;

-- ============================================
-- PASO 2: DESHABILITAR RLS EN TABLAS DE IA
-- ============================================

DO $$
DECLARE
    tabla_name TEXT;
    contador INT := 0;
    tablas_ia TEXT[] := ARRAY[
        'analisis_partes_ia',
        'predicciones_maquina',
        'alertas_predictivas_ia',
        'conocimiento_tecnico_ia',
        'metricas_precision_ia',
        'aprendizaje_ia'
    ];
BEGIN
    RAISE NOTICE '🔓 DESHABILITANDO RLS EN TABLAS DE IA...';

    FOREACH tabla_name IN ARRAY tablas_ia
    LOOP
        -- Verificar si la tabla existe antes de intentar deshabilitar RLS
        IF EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = tabla_name
        ) THEN
            EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', tabla_name);
            contador := contador + 1;
            RAISE NOTICE '   ✓ RLS deshabilitado en: %', tabla_name;
        ELSE
            RAISE NOTICE '   ⚠️  Tabla no existe: %', tabla_name;
        END IF;
    END LOOP;

    RAISE NOTICE '   ✓ Total tablas procesadas: %', contador;
END
$$;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

DO $$
DECLARE
    rls_count INT;
    policy_count INT;
BEGIN
    -- Contar tablas de IA con RLS habilitado
    SELECT COUNT(*) INTO rls_count
    FROM pg_tables t
    JOIN pg_class c ON c.relname = t.tablename
    WHERE t.schemaname = 'public'
    AND t.tablename IN (
        'analisis_partes_ia',
        'predicciones_maquina',
        'alertas_predictivas_ia',
        'conocimiento_tecnico_ia',
        'metricas_precision_ia',
        'aprendizaje_ia'
    )
    AND c.relrowsecurity = true;

    -- Contar políticas en tablas de IA
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
    AND tablename IN (
        'analisis_partes_ia',
        'predicciones_maquina',
        'alertas_predictivas_ia',
        'conocimiento_tecnico_ia',
        'metricas_precision_ia',
        'aprendizaje_ia'
    );

    RAISE NOTICE '═══════════════════════════════════════════';
    RAISE NOTICE '✅ MIGRACIÓN 014 COMPLETADA';
    RAISE NOTICE '═══════════════════════════════════════════';
    RAISE NOTICE '📊 ESTADO FINAL TABLAS DE IA:';
    RAISE NOTICE '   • Tablas IA con RLS habilitado: %', rls_count;
    RAISE NOTICE '   • Políticas RLS activas en tablas IA: %', policy_count;
    RAISE NOTICE '';

    IF rls_count > 0 OR policy_count > 0 THEN
        RAISE WARNING '⚠️  Aún hay tablas de IA con RLS o políticas activas';
    ELSE
        RAISE NOTICE '✅ Todas las tablas de IA tienen RLS deshabilitado';
        RAISE NOTICE '✅ Todas las políticas RLS eliminadas de tablas de IA';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '📝 RESULTADO:';
    RAISE NOTICE '   Las tablas de IA ahora están alineadas con el resto de la BD';
    RAISE NOTICE '   (RLS deshabilitado según migraciones 011 y 012)';
END
$$;

-- Registrar esta migración
INSERT INTO schema_migrations (version, name, executed_at)
VALUES ('014', 'disable_rls_ia_tables', NOW())
ON CONFLICT (version) DO NOTHING;
