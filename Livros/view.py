# baixar: python -m pip install argon2-cffi
import sqlite3
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

gerador_hash = PasswordHasher()

def connect():
    caminho_banco = Path(__file__).resolve().parent.parent / "dados.db"
    conn = sqlite3.connect(caminho_banco)
    return conn

# funçao para inserir livros
def insert_book(titulo, autor, editora, ano_publicacao, isbn):
    conn = connect()
    conn.execute('INSERT INTO livros(titulo, autor, editora, ano_publicacao, isbn) VALUES (?, ?, ?, ?, ?)',
                (titulo, autor, editora, ano_publicacao, isbn))
    conn.commit()
    conn.close()

# Funçao para inserir Usuarios

def insert_user(nome, sobrenome, endereco, email, telefone, senha):
    senha_hash = gerador_hash.hash(senha)
    conn = connect()
    conn.execute(
        """
        INSERT INTO usuarios (nome, sobrenome, endereco, email, telefone, senha_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (nome, sobrenome, endereco, email, telefone, senha_hash),
    )
    conn.commit()
    conn.close()


# função para exibir os livros

def exibir_livros():
    conn = connect()

    livros = conn.execute('SELECT * FROM livros').fetchall()
    conn.close()

    if not livros:
        print("Nenhum livro cadastrado.")
        return

    print("Livros na biblioteca: ")
    for livro in livros:
        print(f"ID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Autor: {livro[2]}")
        print(f"Editora: {livro[3]}")
        print(f"Ano de Publicação: {livro[4]}")
        print(f"ISBN: {livro[5]}")
        print("\n")

# listar livros

def listar_livros():
    conn = connect()

    try:
        cursor = conn.execute("""
            SELECT id, titulo, autor, editora,
                   ano_publicacao, isbn
            FROM livros
            ORDER BY id DESC
        """)

        colunas = [coluna[0] for coluna in cursor.description]
        livros = cursor.fetchall()

        return [dict(zip(colunas, livro)) for livro in livros]

    finally:
        conn.close()


# Criar tabela para a lista de desejos

def criar_tabela_desejos():
    conn = connect()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS lista_desejos (
            usuario_id INTEGER,
            livro_id INTEGER,
            PRIMARY KEY (usuario_id, livro_id)
        )
    """)

    conn.commit()
    conn.close()


# Adicionar livro à lista de desejos
def adicionar_desejo(usuario_id, livro_id):
    conn = connect()

    conn.execute("""
        INSERT OR IGNORE INTO lista_desejos
        (usuario_id, livro_id)
        VALUES (?, ?)
    """, (usuario_id, livro_id))

    conn.commit()
    conn.close()


# Mostrar os livros desejados pelo usuário
def listar_desejos(usuario_id):
    conn = connect()

    livros = conn.execute("""
        SELECT livros.id, livros.titulo
        FROM lista_desejos
        JOIN livros ON lista_desejos.livro_id = livros.id
        WHERE lista_desejos.usuario_id = ?
    """, (usuario_id,)).fetchall()

    conn.close()
    return livros


# Remover livro da lista de desejos
def remover_desejo(usuario_id, livro_id):
    conn = connect()

    conn.execute("""
        DELETE FROM lista_desejos
        WHERE usuario_id = ? AND livro_id = ?
    """, (usuario_id, livro_id))

    conn.commit()
    conn.close()



# Função para editar livros

def editar_livro(id_livro, titulo, autor, editora, ano, isbn):
    conn = connect()

    try:
        conn.execute("""
            UPDATE livros
            SET titulo = ?,
                autor = ?,
                editora = ?,
                ano_publicacao = ?,
                isbn = ?
            WHERE id = ?
        """, (titulo, autor, editora, ano, isbn, id_livro))

        conn.commit()
    finally:
        conn.close()


# Função para excluir livros
def excluir_livro(id_livro):
    conn = connect()

    try:
        conn.execute(
            "DELETE FROM livros WHERE id = ?",
            (id_livro,)
        )

        conn.commit()
    finally:
        conn.close()


# Cadastrar empréstimo para um usuário
def cadastrar_emprestimo(id_usuario, id_livro, data_emprestimo, data_devolucao):
    conn = connect()

    try:
        # Verifica se o usuário existe
        usuario = conn.execute(
            "SELECT id FROM usuarios WHERE id = ?",
            (id_usuario,)
        ).fetchone()

        # Verifica se o livro existe
        livro = conn.execute(
            "SELECT id FROM livros WHERE id = ?",
            (id_livro,)
        ).fetchone()

        if usuario is None:
            raise ValueError("Usuário não encontrado!")

        if livro is None:
            raise ValueError("Livro não encontrado!")

        # Registra o empréstimo
        conn.execute("""
            INSERT INTO emprestimos
            (id_usuario, id_livro, data_emprestimo, data_devolucao)
            VALUES (?, ?, ?, ?)
        """, (id_usuario, id_livro, data_emprestimo, data_devolucao))

        conn.commit()

    finally:
        conn.close()


# Listar empréstimos de um usuário
def listar_emprestimos_usuario(usuario_id):
    conn = connect()

    try:
        emprestimos = conn.execute("""
            SELECT livros.titulo,
                   emprestimos.data_emprestimo,
                   emprestimos.data_devolucao
            FROM emprestimos
            JOIN livros
                ON livros.id = emprestimos.id_livro
            WHERE emprestimos.id_usuario = ?
        """, (usuario_id,)).fetchall()

        return [
            {
                "Produto": livro[0],
                "Retirada": livro[1],
                "Devolver até": livro[2]
            }
            for livro in emprestimos
        ]

    finally:
        conn.close()

# Funcao para exibir usuarios

def exibir_usuarios():
    conn = connect()

    usuarios = conn.execute("SELECT id, nome, sobrenome, email FROM usuarios").fetchall()
    conn.close()
    return usuarios



def autenticar_usuario(email, senha):
    conn = connect()

    usuarios = conn.execute(
        """
        SELECT id, nome, senha_hash, perfil
        FROM usuarios
        WHERE email = ? COLLATE NOCASE
        """,
        (email.strip(),)
    ).fetchall()

    conn.close()

    if len(usuarios) != 1:
        return None

    usuario = usuarios [0]
    senha_hash = usuario[2]

    if not senha_hash:
        return None
    
    try:
        gerador_hash.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return None

    return {
        "id": usuario[0],
        "nome": usuario[1],
        "perfil": usuario[3]
    }









# Teste para adicionar

#insert_book("O Senhor dos Anéis", "J.R.R. Tolkien", "HarperCollins", 1954, "978-0261102385")
#insert_user("João", "Silva", "Rua A, 123", "joao.silva@email.com", "123456789")

if __name__=="__main__":
    exibir_livros()