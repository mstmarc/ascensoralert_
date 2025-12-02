# 🚀 Analítica Avanzada V2 - Sistema de Alertas Predictivas

## 📋 Resumen Ejecutivo

La **Versión 2** del módulo de analítica transforma el sistema de **reactivo** a **proactivo**, pasando de "mostrar datos" a "tomar decisiones automáticas".

**Problema resuelto**: Falta de control técnico con solo Sergio operativo, máquinas que generan trabajo repetitivo, gasto innecesario y pérdida de facturación.

**Solución**: Sistema de detección automática de patrones + alertas prioritarias + backlog técnico inteligente.

---

## 🎯 Diferencias Clave: V1 vs V2

| **Característica** | **V1 (Básica)** | **V2 (Avanzada)** |
|---|---|---|
| **Detección de problemas** | Manual, revisión humana | Automática con 3 detectores |
| **Priorización** | Por índice numérico | Por estado semafórico 🟥🟧🟨🟩 |
| **Alertas** | Pasivas (hay que buscar) | Activas (te notifican) |
| **Backlog técnico** | No existe | Sí, organizado por urgencia |
| **Seguimiento** | Por máquina individual | Por máquina + instalación (IRI) |
| **Pérdidas estimadas** | No calculadas | Sí, automático (€) |
| **Fallas repetidas** | No detectadas | Detectadas con 68 keywords |
| **Recomendaciones ignoradas** | Sin seguimiento | Alerta si generan averías |
| **Mantenimientos omitidos** | Sin control | Alerta automática |

---

## 🧠 Arquitectura del Sistema V2

```
┌─────────────────────────────────────────────────────────────┐
│                     BASE DE DATOS                           │
├─────────────────────────────────────────────────────────────┤
│  NUEVAS TABLAS:                                             │
│  • componentes_criticos (base de conocimiento)              │
│  • alertas_automaticas (alertas generadas)                  │
│  • pendientes_tecnicos (backlog de Sergio)                  │
│                                                             │
│  NUEVAS VISTAS:                                             │
│  • v_estado_maquinas_semaforico (🟥🟧🟨🟩)                    │
│  • v_riesgo_instalaciones (IRI - Índice Riesgo)            │
│  • v_perdidas_por_pendientes (cálculo de €€€)              │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               DETECTORES AUTOMÁTICOS                        │
│               (detectores_alertas.py)                       │
├─────────────────────────────────────────────────────────────┤
│  1. Detector de Fallas Repetidas                            │
│     → 2+ veces en 30 días o 3+ en 90 días                   │
│     → Usa 68 keywords de componentes críticos               │
│                                                             │
│  2. Detector de Recomendaciones Ignoradas                   │
│     → Recomendación sin ejecutar + 2 averías posteriores    │
│                                                             │
│  3. Detector de Mantenimientos Omitidos                     │
│     → 60+ días sin conservación                             │
│     → Urgencia ALTA si además tiene averías recientes       │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     DASHBOARD V2                            │
│                   (/cartera/v2)                             │
├─────────────────────────────────────────────────────────────┤
│  KPIs:                                                      │
│  • Alertas urgentes/altas/pendientes                        │
│  • Máquinas por estado semafórico                           │
│  • Pérdidas estimadas (€€€)                                 │
│  • Top instalaciones de riesgo (IRI)                        │
│                                                             │
│  Acciones:                                                  │
│  • Ejecutar detectores manualmente                          │
│  • Ver alertas críticas (top 10)                            │
│  • Ver backlog técnico (top 10)                             │
│  • Navegar a detalles                                       │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              WORKFLOW DE RESOLUCIÓN                         │
├─────────────────────────────────────────────────────────────┤
│  Alerta → Revisar → Acción:                                 │
│  • Crear Trabajo Técnico (va a backlog)                     │
│  • Crear Oportunidad Comercial (para Julio)                │
│  • Marcar como Resuelta                                     │
│  • Descartar (falso positivo)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Componentes del Sistema

### 1. **Componentes Críticos** (Base de Conocimiento)

Tabla con los 12 componentes más problemáticos de ascensores:

| Componente | Familia | Coste Promedio | Keywords |
|---|---|---|---|
| Puerta automática | PUERTAS | 450€ | puerta, cierre, apertura, hoja |
| Cerradero | PUERTAS | 180€ | cerradero, pestillo, gancho |
| Barrera fotoeléctrica | SEGURIDAD | 220€ | barrera, fotocélula |
| Reenvío de planta | MANIOBRA | 320€ | reenvío, botonera planta |
| Comunicación bidireccional | COMUNICACION | 380€ | bidireccional, gsm |
| Batería auxiliar | ELECTRICA | 150€ | batería, fuente auxiliar |
| Cable viajero | ELECTRICA | 280€ | cable viajero |
| Botonera cabina | CABINA | 250€ | botonera, pulsadores |
| Variador | MANIOBRA | 1200€ | variador, inversor |
| Limitador velocidad | SEGURIDAD | 850€ | limitador |
| Paracaídas | SEGURIDAD | 900€ | paracaídas, freno |
| Contacto de cabina | SEGURIDAD | 120€ | contacto cabina |

**Uso**: Los detectores analizan el campo "resolución" de cada parte y buscan estas keywords para identificar qué componente está fallando.

---

### 2. **Detectores Automáticos**

#### 🔍 **Detector 1: Fallas Repetidas**

**Objetivo**: Detectar componentes que fallan repetidamente → necesitan reparación/sustitución definitiva.

**Criterios**:
- **Alta urgencia**: 2+ averías en los últimos 30 días del mismo componente
- **Media urgencia**: 3+ averías en los últimos 90 días del mismo componente

**Proceso**:
1. Leer todos los partes de averías de los últimos 90 días
2. Para cada parte, detectar componente crítico usando keywords
3. Agrupar averías por (máquina, componente)
4. Aplicar criterios de detección
5. Si cumple criterio → crear alerta `FALLA_REPETIDA`
6. Si ya existe alerta activa para esa máquina/componente → skip

**Ejemplo real**:
```
Máquina: MONTACOCHES (CONCESIONARIO JAGUAR)
Componente: Puerta automática
Averías detectadas:
  - 05/12/2024: "Puerta no cierra correctamente, ajuste de hoja"
  - 18/12/2024: "Puerta vuelve a fallar, cierre defectuoso"

