-- ============================================
-- MÓDULO DE GESTIÓN DE CARTERA Y ANÁLISIS
-- AscensorAlert - Fedes Ascensores
-- ============================================

-- Tabla 1: Instalaciones (Edificios/Comunidades)
-- ============================================
CREATE TABLE IF NOT EXISTS instalaciones (
    id SERIAL PRIMARY KEY,

    -- Identificación
    referencia VARCHAR(100), -- Código interno de referencia
    nombre VARCHAR(255) NOT NULL, -- Nombre del edificio/comunidad

    -- Ubicación
    direccion TEXT NOT NULL,
    municipio VARCHAR(100),
    codigo_postal VARCHAR(10),
    provincia VARCHAR(100) DEFAULT 'Las Palmas',

    -- Cliente/Contacto
    cliente_nombre VARCHAR(255),
    cliente_cif VARCHAR(20),
    contacto_nombre VARCHAR(255),
    contacto_telefono VARCHAR(50),
    contacto_email VARCHAR(255),

    -- Información adicional
    administrador VARCHAR(255), -- Administrador de fincas
    numero_viviendas INTEGER,
    observaciones TEXT,

    -- Estado
    activo BOOLEAN DEFAULT true,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Instalaciones
CREATE INDEX idx_instalaciones_referencia ON instalaciones(referencia);
CREATE INDEX idx_instalaciones_municipio ON instalaciones(municipio);
CREATE INDEX idx_instalaciones_cliente ON instalaciones(cliente_nombre);
CREATE INDEX idx_instalaciones_activo ON instalaciones(activo) WHERE activo = true;

-- Tabla 2: Máquinas de Cartera (Ascensores)
-- ============================================
CREATE TABLE IF NOT EXISTS maquinas_cartera (
    id SERIAL PRIMARY KEY,

    -- Relación con instalación
    instalacion_id INTEGER NOT NULL REFERENCES instalaciones(id) ON DELETE RESTRICT,

    -- Identificación (enlaza con inspecciones.maquina)
    identificador VARCHAR(100) NOT NULL UNIQUE, -- Este campo enlaza con inspecciones.maquina
    rae VARCHAR(100), -- Registro de Aparatos Elevadores

    -- Datos técnicos
    tipo_maquina VARCHAR(100), -- Ascensor, Montacargas, Plataforma, etc.
    marca VARCHAR(100),
    modelo VARCHAR(100),
    año_instalacion INTEGER,
    numero_serie VARCHAR(100),
    capacidad_kg INTEGER,
    capacidad_personas INTEGER,
    numero_paradas INTEGER,

    -- Contrato
    tipo_contrato VARCHAR(100), -- MANTENIMIENTO_INTEGRAL, SOLO_AVERIAS, INSPECCION, etc.
    fecha_inicio_contrato DATE,
    fecha_fin_contrato DATE,
    importe_mensual DECIMAL(10,2),

    -- Estado
    estado_maquina VARCHAR(50) DEFAULT 'OPERATIVA', -- OPERATIVA, PARADA, AVERIADA, BAJA
    observaciones TEXT,
    activo BOOLEAN DEFAULT true,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Máquinas
CREATE INDEX idx_maquinas_instalacion ON maquinas_cartera(instalacion_id);
CREATE INDEX idx_maquinas_identificador ON maquinas_cartera(identificador);
CREATE INDEX idx_maquinas_rae ON maquinas_cartera(rae);
CREATE INDEX idx_maquinas_tipo ON maquinas_cartera(tipo_maquina);
CREATE INDEX idx_maquinas_contrato_fin ON maquinas_cartera(fecha_fin_contrato);
CREATE INDEX idx_maquinas_activo ON maquinas_cartera(activo) WHERE activo = true;
CREATE INDEX idx_maquinas_estado ON maquinas_cartera(estado_maquina);

-- Tabla 3: Partes de Trabajo (Historial de Intervenciones)
-- ============================================
CREATE TABLE IF NOT EXISTS partes_trabajo (
    id SERIAL PRIMARY KEY,

    -- Relación con máquina
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE RESTRICT,

    -- Tipo de intervención
    tipo_parte VARCHAR(50) NOT NULL, -- MANTENIMIENTO, AVERIA, REPARACION, INCIDENCIA, MODERNIZACION

    -- Fecha y tiempo
    fecha_parte DATE NOT NULL,
    hora_inicio TIME,
    hora_fin TIME,
    tiempo_empleado INTEGER, -- Minutos totales

    -- Descripción
    descripcion TEXT NOT NULL,
    solucion TEXT, -- Qué se hizo para resolver

    -- Recursos
    tecnico VARCHAR(255), -- Nombre del técnico
    materiales_usados TEXT, -- Descripción de materiales

    -- Costes
    coste_materiales DECIMAL(10,2),
    coste_mano_obra DECIMAL(10,2),
    coste_total DECIMAL(10,2),

    -- Estado
    estado VARCHAR(50) DEFAULT 'COMPLETADO', -- PENDIENTE, EN_PROCESO, COMPLETADO, CANCELADO
    fecha_completado DATE,

    -- Prioridad (para pendientes)
    prioridad VARCHAR(20) DEFAULT 'NORMAL', -- BAJA, NORMAL, ALTA, URGENTE

    -- Información adicional
    requiere_seguimiento BOOLEAN DEFAULT false,
    fecha_seguimiento DATE,
    observaciones TEXT,

    -- Facturación
    facturado BOOLEAN DEFAULT false,
    numero_factura VARCHAR(100),
    fecha_factura DATE,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Partes de Trabajo
CREATE INDEX idx_partes_maquina ON partes_trabajo(maquina_id);
CREATE INDEX idx_partes_tipo ON partes_trabajo(tipo_parte);
CREATE INDEX idx_partes_fecha ON partes_trabajo(fecha_parte DESC);
CREATE INDEX idx_partes_estado ON partes_trabajo(estado);
CREATE INDEX idx_partes_tecnico ON partes_trabajo(tecnico);
CREATE INDEX idx_partes_prioridad ON partes_trabajo(prioridad) WHERE estado != 'COMPLETADO';
CREATE INDEX idx_partes_seguimiento ON partes_trabajo(fecha_seguimiento) WHERE requiere_seguimiento = true;
CREATE INDEX idx_partes_facturado ON partes_trabajo(facturado) WHERE facturado = false;

-- ============================================
-- VISTAS ÚTILES PARA DASHBOARDS Y ANÁLISIS
-- ============================================

-- Vista: Instalaciones con resumen de máquinas
CREATE OR REPLACE VIEW v_instalaciones_completas AS
SELECT
    i.*,
    COUNT(m.id) as total_maquinas,
    COUNT(m.id) FILTER (WHERE m.activo = true) as maquinas_activas,
    COUNT(m.id) FILTER (WHERE m.estado_maquina = 'OPERATIVA') as maquinas_operativas,
    COUNT(m.id) FILTER (WHERE m.estado_maquina = 'AVERIADA') as maquinas_averiadas,
    MIN(m.fecha_fin_contrato) as contrato_proximo_vencimiento,
    -- Contar inspecciones pendientes de segunda
    (SELECT COUNT(DISTINCT insp.id)
     FROM maquinas_cartera mc
     INNER JOIN inspecciones insp ON mc.identificador = insp.maquina
     WHERE mc.instalacion_id = i.id
     AND insp.fecha_segunda_inspeccion IS NOT NULL
     AND insp.fecha_segunda_realizada IS NULL
     AND insp.fecha_segunda_inspeccion < CURRENT_DATE
    ) as inspecciones_vencidas,
    -- Contar partes pendientes
    (SELECT COUNT(p.id)
     FROM maquinas_cartera mc
     INNER JOIN partes_trabajo p ON mc.id = p.maquina_id
     WHERE mc.instalacion_id = i.id
     AND p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id
GROUP BY i.id;

-- Vista: Máquinas con información completa
CREATE OR REPLACE VIEW v_maquinas_completas AS
SELECT
    m.*,
    i.nombre as instalacion_nombre,
    i.direccion as instalacion_direccion,
    i.municipio as instalacion_municipio,
    i.cliente_nombre,
    -- Última inspección
    (SELECT MAX(fecha_inspeccion)
     FROM inspecciones insp
     WHERE insp.maquina = m.identificador
    ) as ultima_inspeccion,
    -- Próxima segunda inspección
    (SELECT MIN(fecha_segunda_inspeccion)
     FROM inspecciones insp
     WHERE insp.maquina = m.identificador
     AND fecha_segunda_realizada IS NULL
     AND fecha_segunda_inspeccion >= CURRENT_DATE
    ) as proxima_segunda_inspeccion,
    -- Defectos pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_pendientes,
    -- Partes de trabajo
    (SELECT COUNT(p.id)
     FROM partes_trabajo p
     WHERE p.maquina_id = m.id
     AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as partes_ultimo_año,
    (SELECT COUNT(p.id)
     FROM partes_trabajo p
     WHERE p.maquina_id = m.id
     AND p.tipo_parte = 'AVERIA'
     AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as averias_ultimo_año,
    (SELECT COUNT(p.id)
     FROM partes_trabajo p
     WHERE p.maquina_id = m.id
     AND p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes,
    -- Última intervención
    (SELECT MAX(fecha_parte)
     FROM partes_trabajo p
     WHERE p.maquina_id = m.id
    ) as ultima_intervencion,
    -- Estado del contrato
    CASE
        WHEN m.fecha_fin_contrato IS NULL THEN 'SIN_FECHA'
        WHEN m.fecha_fin_contrato < CURRENT_DATE THEN 'VENCIDO'
        WHEN m.fecha_fin_contrato <= CURRENT_DATE + INTERVAL '30 days' THEN 'PROXIMO_VENCIMIENTO'
        WHEN m.fecha_fin_contrato <= CURRENT_DATE + INTERVAL '60 days' THEN 'VENCIMIENTO_CERCANO'
        ELSE 'VIGENTE'
    END as estado_contrato
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id;

-- Vista: Partes de trabajo con información completa
CREATE OR REPLACE VIEW v_partes_completos AS
SELECT
    p.*,
    m.identificador as maquina_identificador,
    m.tipo_maquina,
    i.nombre as instalacion_nombre,
    i.direccion as instalacion_direccion,
    i.municipio,
    i.cliente_nombre,
    -- Cálculo de días pendientes
    CASE
        WHEN p.estado IN ('PENDIENTE', 'EN_PROCESO') THEN
            CURRENT_DATE - p.fecha_parte
        ELSE NULL
    END as dias_pendiente,
    -- Nivel de urgencia
    CASE
        WHEN p.estado NOT IN ('PENDIENTE', 'EN_PROCESO') THEN 'COMPLETADO'
        WHEN p.prioridad = 'URGENTE' THEN 'URGENTE'
        WHEN p.prioridad = 'ALTA' THEN 'ALTA'
        WHEN p.fecha_parte < CURRENT_DATE - INTERVAL '7 days' THEN 'ATRASADO'
        ELSE 'NORMAL'
    END as nivel_urgencia
FROM partes_trabajo p
INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id;

-- Vista: Análisis de averías por máquina
CREATE OR REPLACE VIEW v_analisis_averias AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.tipo_maquina,
    i.nombre as instalacion_nombre,
    i.municipio,
    -- Averías del año actual
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE)
    ) as averias_año_actual,
    -- Averías del año anterior
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
    ) as averias_año_anterior,
    -- Tiempo promedio de resolución (en horas)
    AVG(p.tiempo_empleado) FILTER (
        WHERE p.tipo_parte = 'AVERIA' AND p.tiempo_empleado IS NOT NULL
    ) / 60.0 as tiempo_medio_resolucion_horas,
    -- Coste total de averías año actual
    SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE)
    ) as coste_averias_año_actual,
    -- Última avería
    MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte = 'AVERIA') as ultima_averia,
    -- Total de intervenciones
    COUNT(p.id) as total_intervenciones
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, m.tipo_maquina, i.nombre, i.municipio;

-- Vista: Resumen de partes pendientes
CREATE OR REPLACE VIEW v_partes_pendientes AS
SELECT
    p.*,
    m.identificador as maquina_identificador,
    i.nombre as instalacion_nombre,
    i.municipio,
    CURRENT_DATE - p.fecha_parte as dias_pendiente,
    CASE
        WHEN p.prioridad = 'URGENTE' THEN 1
        WHEN p.prioridad = 'ALTA' THEN 2
        WHEN CURRENT_DATE - p.fecha_parte > 7 THEN 3
        ELSE 4
    END as orden_prioridad
FROM partes_trabajo p
INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
ORDER BY orden_prioridad ASC, p.fecha_parte ASC;

-- ============================================
-- VISTAS PARA ANÁLISIS OPERACIONAL AVANZADO
-- ============================================

-- Vista: Índice de Problemas por Máquina (para detectar ascensores críticos)
CREATE OR REPLACE VIEW v_maquinas_problematicas AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.tipo_maquina,
    m.estado_maquina,
    i.nombre as instalacion_nombre,
    i.municipio,
    i.cliente_nombre,

    -- Métricas de averías
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as averias_ultimo_año,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_ultimo_trimestre,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_ultimo_mes,

    -- Tendencia (comparar último trimestre vs trimestre anterior)
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) - COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '6 months'
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '3 months'
    ) as tendencia_averias,

    -- Mantenimientos realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_realizados_año,

    -- Mantenimientos pendientes/cancelados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.estado IN ('PENDIENTE', 'CANCELADO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_no_realizados,

    -- Costes
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_averias_año,

    -- Facturación pendiente
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.estado = 'COMPLETADO'
        AND p.facturado = false
    ), 0) as facturacion_pendiente,

    -- Partes pendientes actuales
    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
    ) as partes_pendientes,

    COUNT(p.id) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
        AND p.prioridad IN ('URGENTE', 'ALTA')
    ) as partes_pendientes_urgentes,

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,

    -- Días desde última intervención
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,

    -- Defectos de inspección pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_inspeccion_pendientes,

    -- Calcular ÍNDICE DE PROBLEMA (score compuesto)
    -- Fórmula: (averías_trimestre * 3) + (averías_mes * 5) + (partes_pendientes_urgentes * 2) + defectos_pendientes
    (
        (COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'AVERIA'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
        ) * 3)
        +
        (COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'AVERIA'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
        ) * 5)
        +
        (COUNT(p.id) FILTER (
            WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
            AND p.prioridad IN ('URGENTE', 'ALTA')
        ) * 2)
        +
        (SELECT COUNT(d.id)
         FROM inspecciones insp
         INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
         WHERE insp.maquina = m.identificador
         AND d.estado = 'PENDIENTE'
        )
    ) as indice_problema,

    -- Clasificación de riesgo
    CASE
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 2)
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 15 THEN 'CRITICO'
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 2)
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 8 THEN 'ALTO'
        WHEN (
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) * 5)
            +
            (COUNT(p.id) FILTER (
                WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
                AND p.prioridad IN ('URGENTE', 'ALTA')
            ) * 2)
            +
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            )
        ) >= 3 THEN 'MEDIO'
        ELSE 'BAJO'
    END as nivel_riesgo

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, m.tipo_maquina, m.estado_maquina, i.nombre, i.municipio, i.cliente_nombre;

