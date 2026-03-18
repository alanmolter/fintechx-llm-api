from fastapi import FastAPI
from app.routers import query
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API baseada em LLM para traduzir linguagem natural em consultas SQL otimizadas para a FinTechX.",
    version="1.0.0"
)

app.include_router(query.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API está rodando."}
