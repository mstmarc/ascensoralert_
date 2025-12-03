# Migración 006: Corrección de Seguridad - RLS y Vistas

**Fecha:** 2025-12-03
**Archivo:** `database/migrations/006_fix_security_rls_and_views.sql`

## 📋 Resumen

Esta migración soluciona los problemas de seguridad detectados por el **Supabase Database Linter**:

- ✅ **9 vistas** con `SECURITY DEFINER` → Recreadas sin este atributo
- ✅ **31 tablas** sin RLS habilitado → RLS habilitado con políticas permisivas
- ✅ Políticas RLS creadas para usuarios autenticados

## 🔍 Problemas Detectados

### 1. Security Definer en Vistas (ERROR)

Las siguientes vistas tenían la propiedad `SECURITY DEFINER`, lo que significa que se ejecutan con los permisos del creador en lugar del usuario que las consulta:

1. `v_perdidas_por_pendientes`
2. `v_riesgo_instalaciones`
3. `v_estado_maquinas_semaforico`
4. `v_resumen_partes_maquina`
5. `v_defectos_con_urgencia`
6. `v_maquinas_problematicas`
7. `v_partes_con_recomendaciones`
8. `v_materiales_con_urgencia`
9. `v_inspecciones_completas`

**Problema:** Esto bypasea el sistema de RLS y puede causar vulnerabilidades de seguridad.

### 2. RLS Deshabilitado en Tablas Públicas (ERROR)

31 tablas en el schema `public` no tenían RLS habilitado, incluyendo:

**Tablas principales:**
- `instalaciones`
- `inspecciones`
- `partes_trabajo`
- `maquinas_cartera`
- `alertas_automaticas`
- `componentes_criticos`
- `pendientes_tecnicos`
- `oportunidades_facturacion`
- `defectos_inspeccion`
- `ocas`
- Y más...

**Tablas de backup/temporales:**
- `administradores_backup_*`
- `clientes_tmp`
- `clientes_backup`

## 🔧 Soluciones Implementadas

### Parte 1: Vistas Sin SECURITY DEFINER

Todas las vistas fueron recreadas **sin** la propiedad `SECURITY DEFINER`:

```sql
CREATE VIEW nombre_vista AS
SELECT ...
```

En lugar de:

```sql
CREATE VIEW nombre_vista
WITH (security_invoker=off) AS  -- ❌ Inseguro
SELECT ...
```

### Parte 2: RLS Habilitado

RLS habilitado en todas las 31 tablas:

```sql
ALTER TABLE nombre_tabla ENABLE ROW LEVEL SECURITY;
```

### Parte 3: Políticas RLS Permisivas

Se crearon políticas permisivas iniciales para **usuarios autenticados**:

**Para tablas principales:**
```sql
CREATE POLICY "Permitir acceso completo a [tabla]"
ON [tabla] FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);
```

**Para tablas de backup (solo lectura):**
```sql
CREATE POLICY "Permitir solo lectura a [tabla_backup]"
ON [tabla_backup] FOR SELECT
TO authenticated
USING (true);
```

**Para tablas de configuración (lectura + escritura limitada):**
```sql
-- Lectura para todos
CREATE POLICY "Permitir lectura a [tabla_config]"
ON [tabla_config] FOR SELECT
TO authenticated
USING (true);

-- Escritura permitida (ajustar según necesidad)
CREATE POLICY "Permitir escritura a [tabla_config]"
ON [tabla_config] FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);
```

## 📦 Cómo Aplicar la Migración

### Opción 1: Desde Supabase Dashboard

