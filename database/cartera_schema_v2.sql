-- ============================================
-- MÓDULO DE ANALÍTICA AVANZADA V2 - AscensorAlert
-- Sistema de Alertas Prioritarias y Gestión Predictiva
-- ============================================
-- Este schema extiende cartera_schema.sql con capacidades predictivas y de alertas

-- ============================================
-- TABLA: Componentes Críticos (Base de Conocimiento)
-- ============================================
CREATE TABLE IF NOT EXISTS componentes_criticos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- Ej: "Puerta", "Cerradero", "Reenvío"
    familia VARCHAR(50) NOT NULL, -- PUERTAS, MANIOBRA, SEGURIDAD, COMUNICACION, CABINA
    descripcion TEXT,

    -- Palabras clave para detección (JSON array de strings)
    keywords TEXT[], -- Ej: {'puerta', 'cierre', 'apertura', 'hoja'}

    -- Criticidad del componente
    nivel_critico VARCHAR(20) DEFAULT 'MEDIO', -- ALTO, MEDIO, BAJO

    -- Coste promedio de reparación (para cálculo de pérdidas)
    coste_reparacion_promedio DECIMAL(10,2),

    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Componentes Críticos
CREATE INDEX IF NOT EXISTS idx_componentes_familia ON componentes_criticos(familia);
CREATE INDEX IF NOT EXISTS idx_componentes_nivel ON componentes_criticos(nivel_critico);

-- Insertar componentes más comunes (ajusta según tu realidad)
INSERT INTO componentes_criticos (nombre, familia, keywords, nivel_critico, coste_reparacion_promedio) VALUES
    ('Puerta automática', 'PUERTAS', ARRAY['puerta', 'cierre', 'apertura', 'hoja', 'corredera'], 'ALTO', 450.00),
    ('Cerradero', 'PUERTAS', ARRAY['cerradero', 'pestillo', 'gancho'], 'ALTO', 180.00),
    ('Barrera fotoeléctrica', 'SEGURIDAD', ARRAY['barrera', 'fotocélula', 'fotocelula', 'fotoeléctrica'], 'ALTO', 220.00),
    ('Reenvío de planta', 'MANIOBRA', ARRAY['reenvío', 'reenvio', 'botonera planta', 'pulsador planta'], 'MEDIO', 320.00),
    ('Comunicación bidireccional', 'COMUNICACION', ARRAY['bidireccional', 'comunicación', 'comunicacion', 'telefonía', 'telefonia', 'gsm'], 'ALTO', 380.00),
    ('Batería auxiliar', 'ELECTRICA', ARRAY['batería', 'bateria', 'bat auxiliar', 'fuente auxiliar'], 'MEDIO', 150.00),
    ('Cable viajero', 'ELECTRICA', ARRAY['cable viajero', 'cables cabina'], 'MEDIO', 280.00),
    ('Botonera cabina', 'CABINA', ARRAY['botonera', 'pulsadores cabina', 'botones'], 'MEDIO', 250.00),
    ('Variador', 'MANIOBRA', ARRAY['variador', 'inversor', 'convertidor'], 'ALTO', 1200.00),
    ('Limitador velocidad', 'SEGURIDAD', ARRAY['limitador', 'regulador velocidad'], 'ALTO', 850.00),
    ('Paracaídas', 'SEGURIDAD', ARRAY['paracaidas', 'paracaídas', 'freno seguridad'], 'ALTO', 900.00),
    ('Contacto de cabina', 'SEGURIDAD', ARRAY['contacto cabina', 'contacto puerta'], 'MEDIO', 120.00)
ON CONFLICT (nombre) DO NOTHING;

