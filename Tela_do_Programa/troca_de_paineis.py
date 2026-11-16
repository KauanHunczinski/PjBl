import streamlit as st


login = st.Page("login.py", title="login", default=True)
painel = st.Page("painel.py", title="Meu painel", url_path="painel")
busca = st.Page(
    "busca_de_Livros.py",
    title="Biblioteca Digital",
    url_path="biblioteca",
)
gerencia = st.Page(
    "painel_gerencia.py",
    title="Gerencia"
)

pagina = st.navigation([login, painel, busca, gerencia], position="hidden")
pagina.run()