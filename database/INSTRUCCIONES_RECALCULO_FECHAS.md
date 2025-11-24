# Recalcular Fechas de Segunda Inspección

## Problema
Cuando se edita la fecha de inspección de inspecciones ya existentes, el sistema ahora recalcula correctamente la `fecha_segunda_inspeccion`. Sin embargo, las inspecciones que ya existían en la base de datos antes de este cambio mantienen sus fechas antiguas (potencialmente incorrectas).

## Solución
Ejecutar el script SQL de migración para recalcular todas las fechas de segunda inspección.

## Pasos para ejecutar la migración

### Opción 1: Desde Supabase Dashboard (Recomendado)
1. Ve a tu proyecto en Supabase Dashboard
2. Navega a **SQL Editor** en el menú lateral
3. Crea una nueva query
4. Copia y pega el contenido del archivo: `database/recalcular_todas_fechas_segunda_inspeccion.sql`
5. Haz clic en **Run** para ejecutar la migración
6. Revisa los resultados mostrados para verificar que todo está correcto

### Opción 2: Desde psql (si tienes acceso directo)
```bash
psql -h <host> -U postgres -d postgres -f database/recalcular_todas_fechas_segunda_inspeccion.sql
```

## Qué hace el script
- Actualiza **TODAS** las inspecciones pendientes de verificación (donde `fecha_segunda_realizada IS NULL`)
- Recalcula `fecha_segunda_inspeccion` como `fecha_inspeccion + 6 meses`
- NO modifica las inspecciones ya completadas (donde `fecha_segunda_realizada` ya tiene valor)
- Muestra un reporte detallado de todas las inspecciones con su nueva categorización
- Proporciona un resumen estadístico de la actualización

## Verificación
Después de ejecutar el script, verifica que:
1. Las inspecciones muestran las fechas límite correctas
2. El dashboard muestra el cálculo de días correcto
3. Las categorías (VENCIDA, URGENTE, PRÓXIMA, NORMAL) son apropiadas

## Resultado esperado
Todas las inspecciones pendientes tendrán su `fecha_segunda_inspeccion` correctamente calculada como `fecha_inspeccion + 6 meses`, y el dashboard mostrará los días restantes correctos.
