-- =====================================================
-- TABLA: seguimiento_comercial_tareas
-- Sistema de gestión de tareas comerciales automáticas
-- =====================================================

CREATE TABLE IF NOT EXISTS seguimiento_comercial_tareas (
  id BIGSERIAL PRIMARY KEY,
  cliente_id BIGINT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  equipo_id BIGINT REFERENCES equipos(id) ON DELETE SET NULL,

  -- Estados de la tarea
  estado VARCHAR(20) DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),

  -- Fechas importantes
  fecha_creacion TIMESTAMP DEFAULT NOW(),
  fecha_actualizacion TIMESTAMP DEFAULT NOW(),
  fecha_cierre TIMESTAMP NULL,
  aplazada_hasta DATE NULL,

  -- Contexto de creación
  motivo_creacion VARCHAR(50) DEFAULT 'ipo_15_dias' CHECK (
    motivo_creacion IN ('ipo_15_dias', 'aplazada_vuelve', 'manual')
  ),
  dias_desde_ipo INT, -- Días desde IPO al crear la tarea

  -- Información de cierre
  tipo_cierre VARCHAR(30) NULL CHECK (
    tipo_cierre IN (
      'convertida_oportunidad',
      'descartada_sin_interes',
      'descartada_tiene_contrato',
      'descartada_otro'
    )
  ),
  motivo_cierre TEXT NULL,
  oportunidad_id BIGINT NULL REFERENCES oportunidades(id) ON DELETE SET NULL,

  -- Aplazamiento
  motivo_aplazamiento TEXT NULL,

  -- Timeline de notas/seguimiento (JSON array)
  -- Formato: [{"fecha": "2025-01-15T10:30:00", "usuario": "Julio", "texto": "Llamado, no contestan"}, ...]
  notas JSONB DEFAULT '[]'::jsonb,

  -- Metadata
  creado_por VARCHAR(100),

  -- CONSTRAINT: Solo una tarea abierta por cliente
  CONSTRAINT unica_tarea_abierta_por_cliente UNIQUE (cliente_id, estado)
);

-- Índices para optimizar consultas
CREATE INDEX idx_tareas_estado ON seguimiento_comercial_tareas(estado);
CREATE INDEX idx_tareas_aplazada ON seguimiento_comercial_tareas(aplazada_hasta) WHERE estado = 'abierta';
CREATE INDEX idx_tareas_cliente ON seguimiento_comercial_tareas(cliente_id);
CREATE INDEX idx_tareas_fecha_creacion ON seguimiento_comercial_tareas(fecha_creacion DESC);

-- Función para actualizar fecha_actualizacion automáticamente
CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion_tarea()
RETURNS TRIGGER AS $$
BEGIN
  NEW.fecha_actualizacion = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar fecha_actualizacion
CREATE TRIGGER trigger_actualizar_fecha_tarea
BEFORE UPDATE ON seguimiento_comercial_tareas
FOR EACH ROW
EXECUTE FUNCTION actualizar_fecha_actualizacion_tarea();

-- Comentarios para documentación
COMMENT ON TABLE seguimiento_comercial_tareas IS 'Gestión de tareas comerciales automáticas post-IPO';
COMMENT ON COLUMN seguimiento_comercial_tareas.estado IS 'abierta: requiere gestión | cerrada: resuelta';
COMMENT ON COLUMN seguimiento_comercial_tareas.motivo_creacion IS 'ipo_15_dias: creada automáticamente | aplazada_vuelve: reaparece tras aplazamiento | manual: creada manualmente';
COMMENT ON COLUMN seguimiento_comercial_tareas.tipo_cierre IS 'convertida_oportunidad: pasó a pipeline | descartada_*: no hay oportunidad';
COMMENT ON COLUMN seguimiento_comercial_tareas.notas IS 'Timeline de seguimiento en formato JSON: [{fecha, usuario, texto}]';
COMMENT ON CONSTRAINT unica_tarea_abierta_por_cliente ON seguimiento_comercial_tareas IS 'Solo puede haber una tarea abierta por cliente (evita duplicados)';
