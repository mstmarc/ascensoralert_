# 🤖 Sistema de Análisis Predictivo con IA para Ascensores

## 📋 Descripción

Sistema inteligente de análisis predictivo que utiliza **Claude 3.5 Sonnet** (Anthropic) para analizar partes de trabajo de ascensores y predecir futuras averías con conocimiento técnico especializado.

### ✨ Capacidades

- **Análisis Semántico Profundo**: Entiende el contexto técnico completo de los partes de trabajo
- **Predicción de Averías Futuras**: Predice qué componentes tienen más probabilidad de fallar y cuándo
- **Detección de Patrones**: Identifica patrones de deterioro y comportamientos anómalos
- **Alertas Inteligentes**: Genera alertas predictivas solo cuando hay riesgos reales
- **Estimación de Costes**: Calcula ahorro potencial de intervenciones preventivas vs correctivas
- **Aprendizaje Continuo**: El sistema mejora con el tiempo basándose en feedback

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD WEB (/cartera/ia)                  │
│  Visualización de predicciones, alertas y métricas de IA       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      API ENDPOINTS (app.py)                     │
│  /cartera/ia/*  -  Rutas REST para acceso a datos              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                 MOTOR DE IA (analizador_ia.py)                  │
│  • analizar_parte_con_ia()         - Análisis individual       │
│  • generar_prediccion_maquina()    - Predicciones por máquina  │
│  • generar_alertas_predictivas()   - Generación de alertas     │
│  • procesar_lote_partes()          - Procesamiento masivo      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│              ANTHROPIC CLAUDE 3.5 SONNET API                    │
│  Modelo de IA con conocimiento técnico de ascensores           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│              BASE DE DATOS POSTGRESQL                           │
│  Schema: ia_predictiva_schema.sql                               │
│  • analisis_partes_ia         - Análisis de partes             │
│  • predicciones_maquina        - Predicciones por máquina      │
│  • alertas_predictivas_ia      - Alertas inteligentes          │
│  • conocimiento_tecnico_ia     - Base de conocimiento          │
│  • metricas_precision_ia       - Métricas de rendimiento       │
│  • aprendizaje_ia              - Feedback loop                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- Python 3.8+
- PostgreSQL 12+
- Cuenta en Anthropic (para API de Claude)
- Base de datos de AscensorAlert ya configurada

### 2. Instalar Dependencias

```bash
pip install anthropic>=0.39.0 python-dotenv>=1.0.0
```

O con requirements.txt actualizado:

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Copia `.env.example` a `.env` y configura:

```bash
# API de Anthropic (REQUERIDO para IA)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...

# Base de datos PostgreSQL (REQUERIDO)
DATABASE_URL=postgresql://usuario:password@host:puerto/database

# Otras variables (ya configuradas)
SECRET_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

**Importante**: Obtén tu API key de Anthropic en https://console.anthropic.com/

### 4. Instalar Schema de Base de Datos

Ejecuta el script SQL para crear las tablas de IA:

```bash
psql -d tu_base_datos -f database/ia_predictiva_schema.sql
```

O si usas Supabase:

```bash
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" -f database/ia_predictiva_schema.sql
```

### 5. Verificar Instalación

```bash
python scripts/test_ia_predictiva.py --listar-maquinas
```

Si todo está bien, verás la lista de máquinas disponibles para analizar.

## 📊 Uso del Sistema

### Opción 1: Interfaz Web (Recomendado)

1. Accede al dashboard de IA: `http://localhost:5000/cartera/ia`

2. **Primera vez**: El dashboard estará vacío porque no hay análisis ni predicciones

3. **Generar análisis**: Usa el script de prueba para analizar datos iniciales

### Opción 2: Scripts de Python

#### Analizar Partes de Trabajo

```bash
# Analizar 10 partes de prueba
python scripts/test_ia_predictiva.py --analizar-partes 10

# Analizar 50 partes
python scripts/test_ia_predictiva.py --analizar-partes 50

# Analizar TODOS los partes sin análisis (máx 100)
python scripts/test_ia_predictiva.py --analizar-todo
```

#### Generar Predicciones de Máquinas

```bash
# Listar máquinas disponibles
python scripts/test_ia_predictiva.py --listar-maquinas

# Generar predicción para una máquina específica (por ID)
python scripts/test_ia_predictiva.py --generar-prediccion 123

# Generar predicciones para TODAS las máquinas
python scripts/test_ia_predictiva.py --predicciones-todas
```

### Opción 3: Uso Programático

```python
import psycopg2
import analizador_ia

# Conectar a BD
conn = psycopg2.connect(DATABASE_URL)

# Analizar un parte específico
parte = {
    'id': 12345,
    'numero_parte': '2024000123',
    'tipo_parte_normalizado': 'AVERIA',
    'fecha_parte': '2024-12-04',
    'maquina_texto': 'ASC-001',
    'resolucion': 'Avería en puerta automática, ajuste de hoja...',
    'maquina_id': 456
}

analisis_id = analizador_ia.analizar_parte_con_ia(parte, conn)

# Generar predicción de una máquina
prediccion_id = analizador_ia.generar_prediccion_maquina(456, conn)

# Generar alertas
alertas = analizador_ia.generar_alertas_predictivas(prediccion_id, conn)

conn.close()
```

## 📈 Funcionalidades del Dashboard

### Panel Principal (`/cartera/ia`)

- **Estadísticas Generales**
  - Máquinas críticas y urgentes
  - Alertas activas
  - Ahorro potencial total

- **Top 20 Máquinas con Mayor Riesgo**
  - Estado de salud (puntuación 0-100)
  - Tendencia (mejorando, estable, deteriorando, crítica)
  - Componente en mayor riesgo
  - Probabilidad de fallo y días estimados
  - Ahorro potencial de intervención preventiva

- **Alertas Predictivas Activas**
  - Alertas ordenadas por urgencia
  - Componente afectado
  - Fecha límite de acción
  - Costes estimados

- **Componentes Más Problemáticos**
  - Estadísticas globales por componente
  - Tasa de recurrencia
  - Coste promedio

- **ROI del Sistema**
  - Predicciones generadas vs acertadas
  - Tasa de acierto
  - Ahorro real vs potencial

### Ver Predicción de Máquina (`/cartera/ia/prediccion/<id>`)

- Estado de salud detallado
- Top 3 componentes en riesgo
- Patrón detectado
- Intervención sugerida
- Justificación técnica de la predicción
- Historial de análisis de partes

### Gestión de Alertas (`/cartera/ia/alertas`)

- Filtrar por estado y nivel de urgencia
- Ver detalles de cada alerta
- Marcar como aceptada, descartada o resuelta
- Agregar notas técnicas

### Análisis de Componentes (`/cartera/ia/componentes`)

- Estadísticas globales por componente
- Base de conocimiento técnico
- Patrones de fallo comunes
- Vida útil esperada
- Costes promedio

### Métricas del Sistema (`/cartera/ia/metricas`)

- ROI mensual del sistema
- Tasa de precisión de predicciones
- Averías evitadas
- Ahorro total generado

## 🧠 Cómo Funciona el Sistema

### 1. Análisis de Partes

Cuando se analiza un parte de trabajo:

1. **Extracción de Información**: La IA lee la descripción del trabajo y extrae:
   - Componente principal afectado
   - Tipo de fallo (desgaste, ruptura, desajuste, etc.)
   - Causa raíz del problema
   - Gravedad técnica
   - Señales de deterioro

2. **Análisis Contextual**: Evalúa:
   - Si es parte de un patrón recurrente
   - Relación con partes anteriores
   - Probabilidad de que vuelva a ocurrir

3. **Recomendaciones**: Genera:
   - Recomendación técnica específica
   - Acciones preventivas sugeridas
   - Estimación de costes preventivos vs correctivos

### 2. Predicción de Máquinas

Para generar una predicción de máquina:

1. **Recopilación de Datos**: Obtiene:
   - Histórico completo de partes (últimos 180 días por defecto)
   - Análisis previos con IA
   - Estadísticas de averías y mantenimientos

2. **Análisis de Patrones**: La IA identifica:
   - Componentes con mayor desgaste
   - Tendencias de deterioro
   - Patrones anómalos

3. **Generación de Predicción**:
   - Estado de salud (0-100)
   - Top 3 componentes en riesgo con probabilidades
   - Días estimados hasta próxima avería
   - Intervención sugerida con fecha
   - ROI de actuar preventivamente

4. **Validación de Predicciones**: El sistema aprende:
   - Si las predicciones se cumplen
   - Ajusta probabilidades basándose en resultados reales
   - Mejora continuamente la precisión

### 3. Alertas Predictivas

El sistema genera alertas solo cuando:

- Hay una probabilidad alta de fallo inminente (>70% en <30 días)
- Se detecta un patrón de deterioro progresivo
- Hay comportamiento anómalo que requiere atención
- El coste de no actuar es significativamente mayor

**Tipos de Alertas**:
- `FALLO_INMINENTE`: Alta probabilidad de fallo en días/semanas
- `DETERIORO_PROGRESIVO`: Desgaste continuo que requiere seguimiento
- `PATRON_ANOMALO`: Comportamiento inusual detectado
- `MANTENIMIENTO_URGENTE`: Mantenimiento preventivo necesario ya

## 💰 Costes de Uso

### API de Anthropic (Claude 3.5 Sonnet)

- **Análisis de un parte**: ~$0.003 (0.003€)
- **Predicción de máquina**: ~$0.015 (0.015€)
- **100 partes analizados**: ~$0.30 (0.30€)
- **100 predicciones**: ~$1.50 (1.50€)

### Estimación para una Cartera de 100 Máquinas

**Setup Inicial** (una vez):
- Analizar 500 partes históricos: ~$1.50
- Generar 100 predicciones iniciales: ~$1.50
- **Total inicial**: ~$3.00

**Mantenimiento Mensual**:
- Analizar ~200 nuevos partes: ~$0.60
- Regenerar 100 predicciones: ~$1.50
- **Total mensual**: ~$2.10

**ROI Esperado**:
- Una sola avería evitada puede costar 200-2000€
- El sistema se paga por sí mismo evitando 1-2 averías al año

## 📊 Base de Datos

### Tablas Principales

#### `analisis_partes_ia`
Almacena el análisis detallado de cada parte con IA.

Campos clave:
- `componente_principal`: Componente identificado
- `tipo_fallo`: Clasificación del fallo
- `causa_raiz`: Causa raíz identificada
- `gravedad_tecnica`: LEVE, MODERADA, GRAVE, CRITICA
- `probabilidad_recurrencia`: % de probabilidad de que vuelva a ocurrir
- `recomendacion_ia`: Recomendación técnica
- `confianza_analisis`: % de confianza en el análisis

#### `predicciones_maquina`
Predicciones de averías futuras por máquina.

Campos clave:
- `estado_salud_ia`: EXCELENTE, BUENA, REGULAR, MALA, CRITICA
- `puntuacion_salud`: 0-100
- `componente_riesgo_1/2/3`: Top 3 componentes en riesgo
- `probabilidad_fallo_1/2/3`: % probabilidad de fallo
- `dias_estimados_fallo_1/2/3`: Días estimados
- `prioridad_intervencion`: BAJA, MEDIA, ALTA, URGENTE
- `ahorro_potencial`: Ahorro si se actúa preventivamente

#### `alertas_predictivas_ia`
Alertas generadas por el sistema de IA.

Campos clave:
- `tipo_alerta`: FALLO_INMINENTE, DETERIORO_PROGRESIVO, etc.
- `nivel_urgencia`: BAJA, MEDIA, ALTA, URGENTE, CRITICA
- `componente_afectado`: Componente en riesgo
- `fecha_limite_accion`: Fecha límite para actuar
- `coste_intervencion` vs `coste_si_no_actua`

#### `conocimiento_tecnico_ia`
Base de conocimiento sobre componentes.

Incluye:
- Vida útil esperada
- Costes promedio
- Fallos comunes
- Síntomas de desgaste
- Frecuencia de revisión recomendada

#### `metricas_precision_ia`
Métricas para medir la precisión del sistema.

Incluye:
- Tasa de acierto de predicciones
- Falsos positivos/negativos
- ROI del sistema
- Averías evitadas

### Vistas SQL

- `v_salud_maquinas_ia`: Resumen de salud con predicciones activas
- `v_componentes_problematicos`: Análisis global de componentes
- `v_roi_sistema_ia`: ROI mensual del sistema

## 🔧 Mantenimiento y Buenas Prácticas

### Frecuencia de Análisis Recomendada

- **Partes nuevos**: Analizar en tiempo real al importar
- **Predicciones**: Regenerar cada 30 días
- **Alertas**: Revisar semanalmente

### Validación de Predicciones

Es crucial validar si las predicciones se cumplen:

1. Cuando ocurre una avería, marcar si fue predicha
2. El sistema usa este feedback para mejorar
3. Revisa métricas mensuales de precisión

### Optimización de Costes

- Analiza solo partes de AVERIA y REPARACION (más relevantes)
- No regeneres predicciones si no ha habido cambios significativos
- Usa el filtro de confianza para priorizar (confianza >70%)

## 🐛 Resolución de Problemas

### "ANTHROPIC_API_KEY no configurada"

**Solución**: Agrega tu API key en `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

### "Error conectando a la base de datos"

**Solución**: Verifica tu `DATABASE_URL` en `.env`:
```bash
DATABASE_URL=postgresql://usuario:password@host:puerto/database
```

### "Tabla analisis_partes_ia no existe"

**Solución**: Ejecuta el schema SQL:
```bash
psql -d tu_database -f database/ia_predictiva_schema.sql
```

### "Error parseando JSON del análisis"

**Causa**: La IA devolvió texto extra además del JSON
**Solución**: El sistema intenta extraer el JSON automáticamente, pero si falla:
- Verifica que el prompt esté correcto
- Revisa el log completo del error
- Puede ser un problema temporal de la API

### Límites de Rate (API)

Si ves errores de rate limit:
- Anthropic tiene límites por minuto/día
- Reduce el tamaño de lotes (`--analizar-partes 10` en lugar de 100)
- Agrega delays entre llamadas si haces procesamiento masivo

## 📚 Referencias y Documentación

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Model Pricing](https://www.anthropic.com/pricing)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🎯 Roadmap Futuro

- [ ] Integración con sistema de notificaciones (email/SMS)
- [ ] Generación automática de órdenes de trabajo desde predicciones
- [ ] Fine-tuning del modelo con datos históricos específicos
- [ ] Análisis de imágenes de ascensores (OCR, detección de defectos)
- [ ] Integración con IoT para datos en tiempo real
- [ ] API pública para integraciones externas
- [ ] App móvil para técnicos de campo

## 📞 Soporte

Si tienes problemas o sugerencias:
1. Revisa esta documentación primero
2. Ejecuta el script de test para diagnóstico
3. Revisa los logs de la aplicación
4. Contacta al equipo de desarrollo

## 📄 Licencia

Este sistema es parte de AscensorAlert. Todos los derechos reservados.

---

**Desarrollado con ❤️ usando Claude 3.5 Sonnet**

**Versión**: 1.0.0
**Fecha**: 2025-12-04
