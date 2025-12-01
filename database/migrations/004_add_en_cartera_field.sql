-- Migración: Agregar campo en_cartera a maquinas_cartera
-- Fecha: 2025-12-01

-- Agregar campo en_cartera (Boolean, por defecto TRUE = En Cartera)
ALTER TABLE maquinas_cartera
ADD COLUMN IF NOT EXISTS en_cartera BOOLEAN DEFAULT TRUE;

-- Marcar todas las máquinas existentes como "En Cartera"
UPDATE maquinas_cartera
SET en_cartera = TRUE
WHERE en_cartera IS NULL;

-- Agregar campo fecha_salida_cartera para tracking histórico
ALTER TABLE maquinas_cartera
ADD COLUMN IF NOT EXISTS fecha_salida_cartera DATE;

-- Agregar campo motivo_salida para documentar por qué salió
ALTER TABLE maquinas_cartera
ADD COLUMN IF NOT EXISTS motivo_salida TEXT;

-- Comentarios
COMMENT ON COLUMN maquinas_cartera.en_cartera IS 'TRUE = Máquina en cartera activa, FALSE = Fuera de cartera';
COMMENT ON COLUMN maquinas_cartera.fecha_salida_cartera IS 'Fecha en que la máquina salió de cartera';
COMMENT ON COLUMN maquinas_cartera.motivo_salida IS 'Razón de salida: Cliente cambió empresa, contrato finalizado, etc.';
