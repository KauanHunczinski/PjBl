import streamlit as st
from Livros.view import insert_user, exibir_usuarios
from pathlib import Path


st.set_page_config(
    page_title="Gerencia",
    layout="wide",
    initial_sidebar_state="expanded"
)


usuario_logado = st.session_state.get("usuario_logado")

if usuario_logado is None:
    st.switch_page("login.py")

elif usuario_logado.get("perfil") != "gerente":
    st.switch_page("painel.py")


with st.sidebar:
    st.subheader("Area da Gerencia")
    if st.button("Voltar ao login"):
        st.session_state.clear()
        st.switch_page("login.py")
    st.subheader("Cadastro de Usuarios")
    with st.form("cadastro_de_usuario", clear_on_submit=True):
                nome = st.text_input("Nome")
                sobrenome = st.text_input("Sobrenome")
                endereco = st.text_input("Endereco")
                email = st.text_input("Email")
                telefone = st.text_input("Telefone")
                senha = st.text_input("Senha", type="password")
                confirmar_senha = st.text_input("Confirme sua senha", type="password")
                cadastrar = st.form_submit_button(
                    "Cadastrar",
                    type="primary"
                )
    if cadastrar:
        if nome.strip() == "" or sobrenome.strip() == "" or endereco.strip() == "" or email.strip() == "" or telefone.strip() == "":
            st.write("Preencha todos os campos")
        elif senha == "" or confirmar_senha == "":
            st.write("Preencha a senha e a confirmacao.")
        elif senha != confirmar_senha:
            st.write("As senhas nao coincidem.") 
        else:
            insert_user(
                nome.strip(),
                sobrenome.strip(),
                endereco.strip(),
                email.strip(),
                telefone.strip(),
                senha
            )
            st.write("Usuario cadastrado com sucesso!")
            st.session_state.clear()



st. title("Painel Gerencia")
st.write("Gerencie produtos, Usuarios, emprestimos e devoluçoes")

usuarios = exibir_usuarios()
linhas = []

for usuario in usuarios:
    linhas.append({
        "ID": usuario[0],
        "Nome": usuario[1],
        "Sobrenome": usuario[2],
        "E-mail": usuario[3]
    })
st.dataframe(linhas, hide_index=True)