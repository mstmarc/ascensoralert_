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

    -- Datos del Excel original (importación)
    numero_parte VARCHAR(50) UNIQUE, -- Ej: 2024000022
    tipo_parte_original VARCHAR(50) NOT NULL, -- CONSERVACIÓN, AVERÍA, GUARDIA AVISO, etc. (tal cual del Excel)
    codigo_maquina VARCHAR(100), -- CÓD. MÁQUINA del Excel (ej: FGC060-1/10) - Informativo
    maquina_texto VARCHAR(255), -- MÁQUINA del Excel (ej: MANUEL ALEMAN ALAMO 2. PAR) - Este es el identificador
    fecha_parte TIMESTAMP NOT NULL, -- Incluye fecha y hora (01/01/2024 21:27)
    codificacion_adicional TEXT, -- Campo CODIFICACIÓN ADICIONAL del Excel
    resolucion TEXT, -- Campo RESOLUCIÓN del Excel (descripción completa del trabajo)

    -- Relación con nuestra BD (una vez mapeada durante importación)
    maquina_id INTEGER REFERENCES maquinas_cartera(id) ON DELETE SET NULL, -- NULL si no se encuentra la máquina

    -- Tipo normalizado para análisis (mapeado desde tipo_parte_original)
    tipo_parte_normalizado VARCHAR(50), -- MANTENIMIENTO, AVERIA, REPARACION, INCIDENCIA, MODERNIZACION, INSPECCION

    -- Detección automática de recomendaciones
    tiene_recomendacion BOOLEAN DEFAULT false,
    recomendaciones_extraidas TEXT, -- Texto de recomendación si se detecta en RESOLUCIÓN
    recomendacion_revisada BOOLEAN DEFAULT false, -- Si ya fue revisada por el usuario

    -- Oportunidades de facturación
    oportunidad_creada BOOLEAN DEFAULT false,
    oportunidad_id INTEGER REFERENCES oportunidades_facturacion(id) ON DELETE SET NULL,

    -- Gestión adicional (campos que tú gestionas manualmente o calculas)
    estado VARCHAR(50) DEFAULT 'COMPLETADO', -- COMPLETADO (default al importar), PENDIENTE, EN_PROCESO, CANCELADO
    prioridad VARCHAR(20) DEFAULT 'NORMAL', -- BAJA, NORMAL, ALTA, URGENTE

    -- Costes (puedes añadirlos manualmente después de importar)
    coste_materiales DECIMAL(10,2),
    coste_mano_obra DECIMAL(10,2),
    coste_total DECIMAL(10,2),

    -- Facturación
    facturado BOOLEAN DEFAULT false,
    numero_factura VARCHAR(100),
    fecha_factura DATE,

    -- Notas internas adicionales (separadas de la resolución original)
    notas_internas TEXT,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importado BOOLEAN DEFAULT true -- true si viene de Excel, false si se crea manual
);

-- Índices para Partes de Trabajo
CREATE INDEX idx_partes_numero ON partes_trabajo(numero_parte);
CREATE INDEX idx_partes_maquina ON partes_trabajo(maquina_id);
CREATE INDEX idx_partes_tipo_original ON partes_trabajo(tipo_parte_original);
CREATE INDEX idx_partes_tipo_normalizado ON partes_trabajo(tipo_parte_normalizado);
CREATE INDEX idx_partes_fecha ON partes_trabajo(fecha_parte DESC);
CREATE INDEX idx_partes_estado ON partes_trabajo(estado);
CREATE INDEX idx_partes_prioridad ON partes_trabajo(prioridad) WHERE estado != 'COMPLETADO';
CREATE INDEX idx_partes_facturado ON partes_trabajo(facturado) WHERE facturado = false;
CREATE INDEX idx_partes_recomendacion ON partes_trabajo(tiene_recomendacion) WHERE tiene_recomendacion = true;
CREATE INDEX idx_partes_recomendacion_no_revisada ON partes_trabajo(recomendacion_revisada) WHERE tiene_recomendacion = true AND recomendacion_revisada = false;
CREATE INDEX idx_partes_oportunidad ON partes_trabajo(oportunidad_id) WHERE oportunidad_id IS NOT NULL;
CREATE INDEX idx_partes_maquina_texto ON partes_trabajo(maquina_texto); -- Para búsquedas durante importación

