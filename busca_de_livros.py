# Este aqui é a estrutura planejada da página de busca dos livros, Podem alterar este comentário se quiserem mudanças
import streamlit as st
from tela_Api import buscar_livros

st.title("Biblioteca Digital")
st.write("Pesquise livros pelo título, autor ou assunto.")

termo = st.text_input(
    "Digite o nome do livro:",
    placeholder="Ex.: Clean Code"
)

if st.button("Pesquisar livros"):
    if not termo.strip():
        st.warning("Digite o nome de um livro.")
    else:
        with st.spinner("Pesquisando livros..."):
            livros = buscar_livros(termo)

        if livros is None:
            st.error(
                "Não foi possível acessar o Google Books. "
                "Verifique sua conexão e tente novamente."
            )

        elif not livros:
            st.info("Nenhum livro encontrado.")

        else:
            st.success(f"{len(livros)} livros encontrados!")

            for livro in livros:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        if livro["imagem"]:
                            st.image(
                                livro["imagem"],
                                use_container_width=True
                            )

                    with col2:
                        st.subheader(livro["titulo"])

                        st.write(
                            "Autor(es): "
                            + ", ".join(livro["autores"])
                        )

                        st.write(f"Ano: {livro['ano']}")

                        st.write(livro["descricao"])

                        if livro["link"]:
                            st.link_button(
                                "Ver livro no Google Books",
                                livro["link"]
                            )


import streamlit as st
import requests

st.header("Pesquisar livros")

termo = st.text_input("Digite o nome do livro, autor ou ISBN")

if st.button("Pesquisar"):
    if termo.strip():
        url = "https://www.googleapis.com/books/v1/volumes"

        parametros = {
            "q": termo,
            "maxResults": 10
        }

        try:
            resposta = requests.get(
                url,
                params=parametros,
                timeout=10
            )

            resposta.raise_for_status()
            dados = resposta.json()
            livros = dados.get("items", [])

            if livros:
                for livro in livros:
                    info = livro.get("volumeInfo", {})

                    titulo = info.get(
                        "title", "Título indisponível"
                    )

                    autores = info.get(
                        "authors", ["Autor desconhecido"]
                    )

                    descricao = info.get(
                        "description",
                        "Descrição indisponível"
                    )

                    st.subheader(titulo)
                    st.write("Autor(es): " + ", ".join(autores))
                    st.write(descricao)

                    imagem = info.get(
                        "imageLinks", {}
                    ).get("thumbnail")

                    if imagem:
                        st.image(imagem, width=120)

                    link = info.get("infoLink")

                    if link:
                        st.write(f"[Ver livro no Google Books]({link})")

                    st.divider()

            else:
                st.warning("Nenhum livro encontrado.")

        except requests.RequestException as erro:
            st.error(f"Erro ao pesquisar livros: {erro}")

    else:
        st.warning("Digite o nome de um livro para pesquisar.")
