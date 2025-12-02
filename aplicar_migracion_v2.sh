#!/bin/bash
# Script para aplicar la migración de Analítica Avanzada V2

echo "======================================================================"
echo "  MIGRACIÓN: Analítica Avanzada V2 - Sistema de Alertas Predictivas"
echo "======================================================================"
echo ""

# Configuración
DB_NAME="ascensoralert"
DB_USER="postgres"

echo "📋 Base de datos: $DB_NAME"
echo "👤 Usuario: $DB_USER"
echo ""

# Paso 1: Verificar que existe la base de datos
echo "🔍 Verificando conexión a la base de datos..."
psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se puede conectar a la base de datos $DB_NAME"
    echo "   Verifica que PostgreSQL esté corriendo y que la base de datos exista"
    exit 1
fi
echo "✅ Conexión exitosa"
echo ""

# Paso 2: Verificar que existen las tablas base
echo "🔍 Verificando tablas base (cartera V1)..."
psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM instalaciones;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Las tablas base no existen"
    echo "   Ejecuta primero: psql -U postgres -d ascensoralert -f database/cartera_schema.sql"
    exit 1
fi
echo "✅ Tablas base encontradas"
echo ""

# Paso 3: Aplicar schema V2
echo "📊 Aplicando schema V2 (tablas, vistas, funciones)..."
psql -U $DB_USER -d $DB_NAME -f database/cartera_schema_v2.sql
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Falló la aplicación del schema V2"
    exit 1
fi
echo ""
echo "✅ Schema V2 aplicado correctamente"
echo ""

# Paso 4: Registrar migración
echo "📝 Registrando migración en el log..."
psql -U $DB_USER -d $DB_NAME -f database/migrations/005_analitica_avanzada_v2.sql
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Falló el registro de la migración"
    exit 1
fi
echo ""

echo "======================================================================"
echo "✅ MIGRACIÓN COMPLETADA EXITOSAMENTE"
echo "======================================================================"
echo ""
echo "📋 Resumen:"
echo "   ✅ Tablas creadas: componentes_criticos, alertas_automaticas, pendientes_tecnicos"
echo "   ✅ Vistas creadas: v_estado_maquinas_semaforico, v_riesgo_instalaciones, v_perdidas_por_pendientes"
echo "   ✅ 12 componentes críticos pre-cargados"
echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo ""
echo "   1. Ejecutar detectores para generar alertas iniciales:"
echo "      python detectores_alertas.py"
echo ""
echo "   2. Acceder al dashboard V2:"
echo "      http://localhost:5000/cartera/v2"
echo ""
echo "   3. Configurar cron job para ejecutar detectores diariamente (opcional):"
echo "      crontab -e"
echo "      # Añadir: 0 6 * * * cd /home/user/ascensoralert_ && python detectores_alertas.py"
echo ""
echo "======================================================================"
