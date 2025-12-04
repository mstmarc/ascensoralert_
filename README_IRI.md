# 🔍 Revisión del IRI - Guía de Diagnóstico y Corrección

## Problema Reportado
**"No hay ninguna máquina en el IRI"** - Las instalaciones no aparecen en el dashboard V2.

---

## 📋 Pasos a Seguir

### 1️⃣ PRIMERO: Ejecutar Diagnóstico (OBLIGATORIO)

Ejecutar el script de diagnóstico para identificar la causa raíz:

```bash
psql -U <usuario> -d <database> -f diagnostico_iri.sql
```

O si usas Supabase CLI:
```bash
supabase db execute --file diagnostico_iri.sql
```

**El script generará 14 diagnósticos** que mostrarán:
- ✅ Cuántas instalaciones/máquinas están marcadas como `en_cartera = TRUE`
- ✅ Si hay datos de averías, alertas y pendientes
- ✅ Valores actuales del IRI
- ✅ Simulación de cómo cambiarían con los nuevos criterios

---

### 2️⃣ Identificar el Problema

#### Escenario A: **Instalaciones/Máquinas Fuera de Cartera**

**Síntoma:**
```
Total instalaciones EN cartera = 0
Total máquinas EN cartera = 0
```

**Causa:** Todas las instalaciones/máquinas están marcadas como `en_cartera = FALSE`.

**Solución:** Reactivar instalaciones/máquinas necesarias:

```sql
-- Reactivar todas las instalaciones
UPDATE instalaciones
SET en_cartera = TRUE
WHERE en_cartera = FALSE OR en_cartera IS NULL;

-- Reactivar todas las máquinas
UPDATE maquinas_cartera
SET en_cartera = TRUE
WHERE en_cartera = FALSE OR en_cartera IS NULL;

-- Verificar
SELECT COUNT(*) FROM instalaciones WHERE en_cartera = TRUE;
SELECT COUNT(*) FROM maquinas_cartera WHERE en_cartera = TRUE;
```

**O reactivar selectivamente:**
```sql
-- Reactivar solo instalaciones específicas
UPDATE instalaciones
SET en_cartera = TRUE
WHERE id IN (1, 2, 3, ...);  -- IDs específicos

-- Reactivar máquinas de esas instalaciones
UPDATE maquinas_cartera m
SET en_cartera = TRUE
WHERE instalacion_id IN (1, 2, 3, ...);
```

---

#### Escenario B: **Datos Insuficientes**

**Síntoma:**
```
Total instalaciones EN cartera > 0
Máquinas con averías en último trimestre = 0
Alertas activas = 0
IRI máximo < 10
```

**Causa:** No hay suficientes datos históricos (averías, alertas, pendientes).

**Soluciones:**

1. **Ejecutar detectores de alertas:**
```bash
# Opción 1: Desde la UI
# → Ir a /cartera/v2
# → Clic en "Ejecutar Detectores"

# Opción 2: Manualmente desde Python
python3 -c "import detectores_alertas; detectores_alertas.ejecutar_todos_los_detectores()"
```

2. **Verificar que hay partes de trabajo registrados:**
```sql
SELECT COUNT(*) FROM partes_trabajo
WHERE fecha_parte >= CURRENT_DATE - INTERVAL '3 months';
```

3. **Si no hay datos históricos:** Importar datos o esperar a que se acumulen.

---

#### Escenario C: **Criterios Demasiado Estrictos**

**Síntoma:**
```
Total instalaciones EN cartera > 0
Hay averías registradas
IRI máximo = 8.5 (por ejemplo)
Clasificación = BAJO para todas
```

**Causa:** Los umbrales actuales son muy altos:
- ALTO requiere IRI ≥ 25
- MEDIO requiere IRI ≥ 10

**Solución:** Aplicar migración con nuevos criterios.

---

### 3️⃣ Aplicar Ajustes a los Criterios (Si es necesario)

Si el diagnóstico confirma que el problema son los criterios estrictos:

```bash
psql -U <usuario> -d <database> -f database/migrations/011_ajustar_criterios_iri.sql
```

**Cambios aplicados:**
- ✅ Nuevo nivel **CRÍTICO** (IRI ≥ 40)
- ✅ Umbral **ALTO** bajado de 25 a **15**
- ✅ Umbral **MEDIO** bajado de 10 a **5**
- ✅ Peso de **pendientes urgentes** aumentado (×2 → ×3)

**Impacto esperado:**
| Escenario | IRI Actual | Antes | Después |
|-----------|------------|-------|---------|
| Instalación con 2 averías/trim | 3.6 | BAJO | **MEDIO** ✅ |
| Instalación con 1 máq inestable | 12.4 | MEDIO | **ALTO** ✅ |
| Instalación con múltiples problemas | 38.3 | ALTO | **CRÍTICO** ✅ |

---

### 4️⃣ Verificar Solución

Después de aplicar la corrección, verificar:

```sql
-- Ver top 5 instalaciones por IRI
SELECT
    instalacion_nombre,
    total_maquinas,
    indice_riesgo_instalacion,
    nivel_riesgo_instalacion
FROM v_riesgo_instalaciones
ORDER BY indice_riesgo_instalacion DESC
LIMIT 5;
```

**O desde la UI:**
- Ir a `/cartera/v2`
- Verificar que aparecen instalaciones en "Top Instalaciones de Riesgo (IRI)"

