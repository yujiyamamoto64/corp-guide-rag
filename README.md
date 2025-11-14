# Corp Guide RAG

Base para rastrear portais e guias internos, extrair conteúdo hierárquico e alimentar um pipeline RAG com PostgreSQL + pgvector e OpenAI.

## Visão geral do repositório

| pasta | função |
|-------|--------|
| `crawler/` | download de páginas, limpeza do HTML, normalização de URLs e reconstrução de hierarquias. |
| `ingestion/` | chunking, embeddings, persistência de documentos e lógica de detecção de mudanças. |
| `db/` | conexão SQLAlchemy + pgvector e modelos/tarefas relacionadas ao banco PostgreSQL. |
| `api/` | endpoints FastAPI (`/ingest-url`, `/rebuild-domain`, `/ask`, `/health`). |
| `scripts/` | utilitários para subir o servidor, refazer domínios e perguntar ao RAG. |

## Configuração rápida

1. **Virtualenv** em cada máquina:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
2. **Variáveis de ambiente** (coloque no `.env`):
   - `DATABASE_URL`: `postgresql+psycopg://user:pass@localhost:5432/corp_guide`
   - `OPENAI_API_KEY`: chave para embeddings e respostas
   - (opcional) `ASK_MODEL`: modelo usado no `/ask` (`gpt-4o-mini` por padrão)
3. **Criar tabelas**:
   ```bash
   python -m db.models
   ```
4. **Subir API**:
   ```powershell
   .\scripts\start_api.ps1    # abre um terminal com uvicorn em 127.0.0.1:8011
   ```
5. **Fazer perguntas**:
   ```powershell
   python scripts/ask.py "como faço a migração para o argo cd?"
   ```
6. **Rebuild completo** (crawler + embeddings):
   ```powershell
   python scripts/rebuild_domain.py [URL]
   ```

## Banco de dados (PostgreSQL + pgvector)

### Tabela `documents`
- `id`: chave primária
- `domain`: domínio do documento
- `url`: única por documento
- `title`: título limpo
- `content`: texto sem HTML
- `content_hash`: `sha256(content)` para detecção de mudanças
- `last_update`: timestamp automático

### Tabela `chunks`
- `id`: chave primária
- `document_id`: FK para `documents` (CASCADE delete)
- `chunk_index`: ordem do chunk
- `chunk_text`: markdown limpo
- `embedding`: `Vector(1536)` (OpenAI `text-embedding-3-small`)
- `metadata`: JSON (título, breadcrumbs, URL, domínio, etc.)

Recrie o schema a qualquer momento com `python -m db.models`.

## Endpoints FastAPI

| Método/Rota | Descrição |
|-------------|-----------|
| `GET /health` | status básico do servidor |
| `POST /ingest-url` | `{ "url": "..." }` – baixa a página, compara hash e salva chunks/embeddings |
| `POST /rebuild-domain` | `{ "base_url": "..." }` – remove documentos do domínio e refaz todo o crawl/ingestão (execução bem demorada)|
| `POST /ask` | `{ "question": "...", "top_k": 6 }` – consulta pgvector e pede ao LLM para responder com base nos chunks |

### Exemplos

```bash
# Ingestão incremental
curl -X POST http://127.0.0.1:8011/ingest-url \
     -H "Content-Type: application/json" \
     -d '{"url":"[URL]"}'

# Rebuild completo
curl -X POST http://127.0.0.1:8011/rebuild-domain \
     -H "Content-Type: application/json" \
     -d '{"base_url":"[URL]"}'

# Pergunta usando o helper
python scripts/ask.py "como faço a migração do argo cd?"
```

