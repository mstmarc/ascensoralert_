# Dashboard de Cartera y Análisis - Diseño UI/UX

## 🎯 Objetivo
Detectar ascensores problemáticos, priorizar recursos técnicos limitados y maximizar facturación mediante análisis de datos operacionales.

---

## 📊 DASHBOARD PRINCIPAL: "Análisis Operacional"

### SECCIÓN 1: KPIs Críticos (Cards superiores)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔴 ASCENSORES CRÍTICOS    🟠 PARTES URGENTES    💰 FACTURACIÓN PENDIENTE   │
│        12 máquinas              27 partes              €15,450              │
│     ↑ 3 vs mes anterior       ↓ 5 vs semana           ↑ €2,100             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ MANTENIMIENTOS PENDIENTES   📈 AVERÍAS ESTE MES    ⚙️ TRABAJOS SIN FACTURAR │
│           18 partes                    45 averías              8 trabajos      │
│     Impacto: €3,200               ↑ 12% vs mes ant.          €4,200          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SECCIÓN 2: Top Ascensores Problemáticos (Tabla interactiva)

**Columnas:**
- Identificador | Instalación | Municipio | Índice Problema | Nivel Riesgo | Averías (mes/trim/año) | Pendientes | Acción

**Ejemplo:**
```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ ASCENSOR    INSTALACIÓN              MUN.    ÍNDICE  RIESGO   AVERÍAS      PENDIENTES│
│                                                      (Score)           M  T  A    U  T │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ASC-001    Edificio Palmas          L.Palmas   28   🔴CRÍTICO  3  8  15   2  3  [VER]│
│ ASC-045    Torres del Sur           Agüimes    19   🔴CRÍTICO  2  6  12   1  2  [VER]│
│ ASC-112    Residencial Norte        Telde      14   🟠ALTO     1  5  10   3  4  [VER]│
│ ASC-089    Plaza Mayor              L.Palmas   11   🟠ALTO     2  4   9   0  2  [VER]│
│ ASC-034    Mirador del Océano       Mogán       8   🟡MEDIO    1  3   7   1  1  [VER]│
└────────────────────────────────────────────────────────────────────────────────────┘
      M=Mes | T=Trimestre | A=Año | U=Urgentes | T=Total pendientes
```

**Filtros disponibles:**
- Municipio
- Nivel de riesgo (Crítico, Alto, Medio, Bajo)
- Cliente
- Tipo de contrato

**Ordenamiento por:**
- Índice de problema (default)
- Averías recientes
- Partes pendientes
- Facturación pendiente

### SECCIÓN 3: Análisis de Círculos Viciosos

**Título:** "⚠️ Ascensores con Mantenimientos Incumplidos y Alto Índice de Averías"

Identifica máquinas donde la falta de mantenimiento está generando más averías.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ASCENSOR    INSTALACIÓN       MANT.         MANT.        AVERÍAS   SALUD       │
│                            PROGRAMADOS   COMPLETADOS      AÑO    MANTENIMIENTO │
├────────────────────────────────────────────────────────────────────────────────┤
│ ASC-001    Edificio Palmas      12           5 (42%)       15    🔴 CRÍTICO    │
│ ASC-112    Residencial Norte    12           7 (58%)       10    🟠 DEFICIENTE │
│ ASC-045    Torres del Sur       10           6 (60%)       12    🟡 ACEPTABLE  │
└────────────────────────────────────────────────────────────────────────────────┘

💡 INSIGHT: ASC-001 tiene 7 mantenimientos sin realizar (58% incumplimiento)
            y es el ascensor con más averías. Priorizar mantenimientos.
```

**Botón de acción:** "Generar Plan de Mantenimientos Prioritarios"

### SECCIÓN 4: Análisis Económico

**Dos columnas:**

#### Columna Izquierda: Impacto Económico

```
┌─────────────────────────────────────────────┐
│  💰 IMPACTO ECONÓMICO - ÚLTIMOS 12 MESES    │
├─────────────────────────────────────────────┤
│  Coste Total Averías:        €45,200        │
│  Coste Mantenimientos:       €28,500        │
│  Facturación Reparaciones:   €38,900        │
│  ───────────────────────────────────        │
│  Facturación Pendiente:      €15,450 🔴     │
│  Trabajos Sin Facturar:       8 partes      │
├─────────────────────────────────────────────┤
│  🎯 OPORTUNIDAD DE MEJORA:                   │
│  Si se completan partes pendientes urgentes: │
│  Facturación adicional: €8,200               │
└─────────────────────────────────────────────┘
```

#### Columna Derecha: Top Clientes por Rentabilidad

```
┌──────────────────────────────────────────────────┐
│  📊 RENTABILIDAD POR CLIENTE (PEORES)            │
├──────────────────────────────────────────────────┤
│  CLIENTE           INGRESO   COSTE   MARGEN   %  │
├──────────────────────────────────────────────────┤
│  Torres del Sur    €12,000  €15,200  -€3,200 -27%│
│  Edificio Palmas   €18,000  €19,500  -€1,500  -8%│
│  Plaza Mayor       €10,000   €9,200    €800    8%│
└──────────────────────────────────────────────────┘

