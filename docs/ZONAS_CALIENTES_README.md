# Módulo de Detección de Zonas Calientes

Sistema de análisis geoespacial para identificar áreas con alto potencial de modernización de ascensores, utilizando datos del Catastro español como proxy de antigüedad de edificios.

---

## 🎯 Objetivo Funcional

Detectar y priorizar zonas geográficas (barrios, distritos) donde hay mayor concentración de edificios antiguos que probablemente requieran modernización de ascensores, permitiendo campañas de prospección comercial más efectivas.

---

## 📦 Componentes del Sistema

### 1. **catastro_service.py**
Servicio de integración con la API del Catastro español (OVC).

**Funcionalidades:**
- Consulta de datos catastrales por coordenadas GPS
- Extracción de año de construcción de edificios
- Obtención de datos de uso, superficie y referencia catastral
- Escaneo de áreas mediante cuadrículas
- Sistema de reintentos con exponential backoff

**Métodos principales:**
```python
catastro = CatastroService()

# Consulta por coordenadas
datos = catastro.obtener_datos_por_coordenadas(latitud=28.124167, longitud=-15.437778)

# Escaneo de área
inmuebles = catastro.obtener_datos_area(
    lat_centro=28.124167,
    lon_centro=-15.437778,
    radio_metros=500,
    grid_size=5
)
```

---

### 2. **geocoding_service.py**
Servicio de geocodificación usando Nominatim (OpenStreetMap).

**Funcionalidades:**
- Conversión de direcciones a coordenadas GPS
- Geocodificación de zonas y barrios
- Obtención de bounding boxes
- Geocodificación inversa (coordenadas → dirección)

**Métodos principales:**
```python
geocoding = GeocodingService()

# Geocodificar dirección
coords = geocoding.geocodificar_direccion(
    "Calle Mayor de Triana",
    ciudad="Las Palmas de Gran Canaria"
)

# Geocodificar zona
zona_data = geocoding.geocodificar_zona(
    "Vegueta",
    ciudad="Las Palmas de Gran Canaria"
)
```

---

### 3. **zonas_calientes.py**
Módulo principal de análisis y detección de zonas calientes.

**Clases:**

#### `EdificioCandidato`
Representa un edificio candidato a modernización con:
- Referencia catastral
- Dirección y coordenadas
- Año de construcción y antigüedad
- Score de modernización
- Categoría de antigüedad

#### `ZonaCaliente`
Representa una zona analizada con:
- Estadísticas agregadas (total edificios, distribución por antigüedad)
- Lista de edificios candidatos
- Score total y densidad de oportunidades
- Distribución por década de construcción

#### `DetectorZonasCalientes`
Motor de análisis principal.

**Métodos principales:**
```python
detector = DetectorZonasCalientes()

# Analizar por direcciones semilla
zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=["Calle Aconcagua", "Calle Amazonas"],
    ciudad="Las Palmas de Gran Canaria",
    radio_metros=500
)

# Analizar por nombre de zona
zona = detector.analizar_zona_por_nombre(
    nombre_zona="Vegueta",
    ciudad="Las Palmas de Gran Canaria"
)

# Comparar múltiples zonas
zonas_ordenadas = detector.comparar_zonas([zona1, zona2, zona3])
```

---

## 🚀 Uso del Sistema

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

La única dependencia nueva agregada es:
- `xmltodict>=0.13.0` - Para parsear respuestas XML del Catastro

---

### Ejemplo Básico

```python
from zonas_calientes import DetectorZonasCalientes

# Inicializar detector
detector = DetectorZonasCalientes()

# Analizar barrio Casablanca III
zona = detector.analizar_zona_por_direcciones(
    direcciones_semilla=[
        "Calle Aconcagua",
        "Calle Amazonas",
        "Calle Himalaya"
    ],
    ciudad="Las Palmas de Gran Canaria",
    radio_metros=400,
    solo_residencial=True
)

# Generar reporte
print(detector.generar_reporte_texto(zona))

# Exportar resultados
detector.exportar_zona_json(zona, 'resultados/analisis.json')
detector.exportar_zona_csv(zona, 'resultados/edificios.csv')
```

---

### Script de Análisis de Las Palmas

Se incluye un script completo con ejemplos para Las Palmas de Gran Canaria:

```bash
# Ejecutar menú interactivo
python scripts/analizar_zonas_las_palmas.py

# O ejecutar análisis específico
python scripts/analizar_zonas_las_palmas.py casablanca
python scripts/analizar_zonas_las_palmas.py vegueta
python scripts/analizar_zonas_las_palmas.py triana
python scripts/analizar_zonas_las_palmas.py comparar
```

**Zonas preconfiguradas:**
1. **Casablanca III** - Análisis por direcciones semilla
2. **Vegueta** - Barrio histórico (análisis por nombre)
3. **Triana** - Zona comercial céntrica
4. **Comparación múltiple** - Compara Ciudad Jardín, Miller Bajo, Schamann y Alcaravaneras

---

## 📊 Sistema de Scoring

### Categorización por Antigüedad

| Categoría | Antigüedad | Peso | Descripción |
|-----------|-----------|------|-------------|
| **Muy Antiguo** | >50 años | 3.0 | Máxima prioridad |
| **Antiguo** | 30-50 años | 2.0 | Alta prioridad |
| **Moderno** | <30 años | 0.5 | Baja prioridad |

### Métricas de Zona

- **Score Total**: Suma de scores de todos los edificios
- **Densidad de Oportunidades**: Score promedio por edificio (indica concentración)
- **Distribución por Década**: Histograma de construcción

---

## 📁 Formatos de Exportación

