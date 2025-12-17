# Corrección de Visitas Huérfanas

## Problema

Debido al bug en el filtro de estados de oportunidades (que solo buscaba `estado = "activa"`), las visitas creadas desde oportunidades con otros estados (`"nueva"`, `"en_contacto"`, etc.) se guardaron sin el campo `oportunidad_id`, quedando "huérfanas".

Esto significa que:
- ❌ Las visitas no aparecen en el historial de la oportunidad
- ❌ El seguimiento comercial está incompleto
- ❌ Los reportes no reflejan la actividad real

## Solución

Se proporcionan dos métodos para corregir estas visitas:

### Método 1: Script Python Interactivo (Recomendado)

**Ventajas:**
- ✅ Interactivo y seguro
- ✅ Muestra qué se va a corregir antes de hacerlo
- ✅ Pide confirmación
- ✅ Muestra estadísticas

**Uso:**
```bash
cd /home/user/ascensoralert_
python3 scripts/corregir_visitas_oportunidades.py
```

El script:
1. Analiza todas las visitas sin `oportunidad_id`
2. Busca oportunidades activas del mismo cliente
3. Filtra por fechas (la visita debe ser posterior a la creación de la oportunidad)
4. Muestra las coincidencias encontradas
5. Pide confirmación antes de hacer cambios
6. Aplica las correcciones
7. Muestra estadísticas finales

### Método 2: Scripts SQL Directos

**Ventajas:**
- ✅ Más rápido para grandes volúmenes
- ✅ Puede ejecutarse directamente en Supabase

**Uso:**
```bash
# Desde psql o la consola SQL de Supabase
psql $DATABASE_URL -f scripts/corregir_visitas_oportunidades.sql
```

O copiando y pegando las queries en el editor SQL de Supabase.

**Pasos:**
1. **PASO 1: DIAGNÓSTICO** - Ejecutar las queries de diagnóstico para ver qué se corregirá
2. **Revisar resultados** - Verificar manualmente que las coincidencias son correctas
3. **PASO 2: CORRECCIÓN** - Ejecutar las queries UPDATE (¡hacer backup antes!)
4. **PASO 3: VERIFICACIÓN** - Ejecutar las queries de verificación

## Lógica de Vinculación

El script vincula visitas con oportunidades cuando:

### Para visitas a instalación (`visitas_seguimiento`):
- ✅ Misma `cliente_id`
- ✅ Oportunidad en estado activo (no `ganada` ni `perdida`)
- ✅ `fecha_visita >= fecha_creacion_oportunidad`
- ✅ Si hay múltiples oportunidades, elige la más reciente

### Para visitas a administrador (`visitas_administradores`):
- ✅ Mismo `administrador_id`
- ✅ Busca clientes de ese administrador
- ✅ Busca oportunidades de esos clientes
- ✅ Oportunidad en estado activo
- ✅ `fecha_visita >= fecha_creacion_oportunidad`
- ✅ Ventana de tiempo: hasta 30 días después de la última actualización

## Casos Especiales

### ⚠️ Visitas ambiguas
Si un cliente tiene múltiples oportunidades activas, el script vincula con la más reciente. Si esto no es correcto, se puede ajustar manualmente después.

### ⚠️ Visitas antiguas
Las visitas muy antiguas (antes de que existieran oportunidades) no se vincularán automáticamente.

### ⚠️ Visitas sin contexto
Visitas de administradores sin `administrador_id` no pueden vincularse automáticamente.

## Verificación Post-Corrección

Después de ejecutar la corrección, verificar en la aplicación:

1. Ir a una oportunidad que tuvo visitas
2. Verificar que las visitas aparecen en "📅 Historial de Visitas"
3. Comprobar que las fechas y datos son correctos

También puedes verificar con esta query:
```sql
-- Ver oportunidades con sus visitas
SELECT
    o.id,
    o.tipo,
    o.estado,
    c.nombre_cliente,
    (SELECT COUNT(*) FROM visitas_seguimiento WHERE oportunidad_id = o.id) as visitas_instalacion,
    (SELECT COUNT(*) FROM visitas_administradores WHERE oportunidad_id = o.id) as visitas_admin,
    (SELECT COUNT(*) FROM visitas_seguimiento WHERE oportunidad_id = o.id) +
    (SELECT COUNT(*) FROM visitas_administradores WHERE oportunidad_id = o.id) as total_visitas
FROM oportunidades o
INNER JOIN clientes c ON o.cliente_id = c.id
WHERE o.estado NOT IN ('ganada', 'perdida')
ORDER BY total_visitas DESC;
```

## Rollback

Si necesitas deshacer los cambios:

```sql
-- Deshacer vinculaciones (CUIDADO: esto afecta TODAS las visitas)
UPDATE visitas_seguimiento
SET oportunidad_id = NULL
WHERE updated_at > '2024-XX-XX'; -- Ajustar fecha

UPDATE visitas_administradores
SET oportunidad_id = NULL
WHERE updated_at > '2024-XX-XX'; -- Ajustar fecha
```

## Prevención Futura

El bug original ya fue corregido en el commit `d2549cf`. Las visitas creadas desde ahora se vincularán correctamente automáticamente.

Los cambios aplicados:
- ✅ Filtro de estados actualizado a `estado neq ganada AND estado neq perdida`
- ✅ Campo oculto `oportunidad_id` en formularios
- ✅ Mensajes visuales claros de vinculación
- ✅ Redirección correcta tras guardar

## Soporte

Si tienes dudas o encuentras problemas:
1. Revisa los logs del script Python
2. Verifica las queries SQL de diagnóstico
3. Comprueba que las variables de entorno están configuradas (`SUPABASE_URL`, `SUPABASE_KEY`)
