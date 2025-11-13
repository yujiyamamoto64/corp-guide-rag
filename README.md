# Corp Guide RAG

Sistema base para rastrear portais internos, extrair conteúdo hierárquico e alimentar um pipeline RAG corporativo com PostgreSQL + pgvector.  
A estrutura foi criada para continuar o desenvolvimento citado no resumo técnico do chat.

## Componentes

- `crawler/`: download de páginas, limpeza e estruturação da hierarquia (menu, headings ou caminho da URL).
- `ingestion/`: chunking inteligente, geração de embeddings e atualização de documentos com detecção por hash.
- `db/`: conexão, modelos SQLAlchemy e queries auxiliares para PostgreSQL com pgvector.
- `api/`: endpoints FastAPI `/ingest-url`, `/rebuild-domain` e `/ask`.
- `main.py`: ponto de entrada FastAPI.

## Configuração rápida

1. Crie um virtualenv para cada máquina/ambiente e instale dependências:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate # Linux/Mac
   pip install -r requirements.txt
   ```
   > Ao abrir o projeto em outra máquina é necessário repetir esse passo, pois os pacotes instalados localmente não são compartilhados entre ambientes.
2. Configure variáveis de ambiente:
   - `DATABASE_URL`: string SQLAlchemy, ex.: `postgresql+psycopg://user:pass@host/db`.
   - `OPENAI_API_KEY`: chave para gerar embeddings com `text-embedding-3-small`.
3. Execute migrações iniciais criando tabelas (provisoriamente manual):
   ```bash
   python -m db.models
   ```
4. Rode o servidor:
   ```bash
   uvicorn main:app --reload
   ```

## Próximos passos sugeridos

- Implementar Playwright no crawler para páginas que renderizam via JS.
- Integrar fila/worker para ingestões grandes.
- Criar camada de migrações (Alembic) e testes automatizados.
