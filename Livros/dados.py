import sqlite3

con = sqlite3.connect('dados.db')

# Criado tabela de livros

con.execute('CREATE TABLE Livros (\
                            id INTEGER PRIMARY KEY,\
                            titulo TEXT,\
                            autor TEXT,\
                            editora TEXT,\
                            ano_publicacao INTEGER,\
                            isbn TEXT,\)')