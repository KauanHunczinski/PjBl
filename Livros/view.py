import sqlite3


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

def insert_user(nome, sobrenome, endereco, email, telefone):
    conn = connect()
    conn.execute(
        """
        INSERT INTO usuarios (nome, sobrenome, endereco, email, telefone)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, sobrenome, endereco, email, telefone),
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

# Funcao para exibir usuarios

def exibir_usuarios():
    conn = connect()

    usuarios = conn.execute("SELECT id, nome, sobrenome, email FROM usuarios").fetchall()
    conn.close()
    return usuarios

# Teste para adicionar

#insert_book("O Senhor dos Anéis", "J.R.R. Tolkien", "HarperCollins", 1954, "978-0261102385")
#insert_user("João", "Silva", "Rua A, 123", "joao.silva@email.com", "123456789")

if __name__=="__main__":
    exibir_livros()