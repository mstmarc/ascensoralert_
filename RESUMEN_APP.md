# AscensorAlert - Resumen de la Aplicación

## Descripción General
CRM especializado en gestión de ascensores con **IA predictiva integrada** para empresas de mantenimiento. Combina gestión operativa, análisis inteligente y cumplimiento normativo (ITC-AEM1).

## Stack Técnico
- **Backend**: Python Flask 2.3.3 + PostgreSQL/Supabase
- **Frontend**: Jinja2 + Bootstrap + JavaScript
- **IA**: Anthropic Claude 3.5 Sonnet para análisis predictivo
- **Almacenamiento**: Supabase Storage + Row Level Security

## Funcionalidades Destacadas

### 🤖 Motor de IA Predictiva (Novedad 2025)
- Análisis semántico de partes de trabajo con Claude 3.5 Sonnet
- **Predicción de averías futuras** basada en patrones históricos
- Detección automática de componentes críticos
- Estimación de ROI en mantenimiento preventivo
- Dashboard con alertas predictivas y métricas de precisión

### ⚡ Sistema de Alertas V2 (Automático)
3 detectores ejecutables por cron:
1. **Fallas Repetidas**: 2+ en 30 días o 3+ en 90 días
2. **Recomendaciones Ignoradas**: no ejecutadas + averías posteriores
3. **Mantenimientos Omitidos**: +60 días sin conservación

Incluye cálculo automático del **Índice de Riesgo de Instalaciones (IRI)** y estimación de pérdidas económicas.

### 📋 Módulo de Inspecciones (IPOs)
- Gestión completa conforme a **normativa ITC-AEM1 julio 2024**
- Control de defectos (DL/DG/DMG) con plazos automáticos
- Seguimiento de materiales especiales (cortinas, pesacargas)
- Sistema de estados: PENDIENTE → PEDIDO → RECIBIDO → INSTALADO
- Gestión de OCAs (Organismos Control Autorizados)

### 📊 Cartera y CRM
- Dashboard con KPIs en tiempo real
- Gestión de instalaciones, máquinas y clientes
- Importación masiva desde Excel
- Sistema de recomendaciones
- Oportunidades comerciales post-IPO
- Análisis de zonas calientes por código postal/barrio

### 👥 Control de Acceso (RBAC)
3 perfiles con permisos granulares:
- **Admin**: Acceso total incluido módulo Inspecciones
- **Gestor**: Todos los módulos EXCEPTO Inspecciones
- **Visualizador**: Solo lectura (sin Inspecciones)

## Lo que la hace única

1. **IA Predictiva Especializada**: Única en su clase usando Claude 3.5 Sonnet para análisis técnico de ascensores
2. **Automatización Total**: Detectores ejecutables sin intervención manual
3. **Cumplimiento Normativo**: Implementación completa de ITC-AEM1 (España)
4. **Arquitectura Dual**: Sistema clásico (V1) + sistema inteligente (V2) coexisten
5. **Análisis Geoespacial**: Integración con datos catastrales para prospección
6. **Rendimiento Optimizado**: Sistema de caché multinivel + índices especializados

## Módulos Principales
- **Cartera**: CRM core + IA predictiva
- **Inspecciones**: IPOs + defectos + materiales especiales
- **Alertas V2**: Detectores automáticos + priorización
- **Leads**: Oportunidades comerciales
- **Visitas**: Planificación y seguimiento
- **Análisis**: Zonas calientes + reportes mensuales

## Base de Datos
- 8+ esquemas SQL especializados
- Vistas materializadas para análisis
- Migraciones versionadas
- Row Level Security (RLS)
- 30+ tablas principales

## Deployment
Compatible con Render, Railway y Heroku. Configuración con Docker y variables de entorno (.env).

---

**En resumen**: Sistema empresarial que transforma datos técnicos de ascensores en **inteligencia operativa y predictiva**, optimizando mantenimiento preventivo y detectando riesgos antes de que se materialicen.
