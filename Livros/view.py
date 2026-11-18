import hashlib
import re
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

gerador_hash = PasswordHasher()


def _caminho_banco():
    return Path(__file__).resolve().parent.parent / "dados.db"


def connect():
    conn = sqlite3.connect(_caminho_banco(), timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    _migrar_esquema(conn)
    return conn


def _colunas_tabela(conn, tabela):
    return {
        coluna[1]
        for coluna in conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    }


def _adicionar_coluna(conn, tabela, coluna, definicao):
    if coluna not in _colunas_tabela(conn, tabela):
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def _criar_tabela_aquisicoes(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS solicitacoes_aquisicao (
            id INTEGER PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            google_book_id TEXT,
            titulo TEXT NOT NULL,
            autor TEXT,
            isbn TEXT,
            isbn10 TEXT,
            isbn13 TEXT,
            editora TEXT,
            capa TEXT,
            chave_solicitacao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente'
                CHECK (status IN ('Pendente', 'Em análise', 'Aprovada', 'Recusada', 'Adquirida')),
            criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _migrar_tabela_aquisicoes(conn):
    tabela = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'solicitacoes_aquisicao'"
    ).fetchone()
    if tabela:
        sql_normalizado = re.sub(r"\s+", "", tabela[0] or "").upper()
        if "UNIQUE(USUARIO_ID,CHAVE_SOLICITACAO)" in sql_normalizado:
            conn.execute(
                "ALTER TABLE solicitacoes_aquisicao RENAME TO solicitacoes_aquisicao_legada"
            )
            _criar_tabela_aquisicoes(conn)
            colunas_legadas = _colunas_tabela(conn, "solicitacoes_aquisicao_legada")
            colunas_destino = (
                "id",
                "usuario_id",
                "google_book_id",
                "titulo",
                "autor",
                "isbn",
                "isbn10",
                "isbn13",
                "editora",
                "capa",
                "chave_solicitacao",
                "status",
                "criada_em",
            )
            padroes = {
                "isbn10": "NULL",
                "isbn13": "NULL",
                "editora": "NULL",
            }
            expressoes = [
                coluna if coluna in colunas_legadas else padroes.get(coluna, "NULL")
                for coluna in colunas_destino
            ]
            conn.execute(
                f"""
                INSERT INTO solicitacoes_aquisicao ({", ".join(colunas_destino)})
                SELECT {", ".join(expressoes)}
                FROM solicitacoes_aquisicao_legada
                """
            )
            conn.execute("DROP TABLE solicitacoes_aquisicao_legada")
    _criar_tabela_aquisicoes(conn)
    _adicionar_coluna(conn, "solicitacoes_aquisicao", "isbn10", "TEXT")
    _adicionar_coluna(conn, "solicitacoes_aquisicao", "isbn13", "TEXT")
    _adicionar_coluna(conn, "solicitacoes_aquisicao", "editora", "TEXT")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_solicitacao_ativa_usuario_livro
        ON solicitacoes_aquisicao(usuario_id, chave_solicitacao)
        WHERE status IN ('Pendente', 'Em análise', 'Aprovada')
        """
    )


def _criar_exemplares_legados(conn):
    for (livro_id,) in conn.execute("SELECT id FROM livros").fetchall():
        existentes = conn.execute(
            "SELECT COUNT(*) FROM exemplares WHERE livro_id = ?",
            (livro_id,),
        ).fetchone()[0]
        emprestimos_ativos = conn.execute(
            """
            SELECT COUNT(*)
            FROM emprestimos
            WHERE id_livro = ? AND status = 'Ativo'
            """,
            (livro_id,),
        ).fetchone()[0]
        quantidade_necessaria = max(1, emprestimos_ativos)
        for numero in range(existentes + 1, quantidade_necessaria + 1):
            conn.execute(
                """
                INSERT INTO exemplares (livro_id, codigo)
                VALUES (?, ?)
                """,
                (livro_id, f"L{livro_id}-{numero:03d}"),
            )

        exemplar_ids = [
            linha[0]
            for linha in conn.execute(
                """
                SELECT e.id
                FROM exemplares AS e
                WHERE e.livro_id = ?
                  AND NOT EXISTS (
                      SELECT 1
                      FROM emprestimos AS ep
                      WHERE ep.id_exemplar = e.id AND ep.status = 'Ativo'
                  )
                ORDER BY e.id
                """,
                (livro_id,),
            ).fetchall()
        ]
        emprestimos_sem_exemplar = [
            linha[0]
            for linha in conn.execute(
                """
                SELECT id
                FROM emprestimos
                WHERE id_livro = ? AND status = 'Ativo' AND id_exemplar IS NULL
                ORDER BY id
                """,
                (livro_id,),
            ).fetchall()
        ]
        for emprestimo_id, exemplar_id in zip(
            emprestimos_sem_exemplar,
            exemplar_ids,
        ):
            conn.execute(
                "UPDATE emprestimos SET id_exemplar = ? WHERE id = ?",
                (exemplar_id, emprestimo_id),
            )


def _migrar_esquema(conn):
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY,
                titulo TEXT,
                autor TEXT,
                editora TEXT,
                ano_publicacao INTEGER,
                isbn TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                sobrenome TEXT,
                endereco TEXT,
                email TEXT,
                telefone TEXT,
                senha_hash TEXT,
                perfil TEXT NOT NULL DEFAULT 'usuario'
                    CHECK (perfil IN ('usuario', 'gerente'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY,
                id_livro INTEGER REFERENCES livros(id),
                id_usuario INTEGER REFERENCES usuarios(id),
                data_emprestimo TEXT,
                data_devolucao TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lista_desejos (
                usuario_id INTEGER,
                livro_id INTEGER,
                PRIMARY KEY (usuario_id, livro_id)
            )
            """
        )
        _adicionar_coluna(conn, "usuarios", "senha_hash", "TEXT")
        _adicionar_coluna(
            conn,
            "usuarios",
            "perfil",
            "TEXT NOT NULL DEFAULT 'usuario'",
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exemplares (
                id INTEGER PRIMARY KEY,
                livro_id INTEGER NOT NULL REFERENCES livros(id),
                codigo TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'Disponível'
                    CHECK (status IN ('Disponível', 'Indisponível')),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _adicionar_coluna(
            conn,
            "emprestimos",
            "id_exemplar",
            "INTEGER REFERENCES exemplares(id)",
        )
        _adicionar_coluna(
            conn,
            "emprestimos",
            "status",
            "TEXT NOT NULL DEFAULT 'Ativo'",
        )
        _adicionar_coluna(conn, "emprestimos", "devolvido_em", "TEXT")
        _criar_exemplares_legados(conn)
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_emprestimo_exemplar_ativo
            ON emprestimos(id_exemplar)
            WHERE id_exemplar IS NOT NULL AND status = 'Ativo'
            """
        )
        _migrar_tabela_aquisicoes(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_solicitacoes_aquisicao (
                id INTEGER PRIMARY KEY,
                solicitacao_id INTEGER NOT NULL
                    REFERENCES solicitacoes_aquisicao(id) ON DELETE CASCADE,
                status TEXT NOT NULL,
                alterado_por INTEGER REFERENCES usuarios(id),
                comentario TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO historico_solicitacoes_aquisicao
                (solicitacao_id, status, criado_em)
            SELECT s.id, s.status, s.criada_em
            FROM solicitacoes_aquisicao AS s
            WHERE NOT EXISTS (
                SELECT 1
                FROM historico_solicitacoes_aquisicao AS h
                WHERE h.solicitacao_id = s.id
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS acompanhamentos_disponibilidade (
                id INTEGER PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                livro_id INTEGER NOT NULL REFERENCES livros(id),
                status TEXT NOT NULL DEFAULT 'Ativo'
                    CHECK (status IN ('Ativo', 'Cancelado', 'Notificado')),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_acompanhamento_ativo_usuario_livro
            ON acompanhamentos_disponibilidade(usuario_id, livro_id)
            WHERE status = 'Ativo'
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notificacoes (
                id INTEGER PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                livro_id INTEGER NOT NULL REFERENCES livros(id),
                emprestimo_id INTEGER REFERENCES emprestimos(id),
                evento_chave TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                lida_em TEXT,
                UNIQUE (usuario_id, evento_chave)
            )
            """
        )


# funçao para inserir livros
def insert_book(titulo, autor, editora, ano_publicacao, isbn, operador_id=None):
    _exigir_perfil(operador_id, "gerente")
    conn = connect()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO livros(titulo, autor, editora, ano_publicacao, isbn)
                VALUES (?, ?, ?, ?, ?)
                """,
                (titulo, autor, editora, ano_publicacao, isbn),
            )
            adicionar_exemplar(
                cursor.lastrowid,
                operador_id,
                conn=conn,
            )
    finally:
        conn.close()

# Funçao para inserir Usuarios

def insert_user(
    nome,
    sobrenome,
    endereco,
    email,
    telefone,
    senha,
    operador_id=None,
):
    _exigir_perfil(operador_id, "gerente")
    senha_hash = gerador_hash.hash(senha)
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO usuarios (nome, sobrenome, endereco, email, telefone, senha_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nome, sobrenome, endereco, email, telefone, senha_hash),
        )
        conn.commit()
    finally:
        conn.close()


# função para exibir os livros

def exibir_livros():
    conn = connect()

    livros = conn.execute('SELECT * FROM livros').fetchall()
    conn.close()

    if not livros:
        print("Nenhum livro cadastrado.")
        return

    print("Livros na biblioteca: ")
    for livro in livros:
        print(f"ID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Autor: {livro[2]}")
        print(f"Editora: {livro[3]}")
        print(f"Ano de Publicação: {livro[4]}")
        print(f"ISBN: {livro[5]}")
        print("\n")

# listar livros

def listar_livros():
    conn = connect()

    try:
        cursor = conn.execute("""
            SELECT id, titulo, autor, editora,
                   ano_publicacao, isbn
            FROM livros
            ORDER BY id DESC
        """)

        colunas = [coluna[0] for coluna in cursor.description]
        livros = cursor.fetchall()

        return [dict(zip(colunas, livro)) for livro in livros]

    finally:
        conn.close()


def listar_livros_com_disponibilidade():
    conn = connect()
    try:
        linhas = conn.execute(
            """
            SELECT l.id, l.titulo, l.autor, l.editora, l.ano_publicacao, l.isbn,
                   COUNT(DISTINCT e.id) AS total_exemplares,
                   COUNT(DISTINCT CASE
                       WHEN e.status = 'Disponível' AND ep.id IS NULL THEN e.id
                   END) AS disponiveis,
                   COUNT(DISTINCT CASE
                       WHEN ep.id IS NOT NULL THEN e.id
                   END) AS emprestados,
                   COUNT(DISTINCT CASE
                       WHEN e.status = 'Indisponível' AND ep.id IS NULL THEN e.id
                   END) AS indisponiveis
            FROM livros AS l
            LEFT JOIN exemplares AS e ON e.livro_id = l.id
            LEFT JOIN emprestimos AS ep
                ON ep.id_exemplar = e.id AND ep.status = 'Ativo'
            GROUP BY l.id
            ORDER BY l.id DESC
            """
        ).fetchall()
    finally:
        conn.close()

    colunas = (
        "id",
        "titulo",
        "autor",
        "editora",
        "ano_publicacao",
        "isbn",
        "total_exemplares",
        "disponiveis",
        "emprestados",
        "indisponiveis",
    )
    livros = []
    for linha in linhas:
        livro = dict(zip(colunas, linha))
        total = livro["total_exemplares"]
        emprestados = livro["emprestados"]
        disponiveis = livro["disponiveis"]
        if disponiveis:
            situacao = "Disponível para empréstimo"
        elif total and emprestados == total:
            situacao = "Todos os exemplares emprestados"
        else:
            situacao = "Indisponível"
        livro["situacao"] = situacao
        livro["disponivel"] = disponiveis > 0
        livros.append(livro)
    return livros


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return " ".join(re.sub(r"[^\w]", " ", texto.casefold()).split())


def _normalizar_isbn(valor):
    return re.sub(r"[^0-9x]", "", str(valor or "").casefold())


def _autores_normalizados(autores):
    if isinstance(autores, str):
        autores = [autores]
    return {_normalizar_texto(autor) for autor in (autores or []) if autor}


def _informacoes_volume(livro_google):
    return livro_google.get("volumeInfo") or {}


def _identificadores_isbn(livro_google):
    resultado = {"ISBN_13": set(), "ISBN_10": set()}
    for identificador in _informacoes_volume(livro_google).get("industryIdentifiers") or []:
        tipo = identificador.get("type")
        valor = _normalizar_isbn(identificador.get("identifier"))
        if tipo in resultado and valor:
            resultado[tipo].add(valor)
    return resultado


def _isbn10_para_isbn13(isbn):
    isbn = _normalizar_isbn(isbn)
    if not re.fullmatch(r"\d{9}[\dx]", isbn):
        return ""
    soma = sum(
        int(digito) * peso
        for digito, peso in zip(isbn[:9], range(10, 1, -1))
    )
    verificador = 11 - soma % 11
    esperado = "0" if verificador == 11 else "X" if verificador == 10 else str(verificador)
    if isbn[-1].upper() != esperado:
        return ""

    base = "978" + isbn[:9]
    soma = sum(
        int(digito) * (1 if indice % 2 == 0 else 3)
        for indice, digito in enumerate(base)
    )
    return base + str((10 - soma % 10) % 10)


def _isbn13_para_isbn10(isbn):
    isbn = _normalizar_isbn(isbn)
    if not re.fullmatch(r"978\d{10}", isbn):
        return ""
    base = isbn[3:12]
    soma = sum(
        int(digito) * peso
        for digito, peso in zip(base, range(10, 1, -1))
    )
    verificador = 11 - soma % 11
    digito_final = "0" if verificador == 11 else "X" if verificador == 10 else str(verificador)
    candidato = base + digito_final
    return candidato if _isbn10_para_isbn13(candidato) == isbn else ""


def _pontuar_correspondencia(livro_acervo, livro_google):
    info = livro_google.get("volumeInfo") or {}
    identificadores = _identificadores_isbn(livro_google)
    isbn_local = _normalizar_isbn(livro_acervo.get("isbn"))

    if isbn_local:
        if len(isbn_local) == 13:
            if isbn_local in identificadores["ISBN_13"]:
                return 0
            isbn10_equivalente = _isbn13_para_isbn10(isbn_local)
            if isbn10_equivalente in identificadores["ISBN_10"]:
                return 1
        elif len(isbn_local) == 10:
            isbn13_equivalente = _isbn10_para_isbn13(isbn_local)
            if isbn13_equivalente in identificadores["ISBN_13"]:
                return 0
            if isbn_local in identificadores["ISBN_10"]:
                return 1

    isbns_google = identificadores["ISBN_13"] | identificadores["ISBN_10"]
    isbn_equivalentes = {isbn_local}
    if len(isbn_local) == 10:
        isbn_equivalentes.add(_isbn10_para_isbn13(isbn_local))
    elif len(isbn_local) == 13:
        isbn_equivalentes.add(_isbn13_para_isbn10(isbn_local))
    if isbn_local and isbns_google and not isbn_equivalentes.intersection(isbns_google):
        return None

    google_id_local = str(livro_acervo.get("google_book_id") or "").strip()
    if google_id_local and google_id_local == str(livro_google.get("id") or "").strip():
        return 2

    titulo_google = _normalizar_texto(info.get("title"))
    autores_google = _autores_normalizados(info.get("authors"))
    titulo_acervo = _normalizar_texto(livro_acervo.get("titulo"))
    autores_acervo = _autores_normalizados(livro_acervo.get("autor"))
    if titulo_google and titulo_google == titulo_acervo:
        if autores_google and autores_acervo:
            return 3 if autores_google.intersection(autores_acervo) else None

        editora_google = _normalizar_texto(info.get("publisher"))
        editora_acervo = _normalizar_texto(livro_acervo.get("editora"))
        if editora_google and editora_google == editora_acervo:
            return 4
    return None


def _desempatar_correspondencias(correspondencias, livro_acervo):
    if len(correspondencias) <= 1:
        return correspondencias[0][1] if correspondencias else None

    editora = _normalizar_texto(livro_acervo.get("editora"))
    if editora:
        por_editora = [
            item
            for item in correspondencias
            if _normalizar_texto(_informacoes_volume(item[1]).get("publisher")) == editora
        ]
        if len(por_editora) == 1:
            return por_editora[0][1]

    ano = str(livro_acervo.get("ano_publicacao") or "")[:4]
    if ano:
        por_ano = [
            item
            for item in correspondencias
            if str(_informacoes_volume(item[1]).get("publishedDate") or "")[:4] == ano
        ]
        if len(por_ano) == 1:
            return por_ano[0][1]

    if correspondencias[0][0] <= 2:
        return correspondencias[0][1]
    return None


def selecionar_correspondencia_google(livro_acervo, resultados_google):
    correspondencias = []
    for livro_google in resultados_google:
        pontuacao = _pontuar_correspondencia(livro_acervo, livro_google)
        if pontuacao is not None:
            correspondencias.append((pontuacao, livro_google))

    if not correspondencias:
        return None

    melhor_pontuacao = min(pontuacao for pontuacao, _ in correspondencias)
    melhores = [
        item for item in correspondencias if item[0] == melhor_pontuacao
    ]
    return _desempatar_correspondencias(melhores, livro_acervo)


def livro_pertence_ao_acervo(livro_google, livros_acervo):
    correspondencias = []
    for livro in livros_acervo:
        pontuacao = _pontuar_correspondencia(livro, livro_google)
        if pontuacao is not None:
            correspondencias.append((pontuacao, livro))

    if not correspondencias:
        return None

    melhor_pontuacao = min(pontuacao for pontuacao, _ in correspondencias)
    melhores = [
        item for item in correspondencias if item[0] == melhor_pontuacao
    ]
    if len(melhores) == 1:
        return melhores[0][1]

    if melhor_pontuacao <= 2:
        return melhores[0][1]

    info_google = _informacoes_volume(livro_google)
    editora_google = _normalizar_texto(info_google.get("publisher"))
    if editora_google:
        por_editora = [
            registro
            for _, registro in melhores
            if _normalizar_texto(registro.get("editora")) == editora_google
        ]
        if len(por_editora) == 1:
            return por_editora[0]

    ano_google = str(info_google.get("publishedDate") or "")[:4]
    if ano_google:
        por_ano = [
            registro
            for _, registro in melhores
            if str(registro.get("ano_publicacao") or "")[:4] == ano_google
        ]
        if len(por_ano) == 1:
            return por_ano[0]
    return None


def mapear_correspondencias_google(livros_acervo, resultados_google):
    correspondencias = {}
    for livro_acervo in livros_acervo:
        volume = selecionar_correspondencia_google(
            livro_acervo,
            resultados_google,
        )
        if volume and volume.get("id"):
            correspondencias.setdefault(volume["id"], livro_acervo)
    return correspondencias


def livro_pode_corresponder_ao_acervo(livro_google, livros_acervo):
    info_google = _informacoes_volume(livro_google)
    titulo_google = _normalizar_texto(info_google.get("title"))
    autores_google = _autores_normalizados(info_google.get("authors"))
    isbns_google = _identificadores_isbn(livro_google)
    isbns_google = isbns_google["ISBN_13"] | isbns_google["ISBN_10"]

    for livro_acervo in livros_acervo:
        if titulo_google != _normalizar_texto(livro_acervo.get("titulo")):
            continue

        isbn_local = _normalizar_isbn(livro_acervo.get("isbn"))
        equivalentes = {isbn_local}
        if len(isbn_local) == 10:
            equivalentes.add(_isbn10_para_isbn13(isbn_local))
        elif len(isbn_local) == 13:
            equivalentes.add(_isbn13_para_isbn10(isbn_local))
        if isbn_local and isbns_google and not equivalentes.intersection(isbns_google):
            continue

        autores_local = _autores_normalizados(livro_acervo.get("autor"))
        if autores_local and autores_google:
            if autores_local.intersection(autores_google):
                return True
            continue

        editora_google = _normalizar_texto(info_google.get("publisher"))
        if (
            editora_google
            and editora_google == _normalizar_texto(livro_acervo.get("editora"))
        ):
            return True
    return False


def combinar_dados_livro(livro_acervo, livro_google=None):
    volume = livro_google or {}
    informacoes = dict(_informacoes_volume(volume))
    dados_locais = {
        "title": livro_acervo.get("titulo"),
        "authors": [livro_acervo["autor"]] if livro_acervo.get("autor") else None,
        "publisher": livro_acervo.get("editora"),
        "publishedDate": livro_acervo.get("ano_publicacao"),
    }

    for campo, valor in dados_locais.items():
        if valor:
            informacoes[campo] = valor

    identificadores = list(informacoes.get("industryIdentifiers") or [])
    isbn_local = _normalizar_isbn(livro_acervo.get("isbn"))
    if isbn_local and isbn_local not in {
        _normalizar_isbn(item.get("identifier")) for item in identificadores
    }:
        tipo = "ISBN_13" if len(isbn_local) == 13 else "ISBN_10"
        identificadores.insert(
            0,
            {"type": tipo, "identifier": str(livro_acervo["isbn"])},
        )
    informacoes["industryIdentifiers"] = identificadores

    return {
        "id": volume.get("id") or livro_acervo.get("google_book_id"),
        "volumeInfo": informacoes,
        "accessInfo": volume.get("accessInfo") or {},
        "saleInfo": volume.get("saleInfo") or {},
        "acervo": livro_acervo,
    }


def _chave_solicitacao(
    google_book_id,
    isbn,
    titulo,
    autor,
    isbn10=None,
    isbn13=None,
):
    isbn_normalizado = _normalizar_isbn(
        isbn13 or _isbn10_para_isbn13(isbn10) or isbn
    )
    if isbn_normalizado:
        identidade = "isbn:" + isbn_normalizado
    elif google_book_id:
        identidade = "google:" + str(google_book_id).strip()
    else:
        identidade = "titulo:" + _normalizar_texto(titulo) + "|autor:" + _normalizar_texto(autor)
    return hashlib.sha256(identidade.encode("utf-8")).hexdigest()


def obter_perfil_usuario(usuario_id):
    if usuario_id is None:
        return None

    conn = connect()
    try:
        usuario = conn.execute(
            "SELECT perfil FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return usuario[0] if usuario else None
    finally:
        conn.close()


def _exigir_perfil(usuario_id, perfil_esperado, conn=None):
    if usuario_id is None:
        raise PermissionError("Autenticação necessária para esta operação.")

    conexao_propria = conn is None
    if conexao_propria:
        conn = connect()
    try:
        perfil = conn.execute(
            "SELECT perfil FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        if perfil is None or perfil[0] != perfil_esperado:
            raise PermissionError("Você não tem permissão para esta operação.")
    finally:
        if conexao_propria:
            conn.close()


def _obter_isbns(info):
    resultado = {"ISBN_10": None, "ISBN_13": None}
    for identificador in info.get("industryIdentifiers") or []:
        tipo = identificador.get("type")
        valor = str(identificador.get("identifier") or "").strip()
        if tipo in resultado and valor:
            resultado[tipo] = valor
    return resultado


def _solicitacao_corresponde_ao_acervo(conn, solicitacao):
    isbn_solicitacao = {
        _normalizar_isbn(solicitacao.get("isbn")),
        _normalizar_isbn(solicitacao.get("isbn10")),
        _normalizar_isbn(solicitacao.get("isbn13")),
    }
    isbn_solicitacao.discard("")
    for isbn in tuple(isbn_solicitacao):
        if len(isbn) == 10:
            isbn_solicitacao.add(_isbn10_para_isbn13(isbn))
        elif len(isbn) == 13:
            isbn_solicitacao.add(_isbn13_para_isbn10(isbn))
    isbn_solicitacao.discard("")

    livros = conn.execute(
        "SELECT titulo, autor, isbn FROM livros"
    ).fetchall()
    for titulo, autor, isbn in livros:
        isbn_local = _normalizar_isbn(isbn)
        if isbn_local and isbn_local in isbn_solicitacao:
            return True
        if (
            not isbn_solicitacao
            and _normalizar_texto(titulo)
            == _normalizar_texto(solicitacao.get("titulo"))
            and _normalizar_texto(autor)
            and _normalizar_texto(autor)
            == _normalizar_texto(solicitacao.get("autor"))
        ):
            return True
    return False


def solicitar_aquisicao(usuario_id, livro_google):
    info = livro_google.get("volumeInfo") or {}
    titulo = str(info.get("title") or "").strip()
    if not titulo:
        raise ValueError("O livro precisa ter título para solicitar aquisição.")

    autores = info.get("authors") or []
    autor = ", ".join(str(nome).strip() for nome in autores if str(nome).strip())
    isbns = _obter_isbns(info)
    isbn10 = isbns["ISBN_10"]
    isbn13 = isbns["ISBN_13"]
    isbn = isbn13 or isbn10
    imagens = info.get("imageLinks") or {}
    capa = (
        imagens.get("thumbnail")
        or imagens.get("smallThumbnail")
        or imagens.get("small")
        or ""
    )
    editora = str(info.get("publisher") or "").strip()
    google_book_id = str(livro_google.get("id") or "").strip()
    chave = _chave_solicitacao(
        google_book_id,
        isbn,
        titulo,
        autor,
        isbn10=isbn10,
        isbn13=isbn13,
    )

    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        solicitacao = {
            "titulo": titulo,
            "autor": autor,
            "isbn": isbn,
            "isbn10": isbn10,
            "isbn13": isbn13,
        }
        if _solicitacao_corresponde_ao_acervo(conn, solicitacao):
            raise ValueError("Este livro já pertence ao acervo da biblioteca.")

        with conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO solicitacoes_aquisicao
                    (usuario_id, google_book_id, titulo, autor, isbn, isbn10,
                     isbn13, editora, capa, chave_solicitacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    usuario_id,
                    google_book_id or None,
                    titulo,
                    autor,
                    isbn or None,
                    isbn10,
                    isbn13,
                    editora or None,
                    capa or None,
                    chave,
                ),
            )
            if cursor.rowcount == 1:
                conn.execute(
                    """
                    INSERT INTO historico_solicitacoes_aquisicao
                        (solicitacao_id, status)
                    VALUES (?, 'Pendente')
                    """,
                    (cursor.lastrowid,),
                )
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_solicitacoes_aquisicao(operador_id=None, status=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        clausula_status = "WHERE s.status = ?" if status else ""
        parametros = (status,) if status else ()
        cursor = conn.execute(
            f"""
            SELECT s.id, u.nome, u.sobrenome, u.email,
                   s.titulo, s.autor, s.isbn,
                   s.isbn10, s.isbn13, s.editora, s.capa, s.google_book_id,
                   s.usuario_id, s.status, s.criada_em
            FROM solicitacoes_aquisicao AS s
            JOIN usuarios AS u ON u.id = s.usuario_id
            {clausula_status}
            ORDER BY s.criada_em DESC, s.id DESC
            """,
            parametros,
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def listar_solicitacoes_usuario(usuario_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        cursor = conn.execute(
            """
            SELECT id, titulo, autor, isbn, isbn10, isbn13, editora, capa,
                   status, criada_em
            FROM solicitacoes_aquisicao
            WHERE usuario_id = ?
            ORDER BY criada_em DESC, id DESC
            """,
            (usuario_id,),
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def listar_historico_solicitacao(solicitacao_id, operador_id=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        cursor = conn.execute(
            """
            SELECT h.status, h.comentario, h.criado_em,
                   u.nome, u.sobrenome
            FROM historico_solicitacoes_aquisicao AS h
            LEFT JOIN usuarios AS u ON u.id = h.alterado_por
            WHERE h.solicitacao_id = ?
            ORDER BY h.id
            """,
            (solicitacao_id,),
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def atualizar_status_solicitacao(
    solicitacao_id,
    status,
    operador_id=None,
    comentario=None,
):
    status_permitidos = {
        "Pendente",
        "Em análise",
        "Aprovada",
        "Recusada",
        "Adquirida",
    }
    if status not in status_permitidos:
        raise ValueError("Situação de aquisição inválida.")

    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        solicitacao = conn.execute(
            """
            SELECT id, usuario_id, google_book_id, titulo, autor, isbn,
                   isbn10, isbn13, editora, capa, chave_solicitacao, status
            FROM solicitacoes_aquisicao
            WHERE id = ?
            """,
            (solicitacao_id,),
        ).fetchone()
        if solicitacao is None:
            raise ValueError("Solicitação não encontrada.")

        colunas = (
            "id",
            "usuario_id",
            "google_book_id",
            "titulo",
            "autor",
            "isbn",
            "isbn10",
            "isbn13",
            "editora",
            "capa",
            "chave_solicitacao",
            "status",
        )
        dados_solicitacao = dict(zip(colunas, solicitacao))
        if (
            status == "Adquirida"
            and not _solicitacao_corresponde_ao_acervo(conn, dados_solicitacao)
        ):
            raise ValueError(
                "Cadastre o livro no acervo antes de marcá-lo como adquirido."
            )

        if dados_solicitacao["status"] == status:
            return False

        with conn:
            conn.execute(
                "UPDATE solicitacoes_aquisicao SET status = ? WHERE id = ?",
                (status, solicitacao_id),
            )
            conn.execute(
                """
                INSERT INTO historico_solicitacoes_aquisicao
                    (solicitacao_id, status, alterado_por, comentario)
                VALUES (?, ?, ?, ?)
                """,
                (solicitacao_id, status, operador_id, comentario),
            )
        return True
    except sqlite3.IntegrityError as erro:
        raise ValueError(
            "Já existe uma solicitação ativa deste livro para esse usuário."
        ) from erro
    finally:
        conn.close()


# Criar tabela para a lista de desejos

def criar_tabela_desejos():
    conn = connect()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS lista_desejos (
            usuario_id INTEGER,
            livro_id INTEGER,
            PRIMARY KEY (usuario_id, livro_id)
        )
    """)

    conn.commit()
    conn.close()


# Adicionar livro à lista de desejos
def adicionar_desejo(usuario_id, livro_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        conn.execute(
            """
            INSERT OR IGNORE INTO lista_desejos
            (usuario_id, livro_id)
            VALUES (?, ?)
            """,
            (usuario_id, livro_id),
        )
        conn.commit()
    finally:
        conn.close()


# Mostrar os livros desejados pelo usuário
def listar_desejos(usuario_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        return conn.execute(
            """
            SELECT livros.id, livros.titulo
            FROM lista_desejos
            JOIN livros ON lista_desejos.livro_id = livros.id
            WHERE lista_desejos.usuario_id = ?
            """,
            (usuario_id,),
        ).fetchall()
    finally:
        conn.close()


# Remover livro da lista de desejos
def remover_desejo(usuario_id, livro_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        conn.execute(
            """
            DELETE FROM lista_desejos
            WHERE usuario_id = ? AND livro_id = ?
            """,
            (usuario_id, livro_id),
        )
        conn.commit()
    finally:
        conn.close()



# Função para editar livros

def editar_livro(
    id_livro,
    titulo,
    autor,
    editora,
    ano,
    isbn,
    operador_id=None,
):
    conn = connect()

    try:
        _exigir_perfil(operador_id, "gerente", conn)
        conn.execute(
            """
            UPDATE livros
            SET titulo = ?,
                autor = ?,
                editora = ?,
                ano_publicacao = ?,
                isbn = ?
            WHERE id = ?
            """,
            (titulo, autor, editora, ano, isbn, id_livro),
        )

        conn.commit()
    finally:
        conn.close()


def excluir_livro(id_livro, operador_id=None):
    conn = connect()

    try:
        _exigir_perfil(operador_id, "gerente", conn)
        if conn.execute(
            "SELECT 1 FROM emprestimos WHERE id_livro = ? LIMIT 1",
            (id_livro,),
        ).fetchone():
            raise ValueError(
                "O livro possui histórico de empréstimos e não pode ser excluído."
            )
        if conn.execute(
            """
            SELECT 1
            FROM acompanhamentos_disponibilidade
            WHERE livro_id = ?
            UNION ALL
            SELECT 1 FROM notificacoes WHERE livro_id = ?
            LIMIT 1
            """,
            (id_livro, id_livro),
        ).fetchone():
            raise ValueError(
                "O livro possui acompanhamento ou notificação e não pode ser excluído."
            )
        with conn:
            conn.execute("DELETE FROM exemplares WHERE livro_id = ?", (id_livro,))
            conn.execute(
                "DELETE FROM lista_desejos WHERE livro_id = ?",
                (id_livro,),
            )
            conn.execute(
                "DELETE FROM livros WHERE id = ?",
                (id_livro,),
            )
    finally:
        conn.close()


def _disponibilidade_no_banco(conn, livro_id):
    linha = conn.execute(
        """
        SELECT COUNT(e.id),
               SUM(CASE
                   WHEN e.status = 'Disponível' AND ep.id IS NULL THEN 1
                   ELSE 0
               END),
               SUM(CASE WHEN ep.id IS NOT NULL THEN 1 ELSE 0 END),
               SUM(CASE
                   WHEN e.status = 'Indisponível' AND ep.id IS NULL THEN 1
                   ELSE 0
               END)
        FROM exemplares AS e
        LEFT JOIN emprestimos AS ep
            ON ep.id_exemplar = e.id AND ep.status = 'Ativo'
        WHERE e.livro_id = ?
        """,
        (livro_id,),
    ).fetchone()
    return {
        "total": linha[0] or 0,
        "disponiveis": linha[1] or 0,
        "emprestados": linha[2] or 0,
        "indisponiveis": linha[3] or 0,
    }


def _notificar_se_disponivel(conn, livro_id, disponiveis_antes, evento):
    disponibilidade = _disponibilidade_no_banco(conn, livro_id)
    if disponiveis_antes > 0 or disponibilidade["disponiveis"] <= 0:
        return 0

    livro = conn.execute(
        "SELECT titulo FROM livros WHERE id = ?",
        (livro_id,),
    ).fetchone()
    if livro is None:
        return 0

    acompanhamentos = conn.execute(
        """
        SELECT id, usuario_id
        FROM acompanhamentos_disponibilidade
        WHERE livro_id = ? AND status = 'Ativo'
        """,
        (livro_id,),
    ).fetchall()
    mensagem = (
        f"Boa notícia! O livro {livro[0]} voltou a ficar disponível na biblioteca. "
        "Você já pode comparecer para consultar a possibilidade de empréstimo."
    )
    for acompanhamento_id, usuario_id in acompanhamentos:
        conn.execute(
            """
            INSERT OR IGNORE INTO notificacoes
                (usuario_id, livro_id, emprestimo_id, evento_chave, mensagem)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                usuario_id,
                livro_id,
                evento[1] if evento[0] == "emprestimo" else None,
                f"{evento[0]}:{evento[1]}:{usuario_id}",
                mensagem,
            ),
        )
        conn.execute(
            """
            UPDATE acompanhamentos_disponibilidade
            SET status = 'Notificado',
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'Ativo'
            """,
            (acompanhamento_id,),
        )
    return len(acompanhamentos)


def adicionar_exemplar(livro_id, operador_id=None, conn=None):
    conexao_propria = conn is None
    if conexao_propria:
        conn = connect()

    try:
        _exigir_perfil(operador_id, "gerente", conn)
        if conexao_propria:
            conn.execute("BEGIN IMMEDIATE")
        livro = conn.execute(
            "SELECT id FROM livros WHERE id = ?",
            (livro_id,),
        ).fetchone()
        if livro is None:
            raise ValueError("Livro não encontrado.")

        antes = _disponibilidade_no_banco(conn, livro_id)["disponiveis"]
        proximo_numero = conn.execute(
            """
            SELECT COUNT(*) + 1
            FROM exemplares
            WHERE livro_id = ?
            """,
            (livro_id,),
        ).fetchone()[0]
        codigo = f"L{livro_id}-{proximo_numero:03d}"
        while conn.execute(
            "SELECT 1 FROM exemplares WHERE codigo = ?",
            (codigo,),
        ).fetchone():
            proximo_numero += 1
            codigo = f"L{livro_id}-{proximo_numero:03d}"

        if conexao_propria:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO exemplares (livro_id, codigo)
                    VALUES (?, ?)
                    """,
                    (livro_id, codigo),
                )
                _notificar_se_disponivel(
                    conn,
                    livro_id,
                    antes,
                    ("exemplar", cursor.lastrowid),
                )
        else:
            cursor = conn.execute(
                """
                INSERT INTO exemplares (livro_id, codigo)
                VALUES (?, ?)
                """,
                (livro_id, codigo),
            )
            _notificar_se_disponivel(
                conn,
                livro_id,
                antes,
                ("exemplar", cursor.lastrowid),
            )
        return cursor.lastrowid
    finally:
        if conexao_propria:
            conn.close()


def listar_exemplares(livro_id, operador_id=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        cursor = conn.execute(
            """
            SELECT e.id, e.codigo, e.status,
                   CASE WHEN ep.id IS NULL THEN 0 ELSE 1 END AS emprestado
            FROM exemplares AS e
            LEFT JOIN emprestimos AS ep
                ON ep.id_exemplar = e.id AND ep.status = 'Ativo'
            WHERE e.livro_id = ?
            ORDER BY e.id
            """,
            (livro_id,),
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def listar_exemplares_disponiveis(livro_id):
    conn = connect()
    try:
        return conn.execute(
            """
            SELECT e.id, e.codigo
            FROM exemplares AS e
            WHERE e.livro_id = ?
              AND e.status = 'Disponível'
              AND NOT EXISTS (
                  SELECT 1
                  FROM emprestimos AS ep
                  WHERE ep.id_exemplar = e.id AND ep.status = 'Ativo'
              )
            ORDER BY e.id
            """,
            (livro_id,),
        ).fetchall()
    finally:
        conn.close()


def definir_status_exemplar(exemplar_id, status, operador_id=None):
    if status not in {"Disponível", "Indisponível"}:
        raise ValueError("Situação do exemplar inválida.")

    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        conn.execute("BEGIN IMMEDIATE")
        exemplar = conn.execute(
            """
            SELECT livro_id, status
            FROM exemplares
            WHERE id = ?
            """,
            (exemplar_id,),
        ).fetchone()
        if exemplar is None:
            raise ValueError("Exemplar não encontrado.")
        emprestado = conn.execute(
            """
            SELECT 1
            FROM emprestimos
            WHERE id_exemplar = ? AND status = 'Ativo'
            """,
            (exemplar_id,),
        ).fetchone()
        if emprestado:
            raise ValueError("Não é possível alterar um exemplar emprestado.")

        antes = _disponibilidade_no_banco(conn, exemplar[0])["disponiveis"]
        with conn:
            conn.execute(
                "UPDATE exemplares SET status = ? WHERE id = ?",
                (status, exemplar_id),
            )
            if status == "Disponível":
                _notificar_se_disponivel(
                    conn,
                    exemplar[0],
                    antes,
                    ("exemplar", exemplar_id),
                )
        return True
    finally:
        conn.close()


def cadastrar_emprestimo(
    id_usuario,
    id_livro,
    data_emprestimo,
    data_devolucao,
    operador_id=None,
    exemplar_id=None,
):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT id FROM usuarios WHERE id = ? AND perfil = 'usuario'",
            (id_usuario,),
        ).fetchone() is None:
            raise ValueError("Usuário comum não encontrado.")
        if conn.execute(
            "SELECT id FROM livros WHERE id = ?",
            (id_livro,),
        ).fetchone() is None:
            raise ValueError("Livro não encontrado.")

        exemplares_disponiveis = conn.execute(
            """
            SELECT e.id
            FROM exemplares AS e
            WHERE e.livro_id = ?
              AND e.status = 'Disponível'
              AND NOT EXISTS (
                  SELECT 1
                  FROM emprestimos AS ep
                  WHERE ep.id_exemplar = e.id AND ep.status = 'Ativo'
              )
            ORDER BY e.id
            """,
            (id_livro,),
        ).fetchall()
        ids_disponiveis = {linha[0] for linha in exemplares_disponiveis}
        if exemplar_id is None:
            exemplar_id = (
                exemplares_disponiveis[0][0]
                if exemplares_disponiveis
                else None
            )
        if exemplar_id not in ids_disponiveis:
            raise ValueError("Não há exemplar disponível para empréstimo.")

        with conn:
            conn.execute(
                """
                INSERT INTO emprestimos
                    (id_livro, id_usuario, id_exemplar, data_emprestimo,
                     data_devolucao, status)
                VALUES (?, ?, ?, ?, ?, 'Ativo')
                """,
                (
                    id_livro,
                    id_usuario,
                    exemplar_id,
                    data_emprestimo,
                    data_devolucao,
                ),
            )
    finally:
        conn.close()


def registrar_devolucao(emprestimo_id, operador_id=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        conn.execute("BEGIN IMMEDIATE")
        emprestimo = conn.execute(
            """
            SELECT id_livro, status
            FROM emprestimos
            WHERE id = ?
            """,
            (emprestimo_id,),
        ).fetchone()
        if emprestimo is None:
            raise ValueError("Empréstimo não encontrado.")
        if emprestimo[1] != "Ativo":
            raise ValueError("Este empréstimo já foi devolvido.")

        antes = _disponibilidade_no_banco(conn, emprestimo[0])["disponiveis"]
        data_devolucao_real = date.today().strftime("%d/%m/%Y")
        with conn:
            conn.execute(
                """
                UPDATE emprestimos
                SET status = 'Devolvido', devolvido_em = ?
                WHERE id = ? AND status = 'Ativo'
                """,
                (data_devolucao_real, emprestimo_id),
            )
            _notificar_se_disponivel(
                conn,
                emprestimo[0],
                antes,
                ("emprestimo", emprestimo_id),
            )
        return True
    finally:
        conn.close()


def listar_emprestimos_administrativos(operador_id=None, status=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        clausula_status = "WHERE ep.status = ?" if status else ""
        parametros = (status,) if status else ()
        cursor = conn.execute(
            f"""
            SELECT ep.id, ep.id_livro, l.titulo,
                   ep.id_exemplar, e.codigo AS exemplar,
                   ep.id_usuario, u.nome, u.sobrenome, u.email,
                   ep.data_emprestimo, ep.data_devolucao,
                   ep.devolvido_em, ep.status
            FROM emprestimos AS ep
            JOIN livros AS l ON l.id = ep.id_livro
            JOIN usuarios AS u ON u.id = ep.id_usuario
            LEFT JOIN exemplares AS e ON e.id = ep.id_exemplar
            {clausula_status}
            ORDER BY ep.id DESC
            """,
            parametros,
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def listar_emprestimos_usuario(usuario_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        emprestimos = conn.execute(
            """
            SELECT livros.titulo, emprestimos.data_emprestimo,
                   emprestimos.data_devolucao
            FROM emprestimos
            JOIN livros ON livros.id = emprestimos.id_livro
            WHERE emprestimos.id_usuario = ?
              AND emprestimos.status = 'Ativo'
            ORDER BY emprestimos.id DESC
            """,
            (usuario_id,),
        ).fetchall()
        return [
            {
                "Produto": livro[0],
                "Retirada": livro[1],
                "Devolver até": livro[2],
            }
            for livro in emprestimos
        ]
    finally:
        conn.close()


def listar_usuarios(operador_id=None):
    conn = connect()
    try:
        _exigir_perfil(operador_id, "gerente", conn)
        return conn.execute(
            """
            SELECT id, nome, sobrenome, email
            FROM usuarios
            WHERE perfil = 'usuario'
            ORDER BY nome, sobrenome
            """
        ).fetchall()
    finally:
        conn.close()


def exibir_usuarios(operador_id=None):
    return listar_usuarios(operador_id)


def acompanhar_disponibilidade(usuario_id, livro_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        conn.execute("BEGIN IMMEDIATE")
        disponibilidade = _disponibilidade_no_banco(conn, livro_id)
        if not disponibilidade["total"]:
            raise ValueError("Este livro não possui exemplares no acervo.")
        if disponibilidade["disponiveis"] > 0:
            raise ValueError("O livro já está disponível para empréstimo.")
        if disponibilidade["emprestados"] != disponibilidade["total"]:
            raise ValueError(
                "O aviso só pode ser ativado quando todos os exemplares estão emprestados."
            )
        with conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO acompanhamentos_disponibilidade
                    (usuario_id, livro_id)
                VALUES (?, ?)
                """,
                (usuario_id, livro_id),
            )
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_acompanhamentos_usuario(usuario_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        cursor = conn.execute(
            """
            SELECT a.id, a.livro_id, l.titulo, a.status, a.criado_em,
                   COALESCE(d.disponiveis, 0) AS disponiveis
            FROM acompanhamentos_disponibilidade AS a
            JOIN livros AS l ON l.id = a.livro_id
            LEFT JOIN (
                SELECT e.livro_id,
                       SUM(CASE
                           WHEN e.status = 'Disponível' AND ep.id IS NULL THEN 1
                           ELSE 0
                       END) AS disponiveis
                FROM exemplares AS e
                LEFT JOIN emprestimos AS ep
                    ON ep.id_exemplar = e.id AND ep.status = 'Ativo'
                GROUP BY e.livro_id
            ) AS d ON d.livro_id = l.id
            WHERE a.usuario_id = ?
            ORDER BY a.id DESC
            """,
            (usuario_id,),
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def cancelar_acompanhamento(usuario_id, acompanhamento_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        with conn:
            cursor = conn.execute(
                """
                UPDATE acompanhamentos_disponibilidade
                SET status = 'Cancelado',
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ? AND usuario_id = ? AND status = 'Ativo'
                """,
                (acompanhamento_id, usuario_id),
            )
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_notificacoes_usuario(usuario_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        cursor = conn.execute(
            """
            SELECT id, livro_id, mensagem, criada_em, lida_em
            FROM notificacoes
            WHERE usuario_id = ?
            ORDER BY id DESC
            """,
            (usuario_id,),
        )
        colunas = [coluna[0] for coluna in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def marcar_notificacao_lida(usuario_id, notificacao_id):
    conn = connect()
    try:
        _exigir_perfil(usuario_id, "usuario", conn)
        with conn:
            cursor = conn.execute(
                """
                UPDATE notificacoes
                SET lida_em = CURRENT_TIMESTAMP
                WHERE id = ? AND usuario_id = ? AND lida_em IS NULL
                """,
                (notificacao_id, usuario_id),
            )
        if cursor.rowcount == 0:
            existe = conn.execute(
                "SELECT 1 FROM notificacoes WHERE id = ? AND usuario_id = ?",
                (notificacao_id, usuario_id),
            ).fetchone()
            if existe is None:
                raise PermissionError("Notificação não pertence à sua conta.")
        return cursor.rowcount == 1
    finally:
        conn.close()


def listar_notificacoes_nao_lidas(usuario_id):
    return [
        notificacao
        for notificacao in listar_notificacoes_usuario(usuario_id)
        if notificacao["lida_em"] is None
    ]


def autenticar_usuario(email, senha):
    conn = connect()

    usuarios = conn.execute(
        """
        SELECT id, nome, senha_hash, perfil
        FROM usuarios
        WHERE email = ? COLLATE NOCASE
        """,
        (email.strip(),)
    ).fetchall()

    conn.close()

    if len(usuarios) != 1:
        return None

    usuario = usuarios [0]
    senha_hash = usuario[2]

    if not senha_hash:
        return None
    
    try:
        gerador_hash.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return None

    return {
        "id": usuario[0],
        "nome": usuario[1],
        "perfil": usuario[3]
    }









# Teste para adicionar

#insert_book("O Senhor dos Anéis", "J.R.R. Tolkien", "HarperCollins", 1954, "978-0261102385")
#insert_user("João", "Silva", "Rua A, 123", "joao.silva@email.com", "123456789")

if __name__=="__main__":
    exibir_livros()



# Buscar o livro mais emprestado
def livro_mais_emprestado():
    conn = connect()

    cursor = conn.execute("""
        SELECT livros.titulo, COUNT(*) AS total
        FROM emprestimos
        JOIN livros ON emprestimos.id_livro = livros.id
        GROUP BY livros.id, livros.titulo
        ORDER BY total DESC
        LIMIT 1
    """)

    resultado = cursor.fetchone()
    conn.close()

    return resultado


# Buscar quantidade de empréstimos por livro
def grafico_emprestimos():
    conn = connect()

    livros = conn.execute("""
        SELECT livros.titulo, COUNT(*) AS total
        FROM emprestimos
        JOIN livros ON emprestimos.id_livro = livros.id
        GROUP BY livros.id, livros.titulo
        ORDER BY total DESC
    """).fetchall()

    conn.close()

    return [
        {"Livro": livro[0], "Total": livro[1]}
        for livro in livros
    ]
