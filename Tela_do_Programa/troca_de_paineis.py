import streamlit as st


login = st.Page("login.py", title="login", default=True)
painel = st.Page("painel.py", title="Meu painel", url_path="painel")

pagina = st.navigation([login, painel], position="hidden")
pagina.run()