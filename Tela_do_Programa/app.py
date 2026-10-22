# necessário baixar stremlit no terminal, para baixar digite: python -m pip install streamlit
#para mostrar tela e necessario escrever no terminal: python -m streamlit python -m streamlit run .\Tela_do_Programa\app.py
import streamlit as st

# Para adicionar titulo e subtitulo

st.title("Sistema de Cadastro")
st.write("preencha os dados abaixo. ")

#aba

aba_produtos, aba_gerencia = st.tabs(["Produtos", "Gerencia"])

with aba_produtos:
    st.write("Catalogo de Produtos.")

with aba_gerencia:
    st.write("Preencha os dados abaixo.")

#Para adicionar texto de input no programa


nome = st.text_input("Nome Completo")
email = st.text_input("E-mail")

#Para adicionar opcao de cadastro

if st.button("Cadastrar"):
    if nome.strip == "" or email.strip() == "":
        st.write("Preencha Todos os Campos.")
    else: 
        st.write("Nome:", nome)
        st.write("E-mail:", email)


