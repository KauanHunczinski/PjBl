import streamlit as st
from Livros.view import insert_user, exibir_usuarios, insert_book, listar_livros, editar_livro, excluir_livro, cadastrar_emprestimo
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(
    page_title="Gerencia",
    layout="wide",
    initial_sidebar_state="expanded"
)


usuario_logado = st.session_state.get("usuario_logado")

if usuario_logado is None:
    st.switch_page("login.py")

elif usuario_logado.get("perfil") != "gerente":
    st.switch_page("painel.py")


with st.sidebar:
    st.subheader("Area da Gerencia")
    if st.button("Voltar ao login"):
        st.session_state.clear()
        st.switch_page("login.py")
    st.subheader("Cadastro de Usuarios")
    with st.form("cadastro_de_usuario", clear_on_submit=True):
                nome = st.text_input("Nome")
                sobrenome = st.text_input("Sobrenome")
                endereco = st.text_input("Endereco")
                email = st.text_input("Email")
                telefone = st.text_input("Telefone")
                senha = st.text_input("Senha", type="password")
                confirmar_senha = st.text_input("Confirme sua senha", type="password")
                cadastrar = st.form_submit_button(
                    "Cadastrar",
                    type="primary"
                )
    if cadastrar:
        if nome.strip() == "" or sobrenome.strip() == "" or endereco.strip() == "" or email.strip() == "" or telefone.strip() == "":
            st.write("Preencha todos os campos")
        elif senha == "" or confirmar_senha == "":
            st.write("Preencha a senha e a confirmacao.")
        elif senha != confirmar_senha:
            st.write("As senhas nao coincidem.") 
        else:
            insert_user(
                nome.strip(),
                sobrenome.strip(),
                endereco.strip(),
                email.strip(),
                telefone.strip(),
                senha
            )
            st.write("Usuario cadastrado com sucesso!")




st. title("Painel Gerencia")
st.write("Gerencie produtos, Usuarios, emprestimos e devoluçoes")

usuarios = exibir_usuarios()
linhas = []

for usuario in usuarios:
    linhas.append({
        "ID": usuario[0],
        "Nome": usuario[1],
        "Sobrenome": usuario[2],
        "E-mail": usuario[3]
    })
st.dataframe(linhas, hide_index=True)


# função para aparacer no sistema web


def pagina_livros():

    st.title("Gerenciamento de Livros")

# Mensagens após atualização
    mensagem = st.session_state.pop("mensagem_livro", None)
    if mensagem:
        st.success(mensagem)

    livros = listar_livros()

# Abas de gerenciamento
    aba_cadastrar, aba_editar, aba_excluir = st.tabs([
        "Cadastrar Livro",
        "Editar Livro",
        "Excluir Livro"
    ])

# CADASTRAR LIVROS
    with aba_cadastrar:
        st.subheader("Cadastrar novo livro")

        with st.form("cadastro_livros", clear_on_submit=True):
            titulo = st.text_input("Título")
            autor = st.text_input("Autor")
            editora = st.text_input("Editora")

            ano = st.number_input(
                "Ano de publicação",
                min_value=1000,
                max_value=2100,
                value=2026
            )

            isbn = st.text_input("ISBN")

            cadastrar = st.form_submit_button(
                "Cadastrar Livro"
            )

        if cadastrar:
            if all([
                titulo.strip(),
                autor.strip(),
                editora.strip(),
                isbn.strip()
            ]):
                try:
                    insert_book(
                        titulo.strip(),
                        autor.strip(),
                        editora.strip(),
                        int(ano),
                        isbn.strip()
                    )

                    st.session_state["mensagem_livro"] = (
                        "Livro cadastrado com sucesso!"
                    )
                    st.rerun()

                except Exception as erro:
                    st.error(f"Erro no cadastro: {erro}")
            else:
                st.warning("Preencha todos os campos!")

