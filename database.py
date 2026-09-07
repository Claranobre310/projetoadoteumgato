import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "banco.db")


def get_db():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row 
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def init_db():
    conexao = get_db()
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nome          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            telefone      TEXT,
            senha_hash    TEXT NOT NULL,
            criado_em     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conexao.commit()
    conexao.close()


def buscar_usuario_por_email(email):
    conexao = get_db()
    usuario = conexao.execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    conexao.close()
    return usuario


def buscar_usuario_por_id(usuario_id):
    conexao = get_db()
    usuario = conexao.execute(
        "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    conexao.close()
    return usuario


def criar_usuario(nome, email, telefone, senha_hash):
    """Insere um novo usuário. Lança sqlite3.IntegrityError se o e-mail já existir."""
    conexao = get_db()
    cursor = conexao.execute(
        "INSERT INTO usuarios (nome, email, telefone, senha_hash) VALUES (?, ?, ?, ?)",
        (nome, email, telefone, senha_hash),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id
