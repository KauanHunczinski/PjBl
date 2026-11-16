from datetime import date, datetime
from html import escape
from pathlib import Path
from Livros.view import (
    listar_livros,
    listar_desejos as buscar_desejos,
    adicionar_desejo as salvar_desejo,
    remover_desejo as apagar_desejo,
    listar_emprestimos_usuario,
    obter_perfil_usuario,
    listar_solicitacoes_usuario,
    listar_acompanhamentos_usuario,
    cancelar_acompanhamento,
    listar_notificacoes_usuario,
    marcar_notificacao_lida,
)
import streamlit as st
from streamlit.errors import StreamlitAPIException



# 1. CONFIGURAÇÃO DA PÁGINA

st.set_page_config(
    page_title="Meu painel | Biblioteca",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def carregar_css(nome_arquivo):
    caminho = Path(__file__).parent / nome_arquivo
    if not caminho.exists():
        st.warning(f"Arquivo de estilo não encontrado: {nome_arquivo}. Coloque-o na mesma pasta do painel.py.")
        return
    css = caminho.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


carregar_css("estilo.css")

# logando usuario

usuario_logado = st.session_state.get("usuario_logado")
perfil_usuario = (
    obter_perfil_usuario(usuario_logado.get("id"))
    if isinstance(usuario_logado, dict)
    else None
)
if perfil_usuario is None:
    st.switch_page("login.py")
elif perfil_usuario != "usuario":
    st.switch_page("painel_gerencia.py")



# 2. DADOS E FUNÇÕES AUXILIARES
CATALOGO = {
    livro["id"]: livro["titulo"]
    for livro in listar_livros()
}
FORMATO_DATA = "%d/%m/%Y"

nome_cliente = usuario_logado["nome"]
usuario_id = usuario_logado["id"]
hoje = date.today()

emprestimos = listar_emprestimos_usuario(
    usuario_logado["id"]
)

desejos = buscar_desejos(usuario_id)


def converter_data(texto):
    return datetime.strptime(texto, FORMATO_DATA).date()


def calcular_situacao(texto_data):
    dias_restantes = (converter_data(texto_data) - hoje).days

    if dias_restantes < 0:
        return "Atrasado", "atrasado"
    if dias_restantes == 0:
        return "Vence hoje", "hoje"
    if dias_restantes <= 3:
        plural = "s" if dias_restantes > 1 else ""
        return f"Vence em {dias_restantes} dia{plural}", "aviso"
    return "Em dia", "ok"


def adicionar_desejo():
    livro_id = st.session_state["produto_desejado"]
    salvar_desejo(usuario_id, livro_id)


def remover_desejo(livro_id):
    apagar_desejo(usuario_id, livro_id)


def tabela_emprestimos_html(lista):
    linhas = ""
    for emprestimo in lista:
        texto, nivel = calcular_situacao(emprestimo["Devolver até"])
        linhas += f"""
            <tr>
                <td class="col-produto">{escape(emprestimo['Produto'])}</td>
                <td>{emprestimo['Retirada']}</td>
                <td>{emprestimo['Devolver até']}</td>
                <td><span class="status status-{nivel}">{texto}</span></td>
            </tr>"""

    return f"""
    <div class="tabela-wrap">
        <table class="tabela">
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Retirada</th>
                    <th>Devolver até</th>
                    <th>Situação</th>
                </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
    </div>
    """


# 3. BARRA LATERAL

with st.sidebar:
    st.html('<div class="marca">Biblioteca</div>')

    area_perfil = st.container()

    with st.expander("Alterar foto de perfil"):
        foto = st.file_uploader(
            "Escolha uma foto",
            type=["jpg", "jpeg", "png"],
            key="foto_perfil",
        )

    if foto is not None:
        st.session_state["foto_perfil_bytes"] = foto.getvalue()
    foto_perfil_bytes = st.session_state.get("foto_perfil_bytes")

    with area_perfil:
        if foto_perfil_bytes:
            st.image(foto_perfil_bytes, width=110)
        else:
            inicial = escape(nome_cliente[:1].upper())
            st.html(f'<div class="avatar">{inicial}</div>')
        st.html(f'<div class="perfil-nome">Olá, <strong>{escape(nome_cliente)}</strong>!</div>')

    if st.button(
        "Voltar à biblioteca",
        key="voltar_biblioteca",
        icon=":material/library_books:",
        width="stretch",
    ):
        st.switch_page("busca_de_Livros.py")

    if st.button("Voltar ao login", key="Voltar_ao_login", icon=":material/logout:"):
        try:
            st.switch_page("login.py")
        except StreamlitAPIException:
            st.warning("Página de login não encontrada. Confira o caminho em st.switch_page.")


# 4. CABEÇALHO

st.html(f"""
<div class="cabecalho">
    <h1>Meu painel</h1>
    <p>Acompanhe seus empréstimos presenciais, desejos e interesses no acervo. Hoje é {hoje.strftime(FORMATO_DATA)}.</p>
</div>
""")



# 5. FAIXA DE INDICADORES

total_emprestimos = len(emprestimos)
total_desejos = len(desejos)

if emprestimos:
    proximo = min(emprestimos, key=lambda e: converter_data(e["Devolver até"]))
    texto_situacao, nivel_situacao = calcular_situacao(proximo["Devolver até"])

    valor_proxima = (
        f'<span class="carimbo carimbo-{nivel_situacao}">{proximo["Devolver até"]}</span>'
    )
    legenda_proxima = (
        f'<span class="faixa-situacao">{escape(proximo["Produto"])}: {texto_situacao.lower()}</span>'
    )
else:
    valor_proxima = "-"
    legenda_proxima = ""

st.html(f"""
<div class="faixa">
    <div class="faixa-item">
        <span class="faixa-rotulo">Empréstimos ativos</span>
        <span class="faixa-valor">{total_emprestimos}</span>
    </div>
    <div class="faixa-item">
        <span class="faixa-rotulo">Próxima devolução</span>
        <span class="faixa-valor">{valor_proxima}</span>
        {legenda_proxima}
    </div>
    <div class="faixa-item">
        <span class="faixa-rotulo">Lista de desejos</span>
        <span class="faixa-valor">{total_desejos}</span>
    </div>
</div>
""")



# 6. MEUS EMPRÉSTIMOS

with st.container(key="secao_emprestimos"):
    st.subheader("Meus empréstimos")
    st.caption("Empréstimos cadastrados pela gerência.")

    if not emprestimos:
        st.html(
            '<p class="vazio">Você não tem empréstimos ativos. '
            "Quando retirar um item, ele aparece aqui.</p>"
        )
    else:
        st.html(tabela_emprestimos_html(emprestimos))




# 7. LISTA DE DESEJOS

with st.container(key="secao_desejos"):
    st.subheader("Lista de desejos")

    if CATALOGO:
        col_seletor, col_botao = st.columns(
            [4, 1],
            vertical_alignment="bottom"
        )

        with col_seletor:
            produto_desejado = st.selectbox(
                "Qual livro você deseja pegar emprestado?",
                options=list(CATALOGO.keys()),
                format_func=lambda id: CATALOGO[id],
                key="produto_desejado"
            )

        with col_botao:
            ja_na_lista = produto_desejado in [
                livro[0] for livro in desejos
            ]

            with st.container(key="botao_adicionar"):
                st.button(
                    "Adicionar",
                    type="primary",
                    icon=":material/add:",
                    on_click=adicionar_desejo,
                    disabled=ja_na_lista
                )
    else:
        st.info("Nenhum livro cadastrado.")

    if not desejos:
        st.html(
            '<p class="vazio">'
            'Sua lista está vazia.'
            '</p>'
        )

    for livro_id, titulo in desejos:
        with st.container(key=f"item_desejo_{livro_id}"):

            col_nome, col_remover = st.columns(
                [5, 1],
                vertical_alignment="center"
            )

            with col_nome:
                st.html(
                    f'<span class="nome-desejo">'
                    f'{escape(titulo)}'
                    f'</span>'
                )

            with col_remover:
                st.button(
                    "Remover",
                    key=f"remover_{livro_id}",
                    icon=":material/delete:",
                    on_click=remover_desejo,
                    args=(livro_id,)
                )


st.divider()
st.subheader("Minha biblioteca")
aba_sugestoes, aba_acompanhamentos, aba_notificacoes = st.tabs(
    ["Sugestões de aquisição", "Livros acompanhados", "Notificações"]
)

with aba_sugestoes:
    solicitacoes_usuario = listar_solicitacoes_usuario(usuario_id)
    if not solicitacoes_usuario:
        st.info("Você ainda não enviou sugestões de aquisição.")
    for solicitacao in solicitacoes_usuario:
        st.markdown(f"**{escape(solicitacao['titulo'])}**")
        if solicitacao.get("autor"):
            st.caption(solicitacao["autor"])
        st.write(
            f"Situação: **{solicitacao['status']}** · "
            f"Solicitada em {solicitacao['criada_em']}"
        )

with aba_acompanhamentos:
    acompanhamentos_usuario = listar_acompanhamentos_usuario(usuario_id)
    if not acompanhamentos_usuario:
        st.info("Você ainda não está acompanhando livros.")
    for acompanhamento in acompanhamentos_usuario:
        with st.container(border=True):
            st.markdown(f"**{escape(acompanhamento['titulo'])}**")
            situacao = (
                "Disponível para empréstimo"
                if acompanhamento["disponiveis"] > 0
                else acompanhamento["status"]
            )
            st.caption(
                f"Situação: {situacao} · Acompanhamento criado em "
                f"{acompanhamento['criado_em']}"
            )
            if acompanhamento["status"] == "Ativo" and st.button(
                "Cancelar acompanhamento",
                key=f"cancelar_acompanhamento_{acompanhamento['id']}",
            ):
                if cancelar_acompanhamento(
                    usuario_id,
                    acompanhamento["id"],
                ):
                    st.success("Acompanhamento cancelado.")
                    st.rerun()

with aba_notificacoes:
    notificacoes_usuario = listar_notificacoes_usuario(usuario_id)
    if not notificacoes_usuario:
        st.info("Você ainda não tem notificações.")
    for notificacao in notificacoes_usuario:
        with st.container(border=True):
            if notificacao["lida_em"] is None:
                st.markdown(f"**Não lida** · {notificacao['criada_em']}")
            else:
                st.caption(f"Lida em {notificacao['lida_em']}")
            st.write(notificacao["mensagem"])
            if notificacao["lida_em"] is None and st.button(
                "Marcar como lida",
                key=f"marcar_notificacao_{notificacao['id']}",
            ):
                marcar_notificacao_lida(usuario_id, notificacao["id"])
                st.rerun()
