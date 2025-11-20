-- ============================================
-- IMPORTACIÓN: Datos iniciales de inspecciones
-- Fecha: 2025-11-20
-- Descripción: Importa los primeros registros de inspecciones
-- ============================================

BEGIN;

-- 1. Asegurar que existen las OCAs necesarias (si no existen, crearlas)
INSERT INTO ocas (nombre, activo) VALUES ('9-OCA GLOBAL', true) ON CONFLICT DO NOTHING;
INSERT INTO ocas (nombre, activo) VALUES ('7-EUROCONTROL', true) ON CONFLICT DO NOTHING;
INSERT INTO ocas (nombre, activo) VALUES ('4-ABC INSPECCION', true) ON CONFLICT DO NOTHING;
INSERT INTO ocas (nombre, activo) VALUES ('12-ABACO', true) ON CONFLICT DO NOTHING;
INSERT INTO ocas (nombre, activo) VALUES ('6-APPLUS', true) ON CONFLICT DO NOTHING;

-- 2. Insertar inspecciones
-- Nota: Se usa una subconsulta para obtener el oca_id a partir del nombre

INSERT INTO inspecciones (maquina, fecha_inspeccion, presupuesto, estado, estado_material, oca_id, created_by) VALUES
('ANTONIO ALMEIDA CASTELLANO', '2024-05-08', 'ACEPTADO', 'EN PROCESO', 'PEDIDO A TENERIFE', (SELECT id FROM ocas WHERE nombre = '9-OCA GLOBAL'), 'admin'),
('CIRCULO MERCANTIL', '2024-12-04', 'ACEPTADO', 'FALTAN CORTINAS', NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('VILLAS DE AMADORES 1. RECEPCION', '2024-12-05', 'PENDIENTE', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '4-ABC INSPECCION'), 'admin'),
('VILLAS DE AMADORES 2. CENTRAL', '2024-12-05', 'ACEPTADO', 'FALTA CAMBIO CABLES Y CORTINAS', NULL, (SELECT id FROM ocas WHERE nombre = '4-ABC INSPECCION'), 'admin'),
('VILLAS DE AMADORES 3. PISCINA', '2024-12-05', 'PENDIENTE', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '4-ABC INSPECCION'), 'admin'),
('UNIFAMILIAR ARCHIAUTO EL SEBADAL', '2025-02-03', 'ENVIADO', 'PENDIENTE SUBSANAR LLAMADA SIN CORRIENTE', NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('ALCORAC, 17 - CENFOC', '2025-03-03', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('ARCHIAUTO ARINAGA', '2025-03-28', 'ACEPTADO', 'PENDIENTE SUBSANAR BOTONERA', NULL, (SELECT id FROM ocas WHERE nombre = '9-OCA GLOBAL'), 'admin'),
('LA NAVAL 159', '2024-04-02', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '4-ABC INSPECCION'), 'admin'),
('LA CORNISA II.PORTAL 6.ASC. IZDO.', '2025-05-07', 'ACEPTADO', 'FINAL CARRERA IZQ, SAI, MIRILLA DER', NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('LA CORNISA II.PORTAL 6. ASC. DEREC', '2025-05-07', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('LEON Y CASTILLO 321', '2025-05-07', 'ACEPTADO', 'PENIDENTE MEDIR CABLES', NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('INVERSIONES JINAMAR 2003, S.L.', '2025-05-29', 'ACEPTADO', 'PENDIENTE CERRADURA SALA MAQUINAS', NULL, (SELECT id FROM ocas WHERE nombre = '12-ABACO'), 'admin'),
('IVAN LEON QUEVEDO', '2025-07-10', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '9-OCA GLOBAL'), 'admin'),
('LA BLANCA (C/TAJASTE 4)', '2025-07-18', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '12-ABACO'), 'admin'),
('LA BLANCA (C/ PANCHO GUERRA 14)', '2025-07-18', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '12-ABACO'), 'admin'),
('C.P. EDIF. GAROE', '2025-07-22', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('EUROCENTER. IZQUIERDO', '2025-08-18', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '6-APPLUS'), 'admin'),
('ARCA. DERECHO', '2025-09-23', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('ARCA. IZQUIERDO', '2025-09-23', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('ANGEL GUERRA 24', '2025-09-23', 'EN_PREPARACION', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('PARQUE ATLANTICO I-DCHO', '2025-09-23', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('PARQUE ATLANTICO I-IZQ', '2025-09-23', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('EUROCENTER. DER.-ESPEJO', '2025-10-20', 'ACEPTADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '6-APPLUS'), 'admin'),
('LA VIRGEN', '2025-10-30', 'ENVIADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin'),
('CHOPIN 60', '2025-10-30', 'ENVIADO', NULL, NULL, (SELECT id FROM ocas WHERE nombre = '7-EUROCONTROL'), 'admin');

COMMIT;

-- ============================================
-- FIN DE LA IMPORTACIÓN
-- ============================================

-- Para verificar los datos importados:
-- SELECT maquina, fecha_inspeccion, presupuesto, estado, estado_material, o.nombre as oca
-- FROM inspecciones i
-- LEFT JOIN ocas o ON i.oca_id = o.id
-- ORDER BY fecha_inspeccion DESC;