🔍 Análisis: 2 clientes están generando pérdidas.
   Revisar contratos o subir precios.
```

### SECCIÓN 5: Partes Pendientes Priorizados

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  📋 PARTES PENDIENTES - ORDEN DE PRIORIDAD                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ PRIORIDAD  ASCENSOR   INSTALACIÓN        TIPO          DÍAS      IMPACTO       │
│                                                       PENDIENTE  ESTIMADO  [ACCIÓN]│
├────────────────────────────────────────────────────────────────────────────────┤
│ 🔴 URGENTE ASC-001   Edificio Palmas    REPARACIÓN      15      €1,200   [ASIGNAR]│
│ 🔴 URGENTE ASC-045   Torres del Sur     AVERÍA          12        €800   [ASIGNAR]│
│ 🟠 ALTA    ASC-112   Residencial Norte  MANTENIMIENTO    8        €450   [ASIGNAR]│
│ 🟠 ALTA    ASC-089   Plaza Mayor        REPARACIÓN       7        €600   [ASIGNAR]│
│ 🟡 NORMAL  ASC-034   Mirador Océano     INCIDENCIA       4        €200   [ASIGNAR]│
└────────────────────────────────────────────────────────────────────────────────┘

[ASIGNAR EN LOTE] [EXPORTAR A EXCEL] [GENERAR RUTA TÉCNICO]
```

**Funcionalidades:**
- Asignar técnico directamente
- Cambiar prioridad
- Marcar como completado
- Ver historial de la máquina
- Exportar lista para técnicos

### SECCIÓN 6: Gráficos de Tendencias

**Dos gráficos lado a lado:**

#### Gráfico 1: Tendencia de Averías Mensual (12 meses)
```
Averías por Mes (2024-2025)
│
60│               ╭─╮
  │            ╭──╯ ╰╮
40│         ╭──╯     ╰─╮
  │      ╭──╯          ╰─╮
20│   ╭──╯               ╰─╮
  │╭──╯                    ╰─
0 └────────────────────────────
  E F M A M J J A S O N D E F
      2024            2025

📈 Tendencia: +15% vs mismo periodo año anterior
```

#### Gráfico 2: Top 5 Tipos de Avería
```
Distribución de Averías (Último Trimestre)

Puerta Bloqueada      ████████████████ 35 (28%)
Fallo Motor           ███████████ 25 (20%)
Problemas Cuadro      ████████ 18 (15%)
Pulsadores            ██████ 14 (11%)
Otros                 ███████████████████ 42 (26%)
```

---

## 🔍 VISTAS DETALLADAS

### VISTA 1: Ficha de Instalación

**Acceso:** Click en nombre de instalación

**Secciones:**
1. **Datos Generales**
   - Nombre, dirección, municipio, cliente, contacto
   - Administrador de fincas
   - Número de viviendas

2. **Resumen de Máquinas**
   - Tabla con todas las máquinas de la instalación
   - Estado operativo
   - Última inspección
   - Defectos pendientes
   - Partes pendientes

3. **Historial Consolidado**
   - Timeline de todas las intervenciones en todas las máquinas
   - Filtros por tipo de intervención
   - Exportar a PDF

4. **Análisis Económico de la Instalación**
   - Ingresos vs costes
   - Rentabilidad
   - Facturación pendiente

### VISTA 2: Ficha de Máquina

**Acceso:** Click en identificador de máquina

**Secciones:**