---

## 📊 Archivos Creados

| Archivo | Descripción |
|---------|-------------|
| `analisis_iri.md` | Análisis completo de los criterios del IRI y problemas identificados |
| `diagnostico_iri.sql` | Script de diagnóstico con 14 verificaciones (EJECUTAR PRIMERO) |
| `database/migrations/011_ajustar_criterios_iri.sql` | Migración con ajustes a los criterios del IRI |
| `README_IRI.md` | Esta guía paso a paso |

---

## 🔧 Resumen de Cambios Propuestos

### Antes (Criterios Actuales)
```
IRI = (30% × promedio_índice × 2) +
      (40% × máquinas_críticas) +
      (30% × alertas_urgentes)

Clasificación:
- ALTO: ≥ 25
- MEDIO: ≥ 10
- BAJO: < 10

Índice problema:
- (averias_trim × 3) + (averias_mes × 5) + (pendientes_urgentes × 2) + defectos
```

### Después (Criterios Ajustados)
```
IRI = (30% × promedio_índice × 2) +
      (40% × máquinas_críticas) +
      (30% × alertas_urgentes)

Clasificación:
- CRÍTICO: ≥ 40  ⬅️ NUEVO
- ALTO: ≥ 15     ⬅️ CAMBIO (antes 25)
- MEDIO: ≥ 5     ⬅️ CAMBIO (antes 10)
- BAJO: < 5

Índice problema:
- (averias_trim × 3) + (averias_mes × 5) + (pendientes_urgentes × 3) + defectos
                                                                    ⬆️ CAMBIO (antes 2)
```

---

## ⚠️ Notas Importantes

1. **Filtro `en_cartera`:**
   - Desde migración 007 (2025-12-04), todas las vistas filtran por `en_cartera = TRUE`
   - Si las instalaciones están dadas de baja, NO aparecerán en el IRI

2. **Detectores de alertas:**
   - El IRI depende de alertas automáticas
   - Ejecutar detectores regularmente (manual o cron)

3. **Datos históricos:**
   - El IRI necesita al menos 3 meses de datos de averías
   - Sin historial, el índice será bajo

4. **Reversión:**
   - Si los nuevos criterios no funcionan, puedes revertir la vista ejecutando la migración 007 original

---

## 🎯 Checklist de Verificación

Antes de reportar que el problema está resuelto, verificar:

- [ ] Ejecuté `diagnostico_iri.sql` y revisé los resultados
- [ ] Verificación: `en_cartera = TRUE` para instalaciones necesarias
- [ ] Verificación: Hay datos de averías en últimos 3 meses
- [ ] Verificación: Ejecuté detectores de alertas
- [ ] Aplicación: Migración 011 (si era necesario)
- [ ] Resultado: Al menos 1 instalación aparece en el dashboard
- [ ] Resultado: Valores de IRI son coherentes

---

## 💡 Ejemplos de Consultas Útiles

### Ver instalaciones y su estado en cartera
```sql
SELECT
    i.id,
    i.nombre,
    i.en_cartera,
    i.fecha_salida_cartera,
    COUNT(m.id) as total_maquinas,
    COUNT(m.id) FILTER (WHERE m.en_cartera = TRUE) as maquinas_activas
FROM instalaciones i
LEFT JOIN maquinas_cartera m ON i.id = m.instalacion_id
GROUP BY i.id, i.nombre, i.en_cartera, i.fecha_salida_cartera
ORDER BY i.nombre;
```

### Ver desglose del IRI por componentes
```sql
SELECT
    instalacion_nombre,
    ROUND((COALESCE(promedio_indice_problema, 0) * 2) * 0.30, 2) as componente_indice,
    ROUND((maquinas_criticas * 20 + maquinas_inestables * 10) * 0.40, 2) as componente_maquinas,
    ROUND((pendientes_urgentes * 8 + alertas_activas * 5) * 0.30, 2) as componente_alertas,
    indice_riesgo_instalacion as iri_total
FROM v_riesgo_instalaciones
ORDER BY iri_total DESC
LIMIT 10;
```

### Ver máquinas con más averías recientes
```sql
SELECT
    m.identificador,
    i.nombre as instalacion,
    COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '1 month') as averias_mes,
    COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months') as averias_trimestre
FROM maquinas_cartera m
INNER JOIN instalaciones i ON m.instalacion_id = i.id
LEFT JOIN partes_trabajo p ON m.id = p.maquina_id AND p.tipo_parte_normalizado = 'AVERIA'
WHERE m.en_cartera = TRUE AND i.en_cartera = TRUE
GROUP BY m.id, m.identificador, i.nombre
HAVING COUNT(p.id) FILTER (WHERE p.fecha_parte >= CURRENT_DATE - INTERVAL '3 months') > 0
ORDER BY averias_mes DESC, averias_trimestre DESC
LIMIT 20;
```

---

## 🆘 Soporte

Si después de seguir esta guía el problema persiste:

1. Compartir resultado de `diagnostico_iri.sql`
2. Compartir consulta:
```sql
SELECT * FROM v_riesgo_instalaciones ORDER BY indice_riesgo_instalacion DESC LIMIT 5;
```
3. Verificar logs de la aplicación para errores en el endpoint `/cartera/v2`

---

**Última actualización:** 2025-12-04
**Autor:** Claude Code
**Versión:** 1.0
