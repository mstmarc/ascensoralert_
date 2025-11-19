# Sistema de Perfiles y Control de Acceso

## Descripción

Este sistema implementa control de acceso basado en roles (RBAC) para AscensorAlert, permitiendo diferentes niveles de permisos para distintos tipos de usuarios.

## Perfiles Disponibles

### 1. Admin (Administrador)
- **Acceso total** al sistema
- Puede **crear, editar y eliminar** en todos los módulos
- **Único perfil con acceso al módulo de Inspecciones (IPOs)**
- Gestión completa de usuarios

**Módulos permitidos:**
- ✅ Clientes/Instalaciones
- ✅ Equipos/Ascensores
- ✅ Administradores de Fincas
- ✅ Oportunidades Comerciales
- ✅ Visitas
- ✅ **Inspecciones (IPOs)** 🔒
- ✅ Materiales Especiales
- ✅ OCAs

---

### 2. Gestor
- Acceso a **todos los módulos EXCEPTO Inspecciones**
- Puede **crear, editar y eliminar** en módulos permitidos
- Perfecto para empleados de confianza que gestionan el día a día

**Módulos permitidos:**
- ✅ Clientes/Instalaciones
- ✅ Equipos/Ascensores
- ✅ Administradores de Fincas
- ✅ Oportunidades Comerciales
- ✅ Visitas
- ❌ Inspecciones (IPOs) 🔒
- ❌ Materiales Especiales
- ❌ OCAs

---

### 3. Visualizador
- **Solo lectura** en módulos permitidos
- **NO puede crear, editar ni eliminar**
- **NO tiene acceso a Inspecciones**
- Perfecto para personas externas, clientes o colaboradores

**Módulos permitidos (solo lectura):**
- 👁️ Clientes/Instalaciones
- 👁️ Equipos/Ascensores
- 👁️ Administradores de Fincas
- 👁️ Oportunidades Comerciales
- ❌ Inspecciones (IPOs) 🔒

---

## Instalación y Configuración

### Paso 1: Ejecutar el Schema SQL

El schema SQL añade el campo `perfil` a la tabla de usuarios en Supabase:

```bash
# Accede a tu proyecto de Supabase
# Ve a: SQL Editor
# Copia y ejecuta el contenido de:
database/usuarios_perfiles_schema.sql
```

O desde el terminal con psql:
```bash
psql -h db.hvkifqguxsgegzaxwcmj.supabase.co \
     -U postgres \
     -d postgres \
     -f database/usuarios_perfiles_schema.sql
```

### Paso 2: Configurar Perfiles de Usuarios

Ejecuta el script de migración interactivo:

```bash
# Asegúrate de tener la variable de entorno configurada
export SUPABASE_KEY='tu_clave_de_supabase'

# Ejecuta el script de migración
python3 database/migrar_perfiles_usuarios.py
```

El script te guiará para:
1. Ver todos los usuarios actuales
2. Asignar un perfil a cada usuario
3. Confirmar los cambios
4. Verificar la configuración final

### Paso 3: Verificar Funcionamiento

1. Cierra todas las sesiones activas
2. Inicia sesión con cada tipo de usuario
3. Verifica que:
   - El menú lateral muestra solo las opciones permitidas
   - Los usuarios **visualizadores** NO ven botones de "Crear", "Editar" o "Eliminar"
   - Solo **admin** puede acceder a "Inspecciones"
   - **Gestor** (Julio) ve todo excepto Inspecciones

---

## Ejemplo de Configuración

### Configuración Recomendada

```sql
-- Configurar admin (tú)
UPDATE usuarios SET perfil = 'admin'
WHERE nombre_usuario = 'tu_usuario';

-- Configurar gestor (Julio)
UPDATE usuarios SET perfil = 'gestor'
WHERE nombre_usuario = 'julio';

-- Configurar visualizadores (externos)
UPDATE usuarios SET perfil = 'visualizador'
WHERE nombre_usuario IN ('usuario1', 'usuario2');
```

---

## Funcionamiento Técnico

### Backend (Flask)

1. **Login**: Al hacer login, se carga el `perfil` del usuario en la sesión
2. **Decoradores**: Las rutas están protegidas con decoradores:
   - `@helpers.login_required` - Requiere estar autenticado
   - `@helpers.requiere_permiso('modulo', 'accion')` - Verifica permisos
   - `@helpers.solo_admin` - Solo para administradores

3. **Ejemplo de ruta protegida**:
```python
@app.route("/inspecciones")
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def inspecciones_dashboard():
    # Solo admin puede acceder
    ...
```

### Frontend (Templates + JavaScript)

1. **Templates**: Reciben funciones de contexto para verificar permisos:
```jinja2
{% if puede_escribir('clientes') %}
    <button>Crear Cliente</button>
{% endif %}
```

