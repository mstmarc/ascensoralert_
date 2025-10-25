// admin-dropdown.js - Componente de dropdown con búsqueda para administradores
// SOLUCIÓN SIMPLIFICADA SIN SELECT2 - Usa datalist nativo de HTML5

(function() {
    console.log('🔧 Iniciando dropdown de administradores (versión simplificada)...');

    function initAdminDropdown() {
        const adminSelect = document.getElementById('administrador_id');

        if (!adminSelect) {
            console.warn('⚠️ No se encontró el elemento #administrador_id');
            return;
        }

        console.log('✅ Elemento encontrado');
        console.log('📊 Opciones disponibles:', adminSelect.options.length);

        // Convertir select a input con datalist para búsqueda nativa
        const parentElement = adminSelect.parentElement;
        const selectValue = adminSelect.value;
        const options = Array.from(adminSelect.options);

        // Crear input de búsqueda
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.id = 'administrador_search';
        searchInput.className = 'admin-search-input';
        searchInput.placeholder = '🔍 Buscar administrador...';
        searchInput.autocomplete = 'off';

        // Crear select oculto para mantener el valor real
        const hiddenSelect = document.createElement('select');
        hiddenSelect.id = 'administrador_id';
        hiddenSelect.name = 'administrador_id';
        hiddenSelect.style.display = 'none';

        // Copiar todas las opciones al select oculto
        options.forEach(option => {
            const newOption = option.cloneNode(true);
            hiddenSelect.appendChild(newOption);
        });

        // Crear dropdown de resultados
        const dropdown = document.createElement('div');
        dropdown.className = 'admin-dropdown-results';
        dropdown.style.display = 'none';

        // Insertar los nuevos elementos
        adminSelect.replaceWith(searchInput);
        parentElement.appendChild(hiddenSelect);
        parentElement.appendChild(dropdown);

        // Crear lista de opciones para búsqueda
        const adminList = options.slice(1).map(opt => ({
            id: opt.value,
            text: opt.textContent.trim()
        }));

        console.log('📋 Administradores cargados:', adminList.length);

        // Función para mostrar resultados
        function showResults(query) {
            dropdown.innerHTML = '';

            if (!query || query.trim().length === 0) {
                // Mostrar todos
                const filtered = adminList;

                if (filtered.length === 0) {
                    dropdown.innerHTML = '<div class="admin-dropdown-item no-results">No hay administradores disponibles</div>';
                    dropdown.style.display = 'block';
                    return;
                }

                filtered.forEach(admin => {
                    const item = document.createElement('div');
                    item.className = 'admin-dropdown-item';
                    item.textContent = admin.text;
                    item.dataset.id = admin.id;
                    item.onclick = function() {
                        selectAdmin(admin);
                    };
                    dropdown.appendChild(item);
                });

                dropdown.style.display = 'block';
            } else {
                // Filtrar por búsqueda
                const searchTerm = query.toLowerCase();
                const filtered = adminList.filter(admin =>
                    admin.text.toLowerCase().includes(searchTerm)
                );

                if (filtered.length === 0) {
                    dropdown.innerHTML = '<div class="admin-dropdown-item no-results">No se encontraron resultados</div>';
                } else {
                    filtered.forEach(admin => {
                        const item = document.createElement('div');
                        item.className = 'admin-dropdown-item';

                        // Resaltar coincidencias
                        const regex = new RegExp(`(${searchTerm})`, 'gi');
                        const highlightedText = admin.text.replace(regex, '<strong>$1</strong>');
                        item.innerHTML = highlightedText;

                        item.dataset.id = admin.id;
                        item.onclick = function() {
                            selectAdmin(admin);
                        };
                        dropdown.appendChild(item);
                    });
                }

                dropdown.style.display = 'block';
            }
        }

        // Función para seleccionar un administrador
        function selectAdmin(admin) {
            searchInput.value = admin.text;
            hiddenSelect.value = admin.id;
            dropdown.style.display = 'none';
            console.log('✅ Administrador seleccionado:', admin.text, '(ID:', admin.id + ')');
        }

        // Eventos del input
        searchInput.addEventListener('focus', function() {
            showResults(this.value);
        });

        searchInput.addEventListener('input', function() {
            showResults(this.value);
        });

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                dropdown.style.display = 'none';
            }
        });

        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', function(e) {
            if (!parentElement.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Si había un valor seleccionado, mantenerlo
        if (selectValue) {
            const selected = adminList.find(a => a.id === selectValue);
            if (selected) {
                selectAdmin(selected);
            }
        }

        console.log('✅ Dropdown inicializado correctamente');
    }

    // Añadir estilos
    function addStyles() {
        if (document.getElementById('admin-dropdown-styles')) {
            return;
        }

        const styles = `
            <style id="admin-dropdown-styles">
                .admin-search-input {
                    width: 100%;
                    padding: 12px 15px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 16px;
                    font-family: 'Montserrat', sans-serif;
                    transition: all 0.3s ease;
                    box-sizing: border-box;
                }

                .admin-search-input:focus {
                    outline: none;
                    border-color: #366092;
                    box-shadow: 0 0 0 3px rgba(54, 96, 146, 0.1);
                }

                .admin-dropdown-results {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    max-height: 300px;
                    overflow-y: auto;
                    background: white;
                    border: 2px solid #366092;
                    border-radius: 8px;
                    margin-top: 5px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
                    z-index: 9999;
                }

                .admin-dropdown-item {
                    padding: 12px 15px;
                    cursor: pointer;
                    font-size: 15px;
                    font-family: 'Montserrat', sans-serif;
                    transition: background 0.2s;
                    border-bottom: 1px solid #f0f0f0;
                }

                .admin-dropdown-item:last-child {
                    border-bottom: none;
                }

                .admin-dropdown-item:hover {
                    background-color: #366092;
                    color: white;
                }

                .admin-dropdown-item.no-results {
                    color: #999;
                    cursor: default;
                    font-style: italic;
                }

                .admin-dropdown-item.no-results:hover {
                    background-color: transparent;
                    color: #999;
                }

                .admin-dropdown-item strong {
                    background-color: rgba(54, 96, 146, 0.2);
                    font-weight: 600;
                }

                /* Asegurar que el contenedor del dropdown tenga position relative */
                .form-group {
                    position: relative;
                }

                @media (max-width: 768px) {
                    .admin-search-input {
                        font-size: 14px;
                    }

                    .admin-dropdown-item {
                        font-size: 14px;
                        padding: 10px 12px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
        console.log('🎨 Estilos añadidos');
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            addStyles();
            initAdminDropdown();
        });
    } else {
        addStyles();
        initAdminDropdown();
    }

    // Exponer función global
    window.initAdminDropdown = function() {
        addStyles();
        initAdminDropdown();
    };
})();
