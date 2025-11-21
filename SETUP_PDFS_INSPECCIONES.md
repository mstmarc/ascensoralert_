# Setup: PDFs en Inspecciones

## Resumen

Esta funcionalidad permite subir y gestionar dos tipos de PDFs por cada inspección:
- **Acta de inspección**: Documento oficial de la inspección
- **Presupuesto**: Presupuesto de reparaciones

Los PDFs son accesibles desde la vista de detalle de cada inspección (`/inspecciones/ver/{id}`).

## Pasos de Instalación

### 1. Ejecutar Migración de Base de Datos

Ejecuta el siguiente script SQL en el editor SQL de Supabase:

```bash
database/agregar_pdfs_inspecciones.sql
```

Este script añade dos columnas a la tabla `inspecciones`:
- `acta_pdf_url` (TEXT)
- `presupuesto_pdf_url` (TEXT)

### 2. Crear Bucket de Storage en Supabase

1. Ve a tu proyecto en Supabase: https://app.supabase.com
2. Menú lateral → **Storage**
3. Click en **"Create a new bucket"**
4. Configuración:
   - **Name**: `inspecciones-pdfs`
   - **Public bucket**: ✅ **ACTIVADO** (importante!)
   - **File size limit**: 50 MB
   - **Allowed MIME types**: `application/pdf`
5. Click **"Create bucket"**

### 3. Configurar Políticas RLS de Storage

Ejecuta el siguiente script SQL en el editor SQL de Supabase:

```bash
database/configurar_storage_rls_policies.sql
```

Este script configura las políticas de acceso:
- **Lectura pública**: Cualquiera puede descargar PDFs
- **Escritura autenticada**: Solo usuarios autenticados pueden subir/modificar

### 4. Verificar la Configuración

#### Verificar Base de Datos:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'inspecciones'
  AND column_name IN ('acta_pdf_url', 'presupuesto_pdf_url');
```

Deberías ver dos columnas de tipo TEXT.

#### Verificar Storage:
1. Ve a **Storage** → **inspecciones-pdfs**
2. Verifica que esté marcado como **Public**
3. Ve a **Policies** y verifica que hay 4 políticas activas

### 5. Desplegar Cambios de Código

Los cambios ya están implementados en:
- `app.py` (líneas 4136-4286): Rutas Flask para upload
- `templates/ver_inspeccion.html` (líneas 326-380): UI de PDFs

No se requiere ninguna acción adicional de código.

## Uso

### Subir un PDF

1. Ve a la vista de una inspección: `/inspecciones/ver/{id}`
2. Busca la sección **"Documentos PDF"**
3. Selecciona el archivo PDF (acta o presupuesto)
4. Click en **"Subir Acta"** o **"Subir Presupuesto"**

### Descargar un PDF

1. En la misma vista, si hay un PDF subido, verás un botón **"📥 Descargar"**
2. Click en el botón para abrir/descargar el PDF

### Reemplazar un PDF

1. Si ya existe un PDF, verás un formulario de **"Reemplazar"**
2. Selecciona el nuevo archivo PDF
3. Click en **"Actualizar Acta"** o **"Actualizar Presupuesto"**
4. El PDF anterior se eliminará automáticamente

## Estructura de Archivos

Los PDFs se almacenan en Supabase Storage con la siguiente estructura:

```
inspecciones-pdfs/
└── inspecciones/
    ├── inspeccion_1_acta.pdf
    ├── inspeccion_1_presupuesto.pdf
    ├── inspeccion_2_acta.pdf
    ├── inspeccion_2_presupuesto.pdf
    └── ...
```

## URLs Públicas

Las URLs siguen este formato:

```
https://hvkifqguxsgegzaxwcmj.supabase.co/storage/v1/object/public/inspecciones-pdfs/inspecciones/inspeccion_{id}_acta.pdf
```

## Características

✅ **Validación de formato**: Solo acepta archivos `.pdf`
✅ **Reemplazo automático**: Al subir un nuevo PDF, el anterior se elimina
✅ **URLs públicas**: Los PDFs son accesibles mediante URL directa
✅ **Permisos**: Solo usuarios con permiso de escritura en inspecciones pueden subir
✅ **Feedback visual**: Mensajes de éxito/error después de cada operación

## Limitaciones

- **Tamaño máximo**: 50 MB por archivo (configurable)
- **Formato**: Solo archivos PDF
- **Permisos**: Se requiere login y permisos de inspecciones

## Troubleshooting

### Error: "Bucket not found"
- Verifica que el bucket `inspecciones-pdfs` esté creado en Supabase Storage
- Verifica el nombre exacto (sin espacios ni mayúsculas)

### Error: "Policy violation"
- Ejecuta el script `configurar_storage_rls_policies.sql`
- Verifica que el bucket esté marcado como **Public**

### Los PDFs no se ven
- Verifica que las columnas `acta_pdf_url` y `presupuesto_pdf_url` existan en la tabla
- Ejecuta el script `agregar_pdfs_inspecciones.sql`

### Error al subir archivo
- Verifica que el archivo sea un PDF válido
- Verifica que no exceda 50 MB
- Verifica que el usuario tenga permisos de escritura en inspecciones

## Documentación Adicional

- `database/configurar_supabase_storage.md`: Guía detallada de configuración
- `database/agregar_pdfs_inspecciones.sql`: Migración de base de datos
- `database/configurar_storage_rls_policies.sql`: Políticas de acceso
- `app.py` (líneas 4136-4286): Implementación Flask
- `templates/ver_inspeccion.html` (líneas 326-380): UI de PDFs