# EDITAR LIVROS
    with aba_editar:
        st.subheader("Editar livro")

        if livros:
            opcoes = {
                f"{livro['id']} - {livro['titulo']}": livro
                for livro in livros
            }

            selecionado = st.selectbox(
                "Selecione um livro",
                list(opcoes.keys()),
                key="livro_editar"
            )

            livro = opcoes[selecionado]

            with st.form(f"editar_{livro['id']}"):
                novo_titulo = st.text_input(
                    "Título",
                    value=livro["titulo"]
                )

                novo_autor = st.text_input(
                    "Autor",
                    value=livro["autor"]
                )

                nova_editora = st.text_input(
                    "Editora",
                    value=livro["editora"]
                )

                novo_ano = st.number_input(
                    "Ano de publicação",
                    min_value=1000,
                    max_value=2100,
                    value=int(livro["ano_publicacao"])
                )

                novo_isbn = st.text_input(
                    "ISBN",
                    value=str(livro["isbn"])
                )

                salvar = st.form_submit_button(
                    "Salvar Alterações"
                )

            if salvar:
                if all([
                    novo_titulo.strip(),
                    novo_autor.strip(),
                    nova_editora.strip(),
                    novo_isbn.strip()
                ]):
                    try:
                        editar_livro(
                            livro["id"],
                            novo_titulo.strip(),
                            novo_autor.strip(),
                            nova_editora.strip(),
                            int(novo_ano),
                            novo_isbn.strip()
                        )

                        st.session_state["mensagem_livro"] = (
                            "Livro atualizado com sucesso!"
                        )
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao editar: {erro}")
                else:
                    st.warning("Preencha todos os campos!")
        else:
            st.info("Nenhum livro cadastrado.")

# EXCLUIR LIVROS
    with aba_excluir:
        st.subheader("Excluir livro")

        if livros:
            opcoes_excluir = {
                f"{livro['id']} - {livro['titulo']}": livro
                for livro in livros
            }

            selecionado_excluir = st.selectbox(
                "Selecione um livro",
                list(opcoes_excluir.keys()),
                key="livro_excluir"
            )

            livro_excluir = opcoes_excluir[selecionado_excluir]

            st.warning(
                "A exclusão é permanente e removerá "
                "o livro do banco de dados."
            )

            with st.form(f"excluir_{livro_excluir['id']}"):
                confirmar = st.checkbox(
                    "Confirmo que desejo excluir este livro"
                )

                apagar = st.form_submit_button(
                    "Excluir Livro"
                )

            if apagar:
                if confirmar:
                    try:
                        excluir_livro(livro_excluir["id"])

                        st.session_state["mensagem_livro"] = (
                            "Livro excluído com sucesso!"
                        )
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao excluir: {erro}")
                else:
                    st.warning("Confirme a exclusão!")
        else:
            st.info("Nenhum livro cadastrado.")

# LISTA DE LIVROS
    st.divider()
    st.subheader("Livros Cadastrados")

    if livros:
        st.dataframe(
            livros,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum livro cadastrado.")


# Exibir o cadastro e a lista de livros

pagina_livros()


# GERENCIAMENTO DE EMPRÉSTIMOS

st.divider()
st.title("Gerenciamento de Empréstimos")

with st.form("cadastro_emprestimo", clear_on_submit=True):

    id_usuario = st.number_input(
        "ID do usuário",
        min_value=1,
        step=1
    )

    id_livro = st.number_input(
        "ID do livro",
        min_value=1,
        step=1
    )

    data_emprestimo = st.date_input(
        "Data do empréstimo",
        value=date.today(),
        format="DD/MM/YYYY"
    )

    data_devolucao = st.date_input(
        "Data prevista para devolução",
        value=date.today() + timedelta(days=7),
        format="DD/MM/YYYY"
    )

    salvar = st.form_submit_button(
        "Cadastrar Empréstimo"
    )

if salvar:

    if data_devolucao < data_emprestimo:
        st.warning(
            "A devolução não pode ser anterior ao empréstimo."
        )

    else:
        try:
            cadastrar_emprestimo(
                int(id_usuario),
                int(id_livro),
                data_emprestimo.strftime("%d/%m/%Y"),
                data_devolucao.strftime("%d/%m/%Y")
            )

            st.success("Empréstimo cadastrado com sucesso!")

        except ValueError as erro:
            st.error(str(erro))

        except Exception as erro:
            st.error(f"Erro ao cadastrar empréstimo: {erro}")
