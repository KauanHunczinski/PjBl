import streamlit as st
from Livros.view import (
    insert_user,
    exibir_usuarios,
    insert_book,
    listar_livros,
    editar_livro,
    excluir_livro,
    cadastrar_emprestimo,
    listar_solicitacoes_aquisicao,
    obter_perfil_usuario,
    listar_usuarios,
    listar_historico_solicitacao,
    atualizar_status_solicitacao,
    listar_livros_com_disponibilidade,
    adicionar_exemplar,
    listar_exemplares,
    definir_status_exemplar,
    listar_exemplares_disponiveis,
    listar_emprestimos_administrativos,
    registrar_devolucao,
)
from datetime import date, timedelta

st.set_page_config(
    page_title="Gerencia",
    layout="wide",
    initial_sidebar_state="expanded"
)


usuario_logado = st.session_state.get("usuario_logado")
perfil_usuario = (
    obter_perfil_usuario(usuario_logado.get("id"))
    if isinstance(usuario_logado, dict)
    else None
)

if perfil_usuario is None:
    st.switch_page("login.py")

elif perfil_usuario != "gerente":
    st.switch_page("painel.py")

operador_id = usuario_logado["id"]

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
                senha,
                operador_id=operador_id,
            )
            st.write("Usuario cadastrado com sucesso!")




st. title("Painel Gerencia")
st.write("Gerencie produtos, Usuarios, emprestimos e devoluçoes")