→ ALERTA GENERADA (ALTA): "Falla repetida: Puerta automática - 2 fallas en 30 días"
```

---

#### 🔍 **Detector 2: Recomendaciones Ignoradas**

**Objetivo**: Detectar recomendaciones técnicas que no se ejecutaron y luego causaron más averías → pérdida de dinero.

**Criterios**:
- Recomendación marcada como `tiene_recomendacion=true`
- NO ejecutada (`recomendacion_revisada=false`, `oportunidad_creada=false`)
- Con antigüedad de más de 15 días
- **Y** que haya generado 2+ averías posteriores

**Proceso**:
1. Leer todas las recomendaciones pendientes (>15 días)
2. Para cada recomendación, contar averías posteriores a su fecha
3. Si averías_posteriores >= 2 → crear alerta `RECOMENDACION_IGNORADA`
4. Urgencia ALTA si averías >= 3, MEDIA si averías = 2

**Ejemplo real**:
```
Parte #2024005234 (10/11/2024):
Recomendación: "Convendría sustituir variador, presenta fallos intermitentes"

Averías posteriores:
  - 25/11/2024: Ascensor parado, fallo de variador
  - 08/12/2024: Nueva avería, variador sin comunicación
  - 22/12/2024: Avería repetida, variador no arranca

→ ALERTA GENERADA (ALTA): "Recomendación ignorada - 3 averías posteriores"
→ Pérdida estimada: 3 averías × 180€ = 540€ (evitables si se hubiera ejecutado)
```

---

#### 🔍 **Detector 3: Mantenimientos Omitidos**

**Objetivo**: Detectar máquinas sin mantenimiento preventivo → alto riesgo de averías.

**Criterios**:
- **Tipo 1 (Media urgencia)**: 60+ días sin conservación
- **Tipo 2 (Alta urgencia)**: 60+ días sin conservación **Y** 2+ averías en los últimos 30 días

**Proceso**:
1. Leer todas las máquinas activas (`en_cartera=true`)
2. Para cada máquina, obtener fecha del último mantenimiento
3. Si fecha > 60 días → mantenimiento atrasado
4. Contar averías en los últimos 30 días
5. Si averías >= 2 → urgencia ALTA (`MANTENIMIENTO_OMITIDO_CON_AVERIAS`)
6. Si averías < 2 → urgencia MEDIA (`MANTENIMIENTO_OMITIDO`)

**Ejemplo real**:
```
Máquina: ASC 3 PLANTA OESTE
Último mantenimiento: 15/09/2024 (109 días atrás)
Averías último mes: 3

