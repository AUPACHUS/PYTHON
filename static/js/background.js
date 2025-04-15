// Lista de imágenes en la carpeta "img"
const images = [
    "../static/img/image1.jpg",
    "../static/img/image2.jpg",
    "../static/img/image3.jpg",
    "../static/img/image4.jpg",
    "../static/img/image5.jpg"
];

// Función para cambiar la imagen de fondo
function changeBackground() {
    const randomIndex = Math.floor(Math.random() * images.length);
    const backgroundContainer = document.getElementById("background-container");
    backgroundContainer.style.backgroundImage = `url('${images[randomIndex]}')`;
    backgroundContainer.style.backgroundSize = "cover";
    backgroundContainer.style.backgroundPosition = "center";
    backgroundContainer.style.position = "fixed";
    backgroundContainer.style.top = "0";
    backgroundContainer.style.left = "0";
    backgroundContainer.style.width = "100%";
    backgroundContainer.style.height = "100%";
    backgroundContainer.style.zIndex = "-1";
}

// Cambiar la imagen de fondo cada minuto
changeBackground();
setInterval(changeBackground, 60000);