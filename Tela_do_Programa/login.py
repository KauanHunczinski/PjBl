import streamlit as st


st.set_page_config(
    page_title="Login",
    layout="centered",
    initial_sidebar_state="collapsed"
)

email = st.text_input("E-mail")
senha = st.text_input("Senha", type="password")

if st.button("Cadastrar", type="primary"):
    if email.strip() == "" or senha.strip() == "":
        st.write("Preencha Todos os Campos.")
    else: 
        st.switch_page("painel.py")


if st.button("Testar usuario"):
    st.switch_page("painel.py")
if st.button("Testar gerencia"):
    st.switch_page("painel_gerencia.py")