→ ALERTA GENERADA (ALTA): "Mantenimiento atrasado + 3 averías recientes"
→ Acción: Programar conservación URGENTE
```

---

### 3. **Estado Semafórico de Máquinas**

Clasificación visual de máquinas en 4 estados:

#### 🟥 **CRÍTICO**
**Criterios** (cualquiera de):
- 3+ averías en el último mes
- 2+ fallas repetidas activas
- Mantenimiento atrasado (60+ días) + 2+ averías recientes

**Acción**: Intervención URGENTE

#### 🟧 **INESTABLE**
**Criterios** (cualquiera de):
- 5+ averías en el último trimestre
- 1 falla repetida activa
- Mantenimiento muy atrasado (90+ días)
- 2+ defectos IPO pendientes

**Acción**: Priorizar en planificación

#### 🟨 **SEGUIMIENTO**
**Criterios** (cualquiera de):
- 2-4 averías en el trimestre
- Recomendaciones vencidas (30+ días sin revisar)
- 1 defecto IPO pendiente

**Acción**: Monitorizar de cerca

#### 🟩 **ESTABLE**
**Criterios**:
- Sin problemas significativos
- Mantenimientos al día
- Sin alertas activas

**Acción**: Continuar mantenimiento normal

---

### 4. **Índice de Riesgo de Instalación (IRI)**

Métrica que evalúa instalaciones completas (no solo máquinas individuales).

**Fórmula**:
```
IRI = (30% × promedio_índice_máquinas) +
      (40% × peso_máquinas_críticas) +
      (30% × peso_alertas_urgentes)

Donde:
- promedio_índice_máquinas: Promedio del índice de problema de todas las máquinas de la instalación
- peso_máquinas_críticas: (máquinas_críticas × 20) + (máquinas_inestables × 10)
- peso_alertas_urgentes: (pendientes_urgentes × 8) + (alertas_urgentes × 5)
```

**Clasificación**:
- **CRÍTICO**: IRI ≥ 50
- **ALTO**: IRI ≥ 25
- **MEDIO**: IRI ≥ 10
- **BAJO**: IRI < 10

**Uso práctico**:
*"Estas 5 instalaciones van a consumir tu semana si no actúas YA"*

---

### 5. **Cálculo de Pérdidas por Pendientes**

Vista SQL que calcula automáticamente cuánto dinero se está dejando de ganar:

**Componentes**:
1. **Recomendaciones vencidas sin ejecutar**:
   - Cantidad: N recomendaciones
   - Valor estimado: N × 350€ (promedio)

2. **Averías evitables** (fallas repetidas):
   - Cantidad: N fallas repetidas activas
   - Coste estimado: N × 180€ (coste promedio de avería evitable)

3. **Oportunidades sin presupuestar**:
   - Cantidad: N oportunidades en estado "DETECTADA"
   - Valor estimado: Σ importes presupuestados o N × 500€

**Total = Componente 1 + Componente 2 + Componente 3**

**Ejemplo real**:
```
📊 Pérdidas Estimadas del Mes:
• 8 recomendaciones vencidas: 8 × 350€ = 2.800€
• 5 fallas repetidas: 5 × 180€ = 900€
• 12 oportunidades sin presupuesto: 12 × 500€ = 6.000€

💰 TOTAL PÉRDIDA ESTIMADA: 9.700€
```

**Uso**: Justificar a dirección la necesidad de más recursos técnicos o contratar a otro técnico.

---

## 🔄 Flujo de Trabajo Completo

### **Fase 1: Detección Automática**

```bash
# Ejecutar detectores (manual o via cron)
python detectores_alertas.py

# O desde el dashboard
POST /cartera/v2/ejecutar-detectores
```

**Resultado**: N alertas nuevas generadas y guardadas en `alertas_automaticas`

---

### **Fase 2: Revisión en Dashboard**

1. Acceder a `/cartera/v2`
2. Ver banner rojo si hay alertas urgentes
3. Ver KPIs de alertas por tipo y urgencia
4. Ver top 10 alertas críticas activas
5. Ver estado semafórico de máquinas
6. Ver pérdidas estimadas
7. Ver top 5 instalaciones de riesgo

---

### **Fase 3: Tomar Acción sobre Alerta**

#### **Opción A: Crear Trabajo Técnico** (para Sergio)
```
Alerta → Botón "Crear Trabajo Técnico"
  ↓
