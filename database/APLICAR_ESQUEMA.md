# Cómo Aplicar el Esquema de Cartera a Supabase

## Opción 1: Dashboard de Supabase (Recomendado - Más Simple)

### Pasos:

1. **Ir al Dashboard de Supabase:**
   - URL: https://supabase.com/dashboard
   - Proyecto: `hvkifqguxsgegzaxwcmj`

2. **Abrir el SQL Editor:**
   - En el menú lateral → "SQL Editor"
   - Click en "New query"

3. **Copiar y Pegar el SQL:**
   - Abrir el archivo `database/cartera_schema.sql`
   - Copiar TODO el contenido
   - Pegarlo en el SQL Editor de Supabase

4. **Ejecutar:**
   - Click en "Run" o `Ctrl+Enter`
   - Esperar confirmación: "Success. No rows returned"

5. **Verificar que se crearon las tablas:**
   - En el menú lateral → "Table Editor"
   - Deberías ver las nuevas tablas:
     - `instalaciones`
     - `maquinas_cartera`
     - `partes_trabajo`
     - `tipos_parte_mapeo` (con 12 registros)
     - `oportunidades_facturacion`

---

## Opción 2: Script Python (Automático)

### Requisitos:
```bash
pip install psycopg2-binary
```

### Variables de entorno necesarias:
```bash
export SUPABASE_DB_PASSWORD="tu_password_de_postgres"
```

### Ejecutar:
```bash
python database/aplicar_esquema.py
```

---

## Verificación Post-Instalación

### Comprobar que todo funcionó:

```sql
-- 1. Ver tablas creadas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%cartera%' OR table_name LIKE '%oportunidades%';

-- 2. Ver que tipos_parte_mapeo tiene 12 registros
SELECT COUNT(*) FROM tipos_parte_mapeo;

-- 3. Ver las vistas creadas
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
AND table_name LIKE 'v_%';
```

Deberías ver:
- ✅ 5 tablas: instalaciones, maquinas_cartera, partes_trabajo, tipos_parte_mapeo, oportunidades_facturacion
- ✅ 12 registros en tipos_parte_mapeo
- ✅ 4 vistas: v_resumen_partes_maquina, v_partes_con_recomendaciones, v_maquinas_problematicas, v_mantenimientos_vs_averias

---

## Troubleshooting

### Error: "relation already exists"
- **Causa:** Las tablas ya existen
- **Solución:** Si quieres recrearlas, primero ejecuta:
  ```sql
  DROP TABLE IF EXISTS oportunidades_facturacion CASCADE;
  DROP TABLE IF EXISTS partes_trabajo CASCADE;
  DROP TABLE IF EXISTS tipos_parte_mapeo CASCADE;
  DROP TABLE IF EXISTS maquinas_cartera CASCADE;
  DROP TABLE IF EXISTS instalaciones CASCADE;
  ```

### Error: "function update_updated_at_column does not exist"
- **Causa:** La función de trigger no existe
- **Solución:** Ejecutar primero el schema de inspecciones que contiene la función

---

**¿Listo para aplicar el esquema?**
