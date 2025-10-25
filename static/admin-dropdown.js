// admin-dropdown.js - Componente reutilizable de dropdown con búsqueda para administradores
// Usa Select2 para búsqueda avanzada y mejor UX

(function() {
    // Inicializar Select2 cuando el DOM esté listo
    function initAdminDropdown() {
        // Configurar Select2 en el campo de administrador
        const adminSelect = document.getElementById('administrador_id');

        if (!adminSelect) {
            console.warn('No se encontró el elemento administrador_id');
            return;
        }

        // Verificar si Select2 está disponible
        if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') {
            console.error('Select2 no está cargado. Asegúrate de incluir jQuery y Select2.');
            return;
        }

        // Configurar Select2
        $(adminSelect).select2({
            placeholder: "🔍 Buscar administrador...",
            allowClear: true,
            language: {
                noResults: function() {
                    return "No se encontraron resultados";
                },
                searching: function() {
                    return "Buscando...";
                },
                inputTooShort: function() {
                    return "Por favor, escribe más caracteres";
                }
            },
            width: '100%',
            theme: 'default',
            // Búsqueda case-insensitive mejorada
            matcher: function(params, data) {
                // Si no hay término de búsqueda, mostrar todo
                if ($.trim(params.term) === '') {
                    return data;
                }

                // Si no hay texto en la opción, no mostrar
                if (typeof data.text === 'undefined') {
                    return null;
                }

                // Búsqueda case-insensitive
                const searchTerm = params.term.toLowerCase();
                const optionText = data.text.toLowerCase();

                // Buscar en el texto de la opción
                if (optionText.indexOf(searchTerm) > -1) {
                    return data;
                }

                // No coincide
                return null;
            }
        });

        // Estilos personalizados para que coincida con el diseño
        const customStyles = `
            <style>
                /* Estilos personalizados para Select2 */
                .select2-container--default .select2-selection--single {
                    border: 2px solid #e1e5e9 !important;
                    border-radius: 8px !important;
                    height: 48px !important;
                    padding: 8px !important;
                    font-size: 16px !important;
                    font-family: 'Montserrat', sans-serif !important;
                }

                .select2-container--default .select2-selection--single .select2-selection__rendered {
                    line-height: 30px !important;
                    padding-left: 8px !important;
                    color: #333 !important;
                }

                .select2-container--default .select2-selection--single .select2-selection__arrow {
                    height: 46px !important;
                }

                .select2-container--default.select2-container--focus .select2-selection--single {
                    border-color: #366092 !important;
                    box-shadow: 0 0 0 3px rgba(54, 96, 146, 0.1) !important;
                }

                .select2-dropdown {
                    border: 2px solid #366092 !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
                }

                .select2-search--dropdown .select2-search__field {
                    border: 2px solid #e1e5e9 !important;
                    border-radius: 6px !important;
                    padding: 8px 12px !important;
                    font-size: 14px !important;
                    font-family: 'Montserrat', sans-serif !important;
                }

                .select2-search--dropdown .select2-search__field:focus {
                    border-color: #366092 !important;
                    outline: none !important;
                }

                .select2-results__option {
                    padding: 10px 15px !important;
                    font-size: 15px !important;
                    font-family: 'Montserrat', sans-serif !important;
                }

                .select2-results__option--highlighted {
                    background-color: #366092 !important;
                }

                .select2-container--default .select2-results__option[aria-selected=true] {
                    background-color: #e8f0f8 !important;
                    color: #366092 !important;
                }

                /* Placeholder */
                .select2-container--default .select2-selection--single .select2-selection__placeholder {
                    color: #999 !important;
                }

                /* Clear button */
                .select2-container--default .select2-selection--single .select2-selection__clear {
                    color: #999 !important;
                    font-size: 18px !important;
                    margin-right: 10px !important;
                }

                /* Mensaje de "no results" */
                .select2-results__option.select2-results__message {
                    color: #666 !important;
                }

                /* Ajuste responsivo */
                @media (max-width: 768px) {
                    .select2-container--default .select2-selection--single {
                        font-size: 14px !important;
                    }

                    .select2-results__option {
                        font-size: 14px !important;
                    }
                }
            </style>
        `;

        // Insertar estilos personalizados si no existen
        if (!document.getElementById('admin-dropdown-styles')) {
            const styleElement = document.createElement('div');
            styleElement.id = 'admin-dropdown-styles';
            styleElement.innerHTML = customStyles;
            document.head.appendChild(styleElement);
        }

        console.log('✅ Dropdown de administradores inicializado correctamente');
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAdminDropdown);
    } else {
        // DOM ya está listo
        initAdminDropdown();
    }

    // También exponer la función globalmente por si se necesita re-inicializar
    window.initAdminDropdown = initAdminDropdown;
})();
