from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin # For constructing absolute URLs
from werkzeug.security import generate_password_hash, check_password_hash # Import for password hashing

app = Flask(__name__)
app.secret_key = "secret_key"  # Necesario para mostrar mensajes flash

# Configuración
app.config['PDF_FOLDER'] = 'static/pdfs'
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# Carpetas para audio e imágenes de fondo
AUDIO_FOLDER_NAME = 'audio'
BACKGROUND_IMG_FOLDER_NAME = os.path.join('img', 'backgrounds')
os.makedirs(os.path.join(app.static_folder, AUDIO_FOLDER_NAME), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, BACKGROUND_IMG_FOLDER_NAME), exist_ok=True)

# Archivos para almacenar datos
USERS_FILE = "users.json"
OPINIONS_FILE = "opinions.json"
NEWS_FILE = "news.json"

# Cargar datos
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip(): # Check if content is empty or just whitespace
                app.logger.warning(f"File {file} is empty or contains only whitespace. Returning empty list.")
                return [] # Consistent default for problematic files
            return json.loads(content)
    except FileNotFoundError:
        app.logger.info(f"File {file} not found. Returning empty list.")
        return []
    except json.JSONDecodeError as e:
        # Log a snippet of the content for easier debugging
        content_snippet = ""
        try:
            with open(file, "r", encoding="utf-8") as f_err: # Re-open to get content if `content` var is not in scope
                content_snippet = f_err.read(200) # Read first 200 chars
        except Exception:
            pass # Ignore if re-reading fails
        app.logger.error(f"Error decoding JSON from {file}: {e}. Content snippet: '{content_snippet}...'. Returning empty list.")
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Función para obtener noticias de Reuters
def fetch_reuters_news():
    url = "https://www.reuters.com/world/"
    base_reuters_url = "https://www.reuters.com"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching Reuters news: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    headlines_data = []
    processed_urls = set() # To avoid duplicates

    # Selectors might need adjustment if Reuters changes their HTML structure.
    # This attempts to find elements containing title text and their associated links.
    # Common pattern: title text is within an <a> tag, or an <a> tag is a close parent.
    title_text_elements = soup.select(".story-title, .MediaStoryCard__title__2PHMe, [data-testid='Heading']")

    for text_el in title_text_elements:
        if len(headlines_data) >= 6:  # Limitar a 6 noticias
            break

        title = text_el.get_text(strip=True)
        
        # Find the closest ancestor <a> tag with an href
        link_tag = text_el.find_parent('a', href=True)
        
        # If the text_el itself is an <a> tag
        if not link_tag and text_el.name == 'a' and text_el.has_attr('href'):
            link_tag = text_el
            
        if title and link_tag and len(title) > 5: # Basic filter for meaningful titles
            href = link_tag.get('href')
            if href:
                absolute_url = urljoin(base_reuters_url, href)
                if absolute_url not in processed_urls: # Avoid duplicates
                    headlines_data.append({"title": title, "url": absolute_url})
                    processed_urls.add(absolute_url)

    save_data(NEWS_FILE, {"last_updated": time.time(), "headlines": headlines_data})
    return headlines_data

# Función para cargar noticias (y actualizarlas si es necesario)
def get_news():
    news_data_raw = load_data(NEWS_FILE)
    
    # Ensure news_data is a dictionary
    if isinstance(news_data_raw, dict):
        news_data = news_data_raw
    else:
        app.logger.warning(
            f"Data loaded from {NEWS_FILE} is not a dictionary (type: {type(news_data_raw)}). "
            f"Assuming corrupted or initial state. Content snippet: '{str(news_data_raw)[:100]}...'"
        )
        news_data = {} # Default to an empty dict to prevent further errors with .get()

    last_updated = news_data.get("last_updated", 0) # Safely get, defaults to 0 if key missing or news_data is {}
    headlines = news_data.get("headlines", [])     # Safely get, defaults to [] if key missing or news_data is {}

    # Actualizar noticias si han pasado más de 5 días o si no hay titulares
    # Also update if news_data was empty/corrupt (which would make last_updated=0 and headlines=[])
    if time.time() - last_updated > 5 * 24 * 60 * 60 or not headlines or not news_data:
        app.logger.info(f"Updating news. Reason: timeout, no headlines, or problematic file.")
        headlines = fetch_reuters_news() # fetch_reuters_news fetches, saves, and returns the new headlines list
    return headlines

