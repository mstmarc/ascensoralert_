# Guía Rápida: Análisis de Zonas Calientes

## 🎯 ¿Qué criterio usar?

### ✅ Por Código Postal (RECOMENDADO para comercial)

**Cuándo usar:**
- Tienes base de datos con CPs de clientes/prospectos
- Quieres segmentar mercado rápidamente
- Necesitas comparar zonas objetivamente
- Planificas campañas de prospección

**Ventajas:**
- ⭐⭐⭐ Muy fácil de usar
- ⭐⭐⭐ Datos disponibles en cualquier BD comercial
- ⭐⭐⭐ Perfecto para análisis masivo
- ⭐⭐⭐ Resultados comparables entre zonas

**Ejemplo:**
```python
from zonas_calientes import DetectorZonasCalientes

detector = DetectorZonasCalientes()

# Analizar un CP
zona = detector.analizar_zona_por_codigo_postal("35001")
print(detector.generar_reporte_texto(zona))

# Comparar múltiples CPs
cps = ["35001", "35002", "35010", "35012"]
zonas = [detector.analizar_zona_por_codigo_postal(cp) for cp in cps]
ranking = detector.comparar_zonas(zonas)

# Ver el mejor
print(f"Zona con más potencial: {ranking[0].nombre}")
print(f"Score: {ranking[0].score_total}")
```

**Scripts disponibles:**
```bash
# Ejemplo rápido (4 CPs)
python ejemplo_analisis_por_cp.py

# Análisis masivo de todos los CPs de Las Palmas
python scripts/analisis_masivo_codigos_postales.py
```

---

### ✅ Por Calle Específica (IDEAL para calles comerciales)

**Cuándo usar:**
- Análisis de calles comerciales principales
- Prospección calle por calle
- Identificar edificios antiguos en calles específicas
- Comparar diferentes calles de la ciudad

**Ventajas:**
- ⭐⭐⭐ Perfecto para calles comerciales
- ⭐⭐⭐ Análisis muy focalizado
- ⭐⭐ Útil para campañas específicas
- ⭐⭐ Control fino del radio de análisis

**Ejemplo:**
```python
from zonas_calientes import DetectorZonasCalientes

detector = DetectorZonasCalientes()

# Analizar una calle
zona = detector.analizar_zona_por_calle(
    "Calle Mayor de Triana",
    radio_metros=300
)
print(detector.generar_reporte_texto(zona))

# Comparar calles comerciales
calles = ["Calle Mayor de Triana", "Calle Mesa y López", "Calle León y Castillo"]
zonas = [detector.analizar_zona_por_calle(c) for c in calles]
ranking = detector.comparar_zonas(zonas)

print(f"Mejor calle: {ranking[0].nombre}")
```

**Script disponible:**
```bash
# Analiza 3 calles comerciales principales
python ejemplo_analisis_por_calle.py
```

---

### ✅ Por Nombre de Barrio/Zona

**Cuándo usar:**
- Conoces bien las zonas de la ciudad
- Quieres analizar barrios específicos
- Presentaciones comerciales ("zona de Vegueta")
- Análisis exploratorio inicial

**Ventajas:**
- ⭐⭐⭐ Muy intuitivo
- ⭐⭐ Coincide con percepción de clientes
- ⭐⭐ Útil para presentaciones
- ⭐⭐ Funciona sin conocer CPs

**Ejemplo:**
```python
detector = DetectorZonasCalientes()

# Analizar por nombre
zona = detector.analizar_zona_por_nombre(
    nombre_zona="Vegueta",
    ciudad="Las Palmas de Gran Canaria"
)

print(detector.generar_reporte_texto(zona))
```

**Script disponible:**
```bash
python scripts/analizar_zonas_las_palmas.py vegueta
```

---

### ⚙️ Por Direcciones Semilla (Avanzado)

**Cuándo usar:**
- Análisis alrededor de clientes existentes
- Zonas sin nombre/CP claro
- Control muy fino del área

**Ejemplo:**
```python
zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=["Calle Aconcagua", "Calle Amazonas"],
    radio_metros=400
)
```

---

## 📊 Códigos Postales de Las Palmas

