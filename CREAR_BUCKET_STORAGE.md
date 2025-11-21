# 🚀 Crear Bucket de Storage para PDFs (5 minutos)

## Error Actual
```
Error al subir archivo: {"statusCode":"404","error":"Bucket not found","message":"Bucket not found"}
```

## Solución: Crear el Bucket en Supabase

### Paso 1: Ir a Supabase Storage
1. Abre tu navegador y ve a: https://app.supabase.com
2. Selecciona tu proyecto: **hvkifqguxsgegzaxwcmj**
3. En el menú lateral izquierdo, haz click en **Storage** 📦

### Paso 2: Crear Nuevo Bucket
1. Haz click en el botón verde **"New bucket"** o **"Create bucket"**
2. Aparecerá un formulario con estos campos:

### Paso 3: Configurar el Bucket
Completa el formulario exactamente así:

| Campo | Valor |
|-------|-------|
| **Name** | `inspecciones-pdfs` |
| **Public bucket** | ✅ **ACTIVADO** (muy importante!) |
| **File size limit** | `52428800` (50 MB) |
| **Allowed MIME types** | `application/pdf` |

**⚠️ IMPORTANTE**: El nombre DEBE ser exactamente `inspecciones-pdfs` (sin espacios, sin mayúsculas)

**⚠️ IMPORTANTE**: El bucket DEBE ser público (checkbox activado)

### Paso 4: Crear el Bucket
1. Haz click en **"Create bucket"** o **"Save"**
2. Deberías ver el bucket `inspecciones-pdfs` en la lista

### Paso 5: Verificar
1. En la lista de buckets, verifica que aparezca `inspecciones-pdfs`
2. Verifica que tenga un ícono de 🌐 (público)

### Paso 6: Configurar Políticas RLS (Opcional pero Recomendado)
1. Ve al menú lateral → **SQL Editor**
2. Abre el archivo: `database/configurar_storage_rls_policies.sql`
3. Copia TODO el contenido del archivo
4. Pégalo en el editor SQL de Supabase
5. Haz click en **"Run"** o **"Execute"**

Si ves errores de "policy already exists", no hay problema, ignóralos.

---

## ✅ Verificar que Funciona

1. Ve a cualquier inspección en tu aplicación
2. Busca la sección **"Documentos PDF"**
3. Intenta subir un PDF (acta o presupuesto)
4. Deberías ver: **"Acta PDF subida correctamente"** o **"Presupuesto PDF subido correctamente"**

---

## 🆘 Si Sigue sin Funcionar

### Error: "Bucket not found"
- Verifica que el nombre sea exactamente `inspecciones-pdfs`
- Verifica que el bucket esté marcado como público

### Error: "Policy violation" o "Access denied"
- Ejecuta el archivo SQL: `database/configurar_storage_rls_policies.sql`
- Verifica que tu usuario esté autenticado

### Error: "File too large"
- El archivo PDF debe ser menor a 50 MB
- Ajusta el límite en la configuración del bucket

---

## 📸 Capturas de Referencia

### Cómo debería verse el formulario:
```
┌─────────────────────────────────────┐
│ Create a new bucket                 │
├─────────────────────────────────────┤
│ Name: inspecciones-pdfs             │
│ ☑ Public bucket                     │
│ File size limit: 52428800           │
│ Allowed MIME types: application/pdf │
│                                     │
│          [Create bucket]            │
└─────────────────────────────────────┘
```

### Cómo debería verse en la lista:
```
Storage Buckets:
┌────────────────────┬────────┬──────────┐
│ Name               │ Public │ Size     │
├────────────────────┼────────┼──────────┤
│ 🌐 inspecciones-pdfs │ ✓ Yes  │ 50.0 MB  │
└────────────────────┴────────┴──────────┘
```

---

## 🎯 Resumen Rápido

**3 cosas importantes:**
1. ✅ Nombre: `inspecciones-pdfs` (exacto)
2. ✅ Público: Activado (checkbox marcado)
3. ✅ Ejecutar SQL: `database/configurar_storage_rls_policies.sql`

**Tiempo estimado:** 5 minutos

**¿Necesitas ayuda?** Avísame si encuentras algún problema.
