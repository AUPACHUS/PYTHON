from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
app.secret_key = "secret_key"  # Necesario para mostrar mensajes flash

# Configuración
app.config['PDF_FOLDER'] = 'static/pdfs'
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# Archivos para almacenar datos
USERS_FILE = "users.json"
OPINIONS_FILE = "opinions.json"
NEWS_FILE = "news.json"

# Cargar datos
def load_data(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Función para obtener noticias de Reuters
def fetch_reuters_news():
    url = "https://www.reuters.com/world/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extraer titulares de noticias
    headlines = []
    for item in soup.select(".story-title, .MediaStoryCard__title__2PHMe"):
        if len(headlines) >= 6:  # Limitar a 6 noticias
            break
        headlines.append(item.get_text(strip=True))

    # Guardar las noticias en un archivo JSON
    save_data(NEWS_FILE, {"last_updated": time.time(), "headlines": headlines})
    return headlines

# Función para cargar noticias (y actualizarlas si es necesario)
def get_news():
    news_data = load_data(NEWS_FILE)
    last_updated = news_data.get("last_updated", 0)
    headlines = news_data.get("headlines", [])

    # Verificar si han pasado más de 5 días (5 * 24 * 60 * 60 segundos)
    if time.time() - last_updated > 5 * 24 * 60 * 60 or not headlines:
        headlines = fetch_reuters_news()

    return headlines

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
    password = request.form["password"]

    # Validar si el usuario ya existe
    if any(user["email"] == email for user in users):
        flash("El usuario ya está registrado.")
        return redirect(url_for("inteligencia_artificial"))

    # Guardar nuevo usuario
    users.append({"username": username, "email": email, "password": password})
    save_data(USERS_FILE, users)
    flash("Usuario registrado exitosamente.")
    return redirect(url_for("inteligencia_artificial"))

# Ruta para la página de opiniones
@app.route("/opinion")
def opinion():
    url = "https://api.apitube.io/v1/news/everything?per_page=10"
    headers = {
        "X-API-Key": "api_live_wMikbbtvTMXb1dxOF9NXyieu5eB8m0DGNW0HUFWUQat"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Ajusta esto según la estructura real de la respuesta de apitube
        headlines = [item.get("title", "Sin título") for item in data.get("data", [])]
    else:
        headlines = ["No se pudieron cargar las noticias."]
    opinions = load_data(OPINIONS_FILE)
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

@app.before_request
def require_login():
    # Permitir acceso solo a login y static antes de iniciar sesión
    if request.endpoint not in ('login', 'static') and 'username' not in session:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        day = request.form.get("day")
        if username and password and day:
            session['username'] = username
            session['day'] = day
            flash(f"¡Bienvenido, {username}! Recuerda que hoy es {day}.")
            return redirect(url_for("home"))
        else:
            flash("Por favor, completa todos los campos.")
    return '''
    <form method="post">
        <h2>Registro</h2>
        <label>Nombre:</label><br>
        <input type="text" name="username" required><br>
        <label>Contraseña:</label><br>
        <input type="password" name="password" required><br>
        <label>Día de la semana favorito:</label><br>
        <input type="text" name="day" required><br>
        <button type="submit">Entrar</button>
    </form>
    <p>Por favor, pon tu nombre y un día de la semana favorito para continuar.</p>
    '''

if __name__ == "__main__":
    app.run(debug=True)