Se crea registro en pendientes_tecnicos
  ↓
Alerta pasa a estado "TRABAJO_PROGRAMADO"
  ↓
Trabajo aparece en /cartera/v2/pendientes-tecnicos
  ↓
Sergio ve su backlog priorizado
```

#### **Opción B: Crear Oportunidad Comercial** (para Julio)
```
Alerta → Botón "Crear Oportunidad"
  ↓
Se crea registro en oportunidades_facturacion
  ↓
Alerta pasa a estado "OPORTUNIDAD_CREADA"
  ↓
Julio ve la oportunidad en /cartera/oportunidades
  ↓
Julio envía presupuesto al cliente
```

#### **Opción C: Marcar como Resuelta**
- El problema ya se resolvió por otra vía
- Alerta pasa a estado "RESUELTA"

#### **Opción D: Descartar**
- Falso positivo
- Alerta pasa a estado "DESCARTADA"

---

### **Fase 4: Gestión del Backlog Técnico**

**Vista**: `/cartera/v2/pendientes-tecnicos`

**Características**:
- Kanban visual por urgencia: URGENTE | ALTA | MEDIA | BAJA
- Filtros: estado, urgencia, asignado a
- Acciones por pendiente:
  - Ver máquina
  - Asignar a técnico
  - Marcar como completado
  - Actualizar estado (PENDIENTE → ASIGNADO → EN_CURSO → COMPLETADO)

**Uso para Sergio**:
*"Cada mañana, Sergio abre su backlog y ve exactamente qué máquinas necesitan atención urgente, priorizadas automáticamente por el sistema"*

---

## 🚀 Instalación y Configuración

### **Paso 1: Aplicar Migración SQL**

```bash
# Opción A: Ejecutar migración directa
psql -U postgres -d ascensoralert -f database/migrations/005_analitica_avanzada_v2.sql

# Opción B: Ejecutar schema completo (si es instalación nueva)
psql -U postgres -d ascensoralert -f database/cartera_schema.sql
psql -U postgres -d ascensoralert -f database/cartera_schema_v2.sql
```

**Verificación**:
```sql
SELECT * FROM componentes_criticos; -- Debe mostrar 12 componentes
SELECT * FROM alertas_automaticas; -- Tabla vacía inicialmente
SELECT * FROM pendientes_tecnicos; -- Tabla vacía inicialmente
SELECT * FROM v_estado_maquinas_semaforico LIMIT 5; -- Debe mostrar máquinas con estado
```

---

### **Paso 2: Ejecutar Detectores Iniciales**

```bash
# Ejecutar detectores por primera vez
python detectores_alertas.py

# Ver log de ejecución
# Debe mostrar cuántas alertas de cada tipo se generaron
```

**Resultado esperado**:
```
🔍 Detector 1: Analizando fallas repetidas...
   Analizando 1,245 averías de los últimos 90 días...
   ✓ Alerta creada: Falla repetida: Puerta automática - ASC 2 EDIFICIO... [ALTA]
   ✓ Alerta creada: Falla repetida: Barrera - MONTACARGAS... [MEDIA]
   📊 Total alertas de fallas repetidas creadas: 8

🔍 Detector 2: Analizando recomendaciones ignoradas...
   Analizando 23 recomendaciones pendientes...
   ✓ Alerta creada: Recomendación ignorada: ASC 1 COMUNIDAD... [ALTA]
   📊 Total alertas de recomendaciones ignoradas: 5

🔍 Detector 3: Analizando mantenimientos omitidos...
   Analizando 156 máquinas activas...
   ✓ Alerta creada: Mantenimiento atrasado: ASC 3 PLANTA... [ALTA]
   📊 Total alertas de mantenimientos omitidos: 12

✅ EJECUCIÓN COMPLETADA
📊 Total de alertas nuevas generadas: 25
```

---

### **Paso 3: Configurar Cron Job (Automatización)**

```bash
# Editar crontab
crontab -e

