// Ensure Tone.js and @tonejs/midi are included in your HTML file as script tags.

// Asegúrate de incluir Tone.js y @tonejs/midi desde un CDN en tu HTML

async function playMidi() {
    // Cargar el archivo MIDI desde la carpeta static
    const response = await fetch("../static/Title01.mid");
    const arrayBuffer = await response.arrayBuffer();

    // Parsear el archivo MIDI
    const midi = new Midi(arrayBuffer);

    // Reproducir cada pista del MIDI
    midi.tracks.forEach(track => {
        const synth = new Tone.PolySynth(Tone.Synth).toDestination();
        track.notes.forEach(note => {
            synth.triggerAttackRelease(note.name, note.duration, note.time);
        });
    });
}

// Manejar los botones de reproducción y detención
document.getElementById('playButton').addEventListener('click', async () => {
    await Tone.start(); // Asegúrate de que Tone.js esté iniciado
    playMidi();
});

document.getElementById('stopButton').addEventListener('click', () => {
    Tone.Transport.stop(); // Detener la reproducción
});