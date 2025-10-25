// admin-dropdown.js - Componente reutilizable de dropdown con búsqueda para administradores
// Usa Select2 para búsqueda avanzada y mejor UX

(function() {
    // Esperar a que jQuery y Select2 estén disponibles
    function waitForDependencies(callback) {
        if (typeof jQuery !== 'undefined' && typeof jQuery.fn.select2 !== 'undefined') {
            callback();
        } else {
            setTimeout(function() {
                waitForDependencies(callback);
            }, 100);
        }
    }

    // Inicializar Select2 cuando el DOM esté listo
    function initAdminDropdown() {
        console.log('🔧 Inicializando dropdown de administradores...');

        // Buscar el campo de administrador
        const adminSelect = jQuery('#administrador_id');

        if (!adminSelect.length) {
            console.warn('⚠️ No se encontró el elemento #administrador_id');
            return;
        }

        console.log('✅ Elemento encontrado:', adminSelect);
        console.log('📊 Opciones disponibles:', adminSelect.find('option').length);

        try {
            // Destruir Select2 si ya existe (para evitar duplicados)
            if (adminSelect.data('select2')) {
                adminSelect.select2('destroy');
            }

            // Configurar Select2
            adminSelect.select2({
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
                    },
                    loadingMore: function() {
                        return "Cargando más resultados...";
                    }
                },
                width: '100%',
                theme: 'default',
                // Búsqueda case-insensitive mejorada
                matcher: function(params, data) {
                    // Si no hay término de búsqueda, mostrar todo
                    if (jQuery.trim(params.term) === '') {
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

            console.log('✅ Select2 inicializado correctamente');

            // Añadir estilos personalizados
            addCustomStyles();

        } catch (error) {
            console.error('❌ Error al inicializar Select2:', error);
        }
    }

    // Añadir estilos personalizados
    function addCustomStyles() {
        // Verificar si ya existen los estilos
        if (document.getElementById('admin-dropdown-styles')) {
            return;
        }

        const customStyles = `
            /* Estilos personalizados para Select2 */
            .select2-container--default .select2-selection--single {
                border: 2px solid #e1e5e9 !important;
                border-radius: 8px !important;
                min-height: 48px !important;
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
                z-index: 9999 !important;
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
        `;

        // Crear elemento style
        const styleElement = document.createElement('style');
        styleElement.id = 'admin-dropdown-styles';
        styleElement.textContent = customStyles;
        document.head.appendChild(styleElement);

        console.log('🎨 Estilos personalizados añadidos');
    }

    // Inicializar cuando todo esté listo
    waitForDependencies(function() {
        console.log('📦 jQuery y Select2 cargados');

        // Esperar a que el DOM esté listo
        jQuery(document).ready(function() {
            console.log('📄 DOM listo');
            initAdminDropdown();
        });
    });

    // También exponer la función globalmente por si se necesita re-inicializar
    window.initAdminDropdown = function() {
        waitForDependencies(function() {
            jQuery(document).ready(initAdminDropdown);
        });
    };
})();
