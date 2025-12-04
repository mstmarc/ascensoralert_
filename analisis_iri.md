# Análisis del IRI (Índice de Riesgo de Instalación)

## Problema Identificado

**No aparecen máquinas en el cálculo del IRI.**

## Causas Potenciales

### 1. Filtro `en_cartera` (MÁS PROBABLE)

Desde la migración 007 (2025-12-04), todas las vistas filtran instalaciones y máquinas con:
```sql
WHERE i.en_cartera = true  -- Solo instalaciones en cartera
AND m.en_cartera = true    -- Solo máquinas en cartera
```

**Si todas las instalaciones/máquinas están marcadas como `en_cartera = FALSE`, el resultado será vacío.**

### 2. Criterios del IRI Demasiado Estrictos

#### Fórmula Actual del IRI
```
IRI = (30% × promedio_índice_máquinas × 2) +
      (40% × peso_máquinas_críticas) +
      (30% × peso_alertas_urgentes)
```

#### Umbrales Actuales
- **ALTO**: IRI ≥ 25
- **MEDIO**: IRI ≥ 10
- **BAJO**: IRI < 10

#### Componentes del Cálculo

##### A. Promedio Índice de Problema (30% del IRI)
```
indice_problema =
    (averias_ultimo_trimestre × 3) +
    (averias_ultimo_mes × 5) +
    (partes_pendientes_urgentes × 2) +
    (defectos_inspeccion_pendientes × 1)
```

**Para lograr IRI ≥ 25 solo con este componente:**
- Promedio índice × 2 × 0.30 = 25
- Promedio índice necesario: **41.67**
- Esto requiere: **8+ averías en el trimestre** + **5+ averías en el mes**

##### B. Máquinas Críticas/Inestables (40% del IRI)
```
peso = (máquinas_CRITICO × 20) + (máquinas_INESTABLE × 10)
```

**Para lograr IRI ≥ 25 solo con este componente:**
- Peso × 0.40 = 25
- Peso necesario: **62.5**
- Esto requiere: **3+ máquinas CRÍTICAS** O **6+ máquinas INESTABLES**

**Criterios para máquina CRÍTICA:**
- 3+ averías en el último mes, O
- 2+ fallas repetidas activas, O
- Mantenimiento atrasado (60+ días) + 2+ averías recientes

**Criterios para máquina INESTABLE:**
- 5+ averías en el trimestre, O
- 1 falla repetida activa, O
- Mantenimiento muy atrasado (90+ días), O
- 2+ defectos IPO pendientes

##### C. Pendientes y Alertas Urgentes (30% del IRI)
```
peso = (pendientes_URGENTES × 8) + (alertas_URGENTES × 5)
```

**Para lograr IRI ≥ 25 solo con este componente:**
- Peso × 0.30 = 25
- Peso necesario: **83.33**
- Esto requiere: **10+ pendientes URGENTES** O **16+ alertas URGENTES**

---

## Análisis de Severidad

### Escenarios Típicos

#### Escenario 1: Instalación con Problemas Moderados
- 2 máquinas con 3 averías en trimestre (índice = 9 cada una)
- Promedio índice: 9 × 2 × 0.30 = **5.4 puntos**
- 1 máquina INESTABLE: 10 × 0.40 = **4.0 puntos**
- 2 alertas URGENTES: 10 × 0.30 = **3.0 puntos**
- **IRI Total: 12.4** → Clasificación: **MEDIO**

#### Escenario 2: Instalación con Problemas Graves
- 3 máquinas con 8 averías en trimestre + 3 en mes (índice = 39 cada una)
- Promedio índice: 39 × 2 × 0.30 = **23.4 puntos**
- 1 máquina CRÍTICA: 20 × 0.40 = **8.0 puntos**
- 3 alertas URGENTES + 1 pendiente URGENTE: 23 × 0.30 = **6.9 puntos**
- **IRI Total: 38.3** → Clasificación: **ALTO**

#### Escenario 3: Instalación con Datos Limitados (PROBLEMA ACTUAL)
- 2 máquinas con 1 avería en trimestre (índice = 3 cada una)
- Promedio índice: 3 × 2 × 0.30 = **1.8 puntos**
- 0 máquinas críticas/inestables: **0 puntos**
- 0 alertas/pendientes urgentes: **0 puntos**
- **IRI Total: 1.8** → Clasificación: **BAJO**
- ⚠️ **Podría no aparecer en el top 5 si hay pocas instalaciones con datos**

---

## Problemas Identificados

### 1. Requisitos Muy Altos para IRI "ALTO"
- IRI ≥ 25 requiere instalaciones con **múltiples problemas graves simultáneos**
- En operación normal, pocas instalaciones alcanzarán este umbral
- **Sugerencia:** Bajar umbral ALTO a ≥ 15

### 2. Falta Nivel "CRÍTICO"
- La clasificación actual solo tiene: ALTO, MEDIO, BAJO
- No hay diferenciación para instalaciones extremadamente problemáticas
- **Sugerencia:** Agregar nivel CRÍTICO ≥ 50

