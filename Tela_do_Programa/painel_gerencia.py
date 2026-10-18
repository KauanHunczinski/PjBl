import streamlit as st

st.set_page_config(
    page_title="Gerencia",
    layout="wide"

)
with st.sidebar:
    st.subheader("Area da Gerencia")
    if st.button("Voltar ao login"):
        st.switch_page("login.py")

st. title("Painel Gerencia")
st.write("Gerencie produtos, Usuarios, emprestimos e devoluçoes")