-- Tabla 4: Mapeo de Tipos de Parte (para normalización)
-- ============================================
CREATE TABLE IF NOT EXISTS tipos_parte_mapeo (
    id SERIAL PRIMARY KEY,
    tipo_original VARCHAR(50) UNIQUE NOT NULL, -- Tipo tal cual viene del Excel
    tipo_normalizado VARCHAR(50) NOT NULL, -- Tipo para análisis
    descripcion TEXT,
    activo BOOLEAN DEFAULT true
);

-- Insertar mapeos según distribución real
INSERT INTO tipos_parte_mapeo (tipo_original, tipo_normalizado, descripcion) VALUES
    ('CONSERVACIÓN', 'MANTENIMIENTO', 'Mantenimiento preventivo regular - 64.22%'),
    ('AVERÍA', 'AVERIA', 'Avería general - 15.78%'),
    ('GUARDIA AVISO', 'AVERIA', 'Avería atendida en guardia - 7.11%'),
    ('RESOL. AVERIAS', 'AVERIA', 'Resolución de averías - 4.22%'),
    ('INSPECCIÓN', 'INSPECCION', 'Inspección técnica - 3.14%'),
    ('RESCATE', 'INCIDENCIA', 'Rescate de personas - 2.06%'),
    ('INCIDENCIAS', 'INCIDENCIA', 'Incidencias generales - 1.60%'),
    ('MANT. PREVENTIVO', 'MANTENIMIENTO', 'Mantenimiento preventivo - 1.29%'),
    ('REPARACIÓN', 'REPARACION', 'Reparación - 0.38%'),
    ('REFORMA', 'MODERNIZACION', 'Reforma/Modernización - 0.12%'),
    ('REVISION SUPERVISOR', 'INSPECCION', 'Revisión de supervisor - 0.05%'),
    ('PUESTA EN MARCHA', 'INSTALACION', 'Puesta en marcha - 0.02%')
ON CONFLICT (tipo_original) DO NOTHING;

