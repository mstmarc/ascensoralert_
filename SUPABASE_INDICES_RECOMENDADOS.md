# Índices Recomendados para Supabase

Este documento contiene los índices recomendados para optimizar aún más el rendimiento de las consultas a Supabase.

## ⚠️ Importante

Los índices se crean desde el **Dashboard de Supabase** en la sección **SQL Editor**. Estos índices mejoran significativamente la velocidad de las queries, especialmente en tablas grandes.

## 📊 Impacto Estimado

Implementar estos índices puede mejorar el rendimiento en **20-50%** adicional para queries con filtros en columnas indexadas.

---

## Tabla: `equipos`

### 1. Índice en `ipo_proxima`

**Por qué**: Se hacen muchas queries filtrando por fechas de IPO (`ipo_proxima=gte.X`, `ipo_proxima=lte.X`)

```sql
CREATE INDEX idx_equipos_ipo_proxima
ON equipos(ipo_proxima)
WHERE ipo_proxima IS NOT NULL;
```

**Queries que se benefician:**
- Home: IPOs de hoy, IPOs esta semana
- Métricas: Conteo de IPOs
- Dashboard: Filtros por fechas de IPO

### 2. Índice en `cliente_id`

**Por qué**: Se usa frecuentemente para hacer JOINs con la tabla `clientes`

```sql
CREATE INDEX idx_equipos_cliente_id
ON equipos(cliente_id);
```

**Queries que se benefician:**
- Todas las queries que usan `equipos(...)` en el select
- JOINs entre equipos y clientes

### 3. Índice en `fecha_vencimiento_contrato`

**Por qué**: Se filtra frecuentemente para encontrar contratos que vencen pronto

```sql
CREATE INDEX idx_equipos_vencimiento_contrato
ON equipos(fecha_vencimiento_contrato)
WHERE fecha_vencimiento_contrato IS NOT NULL;
```

**Queries que se benefician:**
- Home: Alertas de contratos por vencer
- Dashboard: Filtros de vencimiento de contratos

### 4. Índice compuesto para queries complejas

**Por qué**: Queries que filtran por fecha y cliente simultáneamente

```sql
CREATE INDEX idx_equipos_cliente_ipo
ON equipos(cliente_id, ipo_proxima);
```

---

## Tabla: `clientes`

### 1. Índice en `localidad`

**Por qué**: Se usa frecuentemente en filtros del dashboard

```sql
CREATE INDEX idx_clientes_localidad
ON clientes(localidad);
```

**Queries que se benefician:**
- Dashboard de leads: Filtro por localidad
- Caché de filtros

### 2. Índice en `empresa_mantenedora`

**Por qué**: Se usa frecuentemente en filtros del dashboard

```sql
CREATE INDEX idx_clientes_empresa_mantenedora
ON clientes(empresa_mantenedora);
```

**Queries que se benefician:**
- Dashboard de leads: Filtro por empresa
- Caché de filtros

### 3. Índice en `fecha_visita`

**Por qué**: Se ordena por esta columna para obtener últimas instalaciones

```sql
CREATE INDEX idx_clientes_fecha_visita
ON clientes(fecha_visita DESC NULLS LAST);
```

**Queries que se benefician:**
- Home: Últimas instalaciones
- Caché de últimas instalaciones

### 4. Índice en `administrador_id`

**Por qué**: Se usa para filtrar clientes por administrador

```sql
CREATE INDEX idx_clientes_administrador_id
ON clientes(administrador_id);
```

**Queries que se benefician:**
- Dashboard de administradores
- Queries de clientes por administrador

---

## Tabla: `oportunidades`

### 1. Índice en `estado`

**Por qué**: Se filtra frecuentemente por estado='activa'

```sql
CREATE INDEX idx_oportunidades_estado
ON oportunidades(estado);
```

**Queries que se benefician:**
- Home: Oportunidades pendientes
- Métricas: Conteo de oportunidades activas

### 2. Índice en `cliente_id`

**Por qué**: Se usa para JOINs con clientes

```sql
CREATE INDEX idx_oportunidades_cliente_id
ON oportunidades(cliente_id);
```

**Queries que se benefician:**
- Queries con joins a clientes
- Listados de oportunidades por cliente

### 3. Índice en `fecha_creacion`

**Por qué**: Se ordena por esta columna para obtener últimas oportunidades

```sql
CREATE INDEX idx_oportunidades_fecha_creacion
ON oportunidades(fecha_creacion DESC);
```

**Queries que se benefician:**
- Home: Últimas oportunidades
- Caché de últimas oportunidades

---

## Tabla: `visitas_administradores`

### 1. Índice en `fecha_visita`

**Por qué**: Se ordena por esta columna frecuentemente

```sql
CREATE INDEX idx_visitas_admin_fecha
ON visitas_administradores(fecha_visita DESC);
```

**Queries que se benefician:**
- Dashboard de visitas: Ordenamiento por fecha

### 2. Índice en `administrador_id`

**Por qué**: Se filtra por administrador

```sql
CREATE INDEX idx_visitas_admin_administrador_id
ON visitas_administradores(administrador_id);
```

**Queries que se benefician:**
- Queries de visitas por administrador

---

## Tabla: `visitas_seguimiento`

### 1. Índice en `cliente_id`