1. **Cabecera con Datos Técnicos**
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │ ASCENSOR: ASC-001                    ÍNDICE PROBLEMA: 28 🔴      │
   │ Edificio Palmas - Las Palmas                                    │
   ├─────────────────────────────────────────────────────────────────┤
   │ RAE: 123456789  │  Marca: Otis  │  Año: 2010  │  Paradas: 8    │
   │ Tipo Contrato: MANTENIMIENTO_INTEGRAL  │  €150/mes             │
   │ Vencimiento: 15/08/2025  │  Estado: 🟢 OPERATIVA               │
   └─────────────────────────────────────────────────────────────────┘
   ```

2. **KPIs de la Máquina**
   ```
   Averías (año): 15  |  Mantenimientos: 5/12  |  Pendientes: 5  |  Defectos IPO: 3
   ```

3. **Gráfico de Historial de Intervenciones**
   - Línea temporal con puntos por tipo (avería, mantenimiento, reparación)
   - Último año
   - Picos de averías identificados visualmente

4. **Tabla de Partes de Trabajo (filtrable)**
   - Fecha | Tipo | Descripción | Técnico | Estado | Coste | Facturado | Acciones

5. **Sección de Inspecciones**
   - Enlace automático con módulo de inspecciones existente
   - Últimas IPOs
   - Defectos pendientes

6. **Análisis Predictivo**
   ```
   ⚠️ ALERTA: Patrón detectado

   Esta máquina ha tenido 3 averías de "Puerta Bloqueada" en los últimos 2 meses.

   RECOMENDACIÓN: Revisar mecanismo de puertas en próximo mantenimiento.
   Posible causa: Desgaste de guías o desajuste del operador.

   IMPACTO SI NO SE ACTÚA: Estimado +2 averías/mes = +€800/mes en costes
   ```

7. **Botones de Acción**
   - [Crear Parte de Trabajo]
   - [Ver Inspecciones]
   - [Generar Informe Cliente]
   - [Editar Datos Técnicos]

### VISTA 3: Importar Datos desde Excel

**Acceso:** Menú "Cartera" → "Importar Datos"

**Tabs:**

1. **Importar Cartera de Instalaciones**
   ```
   ┌─────────────────────────────────────────────────────┐
   │  📁 Importar Instalaciones y Máquinas               │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  [Descargar Plantilla Excel]                        │
   │                                                     │
   │  ┌─────────────────────────────────────┐            │
   │  │  Arrastra el Excel aquí o haz click │            │
   │  │         para seleccionar            │            │
   │  └─────────────────────────────────────┘            │
   │                                                     │
   │  ✅ El Excel debe contener 2 hojas:                 │
   │     - Instalaciones (datos de edificios)            │
   │     - Maquinas (ascensores con sus instalaciones)   │
   │                                                     │
   │  [SUBIR Y PROCESAR]                                 │
   └─────────────────────────────────────────────────────┘
   ```

2. **Importar Partes de Trabajo**
   ```
   ┌─────────────────────────────────────────────────────┐
   │  📋 Importar Partes de Trabajo (Histórico)          │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  [Descargar Plantilla Excel]                        │
   │                                                     │
   │  Período: [2024] [2025 YTD] ← Carga inicial         │
   │                                                     │
   │  ┌─────────────────────────────────────┐            │
   │  │  Arrastra el Excel aquí o haz click │            │
   │  │         para seleccionar            │            │
   │  └─────────────────────────────────────┘            │
   │                                                     │
   │  ✅ Columnas requeridas:                            │
   │     - Identificador Máquina (debe existir)          │
   │     - Fecha Parte                                   │
   │     - Tipo (MANTENIMIENTO/AVERIA/REPARACION/etc)    │
   │     - Descripción                                   │
   │     - Estado (COMPLETADO/PENDIENTE/etc)             │
   │     - Técnico, Coste, Facturado (opcional)          │
   │                                                     │
   │  [SUBIR Y PROCESAR]                                 │
   └─────────────────────────────────────────────────────┘
   ```

**Proceso de importación:**
1. Usuario sube Excel
2. Sistema valida:
   - Formato correcto
   - Máquinas existen (si es importación de partes)
   - Fechas válidas
   - Tipos de parte correctos
3. Muestra preview con estadísticas:
   - Registros a insertar: X
   - Registros con errores: Y (muestra errores)
   - Duplicados detectados: Z
4. Usuario confirma
5. Importación masiva con barra de progreso
6. Resumen final:
   - ✅ X registros insertados correctamente
   - ⚠️ Y registros con advertencias
   - ❌ Z registros rechazados (descarga Excel con errores)

---

## 🎨 ELEMENTOS DE DISEÑO

### Paleta de Colores

```
🔴 Crítico:    #DC2626 (rojo)
🟠 Alto:       #EA580C (naranja)
🟡 Medio:      #F59E0B (amarillo)
🟢 Bajo/OK:    #16A34A (verde)
🔵 Info:       #2563EB (azul)
⚫ Neutral:    #6B7280 (gris)
```

### Iconos

- 🛗 Máquinas/Ascensores
- 🏢 Instalaciones
- 📋 Partes de trabajo
- 🔧 Mantenimiento
- ⚠️ Averías
- 💰 Económico
- 📊 Análisis
- 📈 Tendencias
- 🎯 Prioridad

### Notificaciones y Alertas

```
┌─────────────────────────────────────────────────────────┐
│ 🔴 ALERTA CRÍTICA                                       │
│ 3 ascensores han superado índice de problema 20         │
│ Se requiere acción inmediata.                           │
│                                    [VER DETALLES] [✕]   │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 NAVEGACIÓN

