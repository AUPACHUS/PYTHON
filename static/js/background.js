// Usar APP_BACKGROUND_IMAGES pasada desde base.html si está definida, sino un array vacío.
const images = typeof APP_BACKGROUND_IMAGES !== 'undefined' ? APP_BACKGROUND_IMAGES : [];

// Función para cambiar la imagen de fondo
function changeBackground() {
    if (images.length === 0) {
        // console.warn("No background images available for slideshow.");
        return;
    }
    const randomIndex = Math.floor(Math.random() * images.length);
    const backgroundContainer = document.getElementById("background-container");
    if (backgroundContainer) {
        backgroundContainer.style.backgroundImage = `url('${images[randomIndex]}')`;
    }
}

// Cambiar la imagen de fondo cada minuto
if (images.length > 0) {
    changeBackground(); // Llamada inicial
    setInterval(changeBackground, 60000); // Cambiar cada minuto
} else {
    // El fallback será manejado por CSS para #background-container
    // console.log("No dynamic background images. CSS fallback will be used for #background-container.");
}