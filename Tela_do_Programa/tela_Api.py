import os
import re
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

from Livros.view import selecionar_correspondencia_google


URL_GOOGLE_BOOKS = "https://www.googleapis.com/books/v1/volumes"


def ler_chave_google():
    chave_api = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
    if chave_api:
        return chave_api

    arquivo_segredos = (
        Path(__file__).resolve().parent.parent
        / ".streamlit"
        / "secrets.toml"
    )
    if not arquivo_segredos.exists():
        return ""

    return st.secrets["GOOGLE_BOOKS_API_KEY"].strip()


@st.cache_data(ttl=3600, show_spinner=False)
def _buscar_json_google(url, parametros, chave_api):
    parametros_requisicao = dict(parametros)
    parametros_requisicao["key"] = chave_api
    resposta = requests.get(
        url,
        params=parametros_requisicao,
        timeout=15,
    )
    if resposta.status_code == 429:
        raise requests.HTTPError(
            "Google Books quota exceeded",
            response=resposta,
        )
    resposta.raise_for_status()
    return resposta.json()


def _consultar_google(url, parametros):
    chave_api = ler_chave_google()
    if not chave_api:
        st.error(
            "A chave da API do Google Books não está configurada neste computador. "
            "Instalar os pacotes de dependencias.txt não configura essa chave."
        )
        st.info(
            "Para configurar: copie .streamlit/secrets.toml.example para "
            ".streamlit/secrets.toml, coloque sua chave em GOOGLE_BOOKS_API_KEY "
            "e reinicie o Streamlit. Você também pode definir essa variável "
            "no ambiente."
        )
        return None

    try:
        return _buscar_json_google(url, parametros, chave_api)
    except requests.HTTPError as erro:
        if erro.response is not None and erro.response.status_code == 429:
            st.error(
                "O Google Books atingiu o limite de consultas. "
                "Verifique a cota da chave configurada e tente novamente mais tarde."
            )
        else:
            st.error("Não foi possível recuperar os dados do Google Books.")
    except requests.RequestException:
        st.error("Não foi possível acessar o Google Books. Verifique a conexão.")
    return None


def buscar_livros(termo_busca, quantidade=10):
    parametros = {
        "q": termo_busca,
        "maxResults": max(1, min(40, quantidade)),
    }
    resposta = _consultar_google(URL_GOOGLE_BOOKS, parametros)
    if resposta is None:
        return None
    return resposta.get("items", [])


def buscar_livro_por_id(volume_id):
    if not volume_id:
        return None
    url = f"{URL_GOOGLE_BOOKS}/{quote(str(volume_id), safe='')}"
    return _consultar_google(url, {"projection": "full"})


def buscar_correspondencia_acervo(livro):
    volume_id = livro.get("google_book_id")
    if volume_id:
        volume = buscar_livro_por_id(volume_id)
        if volume:
            return volume

    titulo = str(livro.get("titulo") or "").strip()
    autor = str(livro.get("autor") or "").strip()
    editora = str(livro.get("editora") or "").strip()
    isbn = re.sub(r"[^0-9x]", "", str(livro.get("isbn") or "").casefold())
    consultas = []

    if isbn:
        consultas.append(f"isbn:{isbn}")

    if titulo and autor:
        consultas.append(f'intitle:"{titulo}" inauthor:"{autor}"')
    elif titulo and editora:
        consultas.append(f'intitle:"{titulo}" inpublisher:"{editora}"')

    for consulta in consultas:
        resultados = buscar_livros(consulta, quantidade=10)
        if resultados is None:
            break
        correspondencia = selecionar_correspondencia_google(livro, resultados)
        if correspondencia is not None:
            return correspondencia
    return None
