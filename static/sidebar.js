// sidebar.js - Menú lateral integrado debajo del header
(function() {
    // NO cargar el menú en la página de login
    if (window.location.pathname === '/' || window.location.pathname === '/login') {
        return; // Salir sin crear el menú
    }

    // CSS del menú lateral integrado
    const sidebarCSS = `
        /* Ajustar header para ancho completo */
        header {
            margin-left: 0 !important;
            width: 100% !important;
        }

        /* Sidebar lateral que empieza debajo del header */
        .sidebar-integrated {
            position: fixed;
            left: 0;
            top: 95px; /* 🔼 Ajustado al header espacioso de 95px */
            width: 240px;
            height: calc(100vh - 95px);
            background: white;
            z-index: 800;
            overflow-y: auto;
            font-family: 'Montserrat', sans-serif;
        }

        /* Navegación */
        .sidebar-integrated-nav {
            padding: 20px 0;
        }

        /* Links del menú */
        .sidebar-integrated-link {
            display: flex;
            align-items: center;
            padding: 14px 20px;
            color: #333;
            text-decoration: none;
            font-size: 15px;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .sidebar-integrated-link:hover {
            background: #f5f5f5;
            border-left-color: #366092;
            color: #366092;
        }

        .sidebar-integrated-link.active {
            background: #e6f2ff;
            color: #366092;
            border-left-color: #366092;
            font-weight: 500;
        }

        .sidebar-integrated-icon {
            width: 22px;
            font-size: 16px;
            margin-right: 12px;
            display: inline-block;
            text-align: center;
        }

        /* Separador sutil */
        .sidebar-integrated-divider {
            height: 1px;
            background: #eee;
            margin: 12px 15px;
        }

        /* Ajustar contenido principal */
        main {
            margin-left: 240px !important;
        }

        /* Responsive - ocultar en móvil */
        @media (max-width: 768px) {
            .sidebar-integrated {
                transform: translateX(-240px);
                transition: transform 0.3s;
                box-shadow: none;
                top: 75px; /* 🔼 Header móvil es 75px */
                height: calc(100vh - 75px);
            }

            .sidebar-integrated.mobile-open {
                transform: translateX(0);
                box-shadow: 2px 0 10px rgba(0,0,0,0.2);
            }

            main {
                margin-left: 0 !important;
            }

            .sidebar-mobile-btn {
                display: flex !important;
            }

            .sidebar-mobile-overlay {
                display: block;
            }
        }

        /* Botón toggle móvil */
        .sidebar-mobile-btn {
            position: fixed;
            top: 20px;
            left: 15px;
            z-index: 801;
            background: transparent;
            color: #333;
            border: none;
            width: 42px;
            height: 42px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 22px;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .sidebar-mobile-btn:hover {
            background: #f5f5f5;
        }

        /* Overlay móvil */
        .sidebar-mobile-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.4);
            z-index: 799;
            display: none;
        }

        .sidebar-mobile-overlay.show {
            display: block;
        }

        /* Scrollbar */
        .sidebar-integrated::-webkit-scrollbar {
            width: 5px;
        }

        .sidebar-integrated::-webkit-scrollbar-track {
            background: #f9f9f9;
        }

        .sidebar-integrated::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 3px;
        }

        .sidebar-integrated::-webkit-scrollbar-thumb:hover {
            background: #999;
        }
    `;

    // Obtener permisos del usuario (inyectados desde el backend)
    const permisos = window.userPermissions || {};

    // Función auxiliar para verificar permisos
    function tienePermiso(modulo, accion = 'read') {
        return permisos[modulo] && permisos[modulo][accion] === true;
    }

    // Construir menú dinámicamente según permisos
    let menuHTML = `
                <!-- Inicio -->
                <a href="/home" class="sidebar-integrated-link">
                    <span class="sidebar-integrated-icon">🏠</span>
                    Inicio
                </a>

                <div class="sidebar-integrated-divider"></div>`;

    // BLOQUE 1: CREAR/AÑADIR (solo si tiene permisos de escritura)
    let crearBloque = '';
    if (tienePermiso('clientes', 'write')) {
        crearBloque += `
                <a href="/formulario_lead" class="sidebar-integrated-link">
                    <span class="sidebar-integrated-icon" style="color: #366092;">➕</span>
                    Visita a Instalación
                </a>`;
    }
    if (tienePermiso('administradores', 'write')) {
        crearBloque += `
                <a href="/visita_administrador" class="sidebar-integrated-link">
                    <span class="sidebar-integrated-icon" style="color: #366092;">➕</span>
                    Visita a Administrador
                </a>`;
    }

    if (crearBloque) {
        menuHTML += crearBloque + `
                <div class="sidebar-integrated-divider"></div>`;
    }

    // BLOQUE 2: VER/LISTAR
    menuHTML += `
                <!-- BLOQUE 2: VER/LISTAR -->`;

    if (tienePermiso('clientes', 'read')) {
        menuHTML += `
                <a href="/leads_dashboard" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Instalaciones
                </a>`;
    }
    if (tienePermiso('administradores', 'read')) {
        menuHTML += `
                <a href="/administradores_dashboard" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Administradores
                </a>`;
    }
    if (tienePermiso('oportunidades', 'read')) {
        menuHTML += `
                <a href="/oportunidades" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Oportunidades
                </a>
                <a href="/mi_agenda" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Mi Agenda
                </a>
                <a href="/oportunidades_post_ipo" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Seguimiento Comercial
                </a>`;
    }

    menuHTML += `
                <div class="sidebar-integrated-divider"></div>`;

    // BLOQUE 3: INSPECCIONES (solo para admin)
    if (tienePermiso('inspecciones', 'read')) {
        menuHTML += `
                <!-- BLOQUE 3: INSPECCIONES -->
                <a href="/inspecciones" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Inspecciones (IPOs)
                </a>
                <a href="/defectos_dashboard" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Dashboard de Defectos
                </a>
                <a href="/materiales_especiales" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Cortinas y Pesacargas
                </a>
                <a href="/ocas" class="sidebar-integrated-link" style="padding-left: 54px;">
                    OCAs
                </a>

                <div class="sidebar-integrated-divider"></div>`;
    }

    // Reportes y Configuración (siempre visible)
    menuHTML += `
                <!-- Reportes y Configuración -->
                <a href="/reporte_mensual" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Reporte Mensual
                </a>
                <a href="/configuracion_avisos" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Configuración de Avisos
                </a>`;

    // Administración de Usuarios (solo para admin)
    const perfilActual = window.perfilUsuario || 'visualizador';
    if (perfilActual === 'admin') {
        menuHTML += `
                <a href="/admin/usuarios" class="sidebar-integrated-link" style="padding-left: 54px;">
                    👥 Gestión de Usuarios
                </a>`;
    }

    menuHTML += `
                <div class="sidebar-integrated-divider"></div>

                <!-- Cerrar Sesión al final -->
                <a href="/logout" class="sidebar-integrated-link" style="padding-left: 54px;">
                    Cerrar Sesión
                </a>`;

    // HTML del sidebar
    const sidebarHTML = `
        <!-- Toggle móvil -->
        <button class="sidebar-mobile-btn" onclick="toggleSidebarInt()">☰</button>

        <!-- Overlay móvil -->
        <div class="sidebar-mobile-overlay" id="sidebarIntOverlay" onclick="closeSidebarInt()"></div>

        <!-- Sidebar integrado -->
        <aside class="sidebar-integrated" id="sidebarIntegrated">
            <nav class="sidebar-integrated-nav">
                ${menuHTML}
            </nav>
        </aside>
    `;

    // Insertar CSS
    const style = document.createElement('style');
    style.textContent = sidebarCSS;
    document.head.appendChild(style);

    // Insertar HTML
    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

    // Marcar link activo
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll('.sidebar-integrated-link');
    links.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Funciones móvil
    window.toggleSidebarInt = function() {
        const sidebar = document.getElementById('sidebarIntegrated');
        const overlay = document.getElementById('sidebarIntOverlay');
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('show');
    };

    window.closeSidebarInt = function() {
        const sidebar = document.getElementById('sidebarIntegrated');
        const overlay = document.getElementById('sidebarIntOverlay');
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('show');
    };

    // Cerrar al hacer clic en link en móvil
    links.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeSidebarInt();
            }
        });
    });
})();
