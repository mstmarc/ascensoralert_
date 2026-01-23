"""
Wrapper unificado para mensajes flash() - UX consistente
"""
from flask import flash as flask_flash


# Emojis para cada tipo de mensaje (opcional, se puede desactivar)
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
}


def flash_success(message, use_emoji=False):
    """
    Muestra un mensaje de éxito

    Args:
        message: Texto del mensaje
        use_emoji: Si True, agrega emoji al principio

    Ejemplo:
        flash_success("Usuario creado correctamente")
        flash_success("Datos guardados", use_emoji=True)  # "✅ Datos guardados"
    """
    if use_emoji:
        message = f"{EMOJIS['success']} {message}"
    flask_flash(message, 'success')


def flash_error(message, use_emoji=False):
    """
    Muestra un mensaje de error

    Args:
        message: Texto del mensaje
        use_emoji: Si True, agrega emoji al principio

    Ejemplo:
        flash_error("No se pudo guardar el registro")
        flash_error("Error de conexión", use_emoji=True)  # "❌ Error de conexión"
    """
    if use_emoji:
        message = f"{EMOJIS['error']} {message}"
    flask_flash(message, 'error')


def flash_warning(message, use_emoji=False):
    """
    Muestra un mensaje de advertencia

    Args:
        message: Texto del mensaje
        use_emoji: Si True, agrega emoji al principio

    Ejemplo:
        flash_warning("Este campo es obligatorio")
        flash_warning("Revisa los datos", use_emoji=True)  # "⚠️ Revisa los datos"
    """
    if use_emoji:
        message = f"{EMOJIS['warning']} {message}"
    flask_flash(message, 'warning')


def flash_info(message, use_emoji=False):
    """
    Muestra un mensaje informativo

    Args:
        message: Texto del mensaje
        use_emoji: Si True, agrega emoji al principio

    Ejemplo:
        flash_info("Los cambios se han guardado")
        flash_info("Operación completada", use_emoji=True)  # "ℹ️ Operación completada"
    """
    if use_emoji:
        message = f"{EMOJIS['info']} {message}"
    flask_flash(message, 'info')


# Alias para mantener compatibilidad con código existente
def flash(message, category='info', use_emoji=False):
    """
    Wrapper genérico que mantiene compatibilidad con flash() nativo

    Args:
        message: Texto del mensaje
        category: 'success', 'error', 'warning', 'info'
        use_emoji: Si True, agrega emoji al principio

    Ejemplo:
        flash("Mensaje genérico", 'success')
        flash("Error", 'error', use_emoji=True)
    """
    if category == 'success':
        flash_success(message, use_emoji)
    elif category == 'error':
        flash_error(message, use_emoji)
    elif category == 'warning':
        flash_warning(message, use_emoji)
    else:
        flash_info(message, use_emoji)
