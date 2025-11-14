# Corp Guide RAG

Sistema base para rastrear portais internos, extrair conteúdo hierárquico e alimentar um pipeline RAG corporativo com PostgreSQL + pgvector.  

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
   ```powershell
   .\scripts\start_api.ps1        # Abre um terminal com o uvicorn (porta padrão 8011)
   ```
5. Faça perguntas pela CLI:
   ```bash
   python scripts/ask.py "como faço a migração do argo cd?"
   # use --url para mudar host/porta
   ```
6. Reprocessar todo o domínio quando precisar (crawler + embeddings):
   ```bash
   python scripts/rebuild_domain.py [URL_BASE_GUIDE]
   ```

## Próximos passos sugeridos

- Implementar Playwright no crawler para páginas que renderizam via JS.
- Integrar fila/worker para ingestões grandes.
- Criar camada de migrações (Alembic) e testes automatizados.
