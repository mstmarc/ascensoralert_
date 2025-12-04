# Aplicar Migración 006: Campos de Baja en Instalaciones

Esta migración agrega funcionalidad para gestionar instalaciones dadas de baja en el sistema de cartera.

## ¿Qué agrega esta migración?

Agrega los siguientes campos a la tabla `instalaciones`:
- `en_cartera` (BOOLEAN): Indica si la instalación está activa (TRUE) o dada de baja (FALSE)
- `fecha_salida_cartera` (DATE): Fecha en que la instalación salió de cartera
- `motivo_salida` (TEXT): Razón de la baja (cambio de empresa, fin de contrato, etc.)

## Cómo aplicar la migración

### Opción 1: Desde Supabase Dashboard (Recomendado)

1. Ve al **Supabase Dashboard**: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **SQL Editor** en el menú lateral
4. Haz clic en **New query**
5. Copia y pega el contenido del archivo `006_add_instalacion_baja_fields.sql`
6. Haz clic en **Run** o presiona `Ctrl+Enter`

### Opción 2: Desde línea de comandos (requiere psycopg2)

Si tienes `psycopg2-binary` instalado y la variable de entorno `SUPABASE_DB_PASSWORD` configurada:

```bash
# Instalar dependencia si es necesario
pip install psycopg2-binary

# Configurar password de Supabase
export SUPABASE_DB_PASSWORD='tu_password_aqui'

# Aplicar migración
python3 database/aplicar_migracion.py database/migrations/006_add_instalacion_baja_fields.sql
```

### Opción 3: Usando psql

```bash
psql postgresql://postgres:[PASSWORD]@hvkifqguxsgegzaxwcmj.supabase.co:5432/postgres < database/migrations/006_add_instalacion_baja_fields.sql
```

## Verificar que se aplicó correctamente

Ejecuta esta consulta en SQL Editor:

```sql
-- Verificar que los campos existen
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'instalaciones'
  AND column_name IN ('en_cartera', 'fecha_salida_cartera', 'motivo_salida');
```

Deberías ver 3 filas con los nuevos campos.

## Funcionalidad agregada

Una vez aplicada la migración, el sistema permitirá:

1. **Dar de baja instalaciones**: Desde el perfil de instalación (`/cartera/instalacion/<id>`), se puede hacer clic en el botón "Dar de Baja" para marcar la instalación como fuera de cartera
2. **Registrar motivo y fecha**: Al dar de baja, se debe especificar la fecha y el motivo
3. **Baja automática de máquinas**: Cuando se da de baja una instalación, todas sus máquinas también se marcan como fuera de cartera
4. **Reactivar instalaciones**: Las instalaciones dadas de baja pueden ser reactivadas con el botón "Reactivar Instalación"
5. **Visualizar estado**: Si una instalación está de baja, se muestra una alerta roja con la fecha y motivo

## Rollback (Deshacer)

Si necesitas revertir esta migración:

```sql
-- Eliminar campos agregados
ALTER TABLE instalaciones
DROP COLUMN IF EXISTS en_cartera,
DROP COLUMN IF EXISTS fecha_salida_cartera,
DROP COLUMN IF EXISTS motivo_salida;

-- Eliminar índice
DROP INDEX IF EXISTS idx_instalaciones_en_cartera;
```
