import os
from pathlib import Path

import requests
import streamlit as st


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


def buscar_livros(termo_busca, quantidade=10):
    chave_api = ler_chave_google()
    if not chave_api:
        st.error(
            "A chave da API do Google Books não está configurada. "
            "Defina GOOGLE_BOOKS_API_KEY no ambiente ou em .streamlit/secrets.toml."
        )
        return None

    parametros = {
        "q": termo_busca,
        "maxResults": max(1, min(40, quantidade)),
        "key": chave_api,
    }

    try:
        resposta = requests.get(URL_GOOGLE_BOOKS, params=parametros, timeout=15)
        if resposta.status_code == 429:
            st.error(
                "O Google Books atingiu o limite de consultas. "
                "Verifique a cota da chave configurada e tente novamente mais tarde."
            )
            return None

        resposta.raise_for_status()
    except requests.RequestException:
        st.error("Não foi possível acessar o Google Books. Verifique a conexão.")
        return None

    return resposta.json().get("items", [])
