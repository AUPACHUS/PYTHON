document.addEventListener('DOMContentLoaded', function() {
    const backgroundContainer = document.getElementById('dynamic-page-background');
    const TRANSITION_DURATION = 500; // 0.5s - debe coincidir con CSS
    const CHANGE_INTERVAL = 10000; // 10 segundos entre cambios

    // Verificar requisitos mínimos
    if (!backgroundContainer || !window.APP_BACKGROUND_IMAGE_URLS || APP_BACKGROUND_IMAGE_URLS.length === 0) {
        console.warn("Dynamic background disabled - container or image URLs not available");
        return;
    }

    let currentBgIndex = -1;
    let bgChangeIntervalId = null;
    let isTransitioning = false;

    // Precargar todas las imágenes
    function preloadImages() {
        APP_BACKGROUND_IMAGE_URLS.forEach(url => {
            const img = new Image();
            img.src = url;
        });
    }

    // Cambiar el fondo con efecto fade
    function setBackgroundWithFade(imageUrl) {
        if (isTransitioning || !imageUrl) return;
        
        isTransitioning = true;
        
        // Fade out
        backgroundContainer.style.opacity = 0;
        
        // Cambiar imagen después de la transición
        setTimeout(() => {
            backgroundContainer.style.backgroundImage = `url('${imageUrl}')`;
            
            // Fade in
            setTimeout(() => {
                backgroundContainer.style.opacity = 1;
                isTransitioning = false;
            }, 50); // Pequeño delay para asegurar el cambio
        }, TRANSITION_DURATION);
    }

    // Seleccionar próxima imagen (round-robin o aleatorio)
    function getNextImageIndex() {
        // Alternativa: return Math.floor(Math.random() * APP_BACKGROUND_IMAGE_URLS.length);
        return (currentBgIndex + 1) % APP_BACKGROUND_IMAGE_URLS.length;
    }

    // Cambiar al siguiente fondo
    function changeDynamicBackground() {
        if (APP_BACKGROUND_IMAGE_URLS.length === 0 || isTransitioning) return;
        
        currentBgIndex = getNextImageIndex();
        const nextImageUrl = APP_BACKGROUND_IMAGE_URLS[currentBgIndex];
        
        // Verificar si la imagen ya está cargada
        const img = new Image();
        img.onload = () => setBackgroundWithFade(nextImageUrl);
        img.onerror = () => {
            console.error("Error loading background image, skipping:", nextImageUrl);
            // Reintentar con la siguiente imagen
            setTimeout(changeDynamicBackground, 1000);
        };
        img.src = nextImageUrl;
    }

    // Iniciar/Restablecer el cambio automático
    function startBackgroundRotation() {
        stopBackgroundRotation();
        bgChangeIntervalId = setInterval(changeDynamicBackground, CHANGE_INTERVAL);
    }

    function stopBackgroundRotation() {
        if (bgChangeIntervalId) {
            clearInterval(bgChangeIntervalId);
            bgChangeIntervalId = null;
        }
    }

    // Inicialización
    function initDynamicBackground() {
        // Precargar imágenes
        preloadImages();
        
        // Establecer fondo inicial
        currentBgIndex = Math.floor(Math.random() * APP_BACKGROUND_IMAGE_URLS.length);
        const initialImageUrl = APP_BACKGROUND_IMAGE_URLS[currentBgIndex];
        
        const img = new Image();
        img.onload = () => {
            backgroundContainer.style.backgroundImage = `url('${initialImageUrl}')`;
            backgroundContainer.style.opacity = 1;
            
            // Iniciar rotación después de un delay
            setTimeout(startBackgroundRotation, CHANGE_INTERVAL);
        };
        img.onerror = () => {
            console.error("Error loading initial background image:", initialImageUrl);
            startBackgroundRotation(); // Intentar con la siguiente
        };
        img.src = initialImageUrl;
    }

    // Event Listeners
    function setupEventListeners() {
        // Pausar rotación cuando la pestaña no está visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopBackgroundRotation();
            } else {
                startBackgroundRotation();
            }
        });
        
        // Cambio manual al hacer clic en el logo/inicio
        const homeLinks = document.querySelectorAll('a[href="{{ url_for('home') }}"], .logo');
        homeLinks.forEach(link => {
            link.addEventListener('click', () => {
                changeDynamicBackground();
                startBackgroundRotation();
            });
        });
    }

    // Iniciar todo
    initDynamicBackground();
    setupEventListeners();
});