-- Tabla 5: Oportunidades de Facturación
-- ============================================
CREATE TABLE IF NOT EXISTS oportunidades_facturacion (
    id SERIAL PRIMARY KEY,

    -- Relación
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE RESTRICT,
    parte_origen_id INTEGER REFERENCES partes_trabajo(id) ON DELETE SET NULL, -- Parte que generó la oportunidad

    -- Descripción
    titulo VARCHAR(255) NOT NULL,
    descripcion_tecnica TEXT NOT NULL,
    tipo VARCHAR(50), -- REPARACION, MEJORA, MODERNIZACION, SUSTITUCION

    -- Estado del proceso
    estado VARCHAR(50) DEFAULT 'DETECTADA',
    -- DETECTADA: Identificada, pendiente hacer presupuesto
    -- PRESUPUESTO_ENVIADO: Presupuesto enviado, esperando respuesta
    -- ACEPTADO: Cliente aceptó, pendiente ejecutar
    -- RECHAZADO: Cliente rechazó
    -- PENDIENTE_REPUESTO: Aceptado pero esperando repuesto
    -- LISTO_EJECUTAR: Todo listo para que técnicos ejecuten
    -- COMPLETADO: Trabajo completado
    -- FACTURADO: Facturado al cliente

    -- Presupuesto (hecho en ERP externo)
    numero_presupuesto_erp VARCHAR(100), -- Referencia del presupuesto en el ERP
    importe_presupuestado DECIMAL(10,2),
    fecha_envio_presupuesto DATE,
    presupuesto_pdf_url TEXT, -- URL del PDF en Supabase Storage (opcional)

    -- Respuesta cliente
    fecha_respuesta_cliente DATE,
    fecha_aceptacion DATE,
    fecha_rechazo DATE,
    motivo_rechazo TEXT,

    -- Gestión de repuestos
    repuestos_necesarios TEXT, -- Descripción de repuestos
    estado_repuestos VARCHAR(50),
    -- DISPONIBLE_LOCAL: En almacén local
    -- SOLICITAR_TENERIFE: Necesita solicitarse a almacén central
    -- COMPRAR_EXTERNO: Necesita comprarse a proveedor
    -- SOLICITADO: Ya solicitado, pendiente recepción
    -- RECIBIDO: Repuesto recibido
    fecha_solicitud_repuesto DATE,
    fecha_recepcion_repuesto DATE,
    proveedor VARCHAR(255), -- Si se compra externo
    referencia_pedido VARCHAR(100), -- Número de pedido
    coste_repuestos DECIMAL(10,2),

    -- Ejecución
    importe_final DECIMAL(10,2), -- Por si difiere del presupuestado
    fecha_programada_ejecucion DATE,
    fecha_completado DATE,
    notas_ejecucion TEXT,

    -- Facturación
    facturado BOOLEAN DEFAULT false,
    numero_factura VARCHAR(100),
    fecha_factura DATE,

    -- Prioridad comercial y observaciones
    prioridad_comercial VARCHAR(20) DEFAULT 'MEDIA', -- BAJA, MEDIA, ALTA
    notas TEXT,

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Oportunidades de Facturación
CREATE INDEX idx_oportunidades_maquina ON oportunidades_facturacion(maquina_id);
CREATE INDEX idx_oportunidades_parte_origen ON oportunidades_facturacion(parte_origen_id);
CREATE INDEX idx_oportunidades_estado ON oportunidades_facturacion(estado);
CREATE INDEX idx_oportunidades_fecha_envio ON oportunidades_facturacion(fecha_envio_presupuesto);
CREATE INDEX idx_oportunidades_pendientes ON oportunidades_facturacion(estado)
    WHERE estado IN ('DETECTADA', 'PRESUPUESTO_ENVIADO', 'ACEPTADO', 'PENDIENTE_REPUESTO');
CREATE INDEX idx_oportunidades_repuesto ON oportunidades_facturacion(estado_repuestos);
CREATE INDEX idx_oportunidades_facturado ON oportunidades_facturacion(facturado) WHERE facturado = false;
CREATE INDEX idx_oportunidades_prioridad ON oportunidades_facturacion(prioridad_comercial);

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
     AND p.tipo_parte_normalizado = 'AVERIA'
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
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE)
    ) as averias_año_actual,
    -- Averías del año anterior
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
    ) as averias_año_anterior,
    -- Tiempo promedio de resolución (en horas)
    AVG(p.tiempo_empleado) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA' AND p.tiempo_empleado IS NOT NULL
    ) / 60.0 as tiempo_medio_resolucion_horas,
    -- Coste total de averías año actual
    SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND EXTRACT(YEAR FROM p.fecha_parte) = EXTRACT(YEAR FROM CURRENT_DATE)
    ) as coste_averias_año_actual,
    -- Última avería
    MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as ultima_averia,
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
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as averias_ultimo_año,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_ultimo_trimestre,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_ultimo_mes,

    -- Tendencia (comparar último trimestre vs trimestre anterior)
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) - COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '6 months'
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '3 months'
    ) as tendencia_averias,

    -- Mantenimientos realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_realizados_año,

    -- Mantenimientos pendientes/cancelados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado IN ('PENDIENTE', 'CANCELADO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_no_realizados,

    -- Costes
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
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
            WHERE p.tipo_parte_normalizado = 'AVERIA'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
        ) * 3)
        +
        (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'AVERIA'
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
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
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
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
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
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) * 3)
            +
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
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
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_averias_año,

    -- Costes de mantenimiento
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as coste_mantenimientos_año,

    -- Reparaciones facturables
    COALESCE(SUM(p.coste_total) FILTER (
        WHERE p.tipo_parte_normalizado IN ('REPARACION', 'MODERNIZACION')
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
        WHERE p.tipo_parte_normalizado IN ('AVERIA', 'MANTENIMIENTO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ), 0) as margen_estimado_año,

    -- Rentabilidad (porcentaje)
    CASE
        WHEN COALESCE(m.importe_mensual * 12, 0) > 0 THEN
            ((COALESCE(m.importe_mensual * 12, 0) -
              COALESCE(SUM(p.coste_total) FILTER (
                  WHERE p.tipo_parte_normalizado IN ('AVERIA', 'MANTENIMIENTO')
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
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_totales,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado = 'COMPLETADO'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_completados,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
        AND p.estado IN ('PENDIENTE', 'CANCELADO')
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as mantenimientos_no_realizados,

    -- Tasa de cumplimiento
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) > 0 THEN
            (COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
                AND p.estado = 'COMPLETADO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )::float /
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )) * 100
        ELSE 100
    END as tasa_cumplimiento_mantenimiento,

    -- Averías después de mantenimientos no realizados
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
    ) as total_averias_año,

    -- Ratio de problemas (averías / mantenimientos completados)
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) > 0 THEN
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )::float /
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
                AND p.estado = 'COMPLETADO'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
            )
        ELSE 999 -- Valor alto si no hay mantenimientos
    END as ratio_averias_mantenimiento,

    -- Clasificación de salud de mantenimiento
    CASE
        WHEN COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ) = 0 THEN 'SIN_PLAN'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ), 0)) * 100 >= 80 THEN 'EXCELENTE'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        ), 0)) * 100 >= 60 THEN 'ACEPTABLE'
        WHEN (COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
            AND p.estado = 'COMPLETADO'
            AND p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months'
        )::float /
        NULLIF(COUNT(p.id) FILTER (
            WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO'
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

-- Trigger para oportunidades_facturacion
DROP TRIGGER IF EXISTS update_oportunidades_updated_at ON oportunidades_facturacion;
CREATE TRIGGER update_oportunidades_updated_at
    BEFORE UPDATE ON oportunidades_facturacion
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE instalaciones IS 'Instalaciones (edificios/comunidades) de la cartera de Gran Canaria';
COMMENT ON TABLE maquinas_cartera IS 'Máquinas (ascensores) de la cartera - enlaza con inspecciones.maquina por campo identificador';
COMMENT ON TABLE partes_trabajo IS 'Historial de partes de trabajo importados desde Excel - mantenimientos, averías, reparaciones, etc.';
COMMENT ON TABLE tipos_parte_mapeo IS 'Mapeo de tipos de parte originales del Excel a tipos normalizados para análisis';
COMMENT ON TABLE oportunidades_facturacion IS 'Oportunidades de facturación detectadas desde recomendaciones técnicas';

COMMENT ON COLUMN maquinas_cartera.identificador IS 'Identificador único que enlaza con inspecciones.maquina y partes_trabajo.maquina_texto';
COMMENT ON COLUMN partes_trabajo.numero_parte IS 'Número de parte del Excel (ej: 2024000022) - UNIQUE';
COMMENT ON COLUMN partes_trabajo.tipo_parte_original IS 'Tipo tal cual viene del Excel: CONSERVACIÓN, AVERÍA, GUARDIA AVISO, etc.';
COMMENT ON COLUMN partes_trabajo.tipo_parte_normalizado IS 'Tipo normalizado para análisis: MANTENIMIENTO, AVERIA, REPARACION, INCIDENCIA, MODERNIZACION, INSPECCION';
COMMENT ON COLUMN partes_trabajo.maquina_texto IS 'Campo MÁQUINA del Excel - es el identificador (ej: MANUEL ALEMAN ALAMO 2. PAR)';
COMMENT ON COLUMN partes_trabajo.codigo_maquina IS 'Campo CÓD. MÁQUINA del Excel - solo informativo (ej: FGC060-1/10)';
COMMENT ON COLUMN partes_trabajo.resolucion IS 'Campo RESOLUCIÓN del Excel - descripción completa del trabajo y recomendaciones del técnico';
COMMENT ON COLUMN partes_trabajo.tiene_recomendacion IS 'Detectado automáticamente si RESOLUCIÓN contiene recomendaciones técnicas';
COMMENT ON COLUMN partes_trabajo.estado IS 'Valores: COMPLETADO (default al importar), PENDIENTE, EN_PROCESO, CANCELADO';
COMMENT ON COLUMN partes_trabajo.prioridad IS 'Valores: BAJA, NORMAL, ALTA, URGENTE';

COMMENT ON COLUMN oportunidades_facturacion.estado IS 'Valores: DETECTADA, PRESUPUESTO_ENVIADO, ACEPTADO, RECHAZADO, PENDIENTE_REPUESTO, LISTO_EJECUTAR, COMPLETADO, FACTURADO';
COMMENT ON COLUMN oportunidades_facturacion.estado_repuestos IS 'Valores: DISPONIBLE_LOCAL, SOLICITAR_TENERIFE, COMPRAR_EXTERNO, SOLICITADO, RECIBIDO';
COMMENT ON COLUMN oportunidades_facturacion.numero_presupuesto_erp IS 'Número de presupuesto generado en el ERP externo de la empresa';

-- ============================================
-- FIN DEL SCRIPT
-- ============================================