# Añadir línea para ejecutar detectores cada día a las 6:00 AM
0 6 * * * cd /home/user/ascensoralert_ && /usr/bin/python3 detectores_alertas.py >> logs/alertas.log 2>&1
```

---

### **Paso 4: Acceder al Dashboard V2**

```
URL: https://tu-dominio.com/cartera/v2
```

**Primera vez**: Verás las alertas generadas + estado semafórico calculado + pérdidas estimadas.

---

## 📱 Vistas del Sistema

### **1. Dashboard V2** (`/cartera/v2`)
- Banner de alertas urgentes
- KPIs de alertas (urgentes, altas, pendientes, por tipo)
- Estado semafórico (🟥🟧🟨🟩)
- Pérdidas estimadas (€€€)
- Top 10 alertas críticas
- Top 5 máquinas críticas
- Top 5 instalaciones de riesgo (IRI)
- Top 10 pendientes técnicos

### **2. Todas las Alertas** (`/cartera/v2/alertas`)
- Lista completa de alertas
- Filtros: estado, tipo, urgencia
- Acciones: ver detalle, resolver, descartar

### **3. Detalle de Alerta** (`/cartera/v2/alerta/:id`)
- Información completa de la alerta
- Máquina e instalación relacionadas
- Datos de detección (JSON)
- Acciones disponibles:
  - Crear trabajo técnico
  - Crear oportunidad comercial
  - Marcar como resuelta
  - Descartar

### **4. Backlog Técnico** (`/cartera/v2/pendientes-tecnicos`)
- Vista Kanban por urgencia
- Filtros: estado, urgencia, asignado
- Acciones por pendiente:
  - Ver máquina
  - Asignar técnico
  - Marcar completado
  - Actualizar estado

### **5. Dashboard V1** (`/cartera`)
- Dashboard original (se mantiene como alternativa)
- Acceso a todas las funciones V1

---

## 🎓 Mejoras Futuras Sugeridas

### **Automatizaciones**

1. **Notificaciones por Email/WhatsApp**
   - Cuando máquina pasa a estado 🟥 CRÍTICO
   - Cuando recomendación cumple 30 días sin ejecutar
   - Cuando repuesto lleva 14+ días en PENDIENTE

2. **Generador de Argumentos Comerciales**
   - Al crear oportunidad desde alerta
   - Texto pre-escrito para Julio
   - Justificación técnica + impacto económico

3. **Integración con IPOs**
   - Cruzar defectos IPO con alertas
   - Si máquina con IPO caducada tiene 2+ averías → alerta CRÍTICA

4. **Dashboard para Julio** (Comercial)
   - Vista filtrada solo de oportunidades
   - KPIs comerciales: presupuestos enviados, aceptados, rechazados
   - Valor total del pipeline

5. **Análisis de Costes Reales**
   - Registrar coste real de cada avería
   - Comparar coste_real vs coste_estimado
   - Refinar algoritmo de pérdidas

6. **Machine Learning** (futuro)
   - Predecir averías antes de que ocurran
   - Basado en histórico de partes + patrones de fallas
   - Modelo entrenado con tus datos reales

---

## 📞 Soporte y Contacto

**Archivos clave**:
- `database/cartera_schema_v2.sql` - Schema completo V2
- `database/migrations/005_analitica_avanzada_v2.sql` - Migración
- `detectores_alertas.py` - Detectores automáticos
- `app.py` (líneas 6642-6996) - Rutas del módulo V2
- `templates/cartera/dashboard_v2.html` - Dashboard principal
- `templates/cartera/pendientes_tecnicos.html` - Backlog técnico

**Rutas principales**:
- `/cartera/v2` - Dashboard V2
- `/cartera/v2/alertas` - Todas las alertas
- `/cartera/v2/pendientes-tecnicos` - Backlog técnico
- `POST /cartera/v2/ejecutar-detectores` - Ejecutar detectores

---

## 🏆 Beneficios del Sistema V2

✅ **Sergio deja de apagar fuegos** → trabaja en problemas raíz

✅ **Hugo puede crecer sin presión** → backlog priorizado y claro

✅ **Tú detectas pérdidas automáticamente** → justificación de recursos

✅ **Julio vende más** → oportunidades con argumentos claros

✅ **Instalaciones críticas se gestionan antes de explotar** → menos estrés

✅ **Puedes demostrar si necesitas más técnico** → datos objetivos

✅ **Dejas de depender del criterio de un técnico saturado** → sistema automatizado

✅ **Gestionas la cartera con datos reales** → decisiones informadas

✅ **Cada fallo repetido se convierte en dinero** → recuperación de facturación perdida

---

**Versión**: 2.0
**Fecha**: Enero 2025
**Estado**: ✅ Listo para producción
