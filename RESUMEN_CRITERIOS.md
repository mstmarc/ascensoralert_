# 🎯 Resumen de Criterios de Búsqueda

## Los 4 Criterios Disponibles

El sistema ahora soporta **4 criterios diferentes** para analizar zonas calientes, cada uno optimizado para diferentes casos de uso:

---

## 1️⃣ Por Código Postal ⭐⭐⭐

**Mejor para:** Análisis comercial masivo y segmentación de mercado

```python
zona = detector.analizar_zona_por_codigo_postal("35001")
```

**Cuándo usar:**
- Tienes base de datos con CPs de clientes
- Quieres comparar zonas objetivamente
- Análisis masivo de ciudad completa
- Planificación de campañas por zona

**Ejemplo rápido:**
```bash
python ejemplo_analisis_por_cp.py
```

**Ventajas:**
- ✅ Datos disponibles en cualquier BD comercial
- ✅ Ideal para análisis masivo (19 CPs en Las Palmas)
- ✅ Resultados comparables entre zonas
- ✅ Fácil de usar y entender

---

## 2️⃣ Por Calle Específica ⭐⭐⭐

**Mejor para:** Prospección focalizada en calles comerciales

```python
zona = detector.analizar_zona_por_calle(
    "Calle Mayor de Triana",
    radio_metros=300
)
```

**Cuándo usar:**
- Análisis de calles comerciales principales
- Prospección calle por calle
- Campañas focalizadas en calles específicas
- Identificar edificios antiguos en calles clave

**Ejemplo rápido:**
```bash
python ejemplo_analisis_por_calle.py
```

**Calles principales de Las Palmas:**
- **Comerciales**: Triana, Mesa y López, León y Castillo
- **Históricas**: Los Balcones, Obispo Codina, Pelota
- **Residenciales**: Aconcagua, Amazonas, Doctor Grau Bassas

**Ventajas:**
- ✅ Muy focalizado y específico
- ✅ Perfecto para calles comerciales
- ✅ Control fino del radio (100-500m)
- ✅ Análisis rápido (3-5 min por calle)

---

## 3️⃣ Por Nombre de Barrio ⭐⭐

**Mejor para:** Análisis exploratorio y presentaciones

```python
zona = detector.analizar_zona_por_nombre("Vegueta")
```

**Cuándo usar:**
- Conoces bien las zonas de la ciudad
- Presentaciones comerciales ("zona de Vegueta")
- Análisis exploratorio inicial
- No tienes códigos postales disponibles

**Ejemplo rápido:**
```bash
python scripts/analizar_zonas_las_palmas.py vegueta
```

**Ventajas:**
- ✅ Muy intuitivo
- ✅ Coincide con percepción de clientes
- ✅ Útil para presentaciones
- ✅ No requiere datos técnicos (CP)

---

## 4️⃣ Por Direcciones Semilla ⭐

**Mejor para:** Casos avanzados y personalizados

```python
zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=["Calle Aconcagua", "Calle Amazonas"],
    radio_metros=400
)
```

**Cuándo usar:**
- Análisis alrededor de clientes existentes
- Zonas sin nombre o CP claro
- Control muy fino del área
- Múltiples puntos de referencia

**Ventajas:**
- ✅ Máximo control del área
- ✅ Múltiples puntos de referencia
- ✅ Flexible y personalizable

---

## 📊 Comparación Rápida

| Criterio | Facilidad | Precisión | Comercial | Tiempo/Zona |
|----------|-----------|-----------|-----------|-------------|
| **Código Postal** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 3-5 min |
| **Calle** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 3-5 min |
| **Barrio** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 3-5 min |
| **Direcciones** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 5-8 min |

---

## 🎯 Recomendaciones por Caso de Uso

### Caso 1: Segmentación de Mercado Completa
**Usar:** Código Postal
```bash
python scripts/analisis_masivo_codigos_postales.py
```
→ Analiza 19 CPs, genera ranking completo

---

### Caso 2: Prospección en Zona Comercial
**Usar:** Calle Específica
```python
calles = ["Calle Mayor de Triana", "Calle Mesa y López"]
zonas = [detector.analizar_zona_por_calle(c) for c in calles]
ranking = detector.comparar_zonas(zonas)
```
→ Compara calles comerciales, identifica la mejor

---

### Caso 3: Presentación a Cliente
**Usar:** Nombre de Barrio
```python
zona = detector.analizar_zona_por_nombre("Vegueta")
print(detector.generar_reporte_texto(zona))
```
→ Reporte legible para presentación comercial

---

### Caso 4: Análisis Alrededor de Cliente Existente
**Usar:** Direcciones Semilla
```python
zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=["Dirección del cliente"],
    radio_metros=300
)
```
→ Identifica oportunidades cerca de clientes actuales

---

## 🚀 Scripts Disponibles