-- ============================================
-- TABLA: Alertas Automáticas
-- ============================================
CREATE TABLE IF NOT EXISTS alertas_automaticas (
    id SERIAL PRIMARY KEY,

    -- Relaciones
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE CASCADE,
    instalacion_id INTEGER NOT NULL REFERENCES instalaciones(id) ON DELETE CASCADE,
    componente_id INTEGER REFERENCES componentes_criticos(id) ON DELETE SET NULL,

    -- Tipo de alerta
    tipo_alerta VARCHAR(50) NOT NULL,
    -- FALLA_REPETIDA: Mismo componente falla 2+ veces en 30 días
    -- RECOMENDACION_IGNORADA: Recomendación sin ejecutar + 2 averías posteriores
    -- MANTENIMIENTO_OMITIDO: 2+ meses sin conservación
    -- MANTENIMIENTO_OMITIDO_CON_AVERIAS: Sin conservación + aumento de averías
    -- DEFECTO_IPO_CRITICO: IPO caducada + 2+ averías en 60 días
    -- INSTALACION_CRITICA: Instalación completa en riesgo alto

    -- Prioridad
    nivel_urgencia VARCHAR(20) DEFAULT 'MEDIA', -- URGENTE, ALTA, MEDIA, BAJA

    -- Datos de la alerta
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    datos_deteccion JSONB, -- Datos estructurados de la detección (frecuencia, fechas, etc.)

    -- Estado
    estado VARCHAR(50) DEFAULT 'PENDIENTE',
    -- PENDIENTE: Detectada, sin acción
    -- EN_REVISION: Alguien la está mirando
    -- OPORTUNIDAD_CREADA: Se convirtió en oportunidad comercial
    -- TRABAJO_PROGRAMADO: Está en el backlog técnico
    -- RESUELTA: Problema resuelto
    -- DESCARTADA: Falso positivo o no relevante

    -- Acciones tomadas
    oportunidad_id INTEGER REFERENCES oportunidades_facturacion(id) ON DELETE SET NULL,
    pendiente_tecnico_id INTEGER, -- FK se agregará después

    -- Seguimiento
    fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_revision TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    revisada_por VARCHAR(100),
    notas_resolucion TEXT,

    -- Notificaciones enviadas
    notificacion_enviada BOOLEAN DEFAULT false,
    fecha_notificacion TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Alertas
CREATE INDEX IF NOT EXISTS idx_alertas_maquina ON alertas_automaticas(maquina_id);
CREATE INDEX IF NOT EXISTS idx_alertas_instalacion ON alertas_automaticas(instalacion_id);
CREATE INDEX IF NOT EXISTS idx_alertas_tipo ON alertas_automaticas(tipo_alerta);
CREATE INDEX IF NOT EXISTS idx_alertas_urgencia ON alertas_automaticas(nivel_urgencia);
CREATE INDEX IF NOT EXISTS idx_alertas_estado ON alertas_automaticas(estado);
CREATE INDEX IF NOT EXISTS idx_alertas_pendientes ON alertas_automaticas(estado) WHERE estado = 'PENDIENTE';
CREATE INDEX IF NOT EXISTS idx_alertas_urgentes ON alertas_automaticas(nivel_urgencia, estado)
    WHERE nivel_urgencia IN ('URGENTE', 'ALTA') AND estado IN ('PENDIENTE', 'EN_REVISION');
CREATE INDEX IF NOT EXISTS idx_alertas_fecha ON alertas_automaticas(fecha_deteccion DESC);

-- ============================================
-- TABLA: Pendientes Técnicos (Backlog de Sergio)
-- ============================================
CREATE TABLE IF NOT EXISTS pendientes_tecnicos (
    id SERIAL PRIMARY KEY,

    -- Relaciones
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE CASCADE,
    instalacion_id INTEGER NOT NULL REFERENCES instalaciones(id) ON DELETE CASCADE,
    alerta_id INTEGER REFERENCES alertas_automaticas(id) ON DELETE SET NULL,
    parte_origen_id INTEGER REFERENCES partes_trabajo(id) ON DELETE SET NULL,

    -- Tipo de trabajo
    tipo_trabajo VARCHAR(50) NOT NULL,
    -- MANTENIMIENTO_PENDIENTE: Conservación atrasada
    -- REPARACION_CRITICA: Avería que se repite
    -- COMPONENTE_RECOMENDADO: Sustitución recomendada
    -- SEGUIMIENTO_TECNICO: Requiere revisión técnica
    -- DEFECTO_INSPECCION: Defecto de IPO por subsanar

    -- Prioridad
    nivel_urgencia VARCHAR(20) DEFAULT 'MEDIA', -- URGENTE, ALTA, MEDIA, BAJA

    -- Descripción
    titulo VARCHAR(255) NOT NULL,
    descripcion_tecnica TEXT NOT NULL,
    componente VARCHAR(100), -- Componente específico involucrado

    -- Estado
    estado VARCHAR(50) DEFAULT 'PENDIENTE',
    -- PENDIENTE: Sin asignar
    -- ASIGNADO: Asignado a técnico
    -- EN_CURSO: Técnico trabajando
    -- BLOQUEADO: Esperando repuesto/aprobación
    -- COMPLETADO: Trabajo terminado
    -- CANCELADO: Ya no aplica

    -- Asignación
    asignado_a VARCHAR(100), -- Email o nombre del técnico
    fecha_asignacion TIMESTAMP,
    fecha_estimada_ejecucion DATE,

    -- Repuestos necesarios
    requiere_repuestos BOOLEAN DEFAULT false,
    descripcion_repuestos TEXT,
    estado_repuestos VARCHAR(50), -- DISPONIBLE, SOLICITADO, PENDIENTE_COMPRA, RECIBIDO

    -- Ejecución
    fecha_inicio TIMESTAMP,
    fecha_completado TIMESTAMP,
    tiempo_estimado_horas DECIMAL(4,1),
    tiempo_real_horas DECIMAL(4,1),
    notas_ejecucion TEXT,

    -- Resultado
    resultado VARCHAR(50), -- EXITOSO, PARCIAL, PENDIENTE_SEGUIMIENTO
    genera_facturacion BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Índices para Pendientes Técnicos
CREATE INDEX IF NOT EXISTS idx_pendientes_maquina ON pendientes_tecnicos(maquina_id);
CREATE INDEX IF NOT EXISTS idx_pendientes_instalacion ON pendientes_tecnicos(instalacion_id);
CREATE INDEX IF NOT EXISTS idx_pendientes_tipo ON pendientes_tecnicos(tipo_trabajo);
CREATE INDEX IF NOT EXISTS idx_pendientes_urgencia ON pendientes_tecnicos(nivel_urgencia);
CREATE INDEX IF NOT EXISTS idx_pendientes_estado ON pendientes_tecnicos(estado);
CREATE INDEX IF NOT EXISTS idx_pendientes_asignado ON pendientes_tecnicos(asignado_a) WHERE estado IN ('ASIGNADO', 'EN_CURSO');
CREATE INDEX IF NOT EXISTS idx_pendientes_activos ON pendientes_tecnicos(estado, nivel_urgencia)
    WHERE estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO', 'BLOQUEADO');
CREATE INDEX IF NOT EXISTS idx_pendientes_urgentes ON pendientes_tecnicos(nivel_urgencia, estado)
    WHERE nivel_urgencia IN ('URGENTE', 'ALTA') AND estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO');

-- Resolver FK circular con alertas
ALTER TABLE alertas_automaticas DROP CONSTRAINT IF EXISTS fk_alertas_pendiente;
ALTER TABLE alertas_automaticas
ADD CONSTRAINT fk_alertas_pendiente
FOREIGN KEY (pendiente_tecnico_id) REFERENCES pendientes_tecnicos(id) ON DELETE SET NULL;

-- ============================================
-- VISTA: Estado Semafórico de Máquinas
-- ============================================
CREATE OR REPLACE VIEW v_estado_maquinas_semaforico AS
SELECT
    m.id as maquina_id,
    m.identificador,
    m.en_cartera,
    m.instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Métricas base
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
    ) as averias_mes,

    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre,

    -- Fallas repetidas (alertas activas)
    (SELECT COUNT(*) FROM alertas_automaticas a
     WHERE a.maquina_id = m.id
     AND a.tipo_alerta = 'FALLA_REPETIDA'
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,

    -- Recomendaciones sin ejecutar
    COUNT(p.id) FILTER (
        WHERE p.tiene_recomendacion = true
        AND p.recomendacion_revisada = false
        AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,

    -- Mantenimientos omitidos
    CASE
        WHEN MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
             < CURRENT_DATE - INTERVAL '60 days' THEN 1
        ELSE 0
    END as mantenimiento_atrasado,

    -- Defectos IPO pendientes
    (SELECT COUNT(d.id)
     FROM inspecciones insp
     INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
     WHERE insp.maquina = m.identificador
     AND d.estado = 'PENDIENTE'
    ) as defectos_ipo_pendientes,

    -- Pendientes técnicos activos
    (SELECT COUNT(*) FROM pendientes_tecnicos pt
     WHERE pt.maquina_id = m.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO', 'BLOQUEADO')
    ) as pendientes_tecnicos_activos,

    -- CÁLCULO DE ESTADO SEMAFÓRICO
    CASE
        -- 🟥 CRÍTICO: Múltiples problemas graves
        WHEN (
            -- 3+ averías en el mes
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
            ) >= 3
            OR
            -- 2+ fallas repetidas activas
            (SELECT COUNT(*) FROM alertas_automaticas a
             WHERE a.maquina_id = m.id
             AND a.tipo_alerta = 'FALLA_REPETIDA'
             AND a.estado IN ('PENDIENTE', 'EN_REVISION')
            ) >= 2
            OR
            -- Mantenimiento atrasado + averías recientes
            (
                MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
                < CURRENT_DATE - INTERVAL '60 days'
                AND
                COUNT(p.id) FILTER (
                    WHERE p.tipo_parte_normalizado = 'AVERIA'
                    AND p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month'
                ) >= 2
            )
        ) THEN 'CRITICO'

        -- 🟧 INESTABLE: Problemas frecuentes o sin mantenimiento
        WHEN (
            -- 5+ averías en trimestre
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) >= 5
            OR
            -- 1 falla repetida
            (SELECT COUNT(*) FROM alertas_automaticas a
             WHERE a.maquina_id = m.id
             AND a.tipo_alerta = 'FALLA_REPETIDA'
             AND a.estado IN ('PENDIENTE', 'EN_REVISION')
            ) >= 1
            OR
            -- Mantenimiento muy atrasado
            MAX(p.fecha_parte) FILTER (WHERE p.tipo_parte_normalizado = 'MANTENIMIENTO')
            < CURRENT_DATE - INTERVAL '90 days'
            OR
            -- 2+ defectos IPO pendientes
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            ) >= 2
        ) THEN 'INESTABLE'

        -- 🟨 SEGUIMIENTO: Requiere atención
        WHEN (
            -- 2-4 averías en trimestre
            COUNT(p.id) FILTER (
                WHERE p.tipo_parte_normalizado = 'AVERIA'
                AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
            ) BETWEEN 2 AND 4
            OR
            -- Recomendaciones vencidas
            COUNT(p.id) FILTER (
                WHERE p.tiene_recomendacion = true
                AND p.recomendacion_revisada = false
                AND p.fecha_parte < CURRENT_DATE - INTERVAL '30 days'
            ) >= 1
            OR
            -- 1 defecto IPO pendiente
            (SELECT COUNT(d.id)
             FROM inspecciones insp
             INNER JOIN defectos_inspeccion d ON insp.id = d.inspeccion_id
             WHERE insp.maquina = m.identificador
             AND d.estado = 'PENDIENTE'
            ) = 1
        ) THEN 'SEGUIMIENTO'

        -- 🟩 ESTABLE: Sin problemas significativos
        ELSE 'ESTABLE'
    END as estado_semaforico,

    -- Última intervención
    MAX(p.fecha_parte) as ultima_intervencion,
    CURRENT_DATE - MAX(p.fecha_parte)::date as dias_sin_intervencion

FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
WHERE m.en_cartera = true
GROUP BY m.id, m.identificador, m.en_cartera, m.instalacion_id, i.nombre, i.municipio;

-- ============================================
-- VISTA: Índice de Riesgo de Instalación (IRI)
-- ============================================
CREATE OR REPLACE VIEW v_riesgo_instalaciones AS
SELECT
    i.id as instalacion_id,
    i.nombre as instalacion_nombre,
    i.municipio,

    -- Total de máquinas
    COUNT(DISTINCT m.id) as total_maquinas,

    -- Máquinas por estado
    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'CRITICO'
    ) as maquinas_criticas,

    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'INESTABLE'
    ) as maquinas_inestables,

    COUNT(DISTINCT m.id) FILTER (
        WHERE esm.estado_semaforico = 'SEGUIMIENTO'
    ) as maquinas_seguimiento,

    -- Promedio de índice de problema (de la vista existente)
    ROUND(AVG(vmp.indice_problema), 2) as promedio_indice_problema,

    -- Alertas activas en la instalación
    (SELECT COUNT(*)
     FROM alertas_automaticas a
     INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
     WHERE mc.instalacion_id = i.id
     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
    ) as alertas_activas,

    -- Pendientes técnicos urgentes
    (SELECT COUNT(*)
     FROM pendientes_tecnicos pt
     WHERE pt.instalacion_id = i.id
     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
     AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
    ) as pendientes_urgentes,

    -- Averías totales en la instalación (último trimestre)
    COUNT(p.id) FILTER (
        WHERE p.tipo_parte_normalizado = 'AVERIA'
        AND p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months'
    ) as averias_trimestre_instalacion,

    -- CÁLCULO DEL ÍNDICE DE RIESGO DE INSTALACIÓN (IRI)
    -- Fórmula: 30% promedio_índice + 40% máquinas_críticas_peso + 30% pendientes_urgentes_peso
    ROUND(
        (
            -- 30% del promedio de índices de máquinas (normalizado a escala 0-100)
            (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
            +
            -- 40% peso de máquinas críticas/inestables
            (
                (
                    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                    COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                ) * 0.40
            )
            +
            -- 30% peso de pendientes urgentes y alertas
            (
                (
                    (SELECT COUNT(*)
                     FROM pendientes_tecnicos pt
                     WHERE pt.instalacion_id = i.id
                     AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                     AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 8
                    +
                    (SELECT COUNT(*)
                     FROM alertas_automaticas a
                     INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                     WHERE mc.instalacion_id = i.id
                     AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                     AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                    ) * 5
                ) * 0.30
            )
        )
    , 2) as indice_riesgo_instalacion,

    -- Clasificación de riesgo de instalación
    CASE
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 50 THEN 'CRITICO'
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 25 THEN 'ALTO'
        WHEN ROUND(
            (
                (COALESCE(AVG(vmp.indice_problema), 0) * 2) * 0.30
                +
                (
                    (
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'CRITICO') * 20 +
                        COUNT(DISTINCT m.id) FILTER (WHERE esm.estado_semaforico = 'INESTABLE') * 10
                    ) * 0.40
                )
                +
                (
                    (
                        (SELECT COUNT(*)
                         FROM pendientes_tecnicos pt
                         WHERE pt.instalacion_id = i.id
                         AND pt.estado IN ('PENDIENTE', 'ASIGNADO', 'EN_CURSO')
                         AND pt.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 8
                        +
                        (SELECT COUNT(*)
                         FROM alertas_automaticas a
                         INNER JOIN maquinas_cartera mc ON a.maquina_id = mc.id
                         WHERE mc.instalacion_id = i.id
                         AND a.estado IN ('PENDIENTE', 'EN_REVISION')
                         AND a.nivel_urgencia IN ('URGENTE', 'ALTA')
                        ) * 5
                    ) * 0.30
                )
            )
        , 2) >= 10 THEN 'MEDIO'
        ELSE 'BAJO'
    END as nivel_riesgo_instalacion

FROM instalaciones i
INNER JOIN maquinas_cartera m ON i.id = m.instalacion_id AND m.en_cartera = true
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id
LEFT JOIN v_maquinas_problematicas vmp ON m.id = vmp.maquina_id
LEFT JOIN v_estado_maquinas_semaforico esm ON m.id = esm.maquina_id
GROUP BY i.id, i.nombre, i.municipio;

-- ============================================
-- VISTA: Resumen de Pérdidas por Pendientes
-- ============================================
CREATE OR REPLACE VIEW v_perdidas_por_pendientes AS
SELECT
    -- Recomendaciones no ejecutadas
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) as recomendaciones_vencidas,

    -- Valor estimado de recomendaciones perdidas (350€ promedio por recomendación)
    (SELECT COUNT(*)
     FROM partes_trabajo
     WHERE tiene_recomendacion = true
     AND recomendacion_revisada = false
     AND oportunidad_creada = false
     AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
    ) * 350.00 as valor_recomendaciones_perdidas,

    -- Averías evitables (fallas repetidas que generan costes)
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) as fallas_repetidas_activas,

    -- Coste promedio de cada avería evitable (180€ promedio)
    (SELECT COUNT(*)
     FROM alertas_automaticas
     WHERE tipo_alerta = 'FALLA_REPETIDA'
     AND estado IN ('PENDIENTE', 'EN_REVISION')
    ) * 180.00 as coste_averias_evitables,

    -- Oportunidades detectadas sin presupuestar
    (SELECT COUNT(*)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
     AND fecha_envio_presupuesto IS NULL
    ) as oportunidades_sin_presupuesto,

    -- Valor de oportunidades sin presupuestar (500€ promedio)
    (SELECT COALESCE(SUM(importe_presupuestado), COUNT(*) * 500.00)
     FROM oportunidades_facturacion
     WHERE estado = 'DETECTADA'
    ) as valor_oportunidades_sin_presupuesto,

    -- Total estimado de pérdida de facturación
    (
        (SELECT COUNT(*)
         FROM partes_trabajo
         WHERE tiene_recomendacion = true
         AND recomendacion_revisada = false
         AND oportunidad_creada = false
         AND fecha_parte < CURRENT_DATE - INTERVAL '30 days'
        ) * 350.00
        +
        (SELECT COUNT(*)
         FROM alertas_automaticas
         WHERE tipo_alerta = 'FALLA_REPETIDA'
         AND estado IN ('PENDIENTE', 'EN_REVISION')
        ) * 180.00
        +
        (SELECT COALESCE(SUM(importe_presupuestado), COUNT(*) * 500.00)
         FROM oportunidades_facturacion
         WHERE estado = 'DETECTADA'
        )
    ) as perdida_total_estimada;

