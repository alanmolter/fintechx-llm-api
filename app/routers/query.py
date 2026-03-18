from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_sql_from_text
from app.services.predefined_queries import find_predefined_query, get_all_example_questions
from app.db.repository import execute_read_query
from app.core.security import validate_sql_guardrails
from app.services.cache_service import get_cached_sql, set_cached_sql
import time

router = APIRouter(prefix="/api/v1", tags=["Query"])


@router.get("/examples", tags=["Query"])
def list_example_questions():
    """
    Retorna a lista das 10 perguntas de exemplo que a API é capaz de responder.
    Utilize qualquer uma delas no endpoint POST /api/v1/query.
    """
    return {
        "total": 10,
        "questions": get_all_example_questions()
    }


@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    start_time = time.time()

    try:
        generated_sql = None
        explanation = None

        cached_result = get_cached_sql(request.question)

        if cached_result:
            generated_sql = cached_result["sql_query"]
            explanation = cached_result["explanation"]
        else:
            predefined = find_predefined_query(request.question)

            if predefined:
                generated_sql = predefined["sql_query"]
                explanation = predefined["explanation"]
            else:
                try:
                    llm_result = await generate_sql_from_text(request.question)
                    generated_sql = llm_result["sql_query"]
                    explanation = llm_result["explanation"]
                except Exception as llm_error:
                    raise HTTPException(
                        status_code=503,
                        detail=f"LLM indisponível e não há query predefinida para esta pergunta. Erro: {str(llm_error)}"
                    )

            if not validate_sql_guardrails(generated_sql):
                raise HTTPException(
                    status_code=400,
                    detail="A query gerada violou as políticas de segurança."
                )

            set_cached_sql(request.question, generated_sql, explanation)

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
