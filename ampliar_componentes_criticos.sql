-- ============================================
-- AMPLIAR COMPONENTES CRÍTICOS
-- Añadir componentes eléctricos y keywords faltantes
-- ============================================

-- Añadir nuevos componentes críticos
INSERT INTO componentes_criticos (nombre, familia, keywords, nivel_critico, coste_reparacion_promedio) VALUES
    -- Componentes eléctricos generales
    ('Fusibles y protecciones', 'ELECTRICA', ARRAY['fusible', 'fusibles', 'magnetotérmico', 'magnetotermico', 'diferencial', 'protección eléctrica', 'proteccion electrica'], 'MEDIO', 120.00),
    ('Cuadro eléctrico', 'ELECTRICA', ARRAY['cuadro eléctrico', 'cuadro electrico', 'armario eléctrico', 'armario electrico', 'centralita'], 'ALTO', 450.00),
    ('Placa electrónica', 'MANIOBRA', ARRAY['placa', 'tarjeta electrónica', 'tarjeta electronica', 'circuito impreso', 'pcb'], 'ALTO', 600.00),

    -- Componentes mecánicos comunes
    ('Guías y rieles', 'MECANICA', ARRAY['guía', 'guia', 'riel', 'rieles', 'deslizamiento'], 'MEDIO', 380.00),
    ('Poleas y cables', 'MECANICA', ARRAY['polea', 'poleas', 'cable de tracción', 'cable traccion'], 'ALTO', 950.00),
    ('Amortiguadores', 'MECANICA', ARRAY['amortiguador', 'amortiguadores', 'tope', 'topes'], 'MEDIO', 220.00),

    -- Componentes de maniobra
    ('Selectores de planta', 'MANIOBRA', ARRAY['selector', 'selectores', 'micro de planta'], 'MEDIO', 180.00),
    ('Encoder / Sistema de posición', 'MANIOBRA', ARRAY['encoder', 'cinta encoder', 'sistema de posición', 'sistema de posicion'], 'ALTO', 520.00)

ON CONFLICT (nombre) DO UPDATE SET
    keywords = EXCLUDED.keywords,
    coste_reparacion_promedio = EXCLUDED.coste_reparacion_promedio;

-- Ampliar keywords de componentes existentes
UPDATE componentes_criticos SET keywords = keywords || ARRAY['puerta cabina', 'cierre puerta', 'apertura puerta']
WHERE nombre = 'Puerta automática';

UPDATE componentes_criticos SET keywords = keywords || ARRAY['comunicador', 'teléfono', 'telefono', 'línea telefónica', 'linea telefonica']
WHERE nombre = 'Comunicación bidireccional';

UPDATE componentes_criticos SET keywords = keywords || ARRAY['pila', 'ups', 'sai']
WHERE nombre = 'Batería auxiliar';

UPDATE componentes_criticos SET keywords = keywords || ARRAY['inverter', 'driver']
WHERE nombre = 'Variador';

UPDATE componentes_criticos SET keywords = keywords || ARRAY['maniobra', 'cuadro de maniobra']
WHERE nombre = 'Botonera cabina';

-- Verificar resultados
SELECT
    nombre,
    familia,
    nivel_critico,
    array_length(keywords, 1) as num_keywords,
    coste_reparacion_promedio
FROM componentes_criticos
ORDER BY familia, nombre;

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✅ Componentes críticos ampliados exitosamente';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Total componentes: %', (SELECT COUNT(*) FROM componentes_criticos);
    RAISE NOTICE '';
    RAISE NOTICE '🔧 Nuevos componentes añadidos:';
    RAISE NOTICE '   - Fusibles y protecciones';
    RAISE NOTICE '   - Cuadro eléctrico';
    RAISE NOTICE '   - Placa electrónica';
    RAISE NOTICE '   - Guías y rieles';
    RAISE NOTICE '   - Poleas y cables';
    RAISE NOTICE '   - Amortiguadores';
    RAISE NOTICE '   - Selectores de planta';
    RAISE NOTICE '   - Encoder / Sistema de posición';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 SIGUIENTE PASO:';
    RAISE NOTICE '   Ejecutar detectores de nuevo: python detectores_alertas.py';
    RAISE NOTICE '   Ahora debería detectar "Fusible quemado" y otros componentes';
END
$$;
