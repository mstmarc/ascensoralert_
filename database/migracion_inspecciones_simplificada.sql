-- ============================================
-- MIGRACIÓN: Simplificación de Tabla Inspecciones
-- Fecha: 2025-11-20
-- Descripción: Simplifica la estructura de inspecciones
-- ============================================

-- IMPORTANTE: Este script modifica la tabla existente
-- Se recomienda hacer backup antes de ejecutar

BEGIN;

-- 1. Agregar nuevos campos
ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS maquina VARCHAR(100);
ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS presupuesto VARCHAR(50) DEFAULT 'PENDIENTE';
ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE inspecciones ADD COLUMN IF NOT EXISTS estado_material TEXT;

-- 2. Migrar datos existentes a nuevos campos
-- Copiar 'rae' a 'maquina' (si existe)
UPDATE inspecciones SET maquina = rae WHERE maquina IS NULL;

-- Copiar 'estado_presupuesto' a 'presupuesto' (si existe)
UPDATE inspecciones SET presupuesto = estado_presupuesto WHERE presupuesto = 'PENDIENTE';

-- Ajustar valores de presupuesto para el nuevo formato
UPDATE inspecciones SET presupuesto = 'EN_PREPARACION' WHERE presupuesto = 'PREPARANDO';

-- 3. Eliminar columnas antiguas que ya no se usan
ALTER TABLE inspecciones DROP COLUMN IF EXISTS rae;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS numero_certificado;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS titular_nombre;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS titular_nif;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS direccion_instalacion;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS municipio;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS tipo_ascensor;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS capacidad;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS carga;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS paradas;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS recorrido;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS velocidad;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_puesta_servicio;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_ultima_inspeccion;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS empresa_conservadora;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS resultado;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS tiene_defectos;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS archivo_pdf;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS estado_presupuesto;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS estado_trabajo;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_envio_presupuesto;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_respuesta_presupuesto;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_inicio_trabajo;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS fecha_fin_trabajo;
ALTER TABLE inspecciones DROP COLUMN IF EXISTS observaciones;

-- 4. Hacer campo 'maquina' NOT NULL (después de migrar datos)
ALTER TABLE inspecciones ALTER COLUMN maquina SET NOT NULL;

-- 5. Eliminar índices antiguos y crear nuevos
DROP INDEX IF EXISTS idx_inspecciones_rae;
DROP INDEX IF EXISTS idx_inspecciones_titular;
DROP INDEX IF EXISTS idx_inspecciones_municipio;
DROP INDEX IF EXISTS idx_inspecciones_estado_presupuesto;
DROP INDEX IF EXISTS idx_inspecciones_estado_trabajo;

CREATE INDEX IF NOT EXISTS idx_inspecciones_maquina ON inspecciones(maquina);
CREATE INDEX IF NOT EXISTS idx_inspecciones_fecha ON inspecciones(fecha_inspeccion DESC);
CREATE INDEX IF NOT EXISTS idx_inspecciones_oca ON inspecciones(oca_id);
CREATE INDEX IF NOT EXISTS idx_inspecciones_presupuesto ON inspecciones(presupuesto);

-- 6. Actualizar vistas
DROP VIEW IF EXISTS v_inspecciones_completas;
CREATE OR REPLACE VIEW v_inspecciones_completas AS
SELECT
    i.*,
    o.nombre as oca_nombre,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id) as total_defectos,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'SUBSANADO') as defectos_subsanados,
    (SELECT COUNT(*) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as defectos_pendientes,
    (SELECT MIN(fecha_limite) FROM defectos_inspeccion WHERE inspeccion_id = i.id AND estado = 'PENDIENTE') as fecha_limite_proxima
FROM inspecciones i
LEFT JOIN ocas o ON i.oca_id = o.id;

DROP VIEW IF EXISTS v_defectos_con_urgencia;
CREATE OR REPLACE VIEW v_defectos_con_urgencia AS
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

COMMIT;

-- ============================================
-- FIN DE LA MIGRACIÓN
-- ============================================

-- Para verificar la estructura actualizada:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'inspecciones'
-- ORDER BY ordinal_position;
