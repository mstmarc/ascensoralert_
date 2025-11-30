-- ============================================
-- MÓDULO DE GESTIÓN DE CARTERA Y ANÁLISIS
-- AscensorAlert - Fedes Ascensores
-- ============================================

-- Tabla 1: Instalaciones (Edificios/Comunidades) - SIMPLIFICADA
-- ============================================
-- NOTA: Datos completos están en el ERP. Esto es solo para identificación y agrupación.
CREATE TABLE IF NOT EXISTS instalaciones (
    id SERIAL PRIMARY KEY,

    -- Identificación mínima (para importación y agrupación)
    nombre VARCHAR(255) NOT NULL, -- Nombre del edificio/comunidad
    municipio VARCHAR(100), -- Para filtros y agrupación en análisis

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Instalaciones
CREATE INDEX IF NOT EXISTS idx_instalaciones_nombre ON instalaciones(nombre);
CREATE INDEX IF NOT EXISTS idx_instalaciones_municipio ON instalaciones(municipio);

-- Tabla 2: Máquinas de Cartera (Ascensores) - SIMPLIFICADA
-- ============================================
-- NOTA: Datos completos están en el ERP. Esto es solo para identificación y enlace con partes/inspecciones.
CREATE TABLE IF NOT EXISTS maquinas_cartera (
    id SERIAL PRIMARY KEY,

    -- Relación con instalación
    instalacion_id INTEGER NOT NULL REFERENCES instalaciones(id) ON DELETE RESTRICT,

    -- Identificación (CLAVE: enlaza con inspecciones.maquina y partes_trabajo.maquina_texto)
    identificador VARCHAR(255) NOT NULL UNIQUE, -- Ej: "MONTACOCHES (CONCESIONARIO JAGUAR)"

    -- Código de máquina (informativo, para referencia con ERP)
    codigo_maquina VARCHAR(100), -- Ej: "V301F8817", "FGC160/2/0"

    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Máquinas
CREATE INDEX IF NOT EXISTS idx_maquinas_instalacion ON maquinas_cartera(instalacion_id);
CREATE INDEX IF NOT EXISTS idx_maquinas_identificador ON maquinas_cartera(identificador);

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
    oportunidad_id INTEGER, -- FK se agregará después de crear oportunidades_facturacion

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
CREATE INDEX IF NOT EXISTS idx_partes_numero ON partes_trabajo(numero_parte);
CREATE INDEX IF NOT EXISTS idx_partes_maquina ON partes_trabajo(maquina_id);
CREATE INDEX IF NOT EXISTS idx_partes_tipo_original ON partes_trabajo(tipo_parte_original);
CREATE INDEX IF NOT EXISTS idx_partes_tipo_normalizado ON partes_trabajo(tipo_parte_normalizado);
CREATE INDEX IF NOT EXISTS idx_partes_fecha ON partes_trabajo(fecha_parte DESC);
CREATE INDEX IF NOT EXISTS idx_partes_estado ON partes_trabajo(estado);
CREATE INDEX IF NOT EXISTS idx_partes_prioridad ON partes_trabajo(prioridad) WHERE estado != 'COMPLETADO';
CREATE INDEX IF NOT EXISTS idx_partes_facturado ON partes_trabajo(facturado) WHERE facturado = false;
CREATE INDEX IF NOT EXISTS idx_partes_recomendacion ON partes_trabajo(tiene_recomendacion) WHERE tiene_recomendacion = true;
CREATE INDEX IF NOT EXISTS idx_partes_recomendacion_no_revisada ON partes_trabajo(recomendacion_revisada) WHERE tiene_recomendacion = true AND recomendacion_revisada = false;
CREATE INDEX IF NOT EXISTS idx_partes_oportunidad ON partes_trabajo(oportunidad_id) WHERE oportunidad_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_partes_maquina_texto ON partes_trabajo(maquina_texto); -- Para búsquedas durante importación

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
CREATE INDEX IF NOT EXISTS idx_oportunidades_maquina ON oportunidades_facturacion(maquina_id);
CREATE INDEX IF NOT EXISTS idx_oportunidades_parte_origen ON oportunidades_facturacion(parte_origen_id);
CREATE INDEX IF NOT EXISTS idx_oportunidades_estado ON oportunidades_facturacion(estado);
CREATE INDEX IF NOT EXISTS idx_oportunidades_fecha_envio ON oportunidades_facturacion(fecha_envio_presupuesto);
CREATE INDEX IF NOT EXISTS idx_oportunidades_pendientes ON oportunidades_facturacion(estado)
    WHERE estado IN ('DETECTADA', 'PRESUPUESTO_ENVIADO', 'ACEPTADO', 'PENDIENTE_REPUESTO');
CREATE INDEX IF NOT EXISTS idx_oportunidades_repuesto ON oportunidades_facturacion(estado_repuestos);
CREATE INDEX IF NOT EXISTS idx_oportunidades_facturado ON oportunidades_facturacion(facturado) WHERE facturado = false;
CREATE INDEX IF NOT EXISTS idx_oportunidades_prioridad ON oportunidades_facturacion(prioridad_comercial);

-- ============================================
-- VISTAS ÚTILES PARA DASHBOARDS Y ANÁLISIS
-- ============================================
-- NOTA: Vistas simplificadas enfocadas en análisis de partes de trabajo
-- Datos de gestión (contratos, clientes, etc.) están en el ERP

-- Vista: Resumen de partes por máquina
CREATE OR REPLACE VIEW v_resumen_partes_maquina AS
SELECT
    m.id as maquina_id,
    m.identificador,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Total de partes
    COUNT(p.id) as total_partes,
    COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '12 months') as partes_ultimo_año,

    -- Por tipo normalizado
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'AVERIA') as total_averias,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO') as total_mantenimientos,
    COUNT(p.id) FILTER (WHERE p.tipo_parte_normalizado = 'REPARACION') as total_reparaciones,

    -- Averías recientes
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

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte) as dias_sin_intervencion,

    -- Recomendaciones
    COUNT(p.id) FILTER (WHERE p.tiene_recomendacion = true) as total_recomendaciones,
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true AND p.recomendacion_revisada = false
    ) as recomendaciones_pendientes,

    -- Oportunidades
    COUNT(p.id) FILTER (WHERE p.oportunidad_creada = true) as total_oportunidades_creadas

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
GROUP BY m.id, m.identificador, i.nombre, i.municipio;

