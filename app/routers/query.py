from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_sql_from_text
from app.db.repository import execute_read_query
from app.core.security import validate_sql_guardrails
from app.services.cache_service import get_cached_sql, set_cached_sql
import time

router = APIRouter(prefix="/api/v1", tags=["Query"])

@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    start_time = time.time()
    
    try:
        # 1. Verificar o Cache Inteligente
        cached_result = get_cached_sql(request.question)
        
        if cached_result:
            generated_sql = cached_result["sql_query"]
            explanation = cached_result["explanation"]
        else:
            # 2. Cache MISS: Chamar o LLM (Operação cara)
            llm_result = await generate_sql_from_text(request.question)
            generated_sql = llm_result["sql_query"]
            explanation = llm_result["explanation"]
            
            # 3. Guardrails: Validar segurança antes de salvar ou executar
            if not validate_sql_guardrails(generated_sql):
                raise HTTPException(status_code=400, detail="A query gerada violou as políticas de segurança.")
            
            # 4. Salvar no Cache para a próxima vez
            set_cached_sql(request.question, generated_sql, explanation)

        # 5. Executar no banco de dados (Sempre executamos para garantir dados frescos)
        result_data = execute_read_query(generated_sql)
        
        process_time = round(time.time() - start_time, 2)
        
        return QueryResponse(
            question=request.question,
            sql_query=generated_sql,
            data=result_data,
            explanation=f"{explanation} (Tempo de resposta: {process_time}s)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))