# Context processor para inyectar datos compartidos en las plantillas
@app.context_processor
def inject_shared_data():
    # Pistas de música
    music_tracks_data = []
    audio_dir_path = os.path.join(app.static_folder, AUDIO_FOLDER_NAME)
    if os.path.exists(audio_dir_path):
        valid_audio_files = sorted([f for f in os.listdir(audio_dir_path) if f.lower().endswith('.mp3')])
        for i, f_name in enumerate(valid_audio_files):
            # Intenta crear un nombre más amigable, quitando la extensión y reemplazando guiones bajos
            track_name_base = os.path.splitext(f_name)[0].replace('_', ' ').replace('-', ' ')
            music_tracks_data.append({"name": f"{track_name_base.title()}", "filename": f_name})

    # Imágenes de fondo
    background_images_data = []
    background_img_dir_path = os.path.join(app.static_folder, BACKGROUND_IMG_FOLDER_NAME)
    if os.path.exists(background_img_dir_path):
        background_images_data = sorted([
            f for f in os.listdir(background_img_dir_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ])
    return dict(
        music_tracks=music_tracks_data,
        background_images=background_images_data,
        current_endpoint=request.endpoint, # Para la navegación activa
        audio_folder_name=AUDIO_FOLDER_NAME,
        background_img_folder_name=BACKGROUND_IMG_FOLDER_NAME
    )
# Ruta principal
@app.route("/")
def home():
    return render_template("index.html")

# Ruta para ver PDFs
@app.route("/ver_pdfs")
def ver_pdfs():
    pdf_folder = os.path.join(app.root_path, 'static', 'pdfs')
    pdfs = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    return render_template("pdfs.html", pdfs=pdfs)

# Ruta para subir PDFs
@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if 'pdf' not in request.files:
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("ver_pdfs"))

    file = request.files['pdf']
    if file.filename == '':
        flash("El archivo no tiene nombre.")
        return redirect(url_for("ver_pdfs"))

    if file and file.filename.endswith('.pdf'):
        file.save(os.path.join(app.config['PDF_FOLDER'], file.filename))
        flash("Archivo subido exitosamente.")
    else:
        flash("Solo se permiten archivos PDF.")
    return redirect(url_for("ver_pdfs"))

# Ruta para descargar PDFs
@app.route('/pdf/<filename>')
def download_pdf(filename):
    return send_from_directory(app.config['PDF_FOLDER'], filename)

@app.route("/galeria")
def galeria():
    img_folder = os.path.join(app.root_path, 'static', 'img')
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    img_files = [f for f in os.listdir(img_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template("galeria.html", images=img_files)

# Ruta para la página de IA
@app.route("/inteligencia_artificial")
def inteligencia_artificial():
    return render_template("inteligencia_artificial.html")

# Ruta para registrar usuarios
@app.route("/register_user", methods=["POST"])
def register_user():
    users = load_data(USERS_FILE)
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"] # Plain text password from form

    # Validar si el usuario ya existe
    if any(user["email"] == email for user in users):
        flash("El usuario ya está registrado.")
        return redirect(url_for("inteligencia_artificial"))

    hashed_password = generate_password_hash(password) # Hash the password
    # Guardar nuevo usuario
    users.append({"username": username, "email": email, "password": hashed_password}) # Store the hashed password
    save_data(USERS_FILE, users)
    flash("Usuario registrado exitosamente.")
    return redirect(url_for("inteligencia_artificial"))

# Ruta para la página de opiniones
@app.route("/opinion")
def opinion():
    headlines = get_news()  # Obtener noticias actualizadas
    opinions = load_data(OPINIONS_FILE)  # Cargar opiniones desde el archivo
    return render_template("opinion.html", headlines=headlines, opinions=opinions)

# Ruta para enviar opiniones
@app.route("/submit_opinion", methods=["POST"])
def submit_opinion():
    opinions = load_data(OPINIONS_FILE)
    username = request.form.get("username", "Anónimo")
    text = request.form["opinion"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Guardar opinión
    opinions.append({"username": username, "text": text, "date": date})
    save_data(OPINIONS_FILE, opinions)
    flash("Opinión enviada exitosamente.")
    return redirect(url_for("opinion"))

@app.route("/social")
def social():
    return render_template("social.html")

@app.route("/cursos")
def cursos():
    return render_template("cursos.html")

@app.route("/enlaces")
def enlaces():
    return render_template("enlaces.html")

if __name__ == "__main__":
    app.run(debug=True)