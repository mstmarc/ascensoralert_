-- ============================================
-- MIGRACIÓN: Crear nueva tabla de inspecciones simplificada
-- Fecha: 2025-11-20
-- Descripción: Crea una nueva tabla desde cero y migra datos
-- ============================================

-- IMPORTANTE: Este script crea una tabla nueva y elimina la antigua
-- Se recomienda hacer backup antes de ejecutar

BEGIN;

-- 1. Crear nueva tabla con estructura simplificada
CREATE TABLE IF NOT EXISTS inspecciones_nueva (
    id SERIAL PRIMARY KEY,

    -- Identificación principal
    maquina VARCHAR(100) NOT NULL,

    -- Fecha de inspección
    fecha_inspeccion DATE NOT NULL,

    -- Estado del presupuesto
    presupuesto VARCHAR(50) DEFAULT 'PENDIENTE',

    -- Estado general (texto libre)
    estado TEXT,

    -- Estado del material (texto libre)
    estado_material TEXT,

    -- Organismo de Control
    oca_id INTEGER REFERENCES ocas(id) ON DELETE SET NULL,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- 2. Migrar datos de la tabla antigua a la nueva
INSERT INTO inspecciones_nueva (
    id,
    maquina,
    fecha_inspeccion,
    presupuesto,
    oca_id,
    created_at,
    updated_at,
    created_by
)
SELECT
    id,
    rae AS maquina,  -- Migrar RAE → MAQUINA
    fecha_inspeccion,
    CASE
        WHEN estado_presupuesto = 'PREPARANDO' THEN 'EN_PREPARACION'
        ELSE COALESCE(estado_presupuesto, 'PENDIENTE')
    END AS presupuesto,  -- Migrar y ajustar estado_presupuesto → presupuesto
    oca_id,
    created_at,
    updated_at,
    created_by
FROM inspecciones;

-- 3. Actualizar la secuencia para que el próximo ID sea correcto
SELECT setval('inspecciones_nueva_id_seq', (SELECT MAX(id) FROM inspecciones_nueva));

-- 4. Eliminar la tabla antigua (CASCADE eliminará las foreign keys)
DROP TABLE IF EXISTS inspecciones CASCADE;

-- 5. Renombrar la nueva tabla
ALTER TABLE inspecciones_nueva RENAME TO inspecciones;

-- 6. Renombrar la secuencia
ALTER SEQUENCE inspecciones_nueva_id_seq RENAME TO inspecciones_id_seq;

-- 7. Recrear las foreign keys en tablas relacionadas
ALTER TABLE defectos_inspeccion
    ADD CONSTRAINT defectos_inspeccion_inspeccion_id_fkey
    FOREIGN KEY (inspeccion_id)
    REFERENCES inspecciones(id)
    ON DELETE CASCADE;

ALTER TABLE materiales_especiales
    ADD CONSTRAINT materiales_especiales_inspeccion_id_fkey
    FOREIGN KEY (inspeccion_id)
    REFERENCES inspecciones(id)
    ON DELETE SET NULL;

-- 8. Crear índices
CREATE INDEX idx_inspecciones_maquina ON inspecciones(maquina);
CREATE INDEX idx_inspecciones_fecha ON inspecciones(fecha_inspeccion DESC);
CREATE INDEX idx_inspecciones_oca ON inspecciones(oca_id);
CREATE INDEX idx_inspecciones_presupuesto ON inspecciones(presupuesto);

-- 9. Crear trigger para updated_at
DROP TRIGGER IF EXISTS update_inspecciones_updated_at ON inspecciones;
CREATE TRIGGER update_inspecciones_updated_at
    BEFORE UPDATE ON inspecciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 10. Recrear vistas con nueva estructura
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
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'inspecciones'
-- ORDER BY ordinal_position;

-- Para verificar que se migraron todos los datos:
-- SELECT COUNT(*) as total_inspecciones FROM inspecciones;
