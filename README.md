# PjBl
Esse repositório foi criado para o trabalho da matéria Raciocínio algoritmo

## Busca de livros

Instale as dependências e inicie o sistema pela tela de login a partir da pasta
principal do projeto:

```powershell
python -m pip install -r dependencias.txt
python -m streamlit run .\Tela_do_Programa\troca_de_paineis.py
```

A página inicial da biblioteca exibe os livros cadastrados no acervo. As
pesquisas consultam o catálogo do Google Books e distinguem os títulos externos.
A página de detalhes combina os dados do acervo com os metadados do Google Books;
ela não redireciona para outros sites. O visualizador oficial de leitura não é
usado, pois as prévias dependem de permissões e disponibilidade regional.
A busca usa a API do Google Books e precisa de uma chave, que não é instalada
junto com os pacotes. Em cada computador, copie
`.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha:

```toml
GOOGLE_BOOKS_API_KEY = "sua-chave"
```

Obtenha a chave no Google Cloud Console ou transfira-a de forma segura do outro
computador. Não compartilhe nem envie o arquivo `secrets.toml`: ele é ignorado
pelo Git. Como alternativa, configure a variável de ambiente
`GOOGLE_BOOKS_API_KEY`.

Execute os testes dos fluxos da biblioteca com:

```powershell
python -m unittest discover -s tests -v
```

## Aquisições, exemplares e empréstimos

Usuários podem sugerir a aquisição de livros externos e acompanhar essas
sugestões em “Minha biblioteca”. A aprovação não cadastra o livro
automaticamente: a gerência deve incluí-lo no acervo antes de marcá-lo como
adquirido. Os empréstimos continuam presenciais; a gerência registra o
exemplar e a devolução no painel, e a disponibilidade pública é calculada a
partir desses exemplares e empréstimos.

Na primeira abertura após esta atualização, a migração cria no mínimo um
exemplar para cada livro já cadastrado e cópias suficientes para vincular
eventuais empréstimos ativos. Empréstimos antigos são preservados como ativos
até a gerência confirmar suas devoluções. Ajuste a quantidade real de
exemplares no painel administrativo. Usuários podem acompanhar livros sem
exemplares disponíveis e receber notificações internas após devoluções.
Notificações por e-mail não estão habilitadas, pois o projeto não possui
serviço SMTP configurado.
