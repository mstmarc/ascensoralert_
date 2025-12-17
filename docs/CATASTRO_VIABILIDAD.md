# Evaluación de Viabilidad: Integración con Catastro

## 🎯 Objetivo
Obtener el año de construcción de edificios mediante coordenadas geográficas o zona, integrando los servicios web del Catastro español.

---

## 📋 Servicios Disponibles de Catastro

### 1. **API REST de Consulta de Coordenadas (OVC)**
- **Endpoint Base**: `http://ovc.catastro.meh.es/ovcservweb/`
- **Método**: Consulta por coordenadas (GET)
- **Acceso**: Libre, sin autenticación
- **Formato**: XML/JSON

#### Ejemplo de consulta:
```
GET http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_CPMRC
Parámetros:
  - SRS: Sistema de referencia (EPSG:4326 para WGS84)
  - Coordenada_X: Longitud
  - Coordenada_Y: Latitud
```

**Respuesta incluye**:
- Referencia catastral
- Dirección
- Uso del inmueble
- **Año de construcción** (en el campo `bico/bi/@ant` o `ant`)

---

### 2. **Servicio SOAP DNPRC (Datos No Protegidos por Referencia Catastral)**
- **Endpoint**: `http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx`
- **Acceso**: Libre
- **Formato**: XML (SOAP)

Permite consulta detallada con referencia catastral obtenida del servicio anterior.

---

### 3. **WFS INSPIRE Cadastral Parcels**
- **Endpoint**: `http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx`
- **Estándar**: OGC WFS 2.0
- **Acceso**: Libre
- **Formato**: GML

Consulta vectorial de parcelas catastrales con información completa.

---

## ✅ Viabilidad Técnica

### **ALTA** ✅

**Razones**:
1. **APIs públicas y gratuitas**: No requiere registro ni autenticación
2. **Documentación disponible**: En la Sede Electrónica del Catastro
3. **Estándares abiertos**: REST, SOAP, WFS
4. **Datos completos**: Incluyen año de construcción
5. **Cobertura total**: Todo el territorio español

---

## 🔧 Implementación Propuesta

### Opción 1: API REST OVC (Recomendada)
**Pros**:
- Más simple y moderna
- Respuesta ligera
- Fácil parsing (XML/JSON)
- Consulta directa por coordenadas

**Contras**:
- Documentación menos formal
- Límite de peticiones no documentado

### Opción 2: WFS INSPIRE
**Pros**:
- Estándar internacional
- Más robusto
- Mejor para consultas masivas

**Contras**:
- Más complejo de implementar
- Respuestas más pesadas (GML)

---

## 📦 Stack Tecnológico

```python
# Librerías necesarias
requests          # HTTP requests
xmltodict         # XML parsing (para respuestas OVC)
owslib            # WFS client (si se usa WFS)
```

---

## 🚀 Flujo de Implementación

```
1. Coordenadas (lat, lon) del ascensor
   ↓
2. Consulta API OVC por coordenadas
   ↓
3. Obtener referencia catastral
   ↓
4. Parsear XML y extraer año construcción
   ↓
5. Almacenar en BD (campo nuevo: año_construccion)
```

---

## ⚠️ Consideraciones

### Limitaciones:
1. **Rate limiting**: Catastro puede limitar peticiones masivas
2. **Precisión**: Coordenadas deben ser precisas (edificio, no zona amplia)
3. **Disponibilidad**: Servicio público, sin SLA garantizado
4. **Datos desactualizados**: Info catastral puede tener retraso

### Recomendaciones:
- ✅ Implementar **caché local** (reducir peticiones)
- ✅ **Retry logic** con exponential backoff
- ✅ **Logging** de consultas fallidas
- ✅ **Validación** de coordenadas antes de consultar
- ✅ Consultar solo ascensores sin año de construcción

---

## 📊 Casos de Uso en AscensorAlert

### Caso 1: Completar datos existentes
```python
# Para ascensores sin año_construccion en BD
ascensores_sin_anio = obtener_ascensores_sin_anio()
for ascensor in ascensores_sin_anio:
    anio = consultar_catastro(ascensor.latitud, ascensor.longitud)
    if anio:
        actualizar_ascensor(ascensor.id, anio_construccion=anio)
```

### Caso 2: Validación al crear ascensor
```python
# Al registrar nuevo ascensor
if not año_proporcionado:
    año = consultar_catastro(latitud, longitud)
    ascensor.año_construccion = año
```

---

## 💰 Costes

- **0 €** - Servicio público gratuito
- **Desarrollo**: ~8-16 horas
  - Investigación y pruebas: 3h
  - Implementación servicio: 4h
  - Integración con BD: 2h
  - Testing y ajustes: 3h
  - Documentación: 2h

---

## 📈 Impacto

### Beneficios:
- ✅ **Enriquecimiento automático** de datos
- ✅ **Mejor análisis predictivo** (edad del edificio correlaciona con fallos)
- ✅ **Priorización de inspecciones** (edificios antiguos)
- ✅ **Valor añadido** para el producto

### Métricas esperadas:
- Completar ~80-90% de ascensores sin año construcción
- Reducir entrada manual de datos
- Mejorar precisión de alertas predictivas

---

## 🎬 Conclusión

**RECOMENDACIÓN: ✅ VIABLE Y RECOMENDADO**

La integración con Catastro es:
- Técnicamente factible
- Bajo coste (gratuito)
- Alto valor añadido
- Baja complejidad técnica

**Próximos pasos sugeridos**:
1. Crear módulo `catastro_service.py`
2. Implementar función `obtener_anio_construccion(lat, lon)`
3. Agregar campo `año_construccion` a tabla ascensores (si no existe)
4. Crear script de migración para datos existentes
5. Integrar en flujo de creación de ascensores

---

## 📚 Referencias

- [Sede Electrónica del Catastro](https://www.sedecatastro.gob.es/)
- [Servicios Web del Catastro](https://www.catastro.hacienda.gob.es/ayuda/servicios_web.htm)
- Documentación OVC: http://ovc.catastro.meh.es/ovcservweb/
- INSPIRE WFS: http://www.catastro.meh.es/inspire/wfs/CP.aspx

---

**Fecha**: 2025-12-16
**Estado**: Evaluación completada
**Decisión requerida**: Aprobación para implementación