usuarios = exibir_usuarios(operador_id)
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
    aba_cadastrar, aba_editar, aba_excluir, aba_exemplares = st.tabs([
        "Cadastrar Livro",
        "Editar Livro",
        "Excluir Livro",
        "Exemplares",
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
                        isbn.strip(),
                        operador_id=operador_id,
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
                            novo_isbn.strip(),
                            operador_id=operador_id,
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
                        excluir_livro(
                            livro_excluir["id"],
                            operador_id=operador_id,
                        )

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

    with aba_exemplares:
        st.subheader("Controle de exemplares")
        if livros:
            opcoes_exemplares = {
                f"{livro['id']} - {livro['titulo']}": livro
                for livro in livros
            }
            livro_selecionado = st.selectbox(
                "Selecione um livro",
                list(opcoes_exemplares),
                key="livro_exemplares",
            )
            livro_exemplar = opcoes_exemplares[livro_selecionado]
            if st.button(
                "Adicionar exemplar",
                key=f"adicionar_exemplar_{livro_exemplar['id']}",
            ):
                adicionar_exemplar(
                    livro_exemplar["id"],
                    operador_id=operador_id,
                )
                st.success("Exemplar adicionado.")
                st.rerun()

            for exemplar in listar_exemplares(
                livro_exemplar["id"],
                operador_id=operador_id,
            ):
                situacao = (
                    "Emprestado"
                    if exemplar["emprestado"]
                    else exemplar["status"]
                )
                col_codigo, col_status, col_acao = st.columns([2, 2, 2])
                col_codigo.write(exemplar["codigo"])
                col_status.write(situacao)
                if not exemplar["emprestado"]:
                    novo_status = (
                        "Indisponível"
                        if exemplar["status"] == "Disponível"
                        else "Disponível"
                    )
                    if col_acao.button(
                        f"Marcar como {novo_status.lower()}",
                        key=f"status_exemplar_{exemplar['id']}",
                    ):
                        definir_status_exemplar(
                            exemplar["id"],
                            novo_status,
                            operador_id=operador_id,
                        )
                        st.rerun()
        else:
            st.info("Cadastre um livro antes de adicionar exemplares.")

# LISTA DE LIVROS
    st.divider()
    st.subheader("Livros Cadastrados")

    livros_com_estoque = listar_livros_com_disponibilidade()
    if livros_com_estoque:
        estoque = [
            {
                "ID": livro["id"],
                "Título": livro["titulo"],
                "Exemplares": livro["total_exemplares"],
                "Disponíveis": livro["disponiveis"],
                "Emprestados": livro["emprestados"],
                "Indisponíveis": livro["indisponiveis"],
                "Situação": livro["situacao"],
            }
            for livro in livros_com_estoque
        ]
        st.dataframe(
            estoque,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("Nenhum livro cadastrado.")


# Exibir o cadastro e a lista de livros

pagina_livros()

st.divider()
st.subheader("Solicitações de aquisição")
status_aquisicoes = (
    "Pendente",
    "Em análise",
    "Aprovada",
    "Recusada",
    "Adquirida",
)
filtro_aquisicao = st.selectbox(
    "Filtrar solicitações",
    ["Todas", *status_aquisicoes],
    key="filtro_solicitacoes_aquisicao",
)
solicitacoes = listar_solicitacoes_aquisicao(
    operador_id,
    status=None if filtro_aquisicao == "Todas" else filtro_aquisicao,
)
if solicitacoes:
    for solicitacao in solicitacoes:
        with st.expander(
            f"{solicitacao['titulo']} — {solicitacao['status']}"
        ):
            capa_coluna, dados_coluna = st.columns([1, 3])
            with capa_coluna:
                if solicitacao["capa"]:
                    st.image(solicitacao["capa"], width="stretch")
            with dados_coluna:
                st.write(
                    f"Solicitado por: {solicitacao['nome']} "
                    f"{solicitacao['sobrenome']}"
                )
                st.caption(solicitacao["email"])
                st.write(f"Autor(es): {solicitacao['autor'] or 'Não informado'}")
                st.write(f"ISBN-10: {solicitacao['isbn10'] or 'Não informado'}")
                st.write(f"ISBN-13: {solicitacao['isbn13'] or 'Não informado'}")
                if solicitacao["isbn"] and not (
                    solicitacao["isbn10"] or solicitacao["isbn13"]
                ):
                    st.write(f"ISBN: {solicitacao['isbn']}")
                st.write(f"Editora: {solicitacao['editora'] or 'Não informada'}")
                st.caption(
                    f"Solicitada em {solicitacao['criada_em']} · "
                    f"Google Books ID: {solicitacao['google_book_id'] or '—'}"
                )

            with st.form(f"status_aquisicao_{solicitacao['id']}"):
                novo_status = st.selectbox(
                    "Situação",
                    status_aquisicoes,
                    index=status_aquisicoes.index(solicitacao["status"]),
                )
                comentario_status = st.text_input(
                    "Observação (opcional)",
                )
                atualizar = st.form_submit_button("Atualizar situação")
            if atualizar:
                try:
                    atualizar_status_solicitacao(
                        solicitacao["id"],
                        novo_status,
                        operador_id=operador_id,
                        comentario=comentario_status.strip() or None,
                    )
                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))
                else:
                    st.success("Situação atualizada.")
                    st.rerun()

            st.markdown("**Histórico**")
            historico = listar_historico_solicitacao(
                solicitacao["id"],
                operador_id=operador_id,
            )
            for evento in historico:
                responsavel = "Sistema"
                if evento["nome"]:
                    responsavel = f"{evento['nome']} {evento['sobrenome'] or ''}".strip()
                observacao = f" · {evento['comentario']}" if evento["comentario"] else ""
                st.caption(
                    f"{evento['criado_em']} · {evento['status']} · "
                    f"{responsavel}{observacao}"
                )
else:
    st.info("Nenhuma solicitação de aquisição para este filtro.")

st.divider()
st.subheader("Empréstimos e devoluções presenciais")
usuarios_disponiveis = listar_usuarios(operador_id)
livros_estoque = listar_livros_com_disponibilidade()
livros_opcoes = {
    f"{livro['id']} - {livro['titulo']}": livro
    for livro in livros_estoque
}
usuarios_opcoes = {
    f"{usuario[0]} - {usuario[1]} {usuario[2]} ({usuario[3]})": usuario[0]
    for usuario in usuarios_disponiveis
}

if not usuarios_opcoes:
    st.info("Cadastre um usuário antes de registrar empréstimos.")
elif not livros_opcoes:
    st.info("Cadastre um livro antes de registrar empréstimos.")
else:
    livro_escolhido_label = st.selectbox(
        "Livro",
        list(livros_opcoes),
        key="livro_para_emprestimo",
    )
    livro_escolhido = livros_opcoes[livro_escolhido_label]
    exemplares_disponiveis = listar_exemplares_disponiveis(
        livro_escolhido["id"],
    )
    if not exemplares_disponiveis:
        st.info("Este livro não possui exemplares disponíveis para empréstimo.")
    else:
        exemplares_opcoes = {
            f"{codigo} (ID {exemplar_id})": exemplar_id
            for exemplar_id, codigo in exemplares_disponiveis
        }
        with st.form("cadastro_emprestimo", clear_on_submit=True):
            usuario_escolhido = st.selectbox(
                "Usuário",
                list(usuarios_opcoes),
            )
            exemplar_escolhido = st.selectbox(
                "Exemplar",
                list(exemplares_opcoes),
            )
            data_emprestimo = st.date_input(
                "Data do empréstimo",
                value=date.today(),
                format="DD/MM/YYYY",
            )
            data_devolucao = st.date_input(
                "Previsão de devolução",
                value=date.today() + timedelta(days=7),
                format="DD/MM/YYYY",
            )
            salvar = st.form_submit_button("Registrar empréstimo")

        if salvar:
            if data_devolucao < data_emprestimo:
                st.warning("A devolução não pode ser anterior ao empréstimo.")
            else:
                try:
                    cadastrar_emprestimo(
                        usuarios_opcoes[usuario_escolhido],
                        livro_escolhido["id"],
                        data_emprestimo.strftime("%d/%m/%Y"),
                        data_devolucao.strftime("%d/%m/%Y"),
                        operador_id=operador_id,
                        exemplar_id=exemplares_opcoes[exemplar_escolhido],
                    )
                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))
                else:
                    st.success("Empréstimo presencial registrado.")
                    st.rerun()

