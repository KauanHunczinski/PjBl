from pathlib import Path

import streamlit as st

from Tela_do_Programa.tela_Api import buscar_livros


st.set_page_config(
    page_title="Biblioteca Digital",
    page_icon="📚",
    layout="wide",
)

caminho_css = Path(__file__).resolve().parent / "design_Tela_Api.css"
if caminho_css.exists():
    st.markdown(
        f"<style>{caminho_css.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

CATEGORIAS = {
    "Todas": "",
    "Ficção": "fiction",
    "Romance": "romance",
    "Aventura": "adventure",
    "Mistério": "mystery",
    "Não ficção": "nonfiction",
}
IDIOMAS = {"Todos": "", "Português": "pt", "Inglês": "en"}


def obter_ano(info):
    data_publicacao = str(info.get("publishedDate", ""))
    return data_publicacao[:4] or "Ano não informado"


def exibir_livro(coluna, livro):
    info = livro.get("volumeInfo", {})
    autores = info.get("authors") or ["Autor não informado"]
    imagem = info.get("imageLinks", {}).get("thumbnail")
    link = info.get("infoLink")

    if imagem:
        imagem = imagem.replace("http://", "https://", 1)

    with coluna:
        with st.container(border=True):
            capa, detalhes = st.columns([1, 2], vertical_alignment="top")

            with capa:
                if imagem:
                    st.image(imagem, use_container_width=True)
                else:
                    st.caption("Capa indisponível")

            with detalhes:
                st.markdown(f"#### {info.get('title', 'Título não informado')}")
                st.write("**Autor(es):** " + ", ".join(autores))
                st.caption(
                    f"{info.get('publisher', 'Editora não informada')} · "
                    f"{obter_ano(info)}"
                )
                avaliacao = info.get("averageRating")
                if avaliacao is not None:
                    st.write(f"⭐ {avaliacao}/5")

            with st.expander("Ver sinopse"):
                st.write(info.get("description", "Sinopse não disponível."))

            if link:
                st.link_button("Mais informações", link, use_container_width=True)


st.title("Biblioteca Digital")
st.write("Pesquise e descubra livros para sua próxima leitura.")

if "busca_atual" not in st.session_state:
    st.session_state["busca_atual"] = ""
if "resultados_guardados" not in st.session_state:
    st.session_state["resultados_guardados"] = {}

with st.form("formulario_pesquisa"):
    termo_digitado = st.text_input(
        "Pesquisar livros",
        placeholder="Digite o título, autor ou assunto",
        key="campo_pesquisa",
    )
    pesquisar = st.form_submit_button("Pesquisar")

if pesquisar:
    st.session_state["busca_atual"] = termo_digitado.strip()

with st.sidebar.form("formulario_filtros"):
    st.header("Filtros")
    categoria = st.selectbox("Categoria", list(CATEGORIAS))
    idioma = st.selectbox("Idioma", list(IDIOMAS))
    ordem = st.selectbox("Ordenar por", ["Relevância", "Mais recentes", "Título"])
    quantidade = st.selectbox("Resultados", [10, 20, 30])
    st.form_submit_button("Aplicar filtros")

termo = st.session_state["busca_atual"]
categoria_google = CATEGORIAS[categoria]
if termo:
    consulta = termo
    if categoria_google:
        consulta = f"{consulta} subject:{categoria_google}"
    st.subheader(f'Resultados para "{termo}"')
else:
    consulta = f"bestseller subject:{categoria_google}" if categoria_google else "bestseller"
    st.subheader("Mais procurados")
    st.caption(
        "Seleção do Google Books por relevância. A API não fornece um ranking "
        "oficial de livros mais lidos."
    )

consulta_guardada = (consulta, quantidade)
if consulta_guardada not in st.session_state["resultados_guardados"]:
    with st.spinner("Carregando livros..."):
        resultado = buscar_livros(consulta, quantidade=quantidade)
    if resultado is not None:
        st.session_state["resultados_guardados"][consulta_guardada] = resultado
else:
    resultado = st.session_state["resultados_guardados"][consulta_guardada]

if resultado is not None:
    livros = resultado
    codigo_idioma = IDIOMAS[idioma]
    if codigo_idioma:
        livros = [
            livro
            for livro in livros
            if livro.get("volumeInfo", {}).get("language") == codigo_idioma
        ]

    if ordem == "Mais recentes":
        livros = sorted(
            livros,
            key=lambda livro: obter_ano(livro.get("volumeInfo", {})),
            reverse=True,
        )
    elif ordem == "Título":
        livros = sorted(
            livros,
            key=lambda livro: livro.get("volumeInfo", {}).get("title", "").casefold(),
        )

    if not livros:
        st.info("Nenhum livro encontrado com esses filtros.")
    else:
        st.caption(f"{len(livros)} livros")
        for indice in range(0, len(livros), 2):
            colunas = st.columns(2)
            for coluna, livro in zip(colunas, livros[indice : indice + 2]):
                exibir_livro(coluna, livro)