2. **Menú Lateral** (`sidebar.js`):
   - Se construye dinámicamente según los permisos del usuario
   - Lee `window.userPermissions` inyectado desde el backend
   - Oculta automáticamente secciones no permitidas

---

## Seguridad

### Protección en Múltiples Capas

1. **Backend** (Python):
   - Decoradores verifican permisos antes de ejecutar cualquier ruta
   - Si no tiene permiso → Redirige a `/home` con mensaje de error

2. **Frontend** (JavaScript):
   - Menú dinámico oculta opciones no permitidas
   - Mejora UX pero NO es la seguridad principal

3. **Templates** (Jinja2):
   - Oculta botones de acciones no permitidas
   - El usuario visualizador NO ve botones de "Editar" o "Eliminar"

### ⚠️ IMPORTANTE
La seguridad real está en el **backend**. Aunque se oculten botones en el frontend, las rutas están protegidas con decoradores que **verifican permisos en el servidor**.

---

## Modificar Perfiles de Usuarios

### Opción 1: SQL Directo (Rápido)

```sql
-- Cambiar usuario a admin
UPDATE usuarios SET perfil = 'admin' WHERE nombre_usuario = 'usuario';

-- Cambiar usuario a gestor
UPDATE usuarios SET perfil = 'gestor' WHERE nombre_usuario = 'usuario';

-- Cambiar usuario a visualizador
UPDATE usuarios SET perfil = 'visualizador' WHERE nombre_usuario = 'usuario';
```

### Opción 2: Script de Migración (Interactivo)

```bash
python3 database/migrar_perfiles_usuarios.py
```

---

## Agregar Nuevos Módulos

Si añades un nuevo módulo al sistema, actualiza:

### 1. `helpers.py` - Definir permisos:
```python
PERMISOS_POR_PERFIL = {
    'admin': {
        'nuevo_modulo': {'read': True, 'write': True, 'delete': True},
        ...
    },
    'gestor': {
        'nuevo_modulo': {'read': True, 'write': True, 'delete': False},
        ...
    },
    'visualizador': {
        'nuevo_modulo': {'read': True, 'write': False, 'delete': False},
        ...
    }
}
```

### 2. `sidebar.js` - Añadir al menú:
```javascript
if (tienePermiso('nuevo_modulo', 'read')) {
    menuHTML += `
        <a href="/nuevo_modulo" class="sidebar-integrated-link">
            Nuevo Módulo
        </a>`;
}
```

### 3. `app.py` - Proteger rutas:
```python
@app.route("/nuevo_modulo")
@helpers.login_required
@helpers.requiere_permiso('nuevo_modulo', 'read')
def nuevo_modulo():
    ...
```

---

## Solución de Problemas

### El menú no se actualiza
- Limpia la caché del navegador (Ctrl + F5)
- Cierra sesión y vuelve a iniciar sesión

### Un usuario no puede acceder a un módulo
1. Verifica el perfil en la base de datos:
```sql
SELECT nombre_usuario, perfil FROM usuarios;
```

2. Verifica que la sesión se haya actualizado:
   - Cierra sesión y vuelve a iniciar

### Error "No tienes permiso para acceder"
- El usuario intentó acceder a una ruta no permitida
- Verifica que su perfil tenga los permisos correctos
- Si es correcto, revisa los decoradores de la ruta en `app.py`

---

## Archivos Relacionados

```
📁 database/
├── usuarios_perfiles_schema.sql      # Schema SQL para añadir campo perfil
└── migrar_perfiles_usuarios.py       # Script interactivo de configuración

📁 /
├── helpers.py                         # Sistema de permisos y decoradores
├── app.py                             # Rutas protegidas con decoradores
└── actualizar_templates_permisos.py  # Script para actualizar templates

📁 static/
└── sidebar.js                         # Menú lateral dinámico

📁 templates/
└── *.html                            # Templates con permisos inyectados
```

---

## Cambios Realizados

### Backend
✅ Campo `perfil` añadido a tabla `usuarios`
✅ Sistema de permisos en `helpers.py`
✅ Decoradores `@requiere_permiso()` y `@solo_admin`
✅ Todas las rutas protegidas con decoradores
✅ Permisos inyectados en context_processor

### Frontend
✅ Menú lateral dinámico según perfil
✅ Script de permisos en todos los templates
✅ Botones ocultos según permisos (próximamente)

### Migración
✅ Script SQL para añadir campo perfil
✅ Script Python interactivo para configurar usuarios
✅ Documentación completa

---

## Soporte

Para preguntas o problemas:
1. Revisa esta documentación
2. Verifica los logs del servidor Flask
3. Consulta el código en `helpers.py` para entender el sistema de permisos
