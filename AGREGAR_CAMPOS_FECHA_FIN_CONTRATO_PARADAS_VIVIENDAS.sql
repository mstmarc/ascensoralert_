-- Migración: Añadir campos fecha_fin_contrato, paradas y viviendas_por_planta a la tabla clientes
-- Fecha: 2025-11-12
-- Descripción:
--   - fecha_fin_contrato: Fecha de finalización del contrato de mantenimiento (dato muy valioso)
--   - paradas: Número de paradas del edificio
--   - viviendas_por_planta: Número de viviendas por planta

-- Añadir columna fecha_fin_contrato (tipo DATE)
ALTER TABLE clientes
ADD COLUMN IF NOT EXISTS fecha_fin_contrato DATE;

-- Añadir columna paradas (tipo INTEGER)
ALTER TABLE clientes
ADD COLUMN IF NOT EXISTS paradas INTEGER;

-- Añadir columna viviendas_por_planta (tipo INTEGER)
ALTER TABLE clientes
ADD COLUMN IF NOT EXISTS viviendas_por_planta INTEGER;

-- Comentarios descriptivos para cada columna
COMMENT ON COLUMN clientes.fecha_fin_contrato IS 'Fecha de fin de contrato de mantenimiento. Genera tareas automáticas 120 días antes (abierta) y 150 días antes (futura)';
COMMENT ON COLUMN clientes.paradas IS 'Número de paradas del edificio/instalación';
COMMENT ON COLUMN clientes.viviendas_por_planta IS 'Número de viviendas por planta en el edificio';

-- Verificar que las columnas se crearon correctamente
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'clientes'
AND column_name IN ('fecha_fin_contrato', 'paradas', 'viviendas_por_planta')
ORDER BY ordinal_position;
