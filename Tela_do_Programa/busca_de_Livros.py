import html
import re
import unicodedata
from pathlib import Path

import streamlit as st

from Livros.view import (
    combinar_dados_livro,
    listar_livros_com_disponibilidade,
    mapear_correspondencias_google,
    livro_pode_corresponder_ao_acervo,
    obter_perfil_usuario,
    solicitar_aquisicao,
    acompanhar_disponibilidade,
)
from Tela_do_Programa.tela_Api import (
    buscar_correspondencia_acervo,
    buscar_livro_por_id,
    buscar_livros,
    ler_chave_google,
)


st.set_page_config(
    page_title="Biblioteca Digital",
    page_icon="📚",
    layout="wide",
)

caminho_css = Path(__file__).resolve().parent / "design_Tela_Api.css"
if caminho_css.exists():
    st.markdown(
        f"<style>{caminho_css.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

usuario_logado = st.session_state.get("usuario_logado")
perfil_usuario = (
    obter_perfil_usuario(usuario_logado.get("id"))
    if isinstance(usuario_logado, dict)
    else None
)
if perfil_usuario is None:
    st.switch_page("login.py")
elif perfil_usuario != "usuario":
    st.switch_page("painel_gerencia.py")

CATEGORIAS = {
    "Todas": "",
    "Ficção": "fiction",
    "Romance": "romance",
    "Aventura": "adventure",
    "Mistério": "mystery",
    "Não ficção": "nonfiction",
}
IDIOMAS = {"Todos": "", "Português": "pt", "Inglês": "en"}


def obter_ano(info):
    data_publicacao = str(info.get("publishedDate", ""))
    return data_publicacao[:4] or "Ano não informado"


def _descricao_plana(descricao):
    texto = re.sub(r"<\s*br\s*/?\s*>|</\s*(p|div|li)\s*>", "\n", descricao or "", flags=re.I)
    texto = re.sub(r"<[^>]*>", " ", texto)
    return html.unescape(texto).strip()


def _solicitar_aquisicao(livro, chave):
    if st.button("Solicitar aquisição", key=chave, width="stretch"):
        try:
            registrada = solicitar_aquisicao(usuario_logado["id"], livro)
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
        else:
            if registrada:
                st.success("Sugestão de aquisição enviada à biblioteca.")
            else:
                st.info("Sua sugestão para este livro já está registrada.")
    st.caption(
        "A sugestão não representa compra automática nem garante a aquisição."
    )


def _acompanhar_livro(acervo, chave):
    if st.button(
        "Avise-me quando estiver disponível",
        key=chave,
        width="stretch",
    ):
        try:
            registrado = acompanhar_disponibilidade(
                usuario_logado["id"],
                acervo["id"],
            )
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
        else:
            if registrado:
                st.success("Você será avisado quando houver um exemplar disponível.")
            else:
                st.info("Você já acompanha a disponibilidade deste livro.")
    st.caption(
        "O aviso não é uma reserva nem garante prioridade; "
        "os empréstimos continuam presenciais."
    )


@st.dialog("Detalhes do livro", width="large")
def mostrar_detalhes(livro, acervo=None):
    volume_id = livro.get("id")
    volume = livro
    if volume_id and ler_chave_google():
        volume_completo = buscar_livro_por_id(volume_id)
        if volume_completo:
            volume = volume_completo
    if acervo is not None:
        volume = combinar_dados_livro(acervo, volume)

    info = volume.get("volumeInfo") or {}
    links_imagem = info.get("imageLinks") or {}
    capa = next(
        (
            links_imagem.get(tamanho)
            for tamanho in ("extraLarge", "large", "medium", "small", "thumbnail", "smallThumbnail")
            if links_imagem.get(tamanho)
        ),
        None,
    )
    if capa:
        capa = capa.replace("http://", "https://", 1)

    coluna_capa, coluna_dados = st.columns([1, 2], vertical_alignment="top")
    with coluna_capa:
        if capa:
            st.image(capa, width="stretch")
        else:
            st.caption("Capa indisponível")

    with coluna_dados:
        titulo = str(info.get("title") or "Título não informado")
        st.html(f"<h3>{html.escape(titulo)}</h3>")
        if info.get("subtitle"):
            st.text(str(info["subtitle"]))

        isbn_por_tipo = {
            item.get("type"): item.get("identifier")
            for item in (info.get("industryIdentifiers") or [])
            if item.get("type") and item.get("identifier")
        }
        isbn10 = isbn_por_tipo.get("ISBN_10")
        isbn13 = isbn_por_tipo.get("ISBN_13")
        if acervo and acervo.get("isbn"):
            isbn_local = str(acervo["isbn"])
            if len(re.sub(r"\D", "", isbn_local)) == 10:
                isbn10 = isbn10 or isbn_local
            else:
                isbn13 = isbn13 or isbn_local

        dados_bibliograficos = [
            ("Autor(es)", ", ".join(info.get("authors") or [])),
            ("Editora", info.get("publisher")),
            ("Publicação", info.get("publishedDate")),
            ("ISBN-10", isbn10),
            ("ISBN-13", isbn13),
            ("Páginas", info.get("pageCount")),
            ("Idioma", info.get("language")),
            ("Categorias", ", ".join(info.get("categories") or [])),
            ("Tipo", info.get("printType")),
            ("Dimensões", ", ".join(
                f"{chave}: {valor}"
                for chave, valor in (info.get("dimensions") or {}).items()
                if valor
            )),
            ("Avaliação", (
                f"{info['averageRating']}/5 ({info.get('ratingsCount', 0)} avaliações)"
                if info.get("averageRating") is not None
                else None
            )),
        ]
        for rotulo, valor in dados_bibliograficos:
            if valor:
                st.markdown(f"**{rotulo}:**")
                st.text(str(valor))

    descricao = _descricao_plana(info.get("description", ""))
    if descricao:
        st.markdown("#### Sinopse")
        st.text(descricao)

    if acervo is not None:
        st.markdown("#### Disponibilidade na biblioteca")
        if acervo["disponiveis"] > 0:
            st.success(
                f"Disponível para empréstimo ({acervo['disponiveis']} de "
                f"{acervo['total_exemplares']} exemplares)"
            )
        elif acervo["situacao"] == "Todos os exemplares emprestados":
            status_coluna, aviso_coluna = st.columns(
                [1, 1.5],
                vertical_alignment="center",
            )
            status_coluna.markdown("**Emprestado para outro usuário**")
            with aviso_coluna:
                _acompanhar_livro(
                    acervo,
                    f"acompanhar_detalhes_{acervo['id']}",
                )
        else:
            st.warning("Indisponível para empréstimo no momento.")
    else:
        _solicitar_aquisicao(
            volume,
            f"solicitar_detalhes_{volume_id or 'livro'}",
        )

    if st.button("Fechar", key=f"fechar_detalhes_{volume_id or 'livro'}"):
        st.rerun()


def exibir_livro(coluna, livro, acervo=None, indice=0):
    info = livro.get("volumeInfo") or {}
    autores = info.get("authors") or ["Autor não informado"]
    links_imagem = info.get("imageLinks") or {}
    imagem = (
        links_imagem.get("medium")
        or links_imagem.get("small")
        or links_imagem.get("thumbnail")
        or links_imagem.get("smallThumbnail")
    )

    if imagem:
        imagem = imagem.replace("http://", "https://", 1)

    if acervo is not None:
        chave = f"livro_acervo_{acervo['id']}_{indice}"
    else:
        identificador = re.sub(r"[^a-zA-Z0-9_-]", "_", str(livro.get("id") or indice))
        chave = f"livro_externo_{identificador}_{indice}"

    with coluna:
        with st.container(border=True, key=chave):
            capa, detalhes = st.columns([1, 2], vertical_alignment="top")

            with capa:
                if imagem:
                    st.image(imagem, width="stretch")
                else:
                    st.caption("Capa indisponível")

            with detalhes:
                titulo = str(info.get("title") or "Título não informado")
                st.html(f"<h4>{html.escape(titulo)}</h4>")
                st.text("Autor(es): " + ", ".join(str(autor) for autor in autores))
                editora = info.get("publisher") or "Editora não informada"
                st.text(f"{editora} · {obter_ano(info)}")

                isbn = next(
                    (
                        item.get("identifier")
                        for item in (info.get("industryIdentifiers") or [])
                        if item.get("identifier")
                    ),
                    None,
                )
                if isbn:
                    st.text(f"ISBN: {isbn}")

                avaliacao = info.get("averageRating")
                if avaliacao is not None:
                    st.write(f"⭐ {avaliacao}/5")

            if st.button(
                "Ver detalhes",
                key=f"detalhes_{chave}",
                width="stretch",
            ):
                mostrar_detalhes(livro, acervo=acervo)

            if acervo is None:
                st.warning("FORA DO ACERVO — indisponível para empréstimo")
                _solicitar_aquisicao(
                    livro,
                    f"solicitar_{chave}",
                )

def _normalizar_consulta(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return " ".join(re.sub(r"[^\w]", " ", texto.casefold()).split())


def _livro_local_corresponde_a_consulta(livro, termo):
    termos = _normalizar_consulta(termo).split()
    campos = _normalizar_consulta(
        " ".join(
            str(livro.get(campo) or "")
            for campo in ("titulo", "autor", "editora", "isbn")
        )
    )
    return bool(termos) and all(termo_individual in campos for termo_individual in termos)


def _enriquecer_livro_local(livro, chave_configurada):
    volume = buscar_correspondencia_acervo(livro) if chave_configurada else None
    return combinar_dados_livro(livro, volume)


st.title("Biblioteca Digital")
st.write("Consulte o acervo da biblioteca ou pesquise livros no Google Books.")

if "busca_atual" not in st.session_state:
    st.session_state["busca_atual"] = ""
if "resultados_guardados" not in st.session_state:
    st.session_state["resultados_guardados"] = {}

with st.form("formulario_pesquisa"):
    termo_digitado = st.text_input(
        "Pesquisar livros",
        placeholder="Digite o título, autor ou assunto",
        key="campo_pesquisa",
    )
    pesquisar = st.form_submit_button("Pesquisar")

if pesquisar:
    st.session_state["busca_atual"] = termo_digitado.strip()

with st.sidebar:
    with st.container(key="perfil_acesso"):
        foto_perfil = st.session_state.get("foto_perfil_bytes")
        coluna_foto, coluna_painel = st.columns(
            [1, 3],
            vertical_alignment="center",
        )
        with coluna_foto:
            if foto_perfil:
                st.image(foto_perfil, width=56)
            else:
                inicial = html.escape(
                    str(usuario_logado.get("nome") or "?")[:1].upper()
                )
                st.html(f'<div class="avatar-catalogo">{inicial}</div>')
        with coluna_painel:
            if st.button(
                "Meu painel",
                key="abrir_painel_usuario",
                icon=":material/account_circle:",
                width="stretch",
            ):
                st.switch_page("painel.py")

with st.sidebar.form("formulario_filtros"):
    st.header("Filtros")
    categoria = st.selectbox("Categoria", list(CATEGORIAS))
    idioma = st.selectbox("Idioma", list(IDIOMAS))
    ordem = st.selectbox("Ordenar por", ["Relevância", "Mais recentes", "Título"])
    quantidade = st.selectbox("Resultados", [10, 20, 30])
    st.form_submit_button("Aplicar filtros")

livros_acervo = listar_livros_com_disponibilidade()
termo = st.session_state["busca_atual"]
chave_configurada = bool(ler_chave_google())

if not termo:
    st.subheader("Livros cadastrados na biblioteca")
    st.caption("A página inicial exibe somente títulos registrados no acervo.")
    if livros_acervo and not chave_configurada:
        st.info("Configure a chave do Google Books para carregar capas e dados bibliográficos.")
    if not livros_acervo:
        st.info("Nenhum livro cadastrado no acervo.")
    else:
        with st.spinner("Carregando dados bibliográficos..."):
            livros_enriquecidos = [
                _enriquecer_livro_local(livro, chave_configurada)
                for livro in livros_acervo
            ]
        for indice in range(0, len(livros_enriquecidos), 2):
            colunas = st.columns(2)
            for coluna, livro in zip(
                colunas,
                livros_enriquecidos[indice : indice + 2],
            ):
                exibir_livro(
                    coluna,
                    livro,
                    acervo=livro["acervo"],
                    indice=indice,
                )
else:
    consulta = termo
    categoria_google = CATEGORIAS[categoria]
    if categoria_google:
        consulta = f"{consulta} subject:{categoria_google}"
    st.subheader(f'Resultados para "{termo}"')

    consulta_guardada = (consulta, quantidade)
    if consulta_guardada not in st.session_state["resultados_guardados"]:
        with st.spinner("Pesquisando no Google Books..."):
            resultado = buscar_livros(consulta, quantidade=quantidade)
        if resultado is not None:
            st.session_state["resultados_guardados"][consulta_guardada] = resultado
    else:
        resultado = st.session_state["resultados_guardados"][consulta_guardada]

    resultados_google = resultado or []
    codigo_idioma = IDIOMAS[idioma]
    if codigo_idioma:
        resultados_google = [
            livro
            for livro in resultados_google
            if (livro.get("volumeInfo") or {}).get("language") == codigo_idioma
        ]

    if ordem == "Mais recentes":
        resultados_google = sorted(
            resultados_google,
            key=lambda livro: obter_ano(livro.get("volumeInfo") or {}),
            reverse=True,
        )
    elif ordem == "Título":
        resultados_google = sorted(
            resultados_google,
            key=lambda livro: (livro.get("volumeInfo") or {})
            .get("title", "")
            .casefold(),
        )

    livros_para_exibir = []
    ids_acervo_exibidos = set()
    correspondencias = mapear_correspondencias_google(
        livros_acervo,
        resultados_google,
    )
    ids_google_exibidos = set()
    for livro_google in resultados_google:
        google_id = livro_google.get("id")
        if google_id and google_id in ids_google_exibidos:
            continue
        if google_id:
            ids_google_exibidos.add(google_id)
        acervo = correspondencias.get(google_id)
        if acervo is not None:
            if acervo["id"] in ids_acervo_exibidos:
                continue
            ids_acervo_exibidos.add(acervo["id"])
            livros_para_exibir.append(
                combinar_dados_livro(acervo, livro_google)
            )
        elif not livro_pode_corresponder_ao_acervo(
            livro_google,
            livros_acervo,
        ):
            livros_para_exibir.append(livro_google)

    for livro in livros_acervo:
        if (
            livro["id"] not in ids_acervo_exibidos
            and _livro_local_corresponde_a_consulta(livro, termo)
        ):
            livros_para_exibir.append(
                _enriquecer_livro_local(livro, chave_configurada)
            )
            ids_acervo_exibidos.add(livro["id"])

    if not livros_para_exibir:
        st.info("Nenhum livro encontrado com esses filtros.")
    else:
        st.caption(f"{len(livros_para_exibir)} livros")
        for indice in range(0, len(livros_para_exibir), 2):
            colunas = st.columns(2)
            for coluna, livro in zip(
                colunas,
                livros_para_exibir[indice : indice + 2],
            ):
                exibir_livro(
                    coluna,
                    livro,
                    acervo=livro.get("acervo"),
                    indice=indice,
                )