### 3. Dependencia de Datos Históricos
- Si no hay averías registradas en los últimos 3 meses, el índice será bajo
- Si no se ejecutan detectores de alertas, no habrá alertas activas
- Si no se crean pendientes técnicos, no se computan
- **Problema:** Datos incompletos = IRI subestimado

### 4. Pesos Desequilibrados
- Máquinas críticas tienen **40% del peso** (más alto)
- Pero criterios para CRÍTICO son **muy estrictos** (3+ averías/mes)
- **Resultado:** Este componente podría estar siempre en 0

---

## Propuestas de Ajuste

### Opción 1: Ajustar Solo Umbrales (CONSERVADOR)
```
- CRÍTICO: IRI ≥ 40
- ALTO: IRI ≥ 15     (antes 25)
- MEDIO: IRI ≥ 5     (antes 10)
- BAJO: IRI < 5
```

**Ventajas:**
- No cambia la lógica de cálculo
- Más instalaciones aparecerán como ALTO/MEDIO
- Fácil de implementar

**Desventajas:**
- No resuelve el problema de datos incompletos

### Opción 2: Ajustar Criterios de Máquinas Críticas (MODERADO)
```sql
-- CRÍTICO (actual: 3+ averías/mes)
→ Cambiar a: 2+ averías/mes O 3+ averías/trimestre

-- INESTABLE (actual: 5+ averías/trimestre)
→ Cambiar a: 3+ averías/trimestre O 1+ avería/mes
```

**Ventajas:**
- Más máquinas se clasificarán como críticas/inestables
- Aumenta el componente del 40% del IRI

**Desventajas:**
- Requiere modificar vista `v_estado_maquinas_semaforico`

### Opción 3: Redistribuir Pesos (AGRESIVO)
```
IRI = (40% × promedio_índice_máquinas × 2) +    (cambio: 30% → 40%)
      (30% × peso_máquinas_críticas) +           (cambio: 40% → 30%)
      (30% × peso_alertas_urgentes)              (sin cambio)
```

**Ventajas:**
- Da más peso al historial de averías (más objetivo)
- Reduce dependencia de clasificación semafórica

**Desventajas:**
- Cambia fundamentalmente el cálculo

### Opción 4: Ajustar Multiplicadores (BALANCEADO)
```
índice_problema =
    (averias_ultimo_trimestre × 2)     (antes 3)
    (averias_ultimo_mes × 4)           (antes 5)
    (partes_pendientes_urgentes × 3)   (antes 2)
    (defectos_inspeccion_pendientes × 2) (antes 1)
```

**Ventajas:**
- Balanceo más realista
- Da más peso a pendientes y defectos
- Mantiene la estructura actual

### Opción 5: Combinar Ajustes (RECOMENDADO)
1. **Ajustar umbrales** (Opción 1)
2. **Suavizar criterios de máquinas críticas** (Opción 2)
3. **Aumentar multiplicador de pendientes urgentes** (de 2 a 3)

---

## Script de Diagnóstico

Ejecutar `diagnostico_iri.sql` para verificar:
1. ¿Cuántas instalaciones tienen `en_cartera = TRUE`?
2. ¿Cuántas máquinas tienen `en_cartera = TRUE`?
3. ¿Qué valores de IRI tienen actualmente?
4. ¿Qué instalaciones deberían aparecer?

---

## Recomendación Final

### ✅ Acción Inmediata (Hoy)
1. Ejecutar script de diagnóstico
2. Verificar si el problema es `en_cartera = FALSE`
3. Si es así: **reactivar instalaciones/máquinas necesarias**

### ✅ Ajuste de Criterios (Corto Plazo)
Implementar **Opción 5 (Combinar Ajustes)**:

```sql
-- Nuevos umbrales
CASE
    WHEN IRI >= 40 THEN 'CRÍTICO'
    WHEN IRI >= 15 THEN 'ALTO'      -- antes 25
    WHEN IRI >= 5 THEN 'MEDIO'       -- antes 10
    ELSE 'BAJO'
END

-- Suavizar criterios de CRÍTICO en v_estado_maquinas_semaforico
-- De: 3+ averías/mes → A: 2+ averías/mes

-- Aumentar peso de pendientes urgentes en v_maquinas_problematicas
-- De: × 2 → A: × 3
```

---

## Impacto Esperado

Con los ajustes propuestos:

| Escenario | IRI Actual | IRI Ajustado | Clasificación |
|-----------|------------|--------------|---------------|
| 1 avería/trimestre | 1.8 | **3.0** | BAJO |
| 2 averías/trimestre | 3.6 | **6.0** | MEDIO ✅ |
| 3 averías/trimestre + 1 inestable | 12.4 | **16.8** | ALTO ✅ |
| 8 averías/trim + 3/mes + 1 crítica | 38.3 | **42.7** | CRÍTICO ✅ |

---

## Conclusión

**El problema más probable es el filtro `en_cartera`**. Si todas las instalaciones están dadas de baja, el resultado será vacío independientemente de los criterios.

**Pasos a seguir:**
1. ✅ Ejecutar diagnóstico SQL
2. ✅ Verificar estado `en_cartera` de instalaciones
3. ✅ Si necesario, ajustar umbrales y criterios
4. ✅ Validar que aparezcan instalaciones en el dashboard
