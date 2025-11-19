-- ============================================
-- MÓDULO DE GESTIÓN DE INSPECCIONES (IPOs)
-- AscensorAlert - Fedes Ascensores
-- ============================================

-- Tabla 1: Organismos de Control Autorizados (OCAs)
-- ============================================
CREATE TABLE IF NOT EXISTS ocas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    contacto_nombre VARCHAR(255),
    contacto_email VARCHAR(255),
    contacto_telefono VARCHAR(50),
    direccion TEXT,
    observaciones TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para OCAs
CREATE INDEX idx_ocas_nombre ON ocas(nombre);

-- Tabla 2: Inspecciones (Actas de IPO)
-- ============================================
CREATE TABLE IF NOT EXISTS inspecciones (
    id SERIAL PRIMARY KEY,

    -- Identificación del ascensor
    rae VARCHAR(50) NOT NULL,
    numero_certificado VARCHAR(100),
    fecha_inspeccion DATE NOT NULL,

    -- Titular (cliente propietario)
    titular_nombre VARCHAR(255) NOT NULL,
    titular_nif VARCHAR(20),
    direccion_instalacion TEXT NOT NULL,
    municipio VARCHAR(100),

    -- Organismo de Control
    oca_id INTEGER REFERENCES ocas(id) ON DELETE SET NULL,

    -- Características técnicas del ascensor
    tipo_ascensor VARCHAR(50), -- Electromecánico/Hidráulico
    capacidad INTEGER, -- personas
    carga INTEGER, -- kg
    paradas INTEGER,
    recorrido NUMERIC(10,2), -- metros
    velocidad NUMERIC(10,2), -- m/s
    fecha_puesta_servicio DATE,
    fecha_ultima_inspeccion DATE,
    empresa_conservadora VARCHAR(255) DEFAULT 'FEDES ASCENSORES',

    -- Resultado de la inspección
    resultado VARCHAR(50) DEFAULT 'Desfavorable', -- Favorable/Desfavorable
    tiene_defectos BOOLEAN DEFAULT true,

    -- Archivo PDF
    archivo_pdf VARCHAR(500), -- Ruta del archivo

    -- Estados de gestión
    estado_presupuesto VARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE/PREPARANDO/ENVIADO/ACEPTADO/RECHAZADO
    estado_trabajo VARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE/EN_EJECUCION/COMPLETADO

    -- Fechas de seguimiento
    fecha_envio_presupuesto DATE,
    fecha_respuesta_presupuesto DATE,
    fecha_inicio_trabajo DATE,
    fecha_fin_trabajo DATE,

    -- Observaciones
    observaciones TEXT,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Inspecciones
CREATE INDEX idx_inspecciones_rae ON inspecciones(rae);
CREATE INDEX idx_inspecciones_fecha ON inspecciones(fecha_inspeccion DESC);
CREATE INDEX idx_inspecciones_titular ON inspecciones(titular_nombre);
CREATE INDEX idx_inspecciones_municipio ON inspecciones(municipio);
CREATE INDEX idx_inspecciones_oca ON inspecciones(oca_id);
CREATE INDEX idx_inspecciones_estado_presupuesto ON inspecciones(estado_presupuesto);
CREATE INDEX idx_inspecciones_estado_trabajo ON inspecciones(estado_trabajo);

-- Tabla 3: Defectos Detectados en Inspecciones
-- ============================================
CREATE TABLE IF NOT EXISTS defectos_inspeccion (
    id SERIAL PRIMARY KEY,
    inspeccion_id INTEGER NOT NULL REFERENCES inspecciones(id) ON DELETE CASCADE,

    -- Identificación del defecto
    codigo VARCHAR(50), -- Ej: 3.04.1, 10.06.5
    descripcion TEXT NOT NULL,
    calificacion VARCHAR(10) NOT NULL, -- DL (Leve) / DG (Grave) / DMG (Muy Grave)

    -- Plazos
    plazo_meses INTEGER DEFAULT 6,
    fecha_limite DATE NOT NULL, -- Calculada: fecha_inspeccion + plazo_meses

    -- Estado
    estado VARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE/SUBSANADO
    fecha_subsanacion DATE,

    -- Marcas especiales (normativa ITC-AEM1 julio 2024)
    es_cortina BOOLEAN DEFAULT false,
    es_pesacarga BOOLEAN DEFAULT false,

    -- Observaciones
    observaciones TEXT,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Defectos
CREATE INDEX idx_defectos_inspeccion ON defectos_inspeccion(inspeccion_id);
CREATE INDEX idx_defectos_estado ON defectos_inspeccion(estado);
CREATE INDEX idx_defectos_fecha_limite ON defectos_inspeccion(fecha_limite);
CREATE INDEX idx_defectos_cortina ON defectos_inspeccion(es_cortina) WHERE es_cortina = true;
CREATE INDEX idx_defectos_pesacarga ON defectos_inspeccion(es_pesacarga) WHERE es_pesacarga = true;

-- Tabla 4: Materiales Especiales (Cortinas y Pesacargas)
-- ============================================
CREATE TABLE IF NOT EXISTS materiales_especiales (
    id SERIAL PRIMARY KEY,

    -- Tipo de material
    tipo VARCHAR(50) NOT NULL, -- CORTINA/PESACARGA

    -- Relación con inspección (opcional, puede añadirse manualmente)
    inspeccion_id INTEGER REFERENCES inspecciones(id) ON DELETE SET NULL,
    defecto_id INTEGER REFERENCES defectos_inspeccion(id) ON DELETE SET NULL,

    -- Cliente
    cliente_nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    municipio VARCHAR(100),

    -- Cantidad y plazo
    cantidad INTEGER NOT NULL DEFAULT 1,
    fecha_limite DATE NOT NULL,

    -- Estados de gestión
    estado VARCHAR(50) DEFAULT 'PENDIENTE', -- PENDIENTE/PEDIDO/RECIBIDO/INSTALADO
    fecha_pedido DATE,
    fecha_recepcion DATE,
    fecha_instalacion DATE,

    -- Observaciones
    observaciones TEXT,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Materiales Especiales
CREATE INDEX idx_materiales_tipo ON materiales_especiales(tipo);
CREATE INDEX idx_materiales_estado ON materiales_especiales(estado);
CREATE INDEX idx_materiales_fecha_limite ON materiales_especiales(fecha_limite);
CREATE INDEX idx_materiales_inspeccion ON materiales_especiales(inspeccion_id);

-- ============================================
-- DATOS INICIALES: OCAs Reales de Fedes Ascensores
-- ============================================
INSERT INTO ocas (nombre, contacto_email, activo) VALUES
    ('ABC INSPECCIONES, S.L.', 'abcinspeccion@gmail.com', true),
    ('APPLUS ORGANISMO DE CONTROL, S.L.U.', 'info@applus.com', true),
    ('TÜV SÜD ATISAE, S.A.', 'tenerife@tuvsud.com', true),
    ('ECA BUREAU VERITAS', 'tqr.dirtec@es.bureauveritas.com', true),
    ('EUROCONTROL, S.A.', 'tenerife@eurocontrol.es', true),
    ('INGENIERÍA DE GESTIÓN INDUSTRIAL, S.A. (INGEIN)', 'ingein@ingein.es', true),
    ('INSP. Y VERIFICACIONES REGLAMENTARIAS (IVR)', 'gestion@ocaivr.com', true),
    ('MARSAN INGENIEROS S.L.', 'marsaningenieros@marsaningenieros.es', true),
    ('OCA INSPECCIÓN, CONTROL Y PREVENCIÓN, S.A. (OCA IPC)', 'canarias@ocaicp.com', true),
    ('LABORAT. DE CERTIFIC. VEGA BAJA, S.L. (LABCER)', 'lanzarote@labcer.es', true),
    ('QUALICONSULT', 'madrid.qce@qualiconsult.es', true),
    ('SGS', 'jose_luis_lucena@sgs.com', true),
    ('SERVICIOS DE CONTROL E INSPECCIÓN', 'tenerife@scisa.es', true),
    ('VERIFICÁLITAS', 'leandro.capece@verificalitasoca.es', true),
    ('ÁBACO INSPECCIONES', 'fherrera@abacoinspecciones.es', true),
    ('OCA GLOBAL INSPECCIONES REGLAMENTARIAS', 'jiten.dadlani@ocaglobal.com', true)
ON CONFLICT DO NOTHING;

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE inspecciones IS 'Registro de actas de inspección periódica de ascensores (IPOs)';
COMMENT ON TABLE defectos_inspeccion IS 'Defectos detectados en cada inspección con sus plazos de corrección';
COMMENT ON TABLE materiales_especiales IS 'Control específico de cortinas fotoeléctricas y pesacargas (normativa ITC-AEM1 julio 2024)';
COMMENT ON TABLE ocas IS 'Catálogo de Organismos de Control Autorizados';

-- ============================================
-- VISTAS ÚTILES PARA DASHBOARDS
-- ============================================

-- Vista: Inspecciones con información del OCA
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

-- Vista: Defectos con urgencia calculada
CREATE OR REPLACE VIEW v_defectos_con_urgencia AS
SELECT
    d.*,
    i.titular_nombre,
    i.direccion_instalacion,
    i.municipio,
    i.rae,
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

-- Vista: Materiales especiales con urgencia
CREATE OR REPLACE VIEW v_materiales_con_urgencia AS
SELECT
    m.*,
    CASE
        WHEN m.estado = 'INSTALADO' THEN 'COMPLETADO'
        WHEN m.fecha_limite < CURRENT_DATE THEN 'VENCIDO'
        WHEN m.fecha_limite <= CURRENT_DATE + INTERVAL '15 days' THEN 'URGENTE'
        WHEN m.fecha_limite <= CURRENT_DATE + INTERVAL '30 days' THEN 'PROXIMO'
        ELSE 'NORMAL'
    END as nivel_urgencia,
    (m.fecha_limite - CURRENT_DATE) as dias_restantes
FROM materiales_especiales m;

-- ============================================
-- TRIGGERS PARA ACTUALIZAR updated_at
-- ============================================

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para inspecciones
DROP TRIGGER IF EXISTS update_inspecciones_updated_at ON inspecciones;
CREATE TRIGGER update_inspecciones_updated_at
    BEFORE UPDATE ON inspecciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para materiales_especiales
DROP TRIGGER IF EXISTS update_materiales_updated_at ON materiales_especiales;
CREATE TRIGGER update_materiales_updated_at
    BEFORE UPDATE ON materiales_especiales
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para ocas
DROP TRIGGER IF EXISTS update_ocas_updated_at ON ocas;
CREATE TRIGGER update_ocas_updated_at
    BEFORE UPDATE ON ocas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
