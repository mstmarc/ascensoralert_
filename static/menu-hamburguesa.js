// menu-hamburguesa.js - Inyecta menú hamburguesa en todas las páginas
(function() {
    // CSS del menú
    const menuCSS = `
        /* Botón hamburguesa */
        .hamburger-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: #1e3c72;
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }

        .hamburger-btn:hover {
            background: #2a5298;
            transform: scale(1.05);
        }

        /* Menú desplegable */
        .hamburger-menu {
            position: fixed;
            top: 0;
            left: -350px;
            width: 320px;
            height: 100vh;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            box-shadow: 2px 0 15px rgba(0,0,0,0.3);
            z-index: 999;
            transition: left 0.3s ease;
            overflow-y: auto;
        }

        .hamburger-menu.open {
            left: 0;
        }

        /* Overlay oscuro */
        .menu-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 998;
            display: none;
        }

        .menu-overlay.show {
            display: block;
        }

        /* Header del menú */
        .menu-header {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.1);
        }

        .menu-header img {
            max-width: 180px;
            margin-bottom: 10px;
        }

        .menu-close {
            position: absolute;
            top: 15px;
            right: 15px;
            background: transparent;
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
            width: 35px;
            height: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 5px;
            transition: background 0.2s;
        }

        .menu-close:hover {
            background: rgba(255,255,255,0.1);
        }

        /* Enlaces del menú */
        .menu-content {
            padding: 20px 0;
        }

        .menu-link {
            display: block;
            padding: 15px 25px;
            color: white;
            text-decoration: none;
            font-size: 16px;
            transition: all 0.2s;
            border-left: 4px solid transparent;
        }

        .menu-link:hover {
            background: rgba(255,255,255,0.1);
            border-left-color: #4CAF50;
            padding-left: 30px;
        }

        .menu-link .emoji {
            display: inline-block;
            width: 30px;
            font-size: 18px;
        }

        /* Secciones */
        .menu-section {
            margin: 10px 0;
        }

        .menu-section-title {
            padding: 15px 25px 10px;
            color: rgba(255,255,255,0.6);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: bold;
        }

        .menu-divider {
            height: 1px;
            background: rgba(255,255,255,0.1);
            margin: 15px 20px;
        }

        /* Usuario info */
        .menu-footer {
            position: absolute;
            bottom: 0;
            width: 100%;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        .menu-user {
            color: white;
            font-size: 14px;
            margin-bottom: 10px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hamburger-menu {
                width: 280px;
                left: -280px;
            }
        }
    `;

    // HTML del menú
    const menuHTML = `
        <!-- Botón Hamburguesa -->
        <button class="hamburger-btn" onclick="abrirMenu()">☰</button>

        <!-- Overlay -->
        <div class="menu-overlay" id="menuOverlay" onclick="cerrarMenu()"></div>

        <!-- Menú -->
        <nav class="hamburger-menu" id="hamburguerMenu">
            <div class="menu-header">
                <button class="menu-close" onclick="cerrarMenu()">✕</button>
                <img src="/static/logo-fedes-ascensores.png" alt="Fedes Ascensores">
            </div>

            <div class="menu-content">
                <!-- Inicio -->
                <a href="/home" class="menu-link">
                    <span class="emoji">🏠</span> Inicio
                </a>

                <div class="menu-divider"></div>

                <!-- Leads -->
                <div class="menu-section">
                    <div class="menu-section-title">Leads & Visitas</div>
                    <a href="/formulario" class="menu-link">
                        <span class="emoji">📋</span> Nueva Visita
                    </a>
                    <a href="/leads" class="menu-link">
                        <span class="emoji">📊</span> Dashboard Leads
                    </a>
                </div>

                <div class="menu-divider"></div>

                <!-- Equipos -->
                <div class="menu-section">
                    <div class="menu-section-title">Equipos</div>
                    <a href="/nuevo_equipo" class="menu-link">
                        <span class="emoji">🔧</span> Nuevo Equipo
                    </a>
                </div>

                <div class="menu-divider"></div>

                <!-- Oportunidades -->
                <div class="menu-section">
                    <div class="menu-section-title">Oportunidades</div>
                    <a href="/oportunidades" class="menu-link">
                        <span class="emoji">💰</span> Ver Oportunidades
                    </a>
                    <a href="/crear_oportunidad" class="menu-link">
                        <span class="emoji">➕</span> Nueva Oportunidad
                    </a>
                </div>

                <div class="menu-divider"></div>

                <!-- Administradores de Fincas -->
                <div class="menu-section">
                    <div class="menu-section-title">Administradores de Fincas</div>
                    <a href="/admin/administradores" class="menu-link">
                        <span class="emoji">🏢</span> Ver Administradores
                    </a>
                    <a href="/nuevo_administrador" class="menu-link">
                        <span class="emoji">➕</span> Nuevo Administrador
                    </a>
                </div>

                <div class="menu-divider"></div>

                <!-- Visitas Admin -->
                <div class="menu-section">
                    <div class="menu-section-title">Visitas Administrador</div>
                    <a href="/visita_administrador" class="menu-link">
                        <span class="emoji">👤</span> Nueva Visita
                    </a>
                    <a href="/visitas_administradores_dashboard" class="menu-link">
                        <span class="emoji">📈</span> Dashboard Visitas
                    </a>
                </div>

                <div class="menu-divider"></div>

                <!-- Reportes -->
                <a href="/reporte_mensual" class="menu-link">
                    <span class="emoji">📊</span> Reporte Mensual
                </a>
            </div>

            <div class="menu-footer">
                <div class="menu-user">👤 Usuario</div>
                <a href="/logout" class="menu-link" style="padding: 10px 0;">
                    <span class="emoji">🚪</span> Cerrar Sesión
                </a>
            </div>
        </nav>
    `;

    // Insertar CSS
    const style = document.createElement('style');
    style.textContent = menuCSS;
    document.head.appendChild(style);

    // Insertar HTML
    document.body.insertAdjacentHTML('afterbegin', menuHTML);

    // Funciones globales
    window.abrirMenu = function() {
        document.getElementById('hamburguerMenu').classList.add('open');
        document.getElementById('menuOverlay').classList.add('show');
        document.body.style.overflow = 'hidden'; // Evita scroll del body
    };

    window.cerrarMenu = function() {
        document.getElementById('hamburguerMenu').classList.remove('open');
        document.getElementById('menuOverlay').classList.remove('show');
        document.body.style.overflow = 'auto';
    };

    // Cerrar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarMenu();
        }
    });
})();
