"""
AdoteUmGatoMoc — backend.

Framework: Flask
Banco de dados: SQLite (banco.db, criado automaticamente ao rodar c/ python)

Rotas dinâmicas:
    GET/POST /cadastro/tela.html      
    GET/POST /cadastro/minhaconta.html 
    GET       /cadastro/conta.html    
    GET       /logout                  

Todo o resto do site (newindex.html, imagens, css, etc.) é servido
como arquivo estático, mantendo a mesma estrutura de pastas do projeto.
"""

import os
import re
import sqlite3

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")

database.init_db()


def email_valido(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


def apenas_digitos(texto):
    return re.sub(r"\D", "", texto or "")


@app.route("/cadastro/tela.html", methods=["GET", "POST"])
def cadastro():
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("conta"))
        return render_template("cadastro/tela.html", valores=None)

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefone = request.form.get("telefone", "").strip()
    senha = request.form.get("senha", "")
    confirmar_senha = request.form.get("confirmar_senha", "")

    valores = {"nome": nome, "email": email, "telefone": telefone}

    erro = None
    if not nome:
        erro = "Por favor, digite seu nome completo."
    elif not email_valido(email):
        erro = "Por favor, digite um e-mail válido."
    elif telefone and len(apenas_digitos(telefone)) < 10:
        erro = "Telefone deve ter pelo menos 10 dígitos (com DDD)."
    elif len(senha) < 6:
        erro = "A senha deve ter pelo menos 6 caracteres."
    elif senha != confirmar_senha:
        erro = "As senhas não coincidem."

    if erro:
        flash(erro, "erro")
        return render_template("cadastro/tela.html", valores=valores), 400

    try:
        novo_id = database.criar_usuario(
            nome=nome,
            email=email,
            telefone=telefone or None,
            senha_hash=generate_password_hash(senha),
        )
    except sqlite3.IntegrityError:
        flash("Esse e-mail já está cadastrado. Tente fazer login.", "erro")
        return render_template("cadastro/tela.html", valores=valores), 400

    # Loga automaticamente após o cadastro
    session["usuario_id"] = novo_id
    flash(f"Cadastro realizado com sucesso! Bem-vindo(a), {nome.split(' ')[0]}!", "sucesso")
    return redirect(url_for("conta"))


@app.route("/cadastro/minhaconta.html", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("conta"))
        return render_template("cadastro/minhaconta.html", email_preenchido=None)

    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    usuario = database.buscar_usuario_por_email(email)

    if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
        flash("E-mail ou senha incorretos.", "erro")
        return render_template("cadastro/minhaconta.html", email_preenchido=email), 401

    session["usuario_id"] = usuario["id"]
    flash(f"Login realizado com sucesso! Bem-vindo(a), {usuario['nome'].split(' ')[0]}!", "sucesso")
    return redirect(url_for("conta"))


@app.route("/cadastro/conta.html")
def conta():
    if "usuario_id" not in session:
        flash("Faça login para acessar sua conta.", "erro")
        return redirect(url_for("login"))

    usuario = database.buscar_usuario_por_id(session["usuario_id"])
    if usuario is None:
        session.clear()
        flash("Sua sessão expirou. Faça login novamente.", "erro")
        return redirect(url_for("login"))

    return render_template("cadastro/conta.html", usuario=usuario)


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("login"))


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "newindex.html")


@app.route("/<path:filepath>")
def arquivos_estaticos(filepath):
    primeiro_segmento = filepath.split("/", 1)[0]
    if primeiro_segmento in PASTAS_PROIBIDAS:
        abort(404)

    _, extensao = os.path.splitext(filepath)
    if extensao.lower() not in EXTENSOES_PERMITIDAS:
        abort(404)

    caminho_completo = os.path.normpath(os.path.join(BASE_DIR, filepath))
    if not (caminho_completo == BASE_DIR or caminho_completo.startswith(BASE_DIR + os.sep)):
        abort(404) 
    if os.path.isfile(caminho_completo):
        diretorio, arquivo = os.path.split(caminho_completo)
        return send_from_directory(diretorio, arquivo)
    abort(404)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