**Por qué**: Se usa para obtener visitas de un cliente específico

```sql
CREATE INDEX idx_visitas_seguimiento_cliente_id
ON visitas_seguimiento(cliente_id);
```

**Queries que se benefician:**
- Ver detalles de lead: Historial de visitas

### 2. Índice en `oportunidad_id`

**Por qué**: Se usa para obtener visitas de una oportunidad específica

```sql
CREATE INDEX idx_visitas_seguimiento_oportunidad_id
ON visitas_seguimiento(oportunidad_id);
```

**Queries que se benefician:**
- Ver detalles de oportunidad: Historial de visitas

### 3. Índice en `fecha_visita`

**Por qué**: Se ordena por esta columna

```sql
CREATE INDEX idx_visitas_seguimiento_fecha
ON visitas_seguimiento(fecha_visita DESC);
```

**Queries que se benefician:**
- Listados ordenados por fecha de visita
- Filtros por rango de fechas

---

## 📝 Cómo Crear los Índices

### Opción 1: Desde Supabase Dashboard (Recomendado)

1. Abre tu proyecto en [https://app.supabase.com](https://app.supabase.com)
2. Ve a **SQL Editor** en el menú lateral
3. Crea un nuevo query
4. Copia y pega los comandos SQL de arriba
5. Haz clic en **Run** para ejecutar

### Opción 2: Todos los Índices de una Vez

Puedes crear un script SQL con todos los índices y ejecutarlo de una vez:

```sql
-- EQUIPOS
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_equipos_ipo_proxima
ON equipos(ipo_proxima) WHERE ipo_proxima IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_equipos_cliente_id
ON equipos(cliente_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_equipos_vencimiento_contrato
ON equipos(fecha_vencimiento_contrato) WHERE fecha_vencimiento_contrato IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_equipos_cliente_ipo
ON equipos(cliente_id, ipo_proxima);

-- CLIENTES
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clientes_localidad
ON clientes(localidad);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clientes_empresa_mantenedora
ON clientes(empresa_mantenedora);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clientes_fecha_visita
ON clientes(fecha_visita DESC NULLS LAST);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clientes_administrador_id
ON clientes(administrador_id);

-- OPORTUNIDADES
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_oportunidades_estado
ON oportunidades(estado);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_oportunidades_cliente_id
ON oportunidades(cliente_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_oportunidades_fecha_creacion
ON oportunidades(fecha_creacion DESC);

-- VISITAS ADMINISTRADORES
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visitas_admin_fecha
ON visitas_administradores(fecha_visita DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visitas_admin_administrador_id
ON visitas_administradores(administrador_id);

-- VISITAS SEGUIMIENTO
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visitas_seguimiento_cliente_id
ON visitas_seguimiento(cliente_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visitas_seguimiento_oportunidad_id
ON visitas_seguimiento(oportunidad_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_visitas_seguimiento_fecha
ON visitas_seguimiento(fecha_visita DESC);
```

**Nota**: Usar `CONCURRENTLY` evita bloquear las tablas durante la creación del índice, permitiendo que la aplicación siga funcionando normalmente.

---

## 🔍 Verificar Índices Existentes

Para ver qué índices ya existen en tu base de datos:

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

---

## 📈 Monitorear Uso de Índices

Después de crear los índices, puedes ver si se están usando:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

Un `idx_scan` alto significa que el índice se está usando frecuentemente (bueno).
Un `idx_scan` bajo o 0 significa que el índice no se usa (considerar eliminarlo).

---

## ⚠️ Consideraciones Importantes

1. **Espacio en disco**: Los índices ocupan espacio adicional. Supabase tier gratuito tiene límite de 500MB.

2. **Impacto en writes**: Los índices hacen los INSERT/UPDATE ligeramente más lentos (generalmente imperceptible).

3. **Priorización**: Si tienes límite de espacio, implementa primero:
   - `idx_equipos_ipo_proxima`
   - `idx_equipos_cliente_id`
   - `idx_clientes_localidad`
   - `idx_oportunidades_estado`

4. **Mantenimiento**: Los índices se mantienen automáticamente, no requieren mantenimiento manual.

---

## 📊 Beneficios Esperados

Con todos los índices implementados:

- **Queries de home**: 30-50% más rápidas
- **Dashboard de leads con filtros**: 40-60% más rápidas
- **JOINs entre tablas**: 50-70% más rápidas
- **Queries de count**: 20-40% más rápidas

---

## 🎯 Resumen de Prioridades

### Alta Prioridad (Implementar primero)
1. `idx_equipos_ipo_proxima` - Muy usado en home y métricas
2. `idx_equipos_cliente_id` - Crítico para JOINs
3. `idx_clientes_localidad` - Usado en filtros frecuentes
4. `idx_oportunidades_estado` - Usado en métricas

### Media Prioridad
5. `idx_clientes_fecha_visita` - Usado en últimas instalaciones
6. `idx_equipos_vencimiento_contrato` - Usado en alertas
7. `idx_oportunidades_fecha_creacion` - Usado en últimas oportunidades

### Baja Prioridad (Implementar si tienes espacio)
8. Índices compuestos
9. Índices de visitas
10. Índices de administradores

---

**Creado**: 2025-10-27
**Optimizaciones anteriores**: N+1 elimination, Caché multi-nivel, Selección específica de campos
