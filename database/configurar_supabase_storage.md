# Configuración de Supabase Storage para PDFs de Inspecciones

## Fecha: 2025-11-21

Este documento explica cómo configurar Supabase Storage para permitir la subida y descarga de PDFs de inspecciones (actas y presupuestos).

## Pasos de Configuración

### 1. Crear el Bucket de Storage

1. Ve a tu proyecto en Supabase (https://app.supabase.com)
2. En el menú lateral, selecciona **Storage**
3. Haz clic en **"Create a new bucket"**
4. Configura el bucket:
   - **Name**: `inspecciones-pdfs`
   - **Public bucket**: ✅ ACTIVADO (necesario para URLs públicas)
   - **File size limit**: 50 MB (ajustar según necesidad)
   - **Allowed MIME types**: `application/pdf`
5. Haz clic en **"Create bucket"**

### 2. Configurar Políticas de Acceso (RLS Policies)

El bucket debe ser público para permitir:
- **Lectura**: Cualquier usuario autenticado puede descargar PDFs
- **Escritura**: Solo usuarios con permisos de inspecciones pueden subir

#### Política de Lectura (SELECT)

```sql
CREATE POLICY "Permitir lectura pública de PDFs de inspecciones"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'inspecciones-pdfs');
```

#### Política de Escritura (INSERT)

```sql
CREATE POLICY "Permitir subida de PDFs a usuarios autenticados"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'inspecciones-pdfs' AND (storage.foldername(name))[1] = 'inspecciones');
```

#### Política de Actualización (UPDATE)

```sql
CREATE POLICY "Permitir actualización de PDFs a usuarios autenticados"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'inspecciones-pdfs')
WITH CHECK (bucket_id = 'inspecciones-pdfs');
```

#### Política de Eliminación (DELETE)

```sql
CREATE POLICY "Permitir eliminación de PDFs a usuarios autenticados"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'inspecciones-pdfs');
```

### 3. Estructura de Carpetas

Los archivos se organizan de la siguiente manera:

```
inspecciones-pdfs/
└── inspecciones/
    ├── inspeccion_1_acta.pdf
    ├── inspeccion_1_presupuesto.pdf
    ├── inspeccion_2_acta.pdf
    ├── inspeccion_2_presupuesto.pdf
    └── ...
```

### 4. Verificar la Configuración

1. Ve a **Storage** > **inspecciones-pdfs** en Supabase
2. Verifica que el bucket esté marcado como **Public**
3. Verifica que las políticas RLS estén activas en la pestaña **Policies**

### 5. URL de Acceso

Las URLs públicas siguen este formato:

```
https://hvkifqguxsgegzaxwcmj.supabase.co/storage/v1/object/public/inspecciones-pdfs/inspecciones/inspeccion_{id}_acta.pdf
```

## Notas Importantes

- **Tamaño máximo de archivo**: Por defecto 50 MB, ajustable en la configuración del bucket
- **Tipos de archivo permitidos**: Solo PDF (`application/pdf`)
- **Nomenclatura**: Los archivos se nombran automáticamente como `inspeccion_{id}_acta.pdf` o `inspeccion_{id}_presupuesto.pdf`
- **Reemplazo**: Al subir un nuevo PDF, el anterior se elimina automáticamente del storage
- **Seguridad**: El bucket es público para lectura, pero solo usuarios autenticados pueden escribir

## Troubleshooting

### Error: "Bucket not found"
- Verifica que el bucket `inspecciones-pdfs` esté creado
- Verifica que el nombre sea exactamente `inspecciones-pdfs` (sin espacios ni mayúsculas)

### Error: "Policy violation"
- Verifica que las políticas RLS estén configuradas correctamente
- Verifica que el bucket esté marcado como público

### Error: "File too large"
- Verifica el límite de tamaño en la configuración del bucket
- Considera aumentar el límite si es necesario

### Los PDFs no se descargan
- Verifica que las URLs sean públicas
- Verifica que el bucket esté configurado como público
- Verifica que la política de lectura esté activa
