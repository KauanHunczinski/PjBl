import streamlit as st
from datetime import datetime

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.subheader("Meu espaco")
    st.write("Area do Usuario")

    if st.button("Voltar ao login", type="primary"):
        st.switch_page("login.py",)





if "desejos" not in st.session_state:
    st.session_state["desejos"] = []

st.title("Meu painel")

# criado lista

exemplo_de_emprestimos = [
    {
        "Produtos": "Furadeira",
        "Retirada": "17/10/2026",
        "Devolver ate": "24/10/2026",
    },

    {
        "Produtos": "Martelo",
        "Retirada": "20/10/2026",
        "Devolver ate": "02/11/2026",
    }
]

datas_devolucao = []

for emprestimo in exemplo_de_emprestimos: 
    texto = emprestimo["Devolver ate"]
    data = datetime.strptime(texto, "%d/%m/%Y")
    datas_devolucao.append(data)
if datas_devolucao:
    menor_data = min(datas_devolucao)
    proxima_devolucao = menor_data.strftime("%d/%m/%Y")
else:
    proxima_devolucao = "-"


col_emprestimos, col_devolucao, col_desejos = st.columns(3)

# para adicionar separar as colunas
with col_emprestimos:
    st.metric("Emprestimos ativos", len(exemplo_de_emprestimos))
with col_devolucao:
    st.metric("Proxima devolução", proxima_devolucao)
with col_desejos:
    st.metric("Lista de Desejos", len(st.session_state["desejos"]) )


st.subheader("Meus emprestimos")
st.write("Dados testes")



if not exemplo_de_emprestimos:
    st.write("Voce nao tem emprestimos.")
else:
    st.dataframe(exemplo_de_emprestimos, hide_index=True)

st.subheader("Lista de Desejos")

produto_desejado = st.selectbox(
    "Qual produto voce deseja pegar emprestado?",
    ["Furadeira", "Martelo", "Escada"]


)
if st.button("Adicionar a lista"):
    if produto_desejado not in st.session_state["desejos"]:
        st.session_state["desejos"].append(produto_desejado)
        st.rerun()
if not st.session_state["desejos"]:
    st.write("Sua lista de desejos esta vazia.")
for produto in st.session_state["desejos"].copy():
    st.write(produto)
    remover = st.button("Remover", key="remover_" + produto)
    if remover:
        st.session_state["desejos"].remove(produto)
        st.rerun()