st.markdown("**Empréstimos ativos**")
emprestimos_ativos = listar_emprestimos_administrativos(
    operador_id,
    status="Ativo",
)
if emprestimos_ativos:
    for emprestimo in emprestimos_ativos:
        coluna_dados, coluna_acao = st.columns([5, 1])
        coluna_dados.write(
            f"**{emprestimo['titulo']}** — {emprestimo['exemplar']} · "
            f"{emprestimo['nome']} {emprestimo['sobrenome']} · "
            f"retirada {emprestimo['data_emprestimo']} · "
            f"prevista {emprestimo['data_devolucao']}"
        )
        if coluna_acao.button(
            "Registrar devolução",
            key=f"devolver_{emprestimo['id']}",
        ):
            try:
                registrar_devolucao(
                    emprestimo["id"],
                    operador_id=operador_id,
                )
            except (ValueError, PermissionError) as erro:
                st.error(str(erro))
            else:
                st.success("Devolução registrada.")
                st.rerun()
else:
    st.info("Não há empréstimos ativos.")

st.markdown("**Histórico de empréstimos**")
historico_emprestimos = listar_emprestimos_administrativos(
    operador_id,
    status="Devolvido",
)
if historico_emprestimos:
    st.dataframe(
        [
            {
                "Livro": emprestimo["titulo"],
                "Exemplar": emprestimo["exemplar"],
                "Usuário": (
                    f"{emprestimo['nome']} {emprestimo['sobrenome']}"
                ),
                "Retirada": emprestimo["data_emprestimo"],
                "Previsão": emprestimo["data_devolucao"],
                "Devolvido em": emprestimo["devolvido_em"],
                "Situação": emprestimo["status"],
            }
            for emprestimo in historico_emprestimos
        ],
        width="stretch",
        hide_index=True,
    )
else:
    st.info("Ainda não há empréstimos devolvidos.")
