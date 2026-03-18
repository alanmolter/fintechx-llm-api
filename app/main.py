"""
main.py - Ponto de entrada da aplicação FastAPI.

Este é o arquivo principal que inicializa a API, registra as rotas
e define endpoints básicos como health check e redirecionamento da raiz.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.routers import query
from app.core.config import settings

# =============================================================================
# Inicialização da aplicação FastAPI
# =============================================================================
# O título e a descrição aparecem automaticamente na documentação Swagger (/docs).
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API baseada em LLM para traduzir perguntas em linguagem natural "
        "em consultas SQL otimizadas para o banco Northwind da FinTechX. "
        "Utiliza GPT-4-turbo com Function Calling, RAG (ChromaDB), "
        "Cache Inteligente e Guardrails de Segurança."
    ),
    version="1.0.0"
)

# Registra o roteador principal que contém os endpoints /api/v1/query e /api/v1/examples
app.include_router(query.router)


# =============================================================================
# Endpoints utilitários
# =============================================================================

@app.get("/", include_in_schema=False)
def root():
    """Redireciona a raiz (/) para a documentação interativa Swagger (/docs)."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de verificação de saúde da API. Útil para monitoramento e load balancers."""
    return {"status": "ok", "message": "API está rodando."}
