# Migración 013: Agregar campo fecha_segunda_realizada

## ¿Qué hace esta migración?

Agrega el campo `fecha_segunda_realizada` a la tabla `inspecciones` para registrar cuándo se realizó la segunda inspección (revisión a los 6 meses).

## ¿Por qué es necesaria?

Sin este campo, la aplicación no puede marcar las segundas inspecciones como realizadas, y se muestra el error:

```
Error al marcar segunda inspección: Could not find the 'fecha_segunda_realizada' column
```

## Cambios que incluye

1. **Nueva columna**: `fecha_segunda_realizada` (tipo DATE, nullable)
2. **Índice**: Para optimizar búsquedas por esta fecha
3. **Vista actualizada**: `v_inspecciones_completas` con lógica de estados mejorada:
   - `REALIZADA`: Segunda inspección completada
   - `ESPERANDO_MATERIALES`: Segunda inspección realizada pero hay materiales pendientes
   - `SEGUNDA_VENCIDA`: Segunda inspección pasó la fecha y no se ha realizado
   - `SEGUNDA_PENDIENTE`: Segunda inspección programada pero no realizada
   - `CERRADA`: Todo completado
   - `ABIERTA`: Estado inicial

---

## 🚀 CÓMO APLICAR LA MIGRACIÓN

### Opción 1: Desde Supabase Dashboard (RECOMENDADO ✓)

1. Ve al **Supabase Dashboard**: https://supabase.com/dashboard
2. Selecciona tu proyecto **hvkifqguxsgegzaxwcmj**
3. Ve a **SQL Editor** en el menú lateral izquierdo
4. Haz clic en **+ New query**
5. Copia y pega el contenido completo del archivo `013_add_fecha_segunda_realizada.sql`
6. Haz clic en **RUN** (o presiona `Ctrl+Enter`)
7. Verifica que aparezca "Success. No rows returned"

### Opción 2: Desde línea de comandos con Python

Si tienes acceso al servidor y las credenciales configuradas:

```bash
# 1. Instalar dependencia (si no está instalada)
pip install psycopg2-binary

# 2. Configurar password de Supabase
export SUPABASE_DB_PASSWORD='tu_password_de_postgres'

# 3. Aplicar migración
python3 database/aplicar_migracion.py database/migrations/013_add_fecha_segunda_realizada.sql
```

El password se encuentra en: **Supabase Dashboard → Settings → Database → Connection String**

### Opción 3: Con psql directo

```bash
psql postgresql://postgres:[TU_PASSWORD]@hvkifqguxsgegzaxwcmj.supabase.co:5432/postgres \
  -f database/migrations/013_add_fecha_segunda_realizada.sql
```

---

## ✅ VERIFICAR QUE SE APLICÓ CORRECTAMENTE

Ejecuta esta consulta en el SQL Editor de Supabase:

```sql
-- Verificar que la columna existe
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'inspecciones'
  AND column_name = 'fecha_segunda_realizada';
```

**Resultado esperado:**
```
column_name               | data_type | is_nullable
--------------------------|-----------|-------------
fecha_segunda_realizada   | date      | YES
```

También puedes verificar la vista:

```sql
-- Ver estructura de la vista actualizada
SELECT * FROM v_inspecciones_completas LIMIT 1;
```

---

## 🧪 PROBAR LA FUNCIONALIDAD

Después de aplicar la migración:

1. Recarga la aplicación Flask (si está corriendo, reinicia con `Ctrl+C` y `flask run`)
2. Ve a cualquier inspección que tenga segunda inspección programada
3. Haz clic en el selector **"Marcar como realizada..."**
4. Selecciona **"Marcar 2ª inspección como REALIZADA"**
5. Confirma la acción

**Resultado esperado:**
- ✅ Mensaje: "Segunda inspección marcada como realizada"
- ✅ El estado de la inspección se actualiza a "REALIZADA"
- ✅ La fecha de hoy se registra en `fecha_segunda_realizada`

---

## 🔄 ROLLBACK (Deshacer cambios)

Si necesitas revertir esta migración:

```sql
BEGIN;

-- Eliminar índice
DROP INDEX IF EXISTS idx_inspecciones_fecha_segunda_realizada;

-- Eliminar columna
ALTER TABLE inspecciones
DROP COLUMN IF EXISTS fecha_segunda_realizada;

-- Recrear vista sin el campo (usa el SQL de la migración anterior)

COMMIT;
```

---

## 📋 NOTAS IMPORTANTES

- Esta migración usa `ADD COLUMN IF NOT EXISTS`, por lo que es **idempotente** (se puede ejecutar múltiples veces sin problemas)
- La columna es **nullable**, por lo que no afecta inspecciones existentes
- La vista `v_inspecciones_completas` se recrea completamente
- No hay pérdida de datos en esta migración

---

## 🐛 TROUBLESHOOTING

### Error: "relation v_inspecciones_completas does not exist"

La vista no existía previamente. Esto es normal, la migración la creará.

### Error: "column already exists"

La columna ya existe. Puedes ignorar este error o verificar con:

```sql
SELECT * FROM inspecciones LIMIT 1;
```

### Error: "permission denied"

Asegúrate de estar usando credenciales con permisos de admin (usuario `postgres`).

---

## 📝 HISTORIAL

- **2026-01-12**: Migración creada para resolver issue #PvjH3
- **Problema resuelto**: Error al marcar segunda inspección como realizada
- **Archivo origen**: `database/agregar_fecha_segunda_realizada.sql`
