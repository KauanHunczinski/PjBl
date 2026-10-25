# para definir digite no terminal: python -m Livros.definir_gerente
from Livros.view import connect

id_usuario = int(input("ID da conta que será gerente: "))

conn = connect()

resultado = conn.execute(
    """
    UPDATE usuarios
    SET perfil = 'gerente'
    WHERE id = ?
      AND perfil = 'usuario'
      AND senha_hash IS NOT NULL
      AND senha_hash <> ''
    """,
    (id_usuario,)
)

conn.commit()
alterados = resultado.rowcount
conn.close()

if alterados == 1:
    print("Conta definida como gerente!")
else:
    print("Usuário inexistente, sem senha ou já definido como gerente.")