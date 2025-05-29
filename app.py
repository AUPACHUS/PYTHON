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
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) # Root directory of the app

# Configuración
# Use absolute path for PDF_FOLDER
PDF_DIR_NAME = 'pdfs'
STATIC_DIR_NAME = 'static'

# Absolute path to the static folder (Flask usually sets app.static_folder to an absolute path)
ABS_STATIC_FOLDER = os.path.join(APP_ROOT, STATIC_DIR_NAME) if not os.path.isabs(app.static_folder) else app.static_folder

app.config['PDF_FOLDER'] = os.path.join(ABS_STATIC_FOLDER, PDF_DIR_NAME)
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

# Función para cargar variables de entorno desde un archivo .ENV
def load_env_vars(filepath=".ENV"):
    env_vars = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"') # Elimina comillas si las hay
    except FileNotFoundError:
        app.logger.warning(f"Archivo de entorno {filepath} no encontrado. Las claves API podrían faltar.")
    return env_vars

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

# Cargar la clave API de NewsAPI al iniciar la aplicación
# ENV_CONFIG = load_env_vars() # Anteriormente se cargaba desde el archivo .ENV
# NEWSAPI_API_KEY = ENV_CONFIG.get("NEWSAPI_API_KEY") # Anteriormente se obtenía de ENV_CONFIG
NEWSAPI_API_KEY = "5dacd13ae1244d20bf78bd9c4d852e66" # Clave API directamente asignada

# Función para obtener noticias de NewsAPI
def fetch_newsapi_news():
    if not NEWSAPI_API_KEY:
        app.logger.error("La clave API de NewsAPI no está configurada. No se pueden obtener noticias.")
        return []

    # Obtener titulares principales de España, máximo 6 artículos
    api_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_API_KEY}&pageSize=6"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        api_response_data = response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error al contactar NewsAPI: {e}")
        return []
    except json.JSONDecodeError as e:
        app.logger.error(f"Error al decodificar la respuesta JSON de NewsAPI: {e}")
        return []

    headlines_data = []
    if api_response_data.get("status") == "ok":
        articles = api_response_data.get("articles", [])
        for article in articles:
            title = article.get("title")
            article_url = article.get("url")

            # vacíos, marcados como eliminados, y asegurar que hay URL
            if title and article_url and "[Removed]" not in title and title.strip():
                headlines_data.append({"title": title, "url": article_url})
            # Aunque pedimos pageSize=6, aseguramos no pasar de 6 por si acaso
            if len(headlines_data) >= 6:
                break
        if not headlines_data and articles:
            app.logger.info("NewsAPI devolvió artículos, pero todos fueron filtrados o no cumplieron los criterios.")
        elif not articles:
            app.logger.info("NewsAPI devolvió status 'ok' pero la lista de artículos estaba vacía.")

    else:
        app.logger.error(f"NewsAPI devolvió un error: Status: {api_response_data.get('status')}, Mensaje: {api_response_data.get('message')}")

    save_data(NEWS_FILE, {"last_updated": time.time(), "headlines": headlines_data})
    return headlines_data

# La función fetch_rtve_news() ya no es necesaria, la comentamos o eliminamos.
# def fetch_rtve_news():
#     url = "https://www.rtve.es/noticias/"
#     base_rtve_url = "https://www.rtve.es"
#     # ... (resto del código de fetch_rtve_news) ...
#     save_data(NEWS_FILE, {"last_updated": time.time(), "headlines": headlines_data})
#     return headlines_data


# Función para cargar noticias (y actualizarlas si es necesario)
def get_news():
    news_data_raw = load_data(NEWS_FILE)
    
    # Ensure news_data is a dictionary
    if isinstance(news_data_raw, dict):
        news_data = news_data_raw
    else:
        app.logger.warning( # Corrected logger warning
            f"Data loaded from {NEWS_FILE} is not a dictionary (type: {type(news_data_raw)}). "
            f"Assuming corrupted or initial state. Content snippet: '{str(news_data_raw)[:100]}...'"
        )
        news_data = {} # Default to an empty dict to prevent further errors with .get()

    last_updated = news_data.get("last_updated", 0) # Safely get, defaults to 0 if key missing or news_data is {}
    headlines = news_data.get("headlines", [])     # Safely get, defaults to [] if key missing or news_data is {}

    # Actualizar noticias si ha pasado más de 1 hora o si no hay titulares
    # Also update if news_data was empty/corrupt (which would make last_updated=0 and headlines=[])
    if time.time() - last_updated > 1 * 60 * 60 or not headlines or not news_data: # Actualizar cada hora
        app.logger.info(f"Updating news. Reason: timeout, no headlines, or problematic file.")
        headlines = fetch_newsapi_news() # Llamar a la nueva función para NewsAPI
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
    pdf_folder_abs = app.config['PDF_FOLDER']
    if not os.path.isdir(pdf_folder_abs): # Check if directory exists
        app.logger.error(f"PDF folder not found at: {pdf_folder_abs}")
        flash("Error: La carpeta de PDFs no se encuentra o no es accesible.")
        pdfs = []
    else:
        pdfs = [f for f in os.listdir(pdf_folder_abs) if f.endswith('.pdf')]
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
@app.route("/inteligencia_artificial") # Moved to the correct top-level scope
def inteligencia_artificial():
    return render_template("inteligencia_artificial.html")

# Ruta para registrar usuarios
@app.route("/register_user", methods=["POST"])
def register_user():
    users = load_data(USERS_FILE)
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not all([username, email, password]):
        flash("Todos los campos (nombre de usuario, email, contraseña) son requeridos.")
        # Assuming the registration form is on inteligencia_artificial.html or a dedicated registration page
        return redirect(url_for("inteligencia_artificial")) # Or your registration page

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
    username = request.form.get("username", "Anónimo") # Keeps default if username is empty
    text = request.form.get("opinion")

    if not text or not text.strip():
        flash("El texto de la opinión no puede estar vacío.")
        return redirect(url_for("opinion"))
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
    # Para desarrollo local, puedes activar el debug explícitamente.
    # En producción, el servidor WSGI (Gunicorn) ejecutará la app,
    # y el modo debug debería estar desactivado.
    # Las plataformas de hosting suelen permitir configurar FLASK_DEBUG=0 como variable de entorno.
    # Si FLASK_DEBUG no está configurada, Flask _DEBUG se establece en False por defecto.
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=debug_mode)