-- ============================================
-- FUNCIONES AUXILIARES
-- ============================================

-- Función: Extraer componente de un texto de resolución
CREATE OR REPLACE FUNCTION detectar_componente_critico(texto_resolucion TEXT)
RETURNS INTEGER AS $$
DECLARE
    componente_record RECORD;
    texto_upper TEXT;
    keyword TEXT;
BEGIN
    IF texto_resolucion IS NULL OR texto_resolucion = '' THEN
        RETURN NULL;
    END IF;

    texto_upper := UPPER(texto_resolucion);

    -- Buscar cada componente crítico
    FOR componente_record IN
        SELECT id, keywords FROM componentes_criticos WHERE activo = true
    LOOP
        -- Revisar cada keyword del componente
        FOREACH keyword IN ARRAY componente_record.keywords
        LOOP
            IF texto_upper LIKE '%' || UPPER(keyword) || '%' THEN
                RETURN componente_record.id;
            END IF;
        END LOOP;
    END LOOP;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE componentes_criticos IS 'Base de conocimiento de componentes críticos para detección automática de patrones';
COMMENT ON TABLE alertas_automaticas IS 'Alertas generadas automáticamente por el sistema de detección de patrones';
COMMENT ON TABLE pendientes_tecnicos IS 'Backlog técnico para Sergio - trabajos pendientes priorizados automáticamente';
COMMENT ON VIEW v_estado_maquinas_semaforico IS 'Estado semafórico de máquinas: CRITICO 🟥 / INESTABLE 🟧 / SEGUIMIENTO 🟨 / ESTABLE 🟩';
COMMENT ON VIEW v_riesgo_instalaciones IS 'Índice de Riesgo de Instalación (IRI) - priorización de instalaciones problemáticas';
COMMENT ON VIEW v_perdidas_por_pendientes IS 'Cálculo de pérdida de facturación estimada por trabajos pendientes';