-- Vista: Análisis de Impacto Económico por Máquina
CREATE OR REPLACE VIEW v_analisis_economico AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.tipo_maquina,
    i.nombre as instalacion_nombre,
    i.cliente_nombre,
    m.tipo_contrato,
    m.importe_mensual,

    -- Ingresos anuales del contrato
    COALESCE(m.importe_mensual * 12, 0) as ingreso_anual_contrato,

    -- Costes de averías
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_averias_año,

    -- Costes de mantenimiento
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_mantenimientos_año,

    -- Reparaciones facturables
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte IN ('REPARACION', 'MODERNIZACION')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as facturacion_reparaciones_año,

    -- Facturación pendiente (trabajo hecho no facturado)
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.estado = 'COMPLETADO'
        AND p.facturado = false
    ), 0) as facturacion_pendiente,

    -- Estimación de pérdida por partes pendientes urgentes
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.estado IN ('PENDIENTE', 'EN_PROCESO')
        AND p.prioridad IN ('URGENTE', 'ALTA')
    ), 0) as perdida_estimada_pendientes,

    -- Margen estimado (ingreso contrato - costes)
    COALESCE(m.importe_mensual * 12, 0) -
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte IN ('AVERIA', 'MANTENIMIENTO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as margen_estimado_año,

    -- Rentabilidad (porcentaje)
    CASE
        WHEN COALESCE(m.importe_mensual * 12, 0) > 0 THEN
            ((COALESCE(m.importe_mensual * 12, 0) -
              COALESCE(SUM(p.coste_total) FILTER (
                  WHERE p.tipo_parte IN ('AVERIA', 'MANTENIMIENTO')
                  AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
              ), 0)) / (m.importe_mensual * 12)) * 100
        ELSE NULL
    END as rentabilidad_porcentaje

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, m.tipo_maquina, i.nombre, i.cliente_nombre,
         m.tipo_contrato, m.importe_mensual;

-- Vista: Análisis de Mantenimientos vs Averías (detectar círculos viciosos)
CREATE OR REPLACE VIEW v_mantenimientos_vs_averias AS
SELECT
    m.id as maquina_id,
    m.identificador,
    i.nombre as instalacion_nombre,
    i.cliente_nombre,

    -- Mantenimientos programados vs realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_totales,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_completados,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'MANTENIMIENTO'
        AND p.estado IN ('PENDIENTE', 'CANCELADO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_no_realizados,

    -- Tasa de cumplimiento
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) > 0 THEN
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'MANTENIMIENTO'
                AND p.estado = 'COMPLETADO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )::float /
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'MANTENIMIENTO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )) * 100
        ELSE 100
    END as tasa_cumplimiento_mantenimiento,

    -- Averías después de mantenimientos no realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as total_averias_año,

    -- Ratio de problemas (averías / mantenimientos completados)
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) > 0 THEN
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )::float /
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte = 'MANTENIMIENTO'
                AND p.estado = 'COMPLETADO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )
        ELSE 999 -- Valor alto si no hay mantenimientos
    END as ratio_averias_mantenimiento,

    -- Clasificación de salud de mantenimiento
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) = 0 THEN 'SIN_PLAN'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ), 0)) * 100 >= 80 THEN 'EXCELENTE'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ), 0)) * 100 >= 60 THEN 'ACEPTABLE'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ), 0)) * 100 >= 40 THEN 'DEFICIENTE'
        ELSE 'CRITICO'
    END as salud_mantenimiento

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, i.nombre, i.cliente_nombre;

