# PjBl
Esse repositório foi criado para o trabalho da matéria Raciocínio algoritmo

## Busca de livros

Instale as dependências e inicie a busca a partir da pasta principal do projeto:

```powershell
python -m pip install -r dependencias.txt
python -m streamlit run .\Tela_do_Programa\busca_de_Livros.py
```

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
