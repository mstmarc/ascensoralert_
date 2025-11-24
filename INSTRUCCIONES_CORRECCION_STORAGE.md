# 🔧 Corrección: Error de Permisos al Subir Archivos

## Problema
```
Error al subir archivo: {"statusCode":"403","error":"Unauthorized","message":"new row violates row-level security policy"}
```

## Causa
Las políticas de seguridad (RLS) de Supabase Storage estaban configuradas solo para usuarios `authenticated`, pero la aplicación usa su propio sistema de autenticación (no Supabase Auth).

## Solución Aplicada

### 1. Código Actualizado (app.py)
Se ha modificado el código para:
- Soportar una clave de servicio opcional (`SUPABASE_SERVICE_KEY`) para operaciones de storage
- Si la clave de servicio no está configurada, usar la clave anon key existente
- Usar headers específicos para operaciones de storage

### 2. Políticas RLS Actualizadas
Se han actualizado las políticas de seguridad en `database/configurar_storage_rls_policies.sql` para permitir operaciones con cualquier rol (anon, authenticated, service_role).

## Pasos para Aplicar la Corrección

### Opción 1: Ejecutar Script SQL (Recomendado)

1. Ve a tu proyecto en Supabase: https://app.supabase.com
2. Selecciona el proyecto: **hvkifqguxsgegzaxwcmj**
3. Ve a **SQL Editor** en el menú lateral
4. Copia y pega el contenido del archivo: `database/configurar_storage_rls_policies.sql`
5. Haz click en **"Run"** para ejecutar el script

### Opción 2: Configurar Service Role Key (Más Seguro)

Si prefieres usar la Service Role Key (recomendado para producción):

1. **Obtener la Service Role Key:**
   - Ve a tu proyecto en Supabase: https://app.supabase.com
   - Selecciona el proyecto: **hvkifqguxsgegzaxwcmj**
   - Ve a **Settings** → **API**
   - Copia la **service_role key** (⚠️ IMPORTANTE: Esta clave nunca debe exponerse al cliente)

2. **Configurar la Variable de Entorno:**
   - Añade la variable `SUPABASE_SERVICE_KEY` con el valor copiado
   - Ejemplo para desarrollo local (.env):
     ```
     SUPABASE_SERVICE_KEY=tu-service-role-key-aqui
     ```
   - Para producción, añádela en tu plataforma de hosting (Heroku, Vercel, etc.)

3. **Reiniciar la Aplicación:**
   - Reinicia tu servidor Flask para que lea la nueva variable de entorno

## Verificación

### Después de aplicar la corrección:

1. Ve a cualquier inspección en tu aplicación
2. Navega a la sección **"Documentos PDF"**
3. Intenta subir un archivo PDF (acta o presupuesto)
4. Deberías ver el mensaje: **"Acta PDF subida correctamente"** o **"Presupuesto PDF subido correctamente"**

## Notas de Seguridad

- **Service Role Key**: Nunca expongas esta clave al cliente (navegador). Solo úsala en el backend.
- **Políticas RLS**: Las políticas actualizadas permiten operaciones desde el backend, pero el acceso está protegido por:
  - Control de acceso a nivel de aplicación (decoradores `@helpers.requiere_permiso`)
  - Sistema de autenticación propio de la aplicación
  - El bucket solo acepta archivos en la carpeta `inspecciones/`

## Diferencias entre las Opciones

| Aspecto | Opción 1: SQL | Opción 2: Service Key |
|---------|---------------|----------------------|
| Seguridad | Buena | Mejor |
| Configuración | Simple | Requiere variable de entorno |
| Bypasa RLS | No | Sí |
| Recomendado para | Desarrollo/Testing | Producción |

## Troubleshooting

### Aún recibo error 403
- Verifica que ejecutaste el script SQL correctamente
- Verifica que el bucket `inspecciones-pdfs` existe
- Verifica que el bucket está marcado como público

### Error: "Bucket not found"
- El bucket debe existir antes de subir archivos
- Nombre exacto: `inspecciones-pdfs`

### La variable SUPABASE_SERVICE_KEY no se detecta
- Verifica que la variable esté configurada en tu entorno
- Reinicia el servidor Flask después de configurarla
- Verifica que el nombre sea exacto: `SUPABASE_SERVICE_KEY`

## Archivos Modificados

- ✅ `app.py` - Líneas 36-57, 4188-4192, 4263-4267
- ✅ `database/configurar_storage_rls_policies.sql` - Políticas RLS actualizadas
- ✅ `INSTRUCCIONES_CORRECCION_STORAGE.md` - Este archivo (nuevo)

## Soporte

Si el problema persiste después de aplicar estas correcciones, verifica:
1. Que el bucket existe y está configurado como público
2. Que el script SQL se ejecutó sin errores
3. Los logs del servidor Flask para más detalles del error
