#UTILIZAR ESTE COMANDO NO TERMINAL COM O STREAMLIT PARA ACESSAR A PÁGINA python -m streamlit run Tela_do_Programa/tela_Api.py
import requests

import streamlit as st


import requests
import streamlit as st
from pathlib import Path





# Identificar a pasta onde está o Python
pasta_projeto = Path(__file__).resolve().parent

# Localizar o CSS
caminho_css = pasta_projeto / "design_Tela_Api.css"

# Carregar o CSS
with open(caminho_css, "r", encoding="utf-8") as arquivo:
    css = arquivo.read()

# Aplicar o CSS no Streamlit
st.markdown(
    f"<style>{css}</style>",
    unsafe_allow_html=True
)





def buscar_livros(termo_busca, quantidade=10):

    url = "https://www.googleapis.com/books/v1/volumes"

    parametros = {
        "q": termo_busca,
        "maxResults": quantidade,
        # Carregar chave da API
        "key": st.secrets["AIzaSyB6S2IkjMausTcow0_aBYodA5y_FCu_NxQ"]}

    
def buscar_livros(termo_busca, quantidade=10):

    url = "https://www.googleapis.com/books/v1/volumes"

    parametros = {
        "q": termo_busca,
        "maxResults": quantidade,
        "key": "AIzaSyB6S2IkjMausTcow0_aBYodA5y_FCu_NxQ"
    }

    try:
        resposta = requests.get(
            url,
            params=parametros,
            timeout=15
        )

        if resposta.status_code == 200:
            dados = resposta.json()
            return dados.get("items", [])

        else:
            st.error(
                f"Erro Google Books: HTTP {resposta.status_code}"
            )

            try:
                st.write(resposta.json().get("error", {}))
            except ValueError:
                st.write(resposta.text)

            return []

    except requests.exceptions.RequestException as erro:
        st.error(f"Erro de conexão: {erro}")
        return []




# INTERFACE DE PESQUISA DA BIBLIOTECA


st.markdown(
    '<h1 class="titulo">Encontre sua próxima leitura.</h1>',
    unsafe_allow_html=True
)

st.write("Pesquise livros pelo título, autor ou assunto.")

# Campo de pesquisa
with st.form("formulario_pesquisa"):
    termo_busca = st.text_input(
        "Pesquisar livros",
        placeholder="Exemplo: Harry Potter, Machado de Assis..."
    )

    pesquisar = st.form_submit_button("Pesquisar livros")

# Executar pesquisa
if pesquisar:

    if termo_busca.strip():

        with st.spinner("Pesquisando livros..."):

            livros = buscar_livros(termo_busca, quantidade=10)

        if livros:

            st.subheader("Resultados da pesquisa")

            # Organizar os livros em duas colunas
            for i in range(0, len(livros), 2):

                colunas = st.columns(2)

                for coluna, livro in zip(
                    colunas,
                    livros[i:i+2]
                ):

                    info = livro.get("volumeInfo", {})

                    titulo = info.get(
                        "title", "Título não informado"
                    )

                    autores = info.get(
                        "authors", ["Autor desconhecido"]
                    )

                    editora = info.get(
                        "publisher", "Editora não informada"
                    )

                    ano = info.get(
                        "publishedDate", "Ano desconhecido"
                    )

                    descricao = info.get(
                        "description", "Descrição não disponível."
                    )

                    imagem = info.get(
                        "imageLinks", {}
                    ).get("thumbnail")

                    link = info.get("infoLink", "")

                    with coluna:

                        with st.container(border=True):

                            if imagem:
                                st.image(imagem, width=140)

                            st.markdown(f"### {titulo}")

                            st.write(
                                "**Autor:** " + ", ".join(autores)
                            )

                            st.write("**Editora:**", editora)

                            st.write("**Publicação:**", ano)

                            with st.expander("Ver descrição"):
                                st.write(descricao)

                            if link:
                                st.link_button(
                                    "Mais informações",
                                    link
                                )

        else:
            st.warning("Nenhum livro encontrado.")

    else:
        st.warning("Digite o nome de um livro para pesquisar.")
