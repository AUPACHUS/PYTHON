document.addEventListener('DOMContentLoaded', function() {
    const backgroundContainer = document.getElementById('dynamic-page-background');

    // APP_BACKGROUND_IMAGE_URLS está definido globalmente en base.html
    if (!backgroundContainer || typeof APP_BACKGROUND_IMAGE_URLS === 'undefined' || APP_BACKGROUND_IMAGE_URLS.length === 0) {
        console.warn("Dynamic background container or APP_BACKGROUND_IMAGE_URLS not found/defined or empty.");
        return;
    }

    let currentBgIndex = -1;
    let bgChangeIntervalId = null;

    function setBackgroundWithFade(imageUrl) {
        if (!imageUrl) return;

        // Inicia el desvanecimiento de salida
        backgroundContainer.style.opacity = 0;

        // Después de que termine la animación de desvanecimiento de salida, cambia la imagen y desvanece la entrada
        setTimeout(() => {
            backgroundContainer.style.backgroundImage = `url('${imageUrl}')`;
            backgroundContainer.style.opacity = 1;
        }, 500); // Esta duración debe coincidir con la transición CSS para la opacidad (0.5s)
    }

    function changeDynamicBackground() {
        if (APP_BACKGROUND_IMAGE_URLS.length === 0) return;

        // Selecciona la siguiente imagen en la secuencia o una aleatoria
        // Para este ejemplo, simplemente cicla a través de ellas
        currentBgIndex = (currentBgIndex + 1) % APP_BACKGROUND_IMAGE_URLS.length;
        const nextImageUrl = APP_BACKGROUND_IMAGE_URLS[currentBgIndex];

        // Precarga la imagen para una transición más suave
        const img = new Image();
        img.onload = () => {
            setBackgroundWithFade(nextImageUrl);
        };
        img.onerror = () => {
            console.error("Error loading background image:", nextImageUrl);
            // Opcionalmente, intenta con la siguiente imagen o salta esta
        };
        img.src = nextImageUrl;
    }

    function startOrResetAutomaticChange() {
        if (bgChangeIntervalId) {
            clearInterval(bgChangeIntervalId);
        }
        if (APP_BACKGROUND_IMAGE_URLS.length > 0) {
            bgChangeIntervalId = setInterval(changeDynamicBackground, 3000); // Cambia cada 3 segundos
        }
    }

    // Cambio inicial de fondo al cargar la página (cubre "cambio al cambiar de sección")
    // Para hacerlo más aleatorio en cada carga de página, elige un índice inicial aleatorio
    if (APP_BACKGROUND_IMAGE_URLS.length > 0) {
        currentBgIndex = Math.floor(Math.random() * APP_BACKGROUND_IMAGE_URLS.length);
         // Llama directamente a setBackgroundWithFade para el primer fondo para evitar doble precarga innecesaria
        const initialImageUrl = APP_BACKGROUND_IMAGE_URLS[currentBgIndex];
        const initialImg = new Image();
        initialImg.onload = () => setBackgroundWithFade(initialImageUrl);
        initialImg.src = initialImageUrl;
    }
    startOrResetAutomaticChange();

    // Manejar clic en el enlace "Inicio"
    // Asegúrate de que tu enlace "Inicio" en base.html tenga id="homeNavLink"
    const homeNavLink = document.querySelector('a.nav-link[href="{{ url_for('home') }}"]'); // O usa un ID si lo tienes
    if (homeNavLink) {
        homeNavLink.addEventListener('click', function() {
            changeDynamicBackground(); // Cambia inmediatamente
            startOrResetAutomaticChange(); // Reinicia el intervalo
        });
    }
});