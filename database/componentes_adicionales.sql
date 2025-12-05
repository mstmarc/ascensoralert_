-- ============================================================================
-- COMPONENTES ADICIONALES (OPCIONAL)
-- ============================================================================
-- Agrega estos componentes adicionales si quieres pre-cargarlos
-- El sistema los descubrirá automáticamente de todas formas

INSERT INTO conocimiento_tecnico_ia (componente, descripcion, vida_util_esperada_meses, coste_promedio, coste_mano_obra_promedio, tiempo_reemplazo_horas, criticidad) VALUES

-- Componentes Mecánicos
('Cables de tracción', 'Cables que soportan y mueven la cabina', 120, 800.00, 500.00, 10.0, 'CRITICA'),
('Guías de cabina', 'Guías metálicas para desplazamiento vertical', 240, 1500.00, 800.00, 16.0, 'ALTA'),
('Amortiguadores', 'Amortiguadores de foso para frenado', 60, 180.00, 100.00, 2.0, 'MEDIA'),
('Polea tractora', 'Polea principal de tracción', 180, 1200.00, 400.00, 8.0, 'CRITICA'),
('Tensor de cables', 'Sistema de tensado de cables', 84, 220.00, 120.00, 3.0, 'MEDIA'),

-- Componentes Hidráulicos (si aplica)
('Pistón hidráulico', 'Cilindro hidráulico de elevación', 180, 3500.00, 1200.00, 20.0, 'CRITICA'),
('Válvula de seguridad', 'Válvula de control de presión', 96, 350.00, 150.00, 3.0, 'ALTA'),
('Bomba hidráulica', 'Bomba del sistema hidráulico', 120, 1800.00, 400.00, 8.0, 'CRITICA'),

-- Componentes Eléctricos
('Selector de planta', 'Sistema de selección de nivel', 96, 420.00, 180.00, 4.0, 'ALTA'),
('Final de carrera', 'Interruptor de límite de recorrido', 60, 80.00, 60.00, 1.0, 'ALTA'),
('Transformador', 'Transformador de potencia', 180, 650.00, 200.00, 4.0, 'MEDIA'),
('Fuente de alimentación', 'Fuente de alimentación del cuadro', 84, 280.00, 100.00, 2.0, 'MEDIA'),

-- Componentes de Seguridad
('Detector de sobrecarga', 'Sistema de detección de peso', 72, 320.00, 120.00, 2.5, 'ALTA'),
('Freno electromagnético', 'Freno de seguridad del motor', 96, 580.00, 250.00, 5.0, 'CRITICA'),
('Cerradura electrónica', 'Sistema de bloqueo de puertas', 60, 150.00, 80.00, 1.5, 'ALTA'),

-- Componentes de Confort
('Iluminación cabina', 'Sistema de iluminación interior', 48, 120.00, 60.00, 1.0, 'BAJA'),
('Ventilador cabina', 'Sistema de ventilación', 60, 180.00, 80.00, 1.5, 'BAJA'),
('Display digital', 'Indicador de planta digital', 72, 220.00, 100.00, 2.0, 'MEDIA'),

-- Componentes Electrónicos
('Tarjeta electrónica', 'Circuito de control electrónico', 84, 450.00, 150.00, 2.0, 'ALTA'),
('Sensor de posición', 'Sensor de ubicación de cabina', 96, 280.00, 120.00, 2.0, 'MEDIA'),
('Módulo de comunicación', 'Sistema de comunicación de control', 60, 350.00, 120.00, 2.0, 'MEDIA')

ON CONFLICT (componente) DO NOTHING;