| Script | Criterio | Tiempo | Qué Hace |
|--------|----------|--------|----------|
| `ejemplo_analisis_por_cp.py` | Código Postal | 15-20 min | Compara 4 CPs clave |
| `ejemplo_analisis_por_calle.py` | Calle | 15-20 min | Compara 3 calles comerciales |
| `scripts/analisis_masivo_codigos_postales.py` | Código Postal | 30-60 min | Analiza 19 CPs completos |
| `scripts/analizar_zonas_las_palmas.py` | Barrio | 3-5 min | Menú interactivo de barrios |

---

## 💡 Combinaciones Poderosas

### Combinación 1: Macro + Micro
```python
# 1. Identificar mejores CPs (macro)
cps = ["35001", "35002", "35010"]
zonas_cp = [detector.analizar_zona_por_codigo_postal(cp) for cp in cps]
mejor_cp = detector.comparar_zonas(zonas_cp)[0]

# 2. Profundizar en calles del mejor CP (micro)
calles_del_cp = ["Calle Mayor de Triana", "Calle Cano"]
zonas_calle = [detector.analizar_zona_por_calle(c) for c in calles_del_cp]
```
→ Estrategia top-down: primero CP, luego calle

---

### Combinación 2: Multi-criterio
```python
# Analizar misma zona con diferentes criterios
zona_cp = detector.analizar_zona_por_codigo_postal("35001")
zona_barrio = detector.analizar_zona_por_nombre("Triana")
zona_calle = detector.analizar_zona_por_calle("Calle Mayor de Triana")

# Comparar resultados
print(f"CP 35001: {zona_cp.score_total}")
print(f"Barrio Triana: {zona_barrio.score_total}")
print(f"Calle Triana: {zona_calle.score_total}")
```
→ Validación cruzada de resultados

---

## 📈 Flujo Completo Recomendado

```python
from zonas_calientes import DetectorZonasCalientes

detector = DetectorZonasCalientes()

# Paso 1: Análisis macro (CPs)
print("=== FASE 1: Análisis por Código Postal ===")
cps_prioritarios = ["35001", "35002", "35010", "35012"]
zonas_cp = []
for cp in cps_prioritarios:
    zona = detector.analizar_zona_por_codigo_postal(cp)
    zonas_cp.append(zona)
    print(f"CP {cp}: {zona.edificios_muy_antiguos} edificios muy antiguos")

# Identificar top 2 CPs
ranking_cp = detector.comparar_zonas(zonas_cp)
top_cps = ranking_cp[:2]
print(f"\nTop 2 CPs: {[z.nombre for z in top_cps]}")

# Paso 2: Análisis micro (Calles del mejor CP)
print("\n=== FASE 2: Análisis por Calle (mejor CP) ===")
# Supongamos que el mejor es CP 35001 (Triana)
calles_triana = [
    "Calle Mayor de Triana",
    "Calle Cano",
    "Calle Domingo Rivero"
]

zonas_calle = []
for calle in calles_triana:
    zona = detector.analizar_zona_por_calle(calle)
    zonas_calle.append(zona)
    print(f"{calle}: {zona.edificios_muy_antiguos} edificios prioritarios")

# Identificar mejor calle
ranking_calle = detector.comparar_zonas(zonas_calle)
mejor_calle = ranking_calle[0]

# Paso 3: Exportar leads de la mejor calle
print(f"\n=== FASE 3: Exportar Leads ===")
print(f"Mejor calle: {mejor_calle.nombre}")
detector.exportar_zona_csv(
    mejor_calle,
    f'leads_{mejor_calle.nombre.replace(" ", "_").lower()}.csv'
)
print(f"✓ {len(mejor_calle.edificios)} leads exportados")
```

---

## 📁 Documentación Completa

- **GUIA_RAPIDA_ZONAS.md** - Guía rápida de uso
- **docs/ZONAS_CALIENTES_README.md** - Documentación técnica completa
- **docs/CATASTRO_VIABILIDAD.md** - Evaluación de viabilidad inicial

---

## ✅ Resumen Ejecutivo

**4 Criterios implementados:**
1. ✅ Código Postal - Para análisis masivo
2. ✅ Calle Específica - Para prospección focalizada
3. ✅ Nombre de Barrio - Para análisis exploratorio
4. ✅ Direcciones Semilla - Para casos avanzados

**Todos incluyen:**
- Geocodificación automática
- Extracción de datos del Catastro
- Sistema de scoring por antigüedad
- Exportación a JSON y CSV
- Generación de reportes de texto
- Comparación de múltiples zonas

**Listo para usar:**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Probar análisis por CP
python ejemplo_analisis_por_cp.py

# Probar análisis por calle
python ejemplo_analisis_por_calle.py
```

---

**¿Cuál usar? Depende de tu objetivo:**
- 🎯 **Análisis masivo** → Código Postal
- 🛍️ **Calles comerciales** → Calle Específica
- 🗺️ **Exploración** → Nombre de Barrio
- 🔧 **Personalizado** → Direcciones Semilla
