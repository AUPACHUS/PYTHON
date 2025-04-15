const player = new Audio();
let currentTrackIndex = 0;

// Lista de pistas
const tracks = [
    "../static/audio/track1.mp3",
    "../static/audio/track2.mp3",
    "../static/audio/track3.mp3"
];

// Cargar la primera pista
function loadTrack(index) {
    player.src = tracks[index];
    player.load();
}

// Reproducir o pausar
document.getElementById("playButton").addEventListener("click", () => {
    if (player.paused) {
        player.play();
        document.getElementById("playButton").textContent = "⏸ Pausar";
    } else {
        player.pause();
        document.getElementById("playButton").textContent = "▶ Reproducir";
    }
});

// Detener
document.getElementById("stopButton").addEventListener("click", () => {
    player.pause();
    player.currentTime = 0;
    document.getElementById("playButton").textContent = "▶ Reproducir";
});

// Siguiente pista
document.getElementById("nextButton").addEventListener("click", () => {
    currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
    loadTrack(currentTrackIndex);
    player.play();
    document.getElementById("playButton").textContent = "⏸ Pausar";
});

// Pista anterior
document.getElementById("prevButton").addEventListener("click", () => {
    currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
    loadTrack(currentTrackIndex);
    player.play();
    document.getElementById("playButton").textContent = "⏸ Pausar";
});

// Control de volumen
document.getElementById("volumeControl").addEventListener("input", (e) => {
    player.volume = e.target.value;
});

// Inicializar el reproductor
loadTrack(currentTrackIndex);