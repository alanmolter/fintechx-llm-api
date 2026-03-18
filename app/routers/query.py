from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_sql_from_text
from app.db.repository import execute_read_query
from app.core.security import validate_sql_guardrails
from app.services.cache_service import get_cached_sql, set_cached_sql
import time

router = APIRouter(prefix="/api/v1", tags=["Query"])

EXAMPLE_QUESTIONS = [
    "Quais são os produtos mais populares entre os clientes corporativos?",
    "Quais são os produtos mais vendidos em termos de quantidade?",
    "Qual é o volume de vendas por cidade?",
    "Quais são os clientes que mais compraram?",
    "Quais são os produtos mais caros da loja?",
    "Quais são os fornecedores mais frequentes nos pedidos?",
    "Quais os melhores vendedores?",
    "Qual é o valor total de todas as vendas realizadas por ano?",
    "Qual é o valor total de vendas por categoria de produto?",
    "Qual o ticket médio por compra?",
]


@router.get("/examples", tags=["Query"])
def list_example_questions():
    """
    Retorna a lista das 10 perguntas de exemplo que a API é capaz de responder.
    Utilize qualquer uma delas no endpoint POST /api/v1/query.
    """
    return {"total": len(EXAMPLE_QUESTIONS), "questions": EXAMPLE_QUESTIONS}


@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    start_time = time.time()

    try:
        # 1. Cache: verifica se a pergunta já foi processada
        cached_result = get_cached_sql(request.question)

        if cached_result:
            generated_sql = cached_result["sql_query"]
            explanation = cached_result["explanation"]
        else:
            # 2. RAG + LLM: gera SQL via Function Calling com contexto de negócios
            llm_result = await generate_sql_from_text(request.question)
            generated_sql = llm_result["sql_query"]
            explanation = llm_result["explanation"]

            # 3. Guardrails: valida segurança da query gerada
            if not validate_sql_guardrails(generated_sql):
                raise HTTPException(
                    status_code=400,
                    detail="A query gerada violou as políticas de segurança."
                )

            # 4. Cache: salva para próximas consultas idênticas
            set_cached_sql(request.question, generated_sql, explanation)

        # 5. Execução: roda a query no banco (sempre executa para dados frescos)
        result_data = execute_read_query(generated_sql)

        process_time = round(time.time() - start_time, 2)

        return QueryResponse(
            question=request.question,
            sql_query=generated_sql,
            data=result_data,
            explanation=f"{explanation} (Tempo de resposta: {process_time}s)"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