-- ============================================
-- TRIGGERS PARA ACTUALIZAR updated_at
-- ============================================

-- Trigger para instalaciones
DROP TRIGGER IF EXISTS update_instalaciones_updated_at ON instalaciones;
CREATE TRIGGER update_instalaciones_updated_at
    BEFORE UPDATE ON instalaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para maquinas_cartera
DROP TRIGGER IF EXISTS update_maquinas_updated_at ON maquinas_cartera;
CREATE TRIGGER update_maquinas_updated_at
    BEFORE UPDATE ON maquinas_cartera
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para partes_trabajo
DROP TRIGGER IF EXISTS update_partes_updated_at ON partes_trabajo;
CREATE TRIGGER update_partes_updated_at
    BEFORE UPDATE ON partes_trabajo
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE instalaciones IS 'Instalaciones (edificios/comunidades) de la cartera de Gran Canaria';
COMMENT ON TABLE maquinas_cartera IS 'Máquinas (ascensores) de la cartera - enlaza con inspecciones por campo identificador';
COMMENT ON TABLE partes_trabajo IS 'Historial de intervenciones técnicas: mantenimientos, averías, reparaciones, incidencias';

COMMENT ON COLUMN maquinas_cartera.identificador IS 'Identificador único que enlaza con inspecciones.maquina';
COMMENT ON COLUMN partes_trabajo.tipo_parte IS 'Valores: MANTENIMIENTO, AVERIA, REPARACION, INCIDENCIA, MODERNIZACION';
COMMENT ON COLUMN partes_trabajo.estado IS 'Valores: PENDIENTE, EN_PROCESO, COMPLETADO, CANCELADO';
COMMENT ON COLUMN partes_trabajo.prioridad IS 'Valores: BAJA, NORMAL, ALTA, URGENTE';

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
