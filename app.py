from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"  # Necesario para mostrar mensajes flash

# Configuración
app.config['PDF_FOLDER'] = 'static/pdfs'
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# Archivos para almacenar datos
USERS_FILE = "users.json"
OPINIONS_FILE = "opinions.json"

# Cargar datos
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

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
    return redirect(url_for("inteligencia_artificial"))

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