-- ============================================================================
-- SCHEMA: Sistema de Análisis Predictivo con IA para Ascensores
-- ============================================================================
-- Descripción: Sistema inteligente que analiza partes de trabajo y predice
--              futuras averías usando modelos de IA con conocimiento técnico
-- Fecha: 2025-12-04
-- ============================================================================

-- ============================================================================
-- TABLA: analisis_partes_ia
-- Almacena el análisis detallado de cada parte con IA
-- ============================================================================
CREATE TABLE IF NOT EXISTS analisis_partes_ia (
    id SERIAL PRIMARY KEY,
    parte_id INTEGER NOT NULL REFERENCES partes_trabajo(id) ON DELETE CASCADE,

    -- Información extraída por IA
    componente_principal VARCHAR(100),           -- Componente identificado (ej: "Puerta automática")
    componentes_secundarios TEXT[],              -- Array de componentes relacionados
    tipo_fallo VARCHAR(100),                     -- Clasificación del fallo (desgaste, ruptura, desajuste, etc.)
    causa_raiz TEXT,                             -- Causa raíz identificada por IA
    gravedad_tecnica VARCHAR(20),                -- LEVE, MODERADA, GRAVE, CRITICA

    -- Análisis contextual
    es_fallo_recurrente BOOLEAN DEFAULT FALSE,   -- ¿Es parte de un patrón repetitivo?
    partes_relacionados INTEGER[],               -- IDs de partes relacionados históricamente
    contexto_tecnico TEXT,                       -- Análisis contextual completo

    -- Señales de alerta temprana
    indicadores_deterioro TEXT[],                -- Señales de deterioro detectadas
    probabilidad_recurrencia DECIMAL(5,2),       -- % de probabilidad de que vuelva a ocurrir
    tiempo_estimado_proxima_falla INTEGER,       -- Días estimados hasta próxima falla (NULL si no aplica)

    -- Recomendaciones IA
    recomendacion_ia TEXT,                       -- Recomendación técnica generada por IA
    acciones_preventivas TEXT[],                 -- Array de acciones sugeridas
    urgencia_ia VARCHAR(20),                     -- BAJA, MEDIA, ALTA, URGENTE
    coste_estimado_preventivo DECIMAL(10,2),     -- Coste estimado de prevención
    coste_estimado_correctivo DECIMAL(10,2),     -- Coste si se deja sin atender

    -- Metadatos del análisis
    modelo_ia_usado VARCHAR(100),                -- Modelo de IA usado (ej: "claude-3-5-sonnet")
    confianza_analisis DECIMAL(5,2),             -- % de confianza en el análisis
    fecha_analisis TIMESTAMP DEFAULT NOW(),
    tiempo_procesamiento_ms INTEGER,             -- Tiempo que tardó el análisis

    -- Validación humana
    validado_por_tecnico BOOLEAN DEFAULT FALSE,
    validado_por_usuario_id INTEGER REFERENCES usuarios(id),
    fecha_validacion TIMESTAMP,
    comentarios_validacion TEXT,
    correccion_humana TEXT,                      -- Si el técnico corrige algo

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para analisis_partes_ia
CREATE INDEX idx_analisis_parte ON analisis_partes_ia(parte_id);
CREATE INDEX idx_analisis_componente ON analisis_partes_ia(componente_principal);
CREATE INDEX idx_analisis_gravedad ON analisis_partes_ia(gravedad_tecnica);
CREATE INDEX idx_analisis_recurrente ON analisis_partes_ia(es_fallo_recurrente) WHERE es_fallo_recurrente = TRUE;
CREATE INDEX idx_analisis_fecha ON analisis_partes_ia(fecha_analisis DESC);
CREATE INDEX idx_analisis_validacion ON analisis_partes_ia(validado_por_tecnico);

-- ============================================================================
-- TABLA: predicciones_maquina
-- Predicciones de averías futuras por máquina
-- ============================================================================
CREATE TABLE IF NOT EXISTS predicciones_maquina (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE CASCADE,

    -- Predicción general
    estado_salud_ia VARCHAR(20),                 -- EXCELENTE, BUENA, REGULAR, MALA, CRITICA
    puntuacion_salud INTEGER CHECK (puntuacion_salud >= 0 AND puntuacion_salud <= 100),
    tendencia VARCHAR(20),                       -- MEJORANDO, ESTABLE, DETERIORANDO, CRITICA

    -- Predicciones específicas por componente
    componente_riesgo_1 VARCHAR(100),            -- Componente con mayor riesgo
    probabilidad_fallo_1 DECIMAL(5,2),           -- % probabilidad de fallo
    dias_estimados_fallo_1 INTEGER,              -- Días estimados hasta fallo

    componente_riesgo_2 VARCHAR(100),
    probabilidad_fallo_2 DECIMAL(5,2),
    dias_estimados_fallo_2 INTEGER,

    componente_riesgo_3 VARCHAR(100),
    probabilidad_fallo_3 DECIMAL(5,2),
    dias_estimados_fallo_3 INTEGER,

    -- Análisis de patrones
    patron_detectado VARCHAR(50),                -- DESGASTE_PROGRESIVO, FALLOS_INTERMITENTES, etc.
    descripcion_patron TEXT,
    componentes_criticos TEXT[],                 -- Array de componentes que necesitan atención

    -- Mantenimiento predictivo
    proxima_intervencion_sugerida DATE,
    tipo_intervencion_sugerida VARCHAR(100),     -- Descripción de la intervención
    prioridad_intervencion VARCHAR(20),          -- BAJA, MEDIA, ALTA, URGENTE

    -- Análisis de costes
    coste_mantenimiento_preventivo DECIMAL(10,2),
    coste_estimado_si_no_actua DECIMAL(10,2),
    ahorro_potencial DECIMAL(10,2),              -- Diferencia entre correctivo y preventivo
    roi_intervencion DECIMAL(5,2),               -- ROI % de actuar preventivamente

    -- Contexto histórico
    partes_analizados INTEGER,                   -- Número de partes incluidos en análisis
    periodo_analisis_dias INTEGER,               -- Días de histórico analizados
    ultima_averia_grave DATE,
    dias_sin_averias INTEGER,

    -- Factores de riesgo detectados
    factores_riesgo TEXT[],                      -- Array de factores identificados
    justificacion_prediccion TEXT,               -- Explicación detallada de la predicción

    -- Metadatos
    fecha_prediccion TIMESTAMP DEFAULT NOW(),
    valida_hasta TIMESTAMP,                      -- Cuándo caduca esta predicción (ej: 30 días)
    modelo_ia_usado VARCHAR(100),
    confianza_prediccion DECIMAL(5,2),           -- % de confianza general

    -- Estado de la predicción
    estado VARCHAR(20) DEFAULT 'ACTIVA',         -- ACTIVA, VENCIDA, CONFIRMADA, DESCARTADA
    confirmada_con_averia BOOLEAN DEFAULT FALSE, -- Si la predicción se cumplió
    parte_confirmacion_id INTEGER REFERENCES partes_trabajo(id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para predicciones_maquina
CREATE INDEX idx_pred_maquina ON predicciones_maquina(maquina_id);
CREATE INDEX idx_pred_estado_salud ON predicciones_maquina(estado_salud_ia);
CREATE INDEX idx_pred_fecha ON predicciones_maquina(fecha_prediccion DESC);
CREATE INDEX idx_pred_activas ON predicciones_maquina(estado) WHERE estado = 'ACTIVA';
CREATE INDEX idx_pred_urgentes ON predicciones_maquina(prioridad_intervencion) WHERE prioridad_intervencion IN ('ALTA', 'URGENTE');
CREATE INDEX idx_pred_valida ON predicciones_maquina(valida_hasta);
CREATE UNIQUE INDEX idx_pred_maquina_activa ON predicciones_maquina(maquina_id) WHERE estado = 'ACTIVA';

-- ============================================================================
-- TABLA: conocimiento_tecnico_ia
-- Base de conocimiento técnico sobre componentes de ascensores
-- ============================================================================
CREATE TABLE IF NOT EXISTS conocimiento_tecnico_ia (
    id SERIAL PRIMARY KEY,
    componente VARCHAR(100) NOT NULL UNIQUE,

    -- Información técnica
    descripcion TEXT,
    vida_util_esperada_meses INTEGER,
    coste_promedio DECIMAL(10,2),
    coste_mano_obra_promedio DECIMAL(10,2),
    tiempo_reemplazo_horas DECIMAL(5,2),

    -- Patrones de fallo
    fallos_comunes TEXT[],                       -- Array de fallos típicos
    sintomas_desgaste TEXT[],                    -- Síntomas de desgaste
    causas_frecuentes TEXT[],                    -- Causas más frecuentes

    -- Relaciones con otros componentes
    componentes_relacionados TEXT[],             -- Componentes que suelen fallar juntos
    componentes_afectados TEXT[],                -- Componentes afectados si este falla

    -- Mantenimiento
    frecuencia_revision_meses INTEGER,
    tareas_mantenimiento TEXT[],
    criticidad VARCHAR(20),                      -- BAJA, MEDIA, ALTA, CRITICA

    -- Estadísticas reales (se actualiza automáticamente)
    veces_aparecido INTEGER DEFAULT 0,
    promedio_dias_entre_fallos DECIMAL(10,2),
    tasa_recurrencia DECIMAL(5,2),               -- % de veces que vuelve a fallar

    -- Normativa
    normativa_aplicable TEXT[],                  -- Referencias a normativas
    codigo_imc VARCHAR(20),                      -- Código de inspección

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para conocimiento_tecnico_ia
CREATE INDEX idx_conocimiento_componente ON conocimiento_tecnico_ia(componente);
CREATE INDEX idx_conocimiento_criticidad ON conocimiento_tecnico_ia(criticidad);

-- ============================================================================
-- TABLA: alertas_predictivas_ia
-- Alertas generadas por el sistema de IA (más inteligentes que las v2)
-- ============================================================================
CREATE TABLE IF NOT EXISTS alertas_predictivas_ia (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER NOT NULL REFERENCES maquinas_cartera(id) ON DELETE CASCADE,
    prediccion_id INTEGER REFERENCES predicciones_maquina(id),

    -- Tipo y severidad
    tipo_alerta VARCHAR(50) NOT NULL,            -- FALLO_INMINENTE, DETERIORO_PROGRESIVO, PATRON_ANOMALO, etc.
    nivel_urgencia VARCHAR(20) NOT NULL,         -- BAJA, MEDIA, ALTA, URGENTE, CRITICA
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,

    -- Detalles técnicos
    componente_afectado VARCHAR(100),
    probabilidad_fallo DECIMAL(5,2),
    dias_estimados_fallo INTEGER,
    impacto_estimado VARCHAR(50),                -- BAJO, MEDIO, ALTO, CRITICO

    -- Recomendaciones
    accion_recomendada TEXT,
    fecha_limite_accion DATE,
    alternativas TEXT[],                         -- Array de alternativas de acción

    -- Costes y ROI
    coste_intervencion DECIMAL(10,2),
    coste_si_no_actua DECIMAL(10,2),
    ahorro_estimado DECIMAL(10,2),

    -- Datos de detección
    partes_evidencia INTEGER[],                  -- IDs de partes que son evidencia
    datos_soporte JSONB,                         -- Datos adicionales en JSON

    -- Estado y seguimiento
    estado VARCHAR(20) DEFAULT 'ACTIVA',         -- ACTIVA, EN_REVISION, ACEPTADA, DESCARTADA, RESUELTA
    fecha_deteccion TIMESTAMP DEFAULT NOW(),
    fecha_revision TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    revisada_por_id INTEGER REFERENCES usuarios(id),

    -- Notificaciones
    notificacion_enviada BOOLEAN DEFAULT FALSE,
    fecha_notificacion TIMESTAMP,
    canal_notificacion VARCHAR(50),              -- EMAIL, SMS, PUSH, DASHBOARD

    -- Resultado
    se_cumplio_prediccion BOOLEAN,
    parte_resultado_id INTEGER REFERENCES partes_trabajo(id),
    notas_resultado TEXT,

    -- Metadatos IA
    modelo_ia_usado VARCHAR(100),
    confianza DECIMAL(5,2),
    explicacion_ia TEXT,                         -- Por qué la IA generó esta alerta

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para alertas_predictivas_ia
CREATE INDEX idx_alertas_ia_maquina ON alertas_predictivas_ia(maquina_id);
CREATE INDEX idx_alertas_ia_prediccion ON alertas_predictivas_ia(prediccion_id);
CREATE INDEX idx_alertas_ia_tipo ON alertas_predictivas_ia(tipo_alerta);
CREATE INDEX idx_alertas_ia_urgencia ON alertas_predictivas_ia(nivel_urgencia);
CREATE INDEX idx_alertas_ia_estado ON alertas_predictivas_ia(estado);
CREATE INDEX idx_alertas_ia_activas ON alertas_predictivas_ia(estado, nivel_urgencia) WHERE estado = 'ACTIVA';
CREATE INDEX idx_alertas_ia_fecha ON alertas_predictivas_ia(fecha_deteccion DESC);

-- ============================================================================
-- TABLA: metricas_precision_ia
-- Métricas para medir la precisión del sistema de IA
-- ============================================================================
CREATE TABLE IF NOT EXISTS metricas_precision_ia (
    id SERIAL PRIMARY KEY,

    -- Período de medición
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,

    -- Predicciones
    total_predicciones INTEGER DEFAULT 0,
    predicciones_confirmadas INTEGER DEFAULT 0,
    predicciones_fallidas INTEGER DEFAULT 0,
    predicciones_pendientes INTEGER DEFAULT 0,

    -- Precisión
    tasa_acierto DECIMAL(5,2),                   -- % de predicciones correctas
    tasa_falsos_positivos DECIMAL(5,2),          -- % de alertas falsas
    tasa_falsos_negativos DECIMAL(5,2),          -- % de averías no predichas

    -- Alertas
    total_alertas INTEGER DEFAULT 0,
    alertas_acertadas INTEGER DEFAULT 0,
    alertas_falsas INTEGER DEFAULT 0,

    -- Valor generado
    averias_evitadas INTEGER DEFAULT 0,
    ahorro_total_estimado DECIMAL(12,2),
    roi_sistema DECIMAL(8,2),                    -- ROI % del sistema

    -- Por componente (JSON con estadísticas detalladas)
    precision_por_componente JSONB,

    -- Tiempos
    tiempo_promedio_analisis_ms INTEGER,
    tiempo_promedio_prediccion_ms INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para metricas_precision_ia
CREATE INDEX idx_metricas_fecha ON metricas_precision_ia(fecha_inicio, fecha_fin);

-- ============================================================================
-- TABLA: aprendizaje_ia
-- Registro de aprendizaje del sistema (feedback loop)
-- ============================================================================
CREATE TABLE IF NOT EXISTS aprendizaje_ia (
    id SERIAL PRIMARY KEY,

    -- Evento que genera aprendizaje
    tipo_evento VARCHAR(50) NOT NULL,            -- PREDICCION_CONFIRMADA, PREDICCION_FALLIDA, CORRECCION_HUMANA, etc.
    maquina_id INTEGER REFERENCES maquinas_cartera(id),
    parte_id INTEGER REFERENCES partes_trabajo(id),
    prediccion_id INTEGER REFERENCES predicciones_maquina(id),
    analisis_id INTEGER REFERENCES analisis_partes_ia(id),

    -- Datos del aprendizaje
    componente VARCHAR(100),
    patron_detectado TEXT,
    resultado_real TEXT,
    diferencia TEXT,                             -- Qué fue diferente de lo esperado

    -- Ajustes sugeridos
    ajuste_sugerido TEXT,
    peso_ajuste DECIMAL(5,2),                    -- Peso del ajuste (0-1)

    -- Metadatos
    fecha_evento TIMESTAMP DEFAULT NOW(),
    aplicado_en_modelo BOOLEAN DEFAULT FALSE,
    fecha_aplicacion TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para aprendizaje_ia
CREATE INDEX idx_aprendizaje_tipo ON aprendizaje_ia(tipo_evento);
CREATE INDEX idx_aprendizaje_componente ON aprendizaje_ia(componente);
CREATE INDEX idx_aprendizaje_fecha ON aprendizaje_ia(fecha_evento DESC);
CREATE INDEX idx_aprendizaje_pendiente ON aprendizaje_ia(aplicado_en_modelo) WHERE aplicado_en_modelo = FALSE;

-- ============================================================================
-- VISTAS: Análisis y reportes
-- ============================================================================

-- Vista: Resumen de salud de máquinas con IA
CREATE OR REPLACE VIEW v_salud_maquinas_ia AS
SELECT
    m.id AS maquina_id,
    m.identificador AS maquina,
    i.nombre AS instalacion,

    -- Última predicción activa
    p.estado_salud_ia,
    p.puntuacion_salud,
    p.tendencia,
    p.componente_riesgo_1,
    p.probabilidad_fallo_1,
    p.dias_estimados_fallo_1,
    p.prioridad_intervencion,
    p.ahorro_potencial,
    p.fecha_prediccion,

    -- Alertas activas
    COUNT(DISTINCT a.id) AS alertas_activas,
    MAX(CASE WHEN a.nivel_urgencia IN ('URGENTE', 'CRITICA') THEN 1 ELSE 0 END) AS tiene_alerta_critica,

    -- Estado general
    CASE
        WHEN p.estado_salud_ia = 'CRITICA' OR MAX(CASE WHEN a.nivel_urgencia = 'CRITICA' THEN 1 ELSE 0 END) = 1 THEN 'CRITICO'
        WHEN p.estado_salud_ia = 'MALA' OR p.prioridad_intervencion = 'URGENTE' THEN 'URGENTE'
        WHEN p.estado_salud_ia = 'REGULAR' OR p.prioridad_intervencion = 'ALTA' THEN 'ATENCION'
        WHEN p.estado_salud_ia = 'BUENA' THEN 'NORMAL'
        ELSE 'EXCELENTE'
    END AS estado_general

FROM maquinas_cartera m
LEFT JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN predicciones_maquina p ON m.id = p.maquina_id AND p.estado = 'ACTIVA'
LEFT JOIN alertas_predictivas_ia a ON m.id = a.maquina_id AND a.estado = 'ACTIVA'
WHERE m.en_cartera = TRUE
GROUP BY m.id, m.identificador, i.nombre, p.estado_salud_ia, p.puntuacion_salud,
         p.tendencia, p.componente_riesgo_1, p.probabilidad_fallo_1,
         p.dias_estimados_fallo_1, p.prioridad_intervencion, p.ahorro_potencial, p.fecha_prediccion;

-- Vista: Componentes más problemáticos (análisis global)
CREATE OR REPLACE VIEW v_componentes_problematicos AS
SELECT
    componente_principal,
    COUNT(*) AS total_fallos,
    COUNT(DISTINCT parte_id) AS partes_afectados,
    COUNT(DISTINCT a.parte_id) / COUNT(DISTINCT pt.maquina_id)::DECIMAL AS fallos_por_maquina,
    AVG(probabilidad_recurrencia) AS prob_recurrencia_promedio,
    AVG(tiempo_estimado_proxima_falla) AS dias_promedio_proxima_falla,
    COUNT(*) FILTER (WHERE es_fallo_recurrente = TRUE) AS fallos_recurrentes,
    AVG(coste_estimado_correctivo) AS coste_promedio,
    SUM(coste_estimado_correctivo) AS coste_total_estimado
FROM analisis_partes_ia a
JOIN partes_trabajo pt ON a.parte_id = pt.id
WHERE componente_principal IS NOT NULL
GROUP BY componente_principal
ORDER BY total_fallos DESC;

-- Vista: ROI del sistema de IA
CREATE OR REPLACE VIEW v_roi_sistema_ia AS
SELECT
    DATE_TRUNC('month', fecha_prediccion) AS mes,
    COUNT(*) AS predicciones_generadas,
    COUNT(*) FILTER (WHERE confirmada_con_averia = TRUE) AS predicciones_acertadas,
    ROUND(COUNT(*) FILTER (WHERE confirmada_con_averia = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 2) AS tasa_acierto,
    SUM(ahorro_potencial) FILTER (WHERE estado = 'CONFIRMADA') AS ahorro_real,
    SUM(ahorro_potencial) FILTER (WHERE estado = 'ACTIVA') AS ahorro_potencial,
    AVG(confianza_prediccion) AS confianza_promedio
FROM predicciones_maquina
WHERE fecha_prediccion >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', fecha_prediccion)
ORDER BY mes DESC;

-- ============================================================================
-- TRIGGERS: Actualización automática
-- ============================================================================

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_analisis_partes_ia_updated_at BEFORE UPDATE ON analisis_partes_ia
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predicciones_maquina_updated_at BEFORE UPDATE ON predicciones_maquina
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conocimiento_tecnico_ia_updated_at BEFORE UPDATE ON conocimiento_tecnico_ia
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alertas_predictivas_ia_updated_at BEFORE UPDATE ON alertas_predictivas_ia
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- DATOS INICIALES: Base de conocimiento técnico
-- ============================================================================

INSERT INTO conocimiento_tecnico_ia (componente, descripcion, vida_util_esperada_meses, coste_promedio, coste_mano_obra_promedio, tiempo_reemplazo_horas, criticidad) VALUES
('Puerta automática', 'Sistema de apertura y cierre automático de puertas de cabina', 60, 450.00, 200.00, 3.0, 'ALTA'),
('Cerradero', 'Dispositivo de cierre mecánico de puertas', 48, 180.00, 120.00, 1.5, 'ALTA'),
('Barrera fotoeléctrica', 'Sistema de seguridad de detección de obstáculos', 72, 220.00, 150.00, 2.0, 'ALTA'),
('Reenvío de planta', 'Sistema de comunicación entre piso y control', 60, 320.00, 180.00, 2.5, 'MEDIA'),
('Comunicación bidireccional', 'Sistema de intercomunicación de emergencia', 84, 380.00, 150.00, 2.0, 'ALTA'),
('Batería auxiliar', 'Batería de respaldo para emergencias', 36, 150.00, 80.00, 1.0, 'MEDIA'),
('Cable viajero', 'Cable de conexión entre cabina y control', 72, 280.00, 200.00, 4.0, 'MEDIA'),
('Botonera cabina', 'Panel de botones de control en cabina', 96, 250.00, 120.00, 2.0, 'MEDIA'),
('Variador', 'Variador de frecuencia del motor', 120, 1200.00, 350.00, 5.0, 'CRITICA'),
('Limitador velocidad', 'Sistema de seguridad de velocidad', 120, 850.00, 300.00, 6.0, 'CRITICA'),
('Paracaídas', 'Sistema de frenado de emergencia', 120, 900.00, 400.00, 8.0, 'CRITICA'),
('Contacto de cabina', 'Interruptor de seguridad de posición', 60, 120.00, 80.00, 1.0, 'MEDIA'),
('Motor', 'Motor eléctrico de tracción', 180, 2500.00, 800.00, 12.0, 'CRITICA'),
('Cuadro de maniobra', 'Sistema de control electrónico', 120, 1800.00, 400.00, 8.0, 'CRITICA'),
('Encoder', 'Sensor de posición y velocidad', 84, 380.00, 150.00, 2.5, 'ALTA'),
('Contactor', 'Interruptor electromagnético', 48, 150.00, 100.00, 1.5, 'MEDIA'),
('Relé de seguridad', 'Sistema de supervisión de seguridad', 72, 280.00, 120.00, 2.0, 'ALTA');

-- ============================================================================
-- COMENTARIOS FINALES
-- ============================================================================

COMMENT ON TABLE analisis_partes_ia IS 'Análisis detallado de cada parte de trabajo usando IA con conocimiento técnico de ascensores';
COMMENT ON TABLE predicciones_maquina IS 'Predicciones de averías futuras y estado de salud de cada máquina';
COMMENT ON TABLE conocimiento_tecnico_ia IS 'Base de conocimiento técnico sobre componentes y patrones de fallo';
COMMENT ON TABLE alertas_predictivas_ia IS 'Alertas inteligentes generadas por el sistema de IA predictiva';
COMMENT ON TABLE metricas_precision_ia IS 'Métricas de precisión y efectividad del sistema de IA';
COMMENT ON TABLE aprendizaje_ia IS 'Registro de aprendizaje continuo del sistema (feedback loop)';

-- ============================================================================
-- FIN DEL SCHEMA
-- ============================================================================
