import streamlit as st
from Livros.view import autenticar_usuario


st.set_page_config(
    page_title="Login",
    layout="centered",
    initial_sidebar_state="collapsed"
)

email = st.text_input("E-mail")
senha = st.text_input("Senha", type="password")

if st.button("Entrar", type="primary"):
    if email.strip() == "" or senha.strip() == "":
        st.error("Preencha o e-mail e a senha.")
    else: 
        usuario = autenticar_usuario(email, senha)
        if usuario is None:
            st.error("E-mail ou senha invalidos.")
        else:
            st.session_state.clear()
            st.session_state["usuario_logado"] = usuario
            st.switch_page("painel.py")
