#!/usr/bin/env python3
"""
Script para añadir <script src="/static/sidebar.js"></script> 
automáticamente a todos los templates HTML
"""

import os
import glob

def add_sidebar_to_templates():
    # Ruta de la carpeta templates
    templates_folder = "templates"
    
    # Línea que vamos a añadir
    sidebar_line = '    <script src="/static/sidebar.js"></script>\n'
    
    # Buscar todos los archivos .html
    html_files = glob.glob(os.path.join(templates_folder, "*.html"))
    
    if not html_files:
        print("❌ No se encontraron archivos HTML en la carpeta 'templates/'")
        return
    
    print(f"📁 Encontrados {len(html_files)} archivos HTML\n")
    
    modified_count = 0
    skipped_count = 0
    
    for html_file in html_files:
        filename = os.path.basename(html_file)
        
        # Leer el contenido del archivo
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene el script
        if 'sidebar.js' in content:
            print(f"⏭️  {filename} - Ya tiene sidebar.js, omitido")
            skipped_count += 1
            continue
        
        # Buscar </body> y añadir el script antes
        if '</body>' in content:
            # Reemplazar la primera ocurrencia de </body>
            new_content = content.replace('</body>', sidebar_line + '</body>', 1)
            
            # Guardar el archivo modificado
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ {filename} - Script añadido correctamente")
            modified_count += 1
        else:
            print(f"⚠️  {filename} - No se encontró </body>, revisar manualmente")
    
    print(f"\n{'='*50}")
    print(f"✅ Archivos modificados: {modified_count}")
    print(f"⏭️  Archivos omitidos: {skipped_count}")
    print(f"📝 Total procesados: {len(html_files)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("🔧 Iniciando modificación de templates...\n")
    
    # Verificar que existe la carpeta templates
    if not os.path.exists("templates"):
        print("❌ Error: No se encuentra la carpeta 'templates/'")
        print("   Asegúrate de ejecutar este script desde la raíz de tu proyecto")
    else:
        add_sidebar_to_templates()
        print("\n✨ ¡Proceso completado!")
        print("👉 Ahora solo necesitas crear el archivo static/sidebar.js")