| CP | Zona | Tipo |
|----|------|------|
| **35001** | Triana - Centro | Comercial/Residencial histórico |
| **35002** | Vegueta - Casco Antiguo | Histórico |
| **35003** | Arenales - Ciudad Jardín | Residencial |
| **35004** | Altavista - Escaleritas | Residencial |
| **35005** | Vegueta zona baja | Histórico |
| **35006** | Puerto - La Luz | Puerto/Comercial |
| **35007** | Zona Portuaria | Industrial/Comercial |
| **35008** | Schamann - La Paterna | Residencial |
| **35009** | Tafira | Residencial alto standing |
| **35010** | Guanarteme - Alcaravaneras | Residencial/Playa |
| **35011** | Santa Catalina - Tomás Morales | Turístico/Comercial |
| **35012** | Ciudad Alta - Miller | Residencial |
| **35013** | Escaleritas - Altavista Sur | Residencial |
| **35014** | San José - El Lasso | Residencial |
| **35015** | Jinámar - Polígonos | Industrial/Residencial |
| **35016** | Tamaraceite | Residencial |
| **35017** | San Lorenzo - Tenoya | Residencial |
| **35018** | Hoya de la Plata - Casa Ayala | Residencial |
| **35019** | Siete Palmas | Residencial moderno |

---

## 🛣️ Calles Principales de Las Palmas

### Comerciales (Alta densidad edificios)
| Calle | Zona | Características |
|-------|------|-----------------|
| **Calle Mayor de Triana** | Centro | Peatonal, comercio histórico |
| **Calle Mesa y López** | Guanarteme | Eje comercial principal |
| **Calle León y Castillo** | Centro-Puerto | Gran arteria comercial |
| **Calle Cano** | Triana | Comercial céntrica |
| **Calle Domingo Rivero** | Triana | Comercial histórica |

### Históricas (Alto potencial antigüedad)
| Calle | Zona | Características |
|-------|------|-----------------|
| **Calle Los Balcones** | Vegueta | Casco histórico |
| **Calle Obispo Codina** | Vegueta | Colonial |
| **Calle Pelota** | Vegueta | Zona antigua |
| **Calle Espíritu Santo** | Vegueta | Histórica |

### Residenciales Principales
| Calle | Zona | Características |
|-------|------|-----------------|
| **Calle Aconcagua** | Casablanca | Residencial |
| **Calle Amazonas** | Casablanca | Residencial |
| **Calle Doctor Grau Bassas** | Ciudad Jardín | Residencial alto |
| **Calle Juan de Quesada** | Centro | Residencial/Comercial |

---

## 🚀 Flujos de Trabajo Recomendados

### Flujo 1: Análisis Comercial Rápido
```bash
# 1. Analizar CPs clave (5 min)
python ejemplo_analisis_por_cp.py

# 2. Revisar ranking
cat resultados/ranking_codigos_postales.json

# 3. Exportar top edificios del mejor CP
# (Ya generado automáticamente como CSV)
```

### Flujo 2: Estudio de Mercado Completo
```bash
# 1. Análisis masivo de todos los CPs (30-60 min)
python scripts/analisis_masivo_codigos_postales.py

# 2. Revisar ranking completo
cat resultados/ranking_cps_resumen.csv

# 3. Profundizar en top 3 CPs
# (Archivos detalle_cp_XXXXX.json ya generados)
```

### Flujo 3: Análisis Alrededor de Clientes
```python
# Tienes lista de clientes con direcciones
clientes = [
    {"nombre": "Cliente A", "direccion": "Calle León y Castillo 100"},
    {"nombre": "Cliente B", "direccion": "Calle Triana 50"}
]

detector = DetectorZonasCalientes()

for cliente in clientes:
    zona = detector.analizar_zona_por_direcciones(
        direcciones_semilla=[cliente["direccion"]],
        radio_metros=300
    )

    print(f"\n{cliente['nombre']}: {zona.edificios_muy_antiguos} edificios prioritarios")
    detector.exportar_zona_csv(
        zona,
        f"resultados/oportunidades_{cliente['nombre']}.csv"
    )
```

---

## 📈 Interpretación de Resultados

### Score Total
- **> 100**: Zona MUY caliente (alta prioridad)
- **50-100**: Zona caliente (prioridad media)
- **< 50**: Zona templada (menor prioridad)

### Densidad de Oportunidades
- **> 2.5**: Concentración ALTA (muchos edificios antiguos)
- **1.5-2.5**: Concentración MEDIA
- **< 1.5**: Concentración BAJA