### Menú Principal (sidebar)

```
🏠 Home
📊 Dashboard CRM
🛗 Cartera y Análisis ← NUEVA SECCIÓN
   ├─ 📊 Dashboard Principal
   ├─ 🏢 Instalaciones
   ├─ 🛗 Máquinas
   ├─ 📋 Partes de Trabajo
   ├─ 📈 Análisis Económico
   └─ 📁 Importar Datos
🔍 Inspecciones (IPO)
👥 Administración
⚙️ Configuración
```

---

## 🚀 FUNCIONALIDADES CLAVE

### 1. Detección Automática de Problemas
- Cálculo diario de índice de problema
- Alertas automáticas cuando máquina entra en zona crítica
- Notificaciones por email (configurable)

### 2. Priorización Inteligente
- Score compuesto basado en:
  - Frecuencia de averías recientes (peso alto en mes actual)
  - Partes pendientes urgentes
  - Defectos de inspección pendientes
  - Mantenimientos no realizados
  - Impacto económico

### 3. Análisis de Círculos Viciosos
- Correlación automática entre mantenimientos no hechos y aumento de averías
- Identificación de patrones temporales
- Recomendaciones de acción

### 4. Seguimiento Económico
- Facturación pendiente
- Trabajos completados sin facturar
- Rentabilidad por cliente/máquina
- Estimación de pérdidas por partes pendientes

### 5. Importación Semanal
- Proceso simplificado de carga de partes
- Validación automática
- Detección de duplicados
- Actualización incremental

### 6. Integración con Inspecciones
- Enlace automático por campo `identificador` = `maquina`
- Vista unificada de defectos + partes
- Score de problema incluye defectos IPO pendientes

---

## 📊 REPORTES GENERABLES

1. **Reporte Ejecutivo Mensual**
   - Top 10 máquinas problemáticas
   - Evolución de averías
   - Impacto económico
   - Recomendaciones

2. **Informe por Cliente**
   - Estado de sus máquinas
   - Historial de intervenciones
   - Facturación y costes
   - Próximas acciones

3. **Plan de Trabajo Semanal**
   - Partes pendientes priorizados
   - Asignación sugerida de técnicos
   - Ruta optimizada

4. **Análisis de Rentabilidad**
   - Por cliente
   - Por máquina
   - Por tipo de contrato

---

## 🎯 MÉTRICAS DE ÉXITO

El dashboard será exitoso si:

1. ✅ Reduce tiempo de identificación de ascensores problemáticos de días → minutos
2. ✅ Aumenta facturación por reducción de trabajos sin facturar
3. ✅ Reduce averías recurrentes mediante detección de patrones
4. ✅ Optimiza asignación de técnicos (priorización correcta)
5. ✅ Mejora rentabilidad identificando contratos no rentables

---

## 🔄 FLUJO DE TRABAJO TÍPICO

### Lunes por la mañana:
1. Abrir Dashboard de Cartera
2. Ver KPIs críticos (¿hay nuevos ascensores en rojo?)
3. Revisar "Top Ascensores Problemáticos"
4. Identificar los 2-3 más urgentes
5. Revisar "Partes Pendientes Priorizados"
6. Asignar trabajos de la semana a técnicos
7. Generar "Plan de Trabajo Semanal" (PDF)
8. Enviar a equipo técnico

### Viernes por la tarde:
1. Importar partes de la semana desde Excel
2. Verificar trabajos completados
3. Revisar "Facturación Pendiente"
4. Generar facturas de trabajos completados
5. Ver evolución de índice de problemas (¿mejoraron los ascensores críticos?)

---

**FIN DEL DOCUMENTO DE DISEÑO**
