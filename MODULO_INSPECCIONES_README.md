# 📋 Módulo de Gestión de Inspecciones (IPOs) - AscensorAlert

## 🎯 Descripción

Módulo completo para la gestión de inspecciones periódicas de ascensores (IPOs) y el seguimiento de subsanación de defectos, con control específico de materiales especiales (cortinas fotoeléctricas y pesacargas) según normativa ITC-AEM1 julio 2024.

## ✨ Funcionalidades Implementadas

### 1. **Gestión de Inspecciones**
- ✅ Registro completo de actas de inspección (IPO)
- ✅ Información del titular, instalación y características técnicas del ascensor
- ✅ Relación con OCAs (Organismos de Control Autorizados)
- ✅ Estados de gestión (Presupuesto y Trabajo)
- ✅ Formularios de creación y edición
- ✅ Vista detallada con toda la información

### 2. **Gestión de Defectos**
- ✅ Registro de defectos detectados (DL, DG, DMG)
- ✅ Cálculo automático de fechas límite
- ✅ Marcado de cortinas y pesacargas (ITC-AEM1)
- ✅ Sistema de alertas por urgencia (vencidos, urgentes, próximos)
- ✅ Estado de subsanación

### 3. **Materiales Especiales (Cortinas y Pesacargas)**
- ✅ Registro manual o automático desde defectos
- ✅ Seguimiento de estados (PENDIENTE → PEDIDO → RECIBIDO → INSTALADO)
- ✅ Alertas de plazos próximos a vencer
- ✅ Vista independiente con filtros

### 4. **Gestión de OCAs**
- ✅ Catálogo de organismos de control
- ✅ Datos de contacto
- ✅ Contador de inspecciones por OCA

### 5. **Dashboard e Informes**
- ✅ Vista principal con estadísticas
- ✅ Alertas críticas, urgentes y próximas
- ✅ Código de colores por urgencia
- ✅ Filtros y búsquedas

## 📂 Estructura de Archivos

### Backend (app.py)
```
app.py
├── Rutas de Dashboard de Inspecciones (línea ~3550)
├── Rutas CRUD de Inspecciones (línea ~3659-3982)
├── Rutas de Defectos (línea ~3987-4133)
├── Rutas de Materiales Especiales (línea ~4139-4297)
└── Rutas de OCAs (línea ~4303-4439)
```

### Frontend (templates/)
```
templates/
├── inspecciones_dashboard.html    # Dashboard principal
├── nueva_inspeccion.html          # Formulario de nueva inspección
├── editar_inspeccion.html         # Formulario de edición
├── ver_inspeccion.html            # Vista detallada con defectos
├── nuevo_defecto.html             # Formulario de nuevo defecto
├── materiales_especiales.html     # Vista de cortinas/pesacargas
├── nuevo_material_especial.html   # Formulario de material
├── lista_ocas.html                # Lista de OCAs
├── nuevo_oca.html                 # Formulario de nuevo OCA
└── editar_oca.html                # Formulario de edición OCA
```

### Base de Datos
```
database/
└── inspecciones_schema.sql        # Script SQL completo
```

### Scripts
```
scripts/
└── importar_excel_inspecciones.py # Importación desde Excel
```

### Navegación
```
static/
└── sidebar.js                      # Menú lateral actualizado
```

## 🗄️ Esquema de Base de Datos

### Tablas Creadas

1. **`ocas`** - Organismos de Control Autorizados
   - Campos: nombre, contacto, email, teléfono, dirección, activo

2. **`inspecciones`** - Actas de IPO
   - Identificación: RAE, número certificado, fecha inspección
   - Titular: nombre, NIF, dirección, municipio
   - Características técnicas: tipo, capacidad, carga, paradas, etc.
   - Estados: estado_presupuesto, estado_trabajo
   - Fechas de seguimiento: envío, respuesta, inicio, fin

3. **`defectos_inspeccion`** - Defectos detectados
   - Defecto: código, descripción, calificación (DL/DG/DMG)
   - Plazos: plazo_meses, fecha_limite
   - Marcas: es_cortina, es_pesacarga
   - Estado: PENDIENTE / SUBSANADO

4. **`materiales_especiales`** - Cortinas y Pesacargas
   - Tipo: CORTINA / PESACARGA
   - Cliente, dirección, cantidad
   - Estados: PENDIENTE → PEDIDO → RECIBIDO → INSTALADO
   - Fechas de seguimiento

### Vistas Creadas

- `v_inspecciones_completas` - Inspecciones con info de OCA y contadores
- `v_defectos_con_urgencia` - Defectos con nivel de urgencia calculado
- `v_materiales_con_urgencia` - Materiales con urgencia

## 🚀 Instrucciones de Despliegue

### Paso 1: Ejecutar Script SQL en Supabase

```bash
# 1. Acceder a Supabase Dashboard
# 2. Ir a SQL Editor
# 3. Copiar y ejecutar el contenido de database/inspecciones_schema.sql
```

El script creará automáticamente:
- ✅ Las 4 tablas principales
- ✅ Todos los índices
- ✅ Las 3 vistas de consulta
- ✅ Los triggers para updated_at
- ✅ Los OCAs iniciales (Eurocontrol, Applus, etc.)

### Paso 2: Desplegar el Código

El código ya está integrado en `app.py` y los templates están en `templates/`.

