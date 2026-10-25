# Aqui será o código da tela de busca para livros
import requests


def buscar_livros(termo_busca, quantidade=10):
    """Pesquisa livros na API do Google Books."""

    termo_busca = termo_busca.strip()

    if not termo_busca:
        return []

    url = "https://www.googleapis.com/books/v1/volumes"

    parametros = {
        "q": termo_busca,
        "maxResults": max(1, min(quantidade, 40)),
        "orderBy": "relevance",
        "printType": "books",
    }

    try:
        resposta = requests.get(
            url,
            params=parametros,
            timeout=10
        )

        resposta.raise_for_status()
        dados = resposta.json()

        livros = []

        for item in dados.get("items", []):
            info = item.get("volumeInfo", {})

            livros.append({
                "titulo": info.get(
                    "title", "Título indisponível"
                ),
                "autores": info.get(
                    "authors", ["Autor desconhecido"]
                ),
                "descricao": info.get(
                    "description", "Sem descrição disponível."
                ),
                "imagem": info.get(
                    "imageLinks", {}
                ).get("thumbnail"),
                "ano": info.get(
                    "publishedDate", "Ano desconhecido"
                ),
                "link": info.get(
                    "infoLink", ""
                )
            })

        return livros

    except requests.RequestException as erro:
        print(f"Erro ao consultar Google Books: {erro}")
        return None
