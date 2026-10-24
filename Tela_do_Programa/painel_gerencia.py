import streamlit as st

st.set_page_config(
    page_title="Gerencia",
    layout="wide"

)
with st.sidebar:
    st.subheader("Area da Gerencia")
    if st.button("Voltar ao login"):
        st.switch_page("login.py")
    st.subheader("Cadastro de Usuarios")
    with st.form("cadastro_de_usuario"):
                nome = st.text_input("Nome")
                sobrenome = st.text_input("Sobrenome")
                endereco = st.text_input("Endereco")
                email = st.text_input("Email")
                telefone = st.text_input("Telefone")
                cadastrar = st.form_submit_button(
                    "Cadastrar",
                    type="primary"
                )







st. title("Painel Gerencia")
st.write("Gerencie produtos, Usuarios, emprestimos e devoluçoes")