-- Vista: Partes con recomendaciones pendientes de revisar
CREATE OR REPLACE VIEW v_partes_con_recomendaciones AS
SELECT
    p.id,
    p.numero_parte,
    p.tipo_parte_original,
    p.fecha_parte,
    p.resolucion,
    p.recomendaciones_extraidas,
    m.identificador as maquina_identificador,
    i.nombre as instalacion_nombre,
    i.municipio
FROM partes_trabajo p
INNER JOIN maquinas_cartera m ON p.maquina_id = m.id
INNER JOIN instalaciones i ON m.instalacion_id = i.id
WHERE p.tiene_recomendacion = true
AND p.recomendacion_revisada = false
AND p.oportunidad_creada = false
ORDER BY p.fecha_parte DESC;

-- ============================================
-- VISTAS PARA ANÁLISIS OPERACIONAL AVANZADO
-- ============================================

-- Vista: Índice de Problemas por Máquina (para detectar ascensores críticos)
CREATE OR REPLACE VIEW v_maquinas_problematicas AS
SELECT
    m.id as maquina_id,
    m.identificador,
    
    
    i.nombre as instalacion_nombre,
    i.municipio,
    

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
GROUP BY m.id, m.identificador,   i.nombre, i.municipio;

-- ============================================
-- FOREIGN KEYS ADICIONALES (después de crear todas las tablas)
-- ============================================
-- Resolver dependencia circular entre partes_trabajo y oportunidades_facturacion

-- Eliminar constraint si existe antes de crearla
ALTER TABLE IF EXISTS partes_trabajo DROP CONSTRAINT IF EXISTS fk_partes_oportunidad;

ALTER TABLE partes_trabajo
ADD CONSTRAINT fk_partes_oportunidad
FOREIGN KEY (oportunidad_id) REFERENCES oportunidades_facturacion(id) ON DELETE SET NULL;

