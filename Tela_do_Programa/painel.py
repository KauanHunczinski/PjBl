from datetime import date, datetime
from html import escape
from pathlib import Path

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
if usuario_logado is None:
    st.switch_page("login.py")



# 2. DADOS E FUNÇÕES AUXILIARES
CATALOGO = ["Furadeira", "Martelo", "Escada"]
FORMATO_DATA = "%d/%m/%Y"

nome_cliente = usuario_logado["nome"]
hoje = date.today()

emprestimos = [
    {"Produto": "Furadeira", "Retirada": "17/10/2026", "Devolver até": "24/10/2026"},
    {"Produto": "Martelo", "Retirada": "20/10/2026", "Devolver até": "02/11/2026"},
]

if "desejos" not in st.session_state:
    st.session_state["desejos"] = []


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
    produto = st.session_state["produto_desejado"]
    if produto not in st.session_state["desejos"]:
        st.session_state["desejos"].append(produto)


def remover_desejo(produto):
    if produto in st.session_state["desejos"]:
        st.session_state["desejos"].remove(produto)


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

    with area_perfil:
        if foto is not None:
            st.image(foto, width=110)
        else:
            inicial = escape(nome_cliente[:1].upper())
            st.html(f'<div class="avatar">{inicial}</div>')
        st.html(f'<div class="perfil-nome">Olá, <strong>{escape(nome_cliente)}</strong>!</div>')

    if st.button("Voltar ao login", key="Voltar_ao_login", icon=":material/logout:"):
        try:
            st.switch_page("login.py")
        except StreamlitAPIException:
            st.warning("Página de login não encontrada. Confira o caminho em st.switch_page.")


# 4. CABEÇALHO

st.html(f"""
<div class="cabecalho">
    <h1>Meu painel</h1>
    <p>Acompanhe seus empréstimos e sua lista de desejos. Hoje é {hoje.strftime(FORMATO_DATA)}.</p>
</div>
""")



# 5. FAIXA DE INDICADORES

total_emprestimos = len(emprestimos)
total_desejos = len(st.session_state["desejos"])

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
    st.caption("Dados de exemplo, ainda sem ligação com o banco de dados.")

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

    col_seletor, col_botao = st.columns([4, 1], vertical_alignment="bottom")

    with col_seletor:
        produto_desejado = st.selectbox(
            "Qual item você deseja pegar emprestado?",
            CATALOGO,
            key="produto_desejado",
        )

    with col_botao:
        ja_na_lista = produto_desejado in st.session_state["desejos"]
        with st.container(key="botao_adicionar"):
            st.button(
                "Adicionar",
                type="primary",
                icon=":material/add:",
                on_click=adicionar_desejo,
                disabled=ja_na_lista,
                help="Este item já está na sua lista." if ja_na_lista else None,
            )

    if not st.session_state["desejos"]:
        st.html(
            '<p class="vazio">Sua lista está vazia. '
            "Escolha um item acima e clique em Adicionar.</p>"
        )

    for i, produto in enumerate(st.session_state["desejos"]):
        with st.container(key=f"item_desejo_{i}"):
            col_nome, col_remover = st.columns([5, 1], vertical_alignment="center")
            with col_nome:
                st.html(f'<span class="nome-desejo">{escape(produto)}</span>')
            with col_remover:
                st.button(
                    "Remover",
                    key=f"remover_{produto}",
                    icon=":material/delete:",
                    on_click=remover_desejo,
                    args=(produto,),
                )