# Guía de Migración a Flask Blueprints

## 📋 Situación Actual

Todas las rutas (177) están en `app_legacy.py`. Esto funciona pero dificulta:
- 🔴 Trabajo en equipo (todos tocan el mismo archivo)
- 🔴 Testing (difícil testear módulos por separado)
- 🔴 Mantenimiento (archivo muy grande)

## 🎯 Objetivo

Migrar gradualmente a **Flask Blueprints** - módulos independientes por funcionalidad.

## ✅ Ventajas de Blueprints

- 📦 **Modularidad** - Cada módulo en su archivo
- 👥 **Trabajo en equipo** - Equipos trabajan en módulos diferentes
- 🧪 **Testing** - Testear módulos por separado
- 🔄 **Reutilización** - Blueprints reutilizables entre proyectos
- 📚 **Organización** - Código más fácil de navegar

## 🗂️ Estructura Propuesta

```
routes/
├── __init__.py
├── auth.py                    # Login, logout, home
├── leads.py                   # Leads, clientes, equipos
├── oportunidades.py           # Oportunidades comerciales
├── inspecciones/
│   ├── __init__.py
│   ├── inspecciones_bp.py     # ✅ EJEMPLO CREADO
│   ├── defectos.py           # Defectos (futuro)
│   └── ocas.py               # OCAs (futuro)
├── administracion/
│   ├── __init__.py
│   ├── administradores.py
│   └── usuarios.py
├── cartera/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── oportunidades.py
│   └── alertas.py
└── ia/
    ├── __init__.py
    ├── predicciones.py
    └── analisis.py
```

## 🚀 Estrategia de Migración (Gradual y Segura)

### Fase 1: Preparación (✅ COMPLETADO)
- ✅ Crear estructura de carpetas `routes/`
- ✅ Crear Blueprint de ejemplo (`inspecciones_bp.py`)
- ✅ Documentar proceso

### Fase 2: Migración por Módulos (Futuro)

#### Orden Recomendado:
1. **OCAs** (más simple, 4 rutas) ← Empezar aquí
2. **Administradores** (7 rutas)
3. **Leads** (11 rutas)
4. **Inspecciones** (16 rutas)
5. **Oportunidades** (16 rutas)
6. **Cartera** (32 rutas)
7. **IA** (36 rutas)

### Fase 3: Cleanup (Futuro)
- Eliminar `app_legacy.py`
- Optimizar imports
- Actualizar tests

## 📘 Cómo Crear un Blueprint

### 1. Crear el archivo del Blueprint

```python
# routes/ocas/ocas_bp.py
from flask import Blueprint, render_template, request
import helpers
from config import config

# Crear Blueprint
ocas_bp = Blueprint('ocas', __name__, url_prefix='/ocas')

@ocas_bp.route('/')  # /ocas
@helpers.login_required
def lista_ocas():
    # ... lógica
    return render_template('lista_ocas.html', ocas=ocas)

@ocas_bp.route('/nuevo', methods=['GET', 'POST'])  # /ocas/nuevo
@helpers.login_required
def nuevo_oca():
    # ... lógica
    pass
```

### 2. Registrar en app.py

```python
# app.py
from routes.ocas.ocas_bp import ocas_bp

# Registrar Blueprint
app.register_blueprint(ocas_bp)
```

### 3. Actualizar Templates

**Antes**:
```html
<a href="{{ url_for('lista_ocas') }}">Ver OCAs</a>
```

**Después**:
```html
<a href="{{ url_for('ocas.lista_ocas') }}">Ver OCAs</a>
<!--              ↑ namespace del Blueprint -->
```

### 4. Actualizar Redirects en el Código

**Antes**:
```python
return redirect(url_for('lista_ocas'))
```

**Después**:
```python
return redirect(url_for('ocas.lista_ocas'))
```

## 🎓 Ejemplo Completo: Migrar OCAs

### Paso 1: Crear `routes/ocas/ocas_bp.py`

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests
import helpers
from config import config
from utils.helpers_actions import obtener_conteos_por_tabla

ocas_bp = Blueprint('ocas', __name__, url_prefix='/ocas')

@ocas_bp.route('/')
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'read')
def lista():
    """Listado de todos los OCAs con conteo optimizado de inspecciones"""
    ocas = obtener_conteos_por_tabla(
        tabla_principal='ocas',
        tabla_relacionada='inspecciones',
        campo_relacion='oca_id',
        filtros_principal='order=nombre.asc'
    )

    for oca in ocas:
        oca['total_inspecciones'] = oca.pop('total_count', 0)

    return render_template("lista_ocas.html", ocas=ocas)