### JSON
Archivo completo con toda la información:
```json
{
  "nombre": "Vegueta",
  "centro": {
    "latitud": 28.100167,
    "longitud": -15.418778
  },
  "resumen": {
    "total_edificios": 45,
    "edificios_muy_antiguos": 23,
    "edificios_antiguos": 15,
    "edificios_modernos": 7,
    "densidad_oportunidades": 2.31,
    "score_total": 104.0,
    "stats_por_decada": {...}
  },
  "edificios": [...]
}
```

### CSV
Tabla con datos de edificios para análisis en Excel:
```csv
Referencia Catastral,Dirección,Latitud,Longitud,Año Construcción,Antigüedad (años),Categoría,Score Modernización,Uso,Superficie (m²)
3578901VK1237N0001,Calle Mayor 45,28.100,-15.419,1965,60,Muy antiguo (>50 años),3.0,Residencial,250.5
```

---

## 🔧 Parámetros de Configuración

### Radio de búsqueda
- **Recomendado**: 300-500 metros para zonas urbanas densas
- **Mayor radio**: 700-1000 metros para zonas dispersas

### Grid Size
Número de puntos de muestreo en la cuadrícula:
- **3x3**: Muestreo rápido (9 puntos)
- **5x5**: Estándar (25 puntos) - **RECOMENDADO**
- **7x7**: Exhaustivo (49 puntos) - Para zonas pequeñas

**Trade-off**: Mayor grid_size = mayor cobertura pero más tiempo de ejecución

### Solo Residencial
- `True`: Filtra solo edificios de uso residencial (recomendado)
- `False`: Incluye todo tipo de inmuebles

---

## ⚙️ Consideraciones Técnicas

### Rate Limiting

**Catastro (OVC):**
- Servicio público sin límite documentado
- Implementado delay de 0.5s entre peticiones
- Sistema de reintentos con exponential backoff

**Nominatim (OpenStreetMap):**
- **OBLIGATORIO**: Máximo 1 petición por segundo
- Implementado delay de 1s automático
- Requiere User-Agent válido

### Precisión de Datos

- **Cobertura**: ~80-90% de edificios tienen año de construcción en Catastro
- **Precisión geoespacial**: Depende de la calidad de geocodificación
- **Datos desactualizados**: Catastro puede tener retraso de 1-2 años

### Rendimiento

Tiempos aproximados (con grid_size=5, radio=500m):
- Análisis por direcciones (3 direcciones): **~5-8 minutos**
- Análisis por zona: **~3-5 minutos**
- Comparación de 4 zonas: **~15-20 minutos**

**Cuellos de botella:**
- Rate limiting de APIs externas
- Tiempo de respuesta del Catastro (variable)

---

## 🎓 Casos de Uso

### 1. Priorización de Campañas Comerciales
Identificar barrios con mayor concentración de edificios antiguos para campañas de modernización.

### 2. Análisis de Mercado
Evaluar potencial de mercado en diferentes zonas de la ciudad.

### 3. Planificación de Recursos
Asignar equipos comerciales a zonas con mayor densidad de oportunidades.

### 4. Estudios de Viabilidad
Analizar rentabilidad de abrir oficinas en nuevas zonas.

---

## 🐛 Troubleshooting

### Error: "No se encontraron resultados para la dirección"
**Causa**: Dirección mal escrita o no reconocida por OpenStreetMap.
**Solución**: Verificar ortografía o usar análisis por nombre de zona.

### Error: "Consulta_CPMRC" timeout
**Causa**: Servicio de Catastro temporalmente lento o caído.
**Solución**: El sistema reintentará automáticamente 3 veces.

### Pocos edificios encontrados
**Causa**: Grid size muy pequeño o radio insuficiente.
**Solución**: Aumentar grid_size a 6-7 o radio a 700-1000m.

### Muchos edificios sin año de construcción
**Causa**: Zona con datos incompletos en Catastro.
**Solución**: Normal en algunas zonas. Score se basa solo en edificios con datos.

---

## 📈 Mejoras Futuras

### Corto Plazo
- [ ] Caché local de consultas al Catastro (reducir peticiones)
- [ ] Exportación a formato GeoJSON para visualización en mapas
- [ ] Filtros adicionales (número de plantas, superficie mínima)

### Medio Plazo
- [ ] Integración con Google Maps API (mejor geocodificación)
- [ ] Clustering automático de edificios cercanos
- [ ] Generación de mapas de calor (heatmaps)

### Largo Plazo
- [ ] Machine Learning para predecir probabilidad de conversión
- [ ] Integración directa con CRM para seguimiento
- [ ] Dashboard web interactivo

---

## 🔒 Privacidad y Legal

- ✅ **Datos públicos**: Toda la información proviene de fuentes públicas (Catastro, OSM)
- ✅ **Sin GDPR issues**: No se recopilan datos personales
- ✅ **Uso comercial**: Permitido según términos de uso de Catastro y OSM
- ⚠️ **Rate limiting**: Respetar límites de peticiones para uso ético

---

## 📚 Referencias

- [Sede Electrónica del Catastro](https://www.sedecatastro.gob.es/)
- [Servicios Web OVC](http://ovc.catastro.meh.es/)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)
- [OpenStreetMap Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)

---

## 👥 Soporte

Para preguntas o issues:
1. Revisar este README y el documento de evaluación de viabilidad
2. Verificar logs del sistema (`logging` configurado en modo INFO)
3. Contactar al equipo de desarrollo con detalles del error

---

**Versión**: 1.0
**Fecha**: Diciembre 2025
**Autor**: Sistema AscensorAlert
**Licencia**: Uso interno