### % Muy Antiguos (>50 años)
- **> 60%**: Zona prioritaria para modernización
- **40-60%**: Zona interesante
- **< 40%**: Zona moderna (menor potencial)

---

## 💡 Casos de Uso Reales

### Caso 1: Priorizar Zonas para Campaña
```python
# Analizar todos los CPs
cps_lpgc = [f"350{i:02d}" for i in range(1, 20)]  # 35001-35019

zonas = []
for cp in cps_lpgc:
    zona = detector.analizar_zona_por_codigo_postal(cp)
    zonas.append(zona)

# Filtrar solo zonas calientes
zonas_calientes = [z for z in zonas if z.score_total > 80]

print(f"Zonas prioritarias: {len(zonas_calientes)}")
for z in sorted(zonas_calientes, key=lambda x: x.score_total, reverse=True):
    print(f"  • {z.nombre}: {z.score_total:.0f} puntos")
```

### Caso 2: Exportar Leads a CRM
```python
# Analizar CP objetivo
zona = detector.analizar_zona_por_codigo_postal("35002")  # Vegueta

# Filtrar edificios muy antiguos
leads = [e for e in zona.edificios if e.antiguedad and e.antiguedad > 50]

# Exportar para comercial
import csv
with open('leads_vegueta.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Dirección', 'Año', 'Antigüedad', 'Prioridad', 'GPS'])

    for edificio in sorted(leads, key=lambda x: x.antiguedad, reverse=True):
        writer.writerow([
            edificio.direccion,
            edificio.anio_construccion,
            edificio.antiguedad,
            "ALTA" if edificio.antiguedad > 60 else "MEDIA",
            f"{edificio.latitud},{edificio.longitud}"
        ])

print(f"{len(leads)} leads exportados a leads_vegueta.csv")
```

### Caso 3: Dashboard de KPIs
```python
# Analizar zona asignada a comercial
zona = detector.analizar_zona_por_codigo_postal("35001")

# KPIs para dashboard
kpis = {
    'zona': zona.nombre,
    'total_edificios': zona.total_edificios,
    'oportunidades_altas': zona.edificios_muy_antiguos,
    'oportunidades_medias': zona.edificios_antiguos,
    'tasa_conversion_esperada': 0.15,  # 15%
    'potencial_clientes': int(zona.edificios_muy_antiguos * 0.15)
}

print("KPIs Comerciales:")
for k, v in kpis.items():
    print(f"  {k}: {v}")
```

---

## ⏱️ Tiempos de Ejecución

| Operación | Tiempo | Edificios |
|-----------|--------|-----------|
| 1 código postal | 3-5 min | ~15-30 |
| 4 códigos postales | 15-20 min | ~60-120 |
| 19 CPs completo | 30-60 min | ~300-500 |
| Zona por nombre | 3-5 min | ~15-30 |
| Direcciones (3) | 5-8 min | ~25-50 |

*Tiempos con grid_size=5, limitados por rate limiting de APIs públicas*

---

## 🎓 Tips y Mejores Prácticas

### ✅ DO
- Usar código postal para análisis masivo y comparaciones
- Usar nombre de barrio para presentaciones y análisis exploratorio
- Exportar siempre a CSV para integración con CRM
- Mantener grid_size=5 para equilibrio velocidad/precisión
- Analizar en horarios de bajo uso para mejor rendimiento

### ❌ DON'T
- No ejecutar análisis masivos repetidamente (cachear resultados)
- No usar grid_size > 7 (muy lento, poco beneficio)
- No ignorar rate limiting (respetar las APIs públicas)
- No analizar la misma zona múltiples veces sin necesidad

---

## 📞 Resumen Ejecutivo

**Para análisis comercial estándar:**
```bash
python ejemplo_analisis_por_cp.py
```

**Para estudio completo de mercado:**
```bash
python scripts/analisis_masivo_codigos_postales.py
```

**Para análisis personalizado:**
```python
from zonas_calientes import DetectorZonasCalientes
detector = DetectorZonasCalientes()

# Por código postal
zona = detector.analizar_zona_por_codigo_postal("35001")

# Por nombre de zona
zona = detector.analizar_zona_por_nombre("Vegueta")

# Por direcciones
zona = detector.analizar_zona_por_direcciones(["Calle Triana"])

# Generar reporte
print(detector.generar_reporte_texto(zona))
```

---

**¿Necesitas ayuda?** Revisa `docs/ZONAS_CALIENTES_README.md` para documentación completa.