1. Accede a tu proyecto en [Supabase](https://app.supabase.com)
2. Ve a **SQL Editor**
3. Copia y pega el contenido de `database/migrations/006_fix_security_rls_and_views.sql`
4. Ejecuta el script

### Opción 2: Desde línea de comandos (si tienes acceso directo a PostgreSQL)

```bash
psql -U postgres -d ascensoralert -f database/migrations/006_fix_security_rls_and_views.sql
```

### Opción 3: Con Supabase CLI (recomendado)

Si tienes configurado el Supabase CLI:

```bash
supabase db push
```

## ✅ Verificación

Después de aplicar la migración, verifica que se solucionaron los problemas:

### 1. Verificar que las vistas NO tienen SECURITY DEFINER

```sql
SELECT
    schemaname,
    viewname,
    viewowner
FROM pg_views
WHERE schemaname = 'public'
AND viewname LIKE 'v_%';
```

### 2. Verificar que RLS está habilitado

```sql
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

Debería mostrar `rowsecurity = true` para todas las tablas.

### 3. Verificar políticas RLS creadas

```sql
SELECT
    tablename,
    policyname,
    cmd,
    roles
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

### 4. Ejecutar el Linter de Supabase nuevamente

En el Dashboard de Supabase:
1. Ve a **Database** > **Linter**
2. Ejecuta el linter
3. Verifica que los errores `security_definer_view` y `rls_disabled_in_public` desaparecieron

## ⚠️ Advertencias y Recomendaciones

### 🔴 IMPORTANTE: Políticas Permisivas

Las políticas RLS creadas son **muy permisivas** (permiten acceso completo a usuarios autenticados). Esto se hizo para **no romper la funcionalidad existente**.

**Se recomienda encarecidamente:**

1. **Revisar y ajustar las políticas según tu modelo de seguridad**
2. **Implementar políticas basadas en roles** (admin, gestor, visualizador)
3. **Restringir operaciones según el perfil de usuario**

### Ejemplo de Política Más Restrictiva

En lugar de:

```sql
-- ❌ Muy permisivo
CREATE POLICY "Permitir acceso completo"
ON instalaciones FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);
```

Considera algo como:

```sql
-- ✅ Más restrictivo basado en roles
-- Solo lectura para visualizadores
CREATE POLICY "Visualizadores pueden leer"
ON instalaciones FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM usuarios
        WHERE auth.uid() = id
        AND perfil IN ('visualizador', 'gestor', 'admin')
    )
);

-- Escritura solo para admin y gestor
CREATE POLICY "Gestores pueden escribir"
ON instalaciones FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM usuarios
        WHERE auth.uid() = id
        AND perfil IN ('gestor', 'admin')
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM usuarios
        WHERE auth.uid() = id
        AND perfil IN ('gestor', 'admin')
    )
);
```

### 🗂️ Tablas de Backup

Las tablas de backup/temporales deberían **moverse a un schema privado**:

```sql
-- Crear schema privado
CREATE SCHEMA IF NOT EXISTS backup;

-- Mover tablas
ALTER TABLE administradores_backup_20251028 SET SCHEMA backup;
ALTER TABLE administradores_backup_charset SET SCHEMA backup;
ALTER TABLE administradores_tmp SET SCHEMA backup;
ALTER TABLE clientes_tmp SET SCHEMA backup;
ALTER TABLE clientes_backup SET SCHEMA backup;
ALTER TABLE administradores_backup_final SET SCHEMA backup;

-- Revocar acceso público al schema backup
REVOKE ALL ON SCHEMA backup FROM public;
GRANT USAGE ON SCHEMA backup TO postgres;
```

## 🎯 Próximos Pasos

1. ✅ Aplicar esta migración
2. ⚠️ **Revisar políticas RLS** y ajustarlas según tu modelo de seguridad
3. 🗂️ Mover tablas de backup a schema privado
4. 🔐 Implementar políticas basadas en roles (usuarios.perfil)
5. 🧪 Probar exhaustivamente las funcionalidades existentes
6. 📊 Ejecutar el linter de Supabase para verificar mejoras

## 📚 Referencias

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase Database Linter](https://supabase.com/docs/guides/database/database-linter)

## 📝 Registro de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-12-03 | 006 | Corrección inicial de seguridad RLS y vistas |
