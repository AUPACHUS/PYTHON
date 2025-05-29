// Usar APP_TRACKS pasada desde base.html si está definida, sino un array vacío.
const tracks = typeof APP_TRACKS !== 'undefined' ? APP_TRACKS : [];
const player = new Audio();
let currentTrackIndex = 0;


// Cargar la primera pista
function loadTrack(index) {
    player.src = tracks[index];
    player.load();
}

// Reproducir o pausar
const playButton = document.getElementById("playButton");
if (playButton) {
    playButton.addEventListener("click", () => {
        if (tracks.length === 0) return;
        if (player.paused) {
            player.play();
            playButton.textContent = "⏸ Pausar";
        } else {
            player.pause();
            playButton.textContent = "▶ Reproducir";
        }
    });
}

// Detener
const stopButton = document.getElementById("stopButton");
if (stopButton) {
    stopButton.addEventListener("click", () => {
        if (tracks.length === 0) return;
        player.pause();
        player.currentTime = 0;
        if(playButton) playButton.textContent = "▶ Reproducir";
    });
}

// Siguiente pista
const nextButton = document.getElementById("nextButton");
if (nextButton) {
    nextButton.addEventListener("click", () => {
        if (tracks.length === 0) return;
        currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
        loadTrack(currentTrackIndex);
        player.play();
        if(playButton) playButton.textContent = "⏸ Pausar";
    });
}

// Pista anterior
const prevButton = document.getElementById("prevButton");
if (prevButton) {
    prevButton.addEventListener("click", () => {
        if (tracks.length === 0) return;
        currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
        loadTrack(currentTrackIndex);
        player.play();
        if(playButton) playButton.textContent = "⏸ Pausar";
    });
}

// Selector de pistas
const trackSelector = document.getElementById("trackSelector");
if (trackSelector) {
    trackSelector.addEventListener("change", (e) => {
        if (tracks.length === 0) return;
        const newIndex = parseInt(e.target.value, 10);
        if (!isNaN(newIndex) && tracks[newIndex] !== undefined) {
            currentTrackIndex = newIndex;
            loadTrack(currentTrackIndex);
            player.play();
            if(playButton) playButton.textContent = "⏸ Pausar";
        }
    });
}

const volumeControl = document.getElementById("volumeControl");
if (volumeControl) {
    volumeControl.addEventListener("input", (e) => {
        player.volume = e.target.value;
    });
}

// Inicializar el reproductor
if (tracks.length > 0) {
    loadTrack(currentTrackIndex);
} else {
    // Opcional: Deshabilitar controles si no hay pistas
    if(playButton) playButton.disabled = true;
    if(stopButton) stopButton.disabled = true;
    if(nextButton) nextButton.disabled = true;
    if(prevButton) prevButton.disabled = true;
    if(trackSelector) trackSelector.disabled = true;
    if(volumeControl) volumeControl.disabled = true;
}