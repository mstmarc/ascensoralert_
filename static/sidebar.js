// sidebar.js - Menú lateral integrado debajo del header
(function() {
// CSS del menú lateral integrado
const sidebarCSS = `
/* Ajustar header para ancho completo */
header {
margin-left: 0 !important;
width: 100% !important;
}

```
    /* Sidebar lateral que empieza debajo del header */
    .sidebar-integrated {
        position: fixed;
        left: 0;
        top: 120px; /* Ajusta según altura de tu header */
        width: 240px;
        height: calc(100vh - 120px);
        background: white;
        border-right: 1px solid #ddd;
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
        border-left-color: #0066cc;
        color: #0066cc;
    }

    .sidebar-integrated-link.active {
        background: #e6f2ff;
        color: #0066cc;
        border-left-color: #0066cc;
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
        top: 140px;
        left: 15px;
        z-index: 801;
        background: white;
        color: #333;
        border: 1px solid #ddd;
        width: 42px;
        height: 42px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 18px;
        display: none;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
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

// HTML del sidebar
const sidebarHTML = `
    <!-- Toggle móvil -->
    <button class="sidebar-mobile-btn" onclick="toggleSidebarInt()">☰</button>
    
    <!-- Overlay móvil -->
    <div class="sidebar-mobile-overlay" id="sidebarIntOverlay" onclick="closeSidebarInt()"></div>

    <!-- Sidebar integrado -->
    <aside class="sidebar-integrated" id="sidebarIntegrated">
        <nav class="sidebar-integrated-nav">
            <!-- Inicio -->
            <a href="/home" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">🏠</span>
                Inicio
            </a>

            <div class="sidebar-integrated-divider"></div>

            <!-- Leads -->
            <a href="/formulario_lead" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">📋</span>
                Visita a Instalación
            </a>
            <a href="/leads_dashboard" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">📊</span>
                Ver Instalaciones
            </a>

            <div class="sidebar-integrated-divider"></div>

            <!-- Oportunidades -->
            <a href="/oportunidades" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">💰</span>
                Oportunidades
            </a>

            <div class="sidebar-integrated-divider"></div>

            <!-- Visitas Admin -->
            <a href="/visita_administrador" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">👤</span>
                Visita Administrador
            </a>
            <a href="/visitas_admin_dashboard" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">📈</span>
                Visitas Admin
            </a>

            <div class="sidebar-integrated-divider"></div>

            <!-- Reportes -->
            <a href="/reporte_mensual" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">📊</span>
                Reporte Mensual
            </a>

            <div class="sidebar-integrated-divider"></div>

            <!-- Cerrar Sesión al final -->
            <a href="/logout" class="sidebar-integrated-link">
                <span class="sidebar-integrated-icon">🚪</span>
                Cerrar Sesión
            </a>
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
```

})();