@ocas_bp.route('/nuevo', methods=["GET", "POST"])
@helpers.login_required
@helpers.requiere_permiso('inspecciones', 'write')
def nuevo():
    """Crear nuevo OCA"""
    if request.method == "POST":
        nombre = request.form.get("nombre")
        contacto = request.form.get("contacto")
        telefono = request.form.get("telefono")
        email = request.form.get("email")

        response = requests.post(
            f"{config.SUPABASE_URL}/rest/v1/ocas",
            headers=config.HEADERS,
            json={
                "nombre": nombre,
                "contacto": contacto,
                "telefono": telefono,
                "email": email,
                "activo": True
            }
        )

        if response.status_code == 201:
            flash("OCA creado correctamente", "success")
            return redirect(url_for('ocas.lista'))
        else:
            flash("Error al crear OCA", "error")

    return render_template("nuevo_oca.html")

# ... más rutas (editar, eliminar, etc.)
```

### Paso 2: Registrar en `app.py`

```python
# app.py (agregar al final, antes de if __name__ == "__main__")

# ============================================
# REGISTRAR BLUEPRINTS
# ============================================

from routes.ocas.ocas_bp import ocas_bp
app.register_blueprint(ocas_bp)
```

### Paso 3: Actualizar Templates

En `lista_ocas.html`:
```html
<!-- ANTES -->
<a href="{{ url_for('nuevo_oca') }}">Nuevo OCA</a>

<!-- DESPUÉS -->
<a href="{{ url_for('ocas.nuevo') }}">Nuevo OCA</a>
```

### Paso 4: Eliminar Rutas del app_legacy.py

Comentar o eliminar las rutas `lista_ocas()`, `nuevo_oca()`, etc. de `app_legacy.py`.

## ⚠️ Consideraciones Importantes

### 1. URLs No Cambian
Los Blueprints mantienen las mismas URLs:
- `/ocas` → sigue siendo `/ocas`
- `/ocas/nuevo` → sigue siendo `/ocas/nuevo`

### 2. Namespace en url_for()
Lo único que cambia es `url_for()`:
- Antes: `url_for('lista_ocas')`
- Después: `url_for('ocas.lista_ocas')` ← namespace.función

### 3. Migración Gradual
Puedes tener Blueprints y rutas legacy coexistiendo:
- ✅ OCAs en Blueprint
- ✅ Leads en app_legacy.py
- ✅ Ambos funcionan simultáneamente

### 4. Testing
Los Blueprints se pueden testear por separado:
```python
# tests/test_ocas.py
from routes.ocas.ocas_bp import ocas_bp

def test_lista_ocas(client):
    response = client.get('/ocas')
    assert response.status_code == 200
```

## 📊 Métricas de Éxito

| Métrica | Antes | Meta |
|---------|-------|------|
| Archivos de rutas | 1 (app_legacy.py) | ~12 Blueprints |
| Líneas por archivo | 8,567 | <500 por Blueprint |
| Testing | Difícil (todo junto) | Fácil (por módulo) |
| Trabajo en equipo | Conflictos frecuentes | Módulos independientes |

## 🎯 Próximos Pasos

### Inmediato (Opcional)
1. Migrar módulo **OCAs** (4 rutas, más simple)
2. Probar que todo funciona
3. Actualizar templates de OCAs

### Corto Plazo
1. Migrar **Administradores** (7 rutas)
2. Migrar **Leads** (11 rutas)

### Largo Plazo
1. Migrar todos los módulos
2. Eliminar `app_legacy.py`
3. Agregar tests por módulo

## 📚 Referencias

- [Flask Blueprints Docs](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Large Applications as Packages](https://flask.palletsprojects.com/en/2.3.x/patterns/packages/)
- `routes/inspecciones/inspecciones_bp.py` - Ejemplo en este proyecto

## ✅ Conclusión

La migración a Blueprints es:
- ✅ **Gradual** - No hay que migrar todo de golpe
- ✅ **Segura** - Blueprints coexisten con código legacy
- ✅ **Beneficiosa** - Mejor organización y mantenibilidad

**Recomendación**: Migrar módulo por módulo, empezando por los más simples (OCAs, Administradores).
