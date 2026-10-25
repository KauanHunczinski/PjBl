from Livros.view import connect

conn = connect()

colunas = conn.execute("PRAGMA Table_info(usuarios)").fetchall()

nomes_colunas = []
for coluna in colunas:
    nomes_colunas.append(coluna[1])

if "senha_hash" not in nomes_colunas:
    conn.execute(
        "ALTER TABLE usuarios ADD COLUMN senha_hash TEXT"
    )
    conn.commit()
    print("Coluna senha_hash adicionada!")
else:
    print("A coluna senha_hash ja existe.")
conn.close()