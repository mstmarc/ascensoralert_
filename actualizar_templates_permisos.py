#!/usr/bin/env python3
"""
Script para añadir el script de permisos a todos los templates que usan sidebar.js
"""
import os
import re

TEMPLATES_DIR = "/home/user/ascensoralert_/templates"

# Script a inyectar ANTES de sidebar.js
PERMISOS_SCRIPT = """    <!-- Inyectar permisos del usuario para JavaScript -->
    <script>
        window.userPermissions = {{ permisos_usuario_json | safe }};
        window.perfilUsuario = '{{ perfil_usuario }}';
    </script>
"""

def actualizar_template(filepath):
    """Añade el script de permisos antes de sidebar.js si no existe"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya tiene el script de permisos
    if 'window.userPermissions' in content:
        print(f"✓ {os.path.basename(filepath)} ya tiene permisos")
        return False

    # Verificar si usa sidebar.js
    if 'sidebar.js' not in content:
        print(f"- {os.path.basename(filepath)} no usa sidebar.js")
        return False

    # Buscar la línea de sidebar.js y añadir el script antes
    # Probar con url_for
    pattern1 = r'(\s*)<script src="{{ url_for\(\'static\', filename=\'sidebar\.js\'\) }}"></script>'
    replacement1 = PERMISOS_SCRIPT + r'\1<script src="{{ url_for(\'static\', filename=\'sidebar.js\') }}"></script>'

    # Probar con ruta directa
    pattern2 = r'(\s*)<script src="/static/sidebar\.js"></script>'
    replacement2 = PERMISOS_SCRIPT + r'\1<script src="/static/sidebar.js"></script>'

    new_content = re.sub(pattern1, replacement1, content)
    if new_content == content:
        new_content = re.sub(pattern2, replacement2, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ {os.path.basename(filepath)} actualizado")
        return True
    else:
        print(f"⚠ {os.path.basename(filepath)} no se pudo actualizar")
        return False

def main():
    """Procesar todos los templates"""
    print("Actualizando templates con script de permisos...\n")

    actualizados = 0
    total = 0

    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.html'):
            filepath = os.path.join(TEMPLATES_DIR, filename)
            total += 1
            if actualizar_template(filepath):
                actualizados += 1

    print(f"\n✅ Proceso completado:")
    print(f"   - Templates procesados: {total}")
    print(f"   - Templates actualizados: {actualizados}")

if __name__ == "__main__":
    main()
