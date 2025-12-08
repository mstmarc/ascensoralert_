-- ============================================================================
-- RLS POLICIES: Sistema de Análisis Predictivo con IA
-- ============================================================================
-- Descripción: Políticas de seguridad para permitir acceso a las tablas de IA
-- Fecha: 2025-12-08
-- ============================================================================

-- ============================================================================
-- TABLA: analisis_partes_ia
-- ============================================================================

-- Habilitar RLS (si no está ya habilitado)
ALTER TABLE analisis_partes_ia ENABLE ROW LEVEL SECURITY;

-- Política: Permitir SELECT a todos los usuarios autenticados
CREATE POLICY "analisis_partes_ia_select_policy"
ON analisis_partes_ia
FOR SELECT
USING (true);

-- Política: Permitir INSERT a todos los usuarios autenticados
CREATE POLICY "analisis_partes_ia_insert_policy"
ON analisis_partes_ia
FOR INSERT
WITH CHECK (true);

-- Política: Permitir UPDATE a todos los usuarios autenticados
CREATE POLICY "analisis_partes_ia_update_policy"
ON analisis_partes_ia
FOR UPDATE
USING (true)
WITH CHECK (true);

-- Política: Permitir DELETE a todos los usuarios autenticados
CREATE POLICY "analisis_partes_ia_delete_policy"
ON analisis_partes_ia
FOR DELETE
USING (true);

-- ============================================================================
-- TABLA: predicciones_maquina
-- ============================================================================

ALTER TABLE predicciones_maquina ENABLE ROW LEVEL SECURITY;

CREATE POLICY "predicciones_maquina_select_policy"
ON predicciones_maquina
FOR SELECT
USING (true);

CREATE POLICY "predicciones_maquina_insert_policy"
ON predicciones_maquina
FOR INSERT
WITH CHECK (true);

CREATE POLICY "predicciones_maquina_update_policy"
ON predicciones_maquina
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "predicciones_maquina_delete_policy"
ON predicciones_maquina
FOR DELETE
USING (true);

-- ============================================================================
-- TABLA: alertas_predictivas_ia
-- ============================================================================

ALTER TABLE alertas_predictivas_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alertas_predictivas_ia_select_policy"
ON alertas_predictivas_ia
FOR SELECT
USING (true);

CREATE POLICY "alertas_predictivas_ia_insert_policy"
ON alertas_predictivas_ia
FOR INSERT
WITH CHECK (true);

CREATE POLICY "alertas_predictivas_ia_update_policy"
ON alertas_predictivas_ia
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "alertas_predictivas_ia_delete_policy"
ON alertas_predictivas_ia
FOR DELETE
USING (true);

-- ============================================================================
-- TABLA: conocimiento_tecnico_ia
-- ============================================================================

ALTER TABLE conocimiento_tecnico_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "conocimiento_tecnico_ia_select_policy"
ON conocimiento_tecnico_ia
FOR SELECT
USING (true);

CREATE POLICY "conocimiento_tecnico_ia_insert_policy"
ON conocimiento_tecnico_ia
FOR INSERT
WITH CHECK (true);

CREATE POLICY "conocimiento_tecnico_ia_update_policy"
ON conocimiento_tecnico_ia
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "conocimiento_tecnico_ia_delete_policy"
ON conocimiento_tecnico_ia
FOR DELETE
USING (true);

-- ============================================================================
-- TABLA: metricas_precision_ia
-- ============================================================================

ALTER TABLE metricas_precision_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "metricas_precision_ia_select_policy"
ON metricas_precision_ia
FOR SELECT
USING (true);

CREATE POLICY "metricas_precision_ia_insert_policy"
ON metricas_precision_ia
FOR INSERT
WITH CHECK (true);

CREATE POLICY "metricas_precision_ia_update_policy"
ON metricas_precision_ia
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "metricas_precision_ia_delete_policy"
ON metricas_precision_ia
FOR DELETE
USING (true);

-- ============================================================================
-- TABLA: aprendizaje_ia
-- ============================================================================

ALTER TABLE aprendizaje_ia ENABLE ROW LEVEL SECURITY;

CREATE POLICY "aprendizaje_ia_select_policy"
ON aprendizaje_ia
FOR SELECT
USING (true);

CREATE POLICY "aprendizaje_ia_insert_policy"
ON aprendizaje_ia
FOR INSERT
WITH CHECK (true);

CREATE POLICY "aprendizaje_ia_update_policy"
ON aprendizaje_ia
FOR UPDATE
USING (true)
WITH CHECK (true);

CREATE POLICY "aprendizaje_ia_delete_policy"
ON aprendizaje_ia
FOR DELETE
USING (true);

-- ============================================================================
-- NOTA IMPORTANTE
-- ============================================================================
-- Estas políticas permiten acceso completo (CRUD) a todos los usuarios
-- autenticados. En producción, podrías querer restringir:
-- - UPDATE/DELETE solo a usuarios con rol específico
-- - SELECT solo a datos del mismo tenant/empresa
--
-- Para mayor seguridad, reemplaza "true" con condiciones como:
-- - auth.uid() IS NOT NULL  (solo usuarios autenticados)
-- - auth.jwt() ->> 'role' = 'admin'  (solo admins)
-- ============================================================================
