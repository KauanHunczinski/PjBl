import sqlite3

con = sqlite3.connect('dados.db')

# Criado tabela de livros

con.execute('CREATE TABLE livros(\
                id INTEGER PRIMARY KEY,\
                titulo TEXT,\
                autor TEXT,\
                editora TEXT,\
                ano_publicacao INTEGER,\
                isbn TEXT)')

# Tabela de Usuarios

con.execute('CREATE TABLE usuarios(\
                id INTEGER PRIMARY KEY,\
                nome TEXT,\
                sobrenome TEXT,\
                endereco TEXT,\
                email TEXTO,\
                telefone TEXT)')


# Tabela de Emprestimos

con.execute('CREATE TABLE emprestimos(\
                id INTEGER PRIMARY KEY,\
                id_livro INTEGER,\
                id_usuario INTEGER,\
                data_emprestimo TEXT,\
                data_devolucao TEXTO,\
                FOREIGN KEY(id_livro)references livros(id),\
                FOREIGN KEY(id_usuario)references usuarios(id))')
