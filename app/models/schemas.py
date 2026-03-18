from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        description="A pergunta em linguagem natural feita pelo usuário.",
        json_schema_extra={
            "examples": [
                "Quais são os produtos mais populares entre os clientes corporativos?",
                "Quais são os produtos mais vendidos em termos de quantidade?",
                "Qual é o volume de vendas por cidade?",
                "Quais são os clientes que mais compraram?",
                "Quais são os produtos mais caros da loja?",
                "Quais são os fornecedores mais frequentes nos pedidos?",
                "Quais os melhores vendedores?",
                "Qual é o valor total de todas as vendas realizadas por ano?",
                "Qual é o valor total de vendas por categoria de produto?",
                "Qual o ticket médio por compra?"
            ]
        }
    )

class QueryResponse(BaseModel):
    question: str
    sql_query: str = Field(..., description="A query SQL gerada pelo LLM.")
    data: List[Dict[str, Any]] = Field(..., description="Os resultados extraídos do banco de dados.")
    explanation: Optional[str] = Field(None, description="Uma explicação contextualizada dos resultados.")
