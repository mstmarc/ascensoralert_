-- ============================================
-- MIGRACIÓN: Analítica Avanzada V2
-- Sistema de Alertas Predictivas
-- Fecha: 2025-01-02
-- ============================================
-- IMPORTANTE: Ejecutar esta migración DESPUÉS de tener cartera_schema.sql aplicado

-- Verificar que las tablas base existen
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'instalaciones') THEN
        RAISE EXCEPTION 'Tabla instalaciones no existe. Ejecuta primero cartera_schema.sql';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'maquinas_cartera') THEN
        RAISE EXCEPTION 'Tabla maquinas_cartera no existe. Ejecuta primero cartera_schema.sql';
    END IF;
END
$$;

-- Ejecutar schema v2
\i ../cartera_schema_v2.sql

-- Log de migración
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) VALUES
    ('005', 'Analítica Avanzada V2 - Sistema de Alertas y Gestión Predictiva')
ON CONFLICT (version) DO NOTHING;

-- ============================================
-- MENSAJES FINALES
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migración 005 completada exitosamente';
    RAISE NOTICE '';
    RAISE NOTICE '📊 TABLAS CREADAS:';
    RAISE NOTICE '   - componentes_criticos (12 componentes pre-cargados)';
    RAISE NOTICE '   - alertas_automaticas';
    RAISE NOTICE '   - pendientes_tecnicos';
    RAISE NOTICE '';
    RAISE NOTICE '📈 VISTAS CREADAS:';
    RAISE NOTICE '   - v_estado_maquinas_semaforico';
    RAISE NOTICE '   - v_riesgo_instalaciones';
    RAISE NOTICE '   - v_perdidas_por_pendientes';
    RAISE NOTICE '';
    RAISE NOTICE '🔧 SIGUIENTE PASO:';
    RAISE NOTICE '   1. Ejecutar detectores: python detectores_alertas.py';
    RAISE NOTICE '   2. Acceder al dashboard: /cartera/v2';
    RAISE NOTICE '';
END
$$;
