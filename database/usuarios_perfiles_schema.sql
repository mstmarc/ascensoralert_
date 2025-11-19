-- ============================================
-- SISTEMA DE PERFILES Y CONTROL DE ACCESO
-- AscensorAlert - Fedes Ascensores
-- ============================================

-- Tabla: Usuarios con campo perfil añadido
-- ============================================
-- NOTA: Este script añade el campo 'perfil' a la tabla usuarios existente

-- Paso 1: Añadir columna perfil si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'usuarios' AND column_name = 'perfil'
    ) THEN
        ALTER TABLE usuarios ADD COLUMN perfil VARCHAR(50) DEFAULT 'visualizador';
    END IF;
END $$;

-- Paso 2: Crear índice para búsquedas por perfil
CREATE INDEX IF NOT EXISTS idx_usuarios_perfil ON usuarios(perfil);

-- Paso 3: Añadir constraint para validar perfiles
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS chk_perfil_valido;
ALTER TABLE usuarios ADD CONSTRAINT chk_perfil_valido
    CHECK (perfil IN ('admin', 'gestor', 'visualizador'));

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON COLUMN usuarios.perfil IS 'Perfil del usuario: admin (acceso total), gestor (todo excepto inspecciones), visualizador (solo lectura)';

-- ============================================
-- DEFINICIÓN DE PERFILES Y PERMISOS
-- ============================================
/*
PERFILES DISPONIBLES:

1. ADMIN
   - Acceso total al sistema
   - Crear, editar y eliminar en todos los módulos
   - Acceso al módulo de Inspecciones
   - Gestión de usuarios

2. GESTOR
   - Acceso a todos los módulos EXCEPTO Inspecciones
   - Crear, editar y eliminar en:
     * Clientes (comunidades)
     * Equipos (ascensores)
     * Oportunidades comerciales
     * Administradores
     * Visitas
   - NO tiene acceso al módulo de Inspecciones (IPOs)

3. VISUALIZADOR
   - Solo lectura en todos los módulos permitidos
   - Ver información de:
     * Clientes
     * Equipos
     * Oportunidades
     * Administradores
   - NO puede crear, editar ni eliminar
   - NO tiene acceso al módulo de Inspecciones
*/

-- ============================================
-- SCRIPT DE MIGRACIÓN PARA USUARIOS EXISTENTES
-- ============================================
/*
INSTRUCCIONES PARA CONFIGURAR USUARIOS EXISTENTES:

-- Establecer como admin (acceso total):
UPDATE usuarios SET perfil = 'admin' WHERE nombre_usuario = 'tu_usuario_admin';

-- Establecer como gestor (sin acceso a inspecciones):
UPDATE usuarios SET perfil = 'gestor' WHERE nombre_usuario = 'julio';

-- Establecer como visualizador (solo lectura):
UPDATE usuarios SET perfil = 'visualizador' WHERE nombre_usuario IN ('usuario1', 'usuario2');
*/

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
