"""
Configuración centralizada de la aplicación
"""
import os
import logging
import sys

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Silenciar logs verbosos de pdfplumber/pdfminer
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('pdfplumber').setLevel(logging.WARNING)

# ============================================
# CONFIGURACIÓN DE FLASK
# ============================================
class Config:
    """Configuración base de la aplicación"""

    # Secret key
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is not set")

    # Supabase
    SUPABASE_URL = "https://hvkifqguxsgegzaxwcmj.supabase.co"
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY environment variable is not set")

    # Headers para operaciones de base de datos (usa anon key)
    @property
    def HEADERS(self):
        return {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    # Headers para operaciones de storage (usa service key si está disponible)
    @property
    def STORAGE_HEADERS(self):
        storage_key = self.SUPABASE_SERVICE_KEY if self.SUPABASE_SERVICE_KEY else self.SUPABASE_KEY
        return {
            "apikey": storage_key,
            "Authorization": f"Bearer {storage_key}",
        }

    # Configuración de Resend para emails
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")


# Instancia global de configuración
config = Config()

# ============================================
# CONSTANTES DE CACHÉ (en minutos)
# ============================================
CACHE_TTL_ADMINISTRADORES = 5
CACHE_TTL_METRICAS_HOME = 5
CACHE_TTL_FILTROS = 30
CACHE_TTL_INSTALACIONES = 10
CACHE_TTL_OPORTUNIDADES = 10
