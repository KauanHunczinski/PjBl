import streamlit as st


login = st.Page("login.py", title="login", default=True)
painel = st.Page("painel.py", title="Meu painel", url_path="painel")
gerencia = st.Page(
    "painel_gerencia.py",
    title="Gerencia"
)

pagina = st.navigation([login, painel, gerencia], position="hidden")
pagina.run()