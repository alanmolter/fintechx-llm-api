"""
query.py - Roteador principal da API (endpoints de consulta).

Contém o endpoint POST /api/v1/query que orquestra todo o pipeline:
  1. Cache → 2. RAG → 3. LLM (Function Calling) → 4. Guardrails → 5. MySQL

Também expõe GET /api/v1/examples com as perguntas de exemplo do desafio.
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_sql_from_text
from app.db.repository import execute_read_query
from app.core.security import validate_sql_guardrails
from app.services.cache_service import get_cached_sql, set_cached_sql
import time

router = APIRouter(prefix="/api/v1", tags=["Query"])

# As 10 perguntas do desafio técnico, expostas no endpoint /examples
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
    Lista as 10 perguntas de exemplo que a API é capaz de responder.
    Copie qualquer uma e envie no POST /api/v1/query para ver o resultado.
    """
    return {"total": len(EXAMPLE_QUESTIONS), "questions": EXAMPLE_QUESTIONS}


@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest):
    """
    Recebe uma pergunta em linguagem natural e retorna dados do banco Northwind.

    Pipeline completo:
      1. **Cache**: Verifica se a pergunta já foi processada (evita custo do LLM).
      2. **RAG + LLM**: Busca contexto de negócios e gera SQL via Function Calling.
      3. **Guardrails**: Valida se a query é segura (somente leitura, tabelas permitidas).
      4. **Cache SET**: Salva a SQL gerada para futuras consultas idênticas.
      5. **Execução**: Roda a query no MySQL e retorna os dados.
    """
    start_time = time.time()

    try:
        # --- ETAPA 1: CACHE (verificação) ---
        # Se a mesma pergunta já foi feita, reutiliza o SQL sem chamar o LLM
        cached_result = get_cached_sql(request.question)

        if cached_result:
            generated_sql = cached_result["sql_query"]
            explanation = cached_result["explanation"]
        else:
            # --- ETAPA 2: RAG + LLM (geração de SQL) ---
            # A função generate_sql_from_text internamente:
            #   a) Busca regras de negócio relevantes no ChromaDB (RAG)
            #   b) Monta o prompt dinâmico (schema + contexto)
            #   c) Chama o GPT-4-turbo com Function Calling
            #   d) Retorna {sql_query, explanation}
            llm_result = await generate_sql_from_text(request.question)
            generated_sql = llm_result["sql_query"]
            explanation = llm_result["explanation"]

            # --- ETAPA 3: GUARDRAILS (validação de segurança) ---
            # Verifica se a SQL gerada é segura antes de executar no banco
            if not validate_sql_guardrails(generated_sql):
                raise HTTPException(
                    status_code=400,
                    detail="A query gerada violou as políticas de segurança."
                )

            # --- ETAPA 4: CACHE (armazenamento) ---
            # Salva a SQL para que a próxima consulta idêntica não precise do LLM
            set_cached_sql(request.question, generated_sql, explanation)

        # --- ETAPA 5: EXECUÇÃO NO BANCO DE DADOS ---
        # Sempre executa a SQL no MySQL para retornar dados atualizados em tempo real
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