```bash
# Si estás en Render, simplemente haz:
git add .
git commit -m "Añade módulo de gestión de inspecciones (IPOs)"
git push origin claude/inspection-management-module-01Asg4yWY4JEzVASpue5CbiV
```

Render detectará el cambio y desplegará automáticamente.

### Paso 3: Verificar Dependencias

Las dependencias ya existen en el proyecto:
- ✅ `flask`
- ✅ `requests`
- ✅ `python-dateutil` (para el script de importación)
- ✅ `openpyxl` (para el script de importación)

Si falta alguna, añadirla a `requirements.txt`:
```
openpyxl==3.1.2
python-dateutil==2.8.2
```

### Paso 4: Importar Datos Existentes (Opcional)

Si tienes el archivo `FICHERO_IPO_GLOBAL.xlsx`:

```bash
# Asegurarse de tener SUPABASE_KEY configurada
export SUPABASE_KEY="tu_clave_de_supabase"

# Ejecutar el script de importación
python scripts/importar_excel_inspecciones.py ruta/al/FICHERO_IPO_GLOBAL.xlsx
```

El script importará:
- 📋 Hoja principal → tabla `inspecciones`
- 🪟 Hoja CORTINAS → tabla `materiales_especiales` (tipo CORTINA)
- ⚖️ Hoja PESACARGAS → tabla `materiales_especiales` (tipo PESACARGA)

## 🎨 Consistencia Visual

El módulo sigue **exactamente** los mismos patrones visuales de AscensorAlert:

- ✅ Color corporativo: `#366092` (#003366 para títulos)
- ✅ Fuente: Montserrat
- ✅ Componentes: cards, tablas, formularios con los mismos estilos
- ✅ Sistema de badges y alertas
- ✅ Responsive design
- ✅ Flash messages
- ✅ Sidebar integrado

## 📱 Navegación

El menú lateral (`sidebar.js`) ha sido actualizado con el nuevo bloque:

```
📋 Inspecciones (IPOs)
   Cortinas y Pesacargas
   OCAs
```

## 🔐 Separación de Datos

**IMPORTANTE:** Este módulo es completamente independiente del CRM comercial.

- ❌ NO comparte tablas con clientes/leads/equipos
- ❌ NO tiene relaciones con oportunidades/visitas
- ✅ Son bases de datos conceptualmente separadas
- ✅ Conviven en la misma app sin interferir

## 📊 Flujo de Trabajo Típico

1. **Recibir Acta de Inspección**
   - Ir a `/inspecciones/nueva`
   - Completar datos del acta
   - Guardar inspección

2. **Añadir Defectos**
   - En la vista de inspección, clic en "+ Añadir Defecto"
   - Completar código, descripción, calificación
   - Marcar si es cortina o pesacarga
   - El sistema calcula automáticamente la fecha límite
   - Si es cortina/pesacarga, se crea automáticamente en materiales especiales

3. **Gestión de Presupuesto**
   - En la vista de inspección, cambiar estado del presupuesto
   - Estados: PENDIENTE → PREPARANDO → ENVIADO → ACEPTADO/RECHAZADO

4. **Ejecución de Trabajos**
   - Cambiar estado de trabajo: PENDIENTE → EN_EJECUCION → COMPLETADO
   - Marcar defectos como subsanados

5. **Seguimiento de Materiales Especiales**
   - Ir a `/materiales_especiales`
   - Ver alertas de plazos próximos
   - Cambiar estados: PENDIENTE → PEDIDO → RECIBIDO → INSTALADO

## 🎯 Criterios de Éxito

Verifica que el módulo funciona correctamente:

- [ ] Puedes crear una inspección completa en 2-3 minutos
- [ ] El dashboard muestra alertas de plazos próximos a vencer
- [ ] Los estados de presupuesto y trabajo se cambian fácilmente
- [ ] Las cortinas y pesacargas se controlan por separado
- [ ] El sistema calcula automáticamente fechas límite
- [ ] Los colores de urgencia se muestran correctamente (rojo/amarillo/verde)
- [ ] El menú de inspecciones aparece en el sidebar
- [ ] La interfaz se ve igual que el resto de AscensorAlert

## 🆘 Soporte

Para preguntas o problemas:
1. Verificar que el SQL se ejecutó correctamente en Supabase
2. Verificar que las variables de entorno están configuradas
3. Revisar los logs de la aplicación en Render
4. Verificar que no hay conflictos en las rutas

## 📝 Notas Técnicas

### Estados de Presupuesto
- `PENDIENTE`: Acaba de llegar, no se ha hecho presupuesto
- `PREPARANDO`: Se está preparando (esperando datos de proveedores)
- `ENVIADO`: Presupuesto enviado al cliente, esperando respuesta
- `ACEPTADO`: Cliente aceptó, hay que ejecutar
- `RECHAZADO`: Cliente rechazó

### Estados de Trabajo
- `PENDIENTE`: Aún no empezado
- `EN_EJECUCION`: Se están realizando las reparaciones
- `COMPLETADO`: Terminado, defectos subsanados

### Niveles de Urgencia (calculados automáticamente)
- **VENCIDO** (rojo): Fecha límite pasada
- **URGENTE** (amarillo): ≤ 15 días
- **PROXIMO** (amarillo claro): 16-30 días
- **NORMAL** (verde): > 30 días
- **COMPLETADO** (verde): Subsanado o instalado

---

**Desarrollado para Fedes Ascensores**
Módulo de Gestión de Inspecciones (IPOs)
Versión 1.0 - 2025
