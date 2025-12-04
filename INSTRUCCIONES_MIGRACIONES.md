# 🚀 Instrucciones para Crear las Vistas del IRI

## Problema Actual

El error `relation "v_riesgo_instalaciones" does not exist` indica que **las vistas del sistema IRI no han sido creadas** en tu base de datos.

---

## 📋 Paso 1: Ejecutar Diagnóstico Simple (Sin Vistas)

Primero, ejecuta el diagnóstico simplificado para verificar el estado:

```bash
# Ejecutar diagnóstico simple
psql -U <usuario> -d <database> -f diagnostico_iri_simple.sql
```

O en Supabase SQL Editor:
1. Abrir `diagnostico_iri_simple.sql`
2. Copiar contenido
3. Pegar en SQL Editor
4. Ejecutar

**Este script te dirá:**
- ✅ Si las tablas base existen
- ✅ Si las vistas del IRI están creadas
- ✅ Cuántas instalaciones/máquinas están activas
- ✅ Qué paso seguir

---

## 📦 Paso 2: Crear las Vistas del IRI

Dependiendo de tu configuración, ejecuta **UNA** de estas opciones:

### Opción A: Ejecutar Schema Completo V2 (Recomendado si es primera vez)

```bash
# Crear todas las vistas del sistema V2
psql -U <usuario> -d <database> -f database/cartera_schema_v2.sql
```

**Esto creará:**
- ✅ `v_estado_maquinas_semaforico` - Clasificación CRÍTICO/INESTABLE/SEGUIMIENTO/ESTABLE
- ✅ `v_maquinas_problematicas` - Índice de problema por máquina
- ✅ `v_riesgo_instalaciones` - **IRI (Índice de Riesgo de Instalación)**
- ✅ Todas las tablas del sistema V2 (si no existen)

### Opción B: Solo Actualizar Vistas (Si ya tienes las tablas)

```bash
# Solo actualizar las vistas con filtros en_cartera
psql -U <usuario> -d <database> -f database/migrations/007_update_views_exclude_baja.sql
```

### Opción C: Aplicar Solo la Vista del IRI Ajustada (Nueva versión)

```bash
# Crear vistas con criterios ajustados
psql -U <usuario> -d <database> -f database/migrations/011_ajustar_criterios_iri.sql
```

⚠️ **Nota:** La opción C requiere que las vistas base ya existan (ejecutar A o B primero).

---

## 🔍 Paso 3: Verificar que se Crearon las Vistas

```sql
-- Verificar vistas creadas
SELECT viewname
FROM pg_views
WHERE viewname LIKE 'v_%'
ORDER BY viewname;
```

**Deberías ver:**
- `v_estado_maquinas_semaforico`
- `v_maquinas_problematicas`
- `v_perdidas_por_pendientes`
- `v_riesgo_instalaciones` ✅
- `v_resumen_partes_maquina`

---

## 📊 Paso 4: Ejecutar Diagnóstico Completo

Una vez creadas las vistas:

```bash
# Ahora sí puedes ejecutar el diagnóstico completo
psql -U <usuario> -d <database> -f diagnostico_iri.sql
```

---

## 🔧 Solución Rápida (Todo en Uno)

Si quieres ejecutar todo de una vez:

```bash
# 1. Crear todas las vistas
psql -U <usuario> -d <database> -f database/cartera_schema_v2.sql

# 2. Actualizar con filtros en_cartera
psql -U <usuario> -d <database> -f database/migrations/007_update_views_exclude_baja.sql

# 3. Aplicar criterios ajustados del IRI
psql -U <usuario> -d <database> -f database/migrations/011_ajustar_criterios_iri.sql

# 4. Ejecutar diagnóstico completo
psql -U <usuario> -d <database> -f diagnostico_iri.sql
```

---

## 🎯 Orden de Ejecución de Migraciones

Si empiezas desde cero, este es el orden correcto:

```
1. database/cartera_schema.sql         → Tablas base
2. database/cartera_schema_v2.sql      → Tablas V2 + Vistas iniciales
3. 004_add_en_cartera_field.sql        → Campo en_cartera en máquinas
4. 006_add_instalacion_baja_fields.sql → Campo en_cartera en instalaciones
5. 007_update_views_exclude_baja.sql   → Actualizar vistas con filtros
6. 011_ajustar_criterios_iri.sql       → Ajustar criterios del IRI (NUEVO)
```

---

## ⚠️ Problemas Comunes

### Error: "table does not exist"
**Causa:** No se han ejecutado los schemas base.
**Solución:** Ejecutar `cartera_schema.sql` y luego `cartera_schema_v2.sql`

### Error: "column en_cartera does not exist"
**Causa:** No se ejecutó la migración 004 o 006.
**Solución:** Ejecutar:
```bash
psql -U <usuario> -d <database> -f database/migrations/004_add_en_cartera_field.sql
psql -U <usuario> -d <database> -f database/migrations/006_add_instalacion_baja_fields.sql
```

### Las vistas existen pero devuelven 0 filas
**Causa:** Todas las instalaciones/máquinas están marcadas como `en_cartera = FALSE`.
**Solución:**
```sql
UPDATE instalaciones SET en_cartera = TRUE;
UPDATE maquinas_cartera SET en_cartera = TRUE;
```

---

## 📱 Para Supabase

Si usas Supabase, puedes ejecutar los scripts directamente desde el **SQL Editor**:

1. Ir a **Database** → **SQL Editor**
2. Abrir archivo (ej: `cartera_schema_v2.sql`)
3. Copiar todo el contenido
4. Pegar en el editor
5. Clic en **Run** o `Ctrl+Enter`
6. Repetir para cada migración en orden

---

## ✅ Verificación Final

Después de ejecutar las migraciones:

```sql
-- Verificar que el IRI se calcula correctamente
SELECT
    instalacion_nombre,
    total_maquinas,
    indice_riesgo_instalacion,
    nivel_riesgo_instalacion
FROM v_riesgo_instalaciones
ORDER BY indice_riesgo_instalacion DESC
LIMIT 5;
```

**Si esto devuelve resultados, ¡estás listo!** 🎉

---

## 🆘 Necesitas Ayuda?

Si después de seguir estas instrucciones sigues teniendo problemas:

1. Ejecuta `diagnostico_iri_simple.sql` y comparte los resultados
2. Comparte el error exacto que recibes
3. Indica qué archivos ya ejecutaste

---

**Última actualización:** 2025-12-04
**Versión:** 1.1
