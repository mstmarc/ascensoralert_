-- Migración: Agregar campos de gestión operativa a defectos_inspeccion
-- Fecha: 2025-01-XX
-- Descripción: Agrega campos para gestionar materiales y asignación de técnicos

-- Agregar campo para gestión de materiales
ALTER TABLE defectos_inspeccion
ADD COLUMN IF NOT EXISTS gestion_material VARCHAR(50);

-- Agregar campo para técnico asignado
ALTER TABLE defectos_inspeccion
ADD COLUMN IF NOT EXISTS tecnico_asignado VARCHAR(50);

-- Comentarios para documentación
COMMENT ON COLUMN defectos_inspeccion.gestion_material IS 'Gestión de materiales: comprar, pedir_tenerife, no_necesita';
COMMENT ON COLUMN defectos_inspeccion.tecnico_asignado IS 'Técnico asignado: sergio, tenerife, guimi, u otro';
