-- ============================================
-- SCRIPT DE CORRECCIÓN: Vincular visitas huérfanas con oportunidades
-- ============================================
-- Este script identifica y corrige visitas que deberían estar vinculadas a oportunidades
-- pero que fueron creadas con el bug del filtro de estados

-- ============================================
-- PASO 1: DIAGNÓSTICO - Ver visitas candidatas a corregir
-- ============================================

-- 1.1. Visitas a instalación sin oportunidad_id
SELECT
    vs.id as visita_id,
    vs.fecha_visita,
    vs.cliente_id,
    c.nombre_cliente,
    c.direccion,
    o.id as oportunidad_candidata_id,
    o.tipo as oportunidad_tipo,
    o.estado as oportunidad_estado,
    o.fecha_creacion as oportunidad_fecha_creacion,
    vs.observaciones
FROM visitas_seguimiento vs
INNER JOIN clientes c ON vs.cliente_id = c.id
LEFT JOIN oportunidades o ON o.cliente_id = vs.cliente_id
    AND o.estado NOT IN ('ganada', 'perdida')  -- Solo oportunidades activas
    AND vs.fecha_visita >= o.fecha_creacion::date  -- La visita es posterior a la oportunidad
    AND vs.fecha_visita <= COALESCE(o.updated_at::date, CURRENT_DATE)  -- Y no mucho después
WHERE vs.oportunidad_id IS NULL  -- Visitas sin vincular
ORDER BY vs.fecha_visita DESC;

-- 1.2. Visitas a administradores sin oportunidad_id
SELECT
    va.id as visita_id,
    va.fecha_visita,
    va.administrador_id,
    va.administrador_fincas,
    va.persona_contacto,
    -- Buscar oportunidades del mismo administrador
    o.id as oportunidad_candidata_id,
    o.tipo as oportunidad_tipo,
    o.estado as oportunidad_estado,
    o.cliente_id,
    c.nombre_cliente,
    va.observaciones
FROM visitas_administradores va
LEFT JOIN administradores a ON va.administrador_id = a.id
-- Buscar clientes del mismo administrador
LEFT JOIN clientes c ON c.administrador_id = va.administrador_id
-- Buscar oportunidades de esos clientes
LEFT JOIN oportunidades o ON o.cliente_id = c.id
    AND o.estado NOT IN ('ganada', 'perdida')
    AND va.fecha_visita >= o.fecha_creacion::date
    AND va.fecha_visita <= COALESCE(o.updated_at::date, CURRENT_DATE) + INTERVAL '30 days'
WHERE va.oportunidad_id IS NULL
ORDER BY va.fecha_visita DESC;

-- ============================================
-- PASO 2: CORRECCIÓN AUTOMÁTICA (usar con precaución)
-- ============================================

-- 2.1. Actualizar visitas_seguimiento
-- IMPORTANTE: Esta query vincula SOLO si hay UNA oportunidad activa para el cliente en las fechas
UPDATE visitas_seguimiento vs
SET oportunidad_id = subquery.oportunidad_id
FROM (
    SELECT DISTINCT ON (vs.id)
        vs.id as visita_id,
        o.id as oportunidad_id
    FROM visitas_seguimiento vs
    INNER JOIN oportunidades o ON o.cliente_id = vs.cliente_id
        AND o.estado NOT IN ('ganada', 'perdida')
        AND vs.fecha_visita >= o.fecha_creacion::date
        AND vs.fecha_visita <= COALESCE(o.updated_at::date, CURRENT_DATE) + INTERVAL '7 days'
    WHERE vs.oportunidad_id IS NULL
    ORDER BY vs.id, o.fecha_creacion DESC  -- Priorizar oportunidad más reciente
) subquery
WHERE vs.id = subquery.visita_id;

-- Ver cuántas se actualizaron
SELECT COUNT(*) as visitas_seguimiento_actualizadas
FROM visitas_seguimiento
WHERE oportunidad_id IS NOT NULL;

-- 2.2. Actualizar visitas_administradores
-- IMPORTANTE: Vincula con la oportunidad más reciente del mismo administrador/cliente
UPDATE visitas_administradores va
SET oportunidad_id = subquery.oportunidad_id
FROM (
    SELECT DISTINCT ON (va.id)
        va.id as visita_id,
        o.id as oportunidad_id
    FROM visitas_administradores va
    INNER JOIN clientes c ON c.administrador_id = va.administrador_id
    INNER JOIN oportunidades o ON o.cliente_id = c.id
        AND o.estado NOT IN ('ganada', 'perdida')
        AND va.fecha_visita >= o.fecha_creacion::date
        AND va.fecha_visita <= COALESCE(o.updated_at::date, CURRENT_DATE) + INTERVAL '30 days'
    WHERE va.oportunidad_id IS NULL
    ORDER BY va.id, o.fecha_creacion DESC
) subquery
WHERE va.id = subquery.visita_id;

-- Ver cuántas se actualizaron
SELECT COUNT(*) as visitas_administrador_actualizadas
FROM visitas_administradores
WHERE oportunidad_id IS NOT NULL;

-- ============================================
-- PASO 3: VERIFICACIÓN POST-CORRECCIÓN
-- ============================================

-- 3.1. Ver estadísticas finales
SELECT
    'visitas_seguimiento' as tabla,
    COUNT(*) as total_visitas,
    COUNT(oportunidad_id) as con_oportunidad,
    COUNT(*) - COUNT(oportunidad_id) as sin_oportunidad
FROM visitas_seguimiento
UNION ALL
SELECT
    'visitas_administradores',
    COUNT(*),
    COUNT(oportunidad_id),
    COUNT(*) - COUNT(oportunidad_id)
FROM visitas_administradores;

-- 3.2. Ver últimas visitas vinculadas a oportunidades
SELECT
    'instalacion' as tipo_visita,
    vs.id,
    vs.fecha_visita,
    c.nombre_cliente,
    o.tipo as oportunidad_tipo,
    o.estado as oportunidad_estado
FROM visitas_seguimiento vs
INNER JOIN clientes c ON vs.cliente_id = c.id
INNER JOIN oportunidades o ON vs.oportunidad_id = o.id
ORDER BY vs.fecha_visita DESC
LIMIT 20;

-- 3.3. Oportunidades y sus visitas
SELECT
    o.id as oportunidad_id,
    o.tipo,
    o.estado,
    c.nombre_cliente,
    (SELECT COUNT(*) FROM visitas_seguimiento WHERE oportunidad_id = o.id) as visitas_instalacion,
    (SELECT COUNT(*) FROM visitas_administradores WHERE oportunidad_id = o.id) as visitas_admin
FROM oportunidades o
INNER JOIN clientes c ON o.cliente_id = c.id
WHERE o.estado NOT IN ('ganada', 'perdida')
ORDER BY o.fecha_creacion DESC;

-- ============================================
-- NOTAS DE USO:
-- ============================================
-- 1. Ejecutar PASO 1 primero para ver qué se va a corregir
-- 2. Revisar los resultados manualmente
-- 3. Si los resultados son correctos, ejecutar PASO 2
-- 4. Ejecutar PASO 3 para verificar
--
-- ADVERTENCIA: El PASO 2 hace cambios permanentes en la BD.
-- Hacer backup antes si es necesario.
