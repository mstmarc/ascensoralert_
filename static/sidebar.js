// sidebar.js - Menú lateral fijo integrado
(function() {
    // CSS del menú lateral fijo
    const sidebarCSS = `
        /* Layout principal con sidebar */
        body {
            margin: 0;
            padding: 0;
        }

        /* Sidebar fijo */
        .sidebar-fixed {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: #f8f9fa;
            border-right: 1px solid #e0e0e0;
            z-index: 900;
            overflow-y: auto;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* Logo en sidebar */
        .sidebar-logo {
            padding: 25px 20px;
            text-align: center;
            background: white;
            border-bottom: 1px solid #e0e0e0;
        }

        .sidebar-logo img {
            max-width: 180px;
            height: auto;
        }

        /* Navegación */
        .sidebar-nav {
            padding: 20px 0;
        }

        /* Links del menú */
        .sidebar-link {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            color: #495057;
            text-decoration: none;
            font-size: 15px;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }

        .sidebar-link:hover {
            background: #e9ecef;
            color: #1e3c72;
            border-left-color: #1e3c72;
        }

        .sidebar-link.active {
            background: #e7f1ff;
            color: #1e3c72;
            border-left-color: #1e3c72;
            font-weight: 500;
        }

        .sidebar-icon {
            width: 24px;
            font-size: 18px;
            margin-right: 12px;
            display: inline-block;
            text-align: center;
        }

        /* Títulos de sección */
        .sidebar-section-title {
            padding: 20px 20px 8px;
            font-size: 11px;
            font-weight: 600;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Separador */
        .sidebar-divider {
            height: 1px;
            background: #e0e0e0;
            margin: 15px 15px;
        }

        /* Footer del sidebar */
        .sidebar-footer {
            position: absolute;
            bottom: 0;
            width: 100%;
            padding: 15px 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .sidebar-user {
            font-size: 13px;
            color: #6c757d;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }

        .sidebar-user-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #1e3c72;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 14px;
        }

        /* Ajustar contenido principal */
        header, main {
            margin-left: 260px;
        }

        /* Responsive - ocultar en móvil */
        @media (max-width: 768px) {
            .sidebar-fixed {
                transform: translateX(-260px);
                transition: transform 0.3s;
            }

            .sidebar-fixed.mobile-open {
                transform: translateX(0);
                box-shadow: 2px 0 10px rgba(0,0,0,0.2);
            }

            header, main {
                margin-left: 0;
            }

            /* Botón toggle para móvil */
            .sidebar-mobile-toggle {
                display: flex !important;
            }

            /* Overlay para móvil */
            .sidebar-overlay-mobile {
                display: block;
            }
        }

        /* Botón toggle móvil */
        .sidebar-mobile-toggle {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 901;
            background: #1e3c72;
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 20px;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .sidebar-mobile-toggle:hover {
            background: #2a5298;
        }

        /* Overlay móvil */
        .sidebar-overlay-mobile {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 899;
            display: none;
        }

        .sidebar-overlay-mobile.show {
            display: block;
        }

        /* Scrollbar personalizado */
        .sidebar-fixed::-webkit-scrollbar {
            width: 6px;
        }

        .sidebar-fixed::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        .sidebar-fixed::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }

        .sidebar-fixed::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    `;

    // HTML del sidebar
    const sidebarHTML = `
        <!-- Toggle móvil -->
        <button class="sidebar-mobile-toggle" onclick="toggleSidebarMobile()">☰</button>
        
        <!-- Overlay móvil -->
        <div class="sidebar-overlay-mobile" id="sidebarOverlay" onclick="closeSidebarMobile()"></div>

        <!-- Sidebar fijo -->
        <aside class="sidebar-fixed" id="sidebarFixed">
            <!-- Logo -->
            <div class="sidebar-logo">
                <a href="/home">
                    <img src="/static/logo-fedes-ascensores.png" alt="Fedes Ascensores">
                </a>
            </div>

            <!-- Navegación -->
            <nav class="sidebar-nav">
                <!-- Inicio -->
                <a href="/home" class="sidebar-link">
                    <span class="sidebar-icon">🏠</span>
                    Inicio
                </a>

                <div class="sidebar-divider"></div>

                <!-- Leads & Visitas -->
                <div class="sidebar-section-title">Leads & Visitas</div>
                <a href="/formulario" class="sidebar-link">
                    <span class="sidebar-icon">📋</span>
                    Nueva Visita
                </a>
                <a href="/leads_dashboard" class="sidebar-link">
                    <span class="sidebar-icon">📊</span>
                    Dashboard Leads
                </a>

                <div class="sidebar-divider"></div>

                <!-- Equipos -->
                <div class="sidebar-section-title">Equipos</div>
                <a href="/nuevo_equipo" class="sidebar-link">
                    <span class="sidebar-icon">🔧</span>
                    Nuevo Equipo
                </a>

                <div class="sidebar-divider"></div>

                <!-- Oportunidades -->
                <div class="sidebar-section-title">Oportunidades</div>
                <a href="/oportunidades" class="sidebar-link">
                    <span class="sidebar-icon">💰</span>
                    Ver Oportunidades
                </a>
                <a href="/crear_oportunidad" class="sidebar-link">
                    <span class="sidebar-icon">➕</span>
                    Nueva Oportunidad
                </a>

                <div class="sidebar-divider"></div>

                <!-- Visitas Administrador -->
                <div class="sidebar-section-title">Visitas Administrador</div>
                <a href="/visita_administrador" class="sidebar-link">
                    <span class="sidebar-icon">👤</span>
                    Nueva Visita
                </a>
                <a href="/visitas_admin_dashboard" class="sidebar-link">
                    <span class="sidebar-icon">📈</span>
                    Dashboard
                </a>

                <div class="sidebar-divider"></div>

                <!-- Reportes -->
                <a href="/reporte_mensual" class="sidebar-link">
                    <span class="sidebar-icon">📊</span>
                    Reporte Mensual
                </a>

                <!-- Espacio para el footer -->
                <div style="height: 80px;"></div>
            </nav>

            <!-- Footer -->
            <div class="sidebar-footer">
                <div class="sidebar-user">
                    <div class="sidebar-user-icon">👤</div>
                    <span>Usuario</span>
                </div>
                <a href="/logout" class="sidebar-link" style="padding: 8px 0; font-size: 14px;">
                    <span class="sidebar-icon">🚪</span>
                    Cerrar Sesión
                </a>
            </div>
        </aside>
    `;

    // Insertar CSS
    const style = document.createElement('style');
    style.textContent = sidebarCSS;
    document.head.appendChild(style);

    // Insertar HTML
    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

    // Marcar link activo según la URL actual
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll('.sidebar-link');
    links.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Funciones para móvil
    window.toggleSidebarMobile = function() {
        const sidebar = document.getElementById('sidebarFixed');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('show');
    };

    window.closeSidebarMobile = function() {
        const sidebar = document.getElementById('sidebarFixed');
        const overlay = document.getElementById('sidebarOverlay');
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('show');
    };

    // Cerrar al hacer clic en un link en móvil
    links.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeSidebarMobile();
            }
        });
    });
})();
