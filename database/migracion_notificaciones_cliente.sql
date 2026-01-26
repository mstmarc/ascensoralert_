-- ============================================
-- MIGRACIÓN: Sistema de Notificaciones a Clientes
-- Fecha: 2026-01-26
-- Descripción: Crea las tablas necesarias para el sistema
--              de notificaciones de parada de ascensores
-- ============================================

-- IMPORTANTE: Ejecutar en Supabase SQL Editor
-- Se recomienda hacer backup antes de ejecutar

BEGIN;

-- ============================================
-- 1. TABLA: motivos_parada
-- Catálogo de motivos predefinidos
-- ============================================

CREATE TABLE IF NOT EXISTS motivos_parada (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descripcion VARCHAR(100) NOT NULL,
    mensaje_cliente TEXT NOT NULL,
    orden INT DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insertar motivos predefinidos
INSERT INTO motivos_parada (codigo, descripcion, mensaje_cliente, orden) VALUES
('REPUESTO', 'Pendiente de repuesto', 'a la espera de recibir el material necesario para su reparación', 1),
('PRESUPUESTO', 'Pendiente de presupuesto', 'pendiente de presupuesto para proceder a su reparación', 2),
('VALORACION', 'Pendiente de valoración técnica', 'pendiente de valoración por nuestro departamento técnico', 3),
('EN_REPARACION', 'En proceso de reparación', 'en proceso de reparación por nuestro equipo técnico', 4),
('SEGURIDAD', 'Por seguridad preventiva', 'detenido preventivamente por seguridad hasta completar la revisión', 5),
('CAUSA_EXTERNA', 'Causa ajena a Fedes', 'por causas ajenas a nuestro servicio (suministro eléctrico, obras, etc.)', 6)
ON CONFLICT (codigo) DO NOTHING;


-- ============================================
-- 2. AÑADIR CAMPOS A TABLA instalaciones
-- Para almacenar datos de contacto
-- ============================================

ALTER TABLE instalaciones ADD COLUMN IF NOT EXISTS email_contacto VARCHAR(150);
ALTER TABLE instalaciones ADD COLUMN IF NOT EXISTS nombre_contacto VARCHAR(100);
ALTER TABLE instalaciones ADD COLUMN IF NOT EXISTS telefono_contacto VARCHAR(20);


-- ============================================
-- 3. TABLA: notificaciones_cliente
-- Registro de todas las notificaciones enviadas
-- ============================================

CREATE TABLE IF NOT EXISTS notificaciones_cliente (
    id SERIAL PRIMARY KEY,

    -- Referencias
    maquina_id INT REFERENCES maquinas_cartera(id),
    instalacion_id INT REFERENCES instalaciones(id),
    motivo_id INT REFERENCES motivos_parada(id),

    -- Datos de la notificación
    motivo_texto VARCHAR(200),
    mensaje_enviado TEXT,

    -- Destinatario
    email_destino VARCHAR(150),
    nombre_destino VARCHAR(100),

    -- Quién envió
    enviado_por_id INT REFERENCES usuarios(id),
    enviado_por_nombre VARCHAR(100),

    -- Estado
    estado VARCHAR(20) DEFAULT 'ENVIADO',
    email_enviado BOOLEAN DEFAULT false,
    error_envio TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_maquina ON notificaciones_cliente(maquina_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_instalacion ON notificaciones_cliente(instalacion_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_fecha ON notificaciones_cliente(created_at DESC);


-- ============================================
-- 4. TABLA: configuracion_notificaciones_cliente
-- Configuración global del sistema
-- ============================================

CREATE TABLE IF NOT EXISTS configuracion_notificaciones_cliente (
    id SERIAL PRIMARY KEY,

    -- Email para copias
    email_copia VARCHAR(150),

    -- Email remitente (debe ser verificado en Resend)
    email_remitente VARCHAR(150) DEFAULT 'avisos@fedes.es',
    nombre_remitente VARCHAR(100) DEFAULT 'Fedes Ascensores',

    -- Configuración
    activo BOOLEAN DEFAULT true,

    -- Timestamps
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insertar configuración por defecto
INSERT INTO configuracion_notificaciones_cliente (email_copia, activo)
VALUES ('', true)
ON CONFLICT DO NOTHING;


-- ============================================
-- 5. VISTA: v_maquinas_para_notificacion
-- Vista simplificada para el buscador
-- ============================================

CREATE OR REPLACE VIEW v_maquinas_para_notificacion AS
SELECT
    m.id,
    m.identificador,
    m.codigo_maquina,
    i.id as instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,
    i.email_contacto,
    i.nombre_contacto,
    m.en_cartera
FROM maquinas_cartera m
LEFT JOIN instalaciones i ON m.instalacion_id = i.id
WHERE m.en_cartera = true
ORDER BY i.nombre, m.identificador;


COMMIT;

-- ============================================
-- NOTAS DE IMPLEMENTACIÓN:
--
-- 1. El perfil 'tecnico' se añade en helpers.py
-- 2. Los usuarios técnicos se crean desde el panel de admin:
--    - Ir a Admin > Usuarios
--    - Crear usuario con perfil "Tecnico"
--    - Usuarios técnicos a crear: Sergio, Federico, Hugo
-- 3. El email remitente debe estar verificado en Resend
-- 4. Configurar email de copia en /avisos-cliente/configuracion
-- ============================================

-- ============================================
-- OPCIONAL: Crear usuarios técnicos por SQL
-- (Alternativa al panel de admin)
-- NOTA: Cambiar las contraseñas antes de ejecutar
-- ============================================

-- INSERT INTO usuarios (nombre_usuario, contrasena, perfil, activo) VALUES
-- ('Sergio', 'CAMBIAR_CONTRASENA', 'tecnico', true),
-- ('Federico', 'CAMBIAR_CONTRASENA', 'tecnico', true),
-- ('Hugo', 'CAMBIAR_CONTRASENA', 'tecnico', true)
-- ON CONFLICT DO NOTHING;
