// script.js

function abrirContenido(elemento) {
    const id = elemento.getAttribute('data-id');
    const titulo = elemento.querySelector('h3').innerText;
    const contenido = elemento.querySelector('p').innerHTML;
  
    // Almacena el contenido en sessionStorage para acceder en la nueva página
    sessionStorage.setItem('contenidoSeleccionado', contenido);
    sessionStorage.setItem('tituloSeleccionado', titulo);
  
    // Abre una nueva pestaña con la página de contenido
    window.open(`/contenido.html?id=${id}`, '_blank');
  }