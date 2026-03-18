"""
schemas.py - Modelos de dados Pydantic (request/response).

Define a estrutura esperada das requisições e respostas da API.
O FastAPI utiliza esses schemas para validação automática,
serialização e geração da documentação Swagger.
"""

from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional


class QueryRequest(BaseModel):
    """Modelo de entrada: a pergunta em linguagem natural do usuário."""

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
    """Modelo de saída: contém a pergunta, o SQL gerado, os dados e a explicação."""

    question: str = Field(..., description="A pergunta original feita pelo usuário.")
    sql_query: str = Field(..., description="A query SQL gerada pelo LLM via Function Calling.")
    data: List[Dict[str, Any]] = Field(..., description="Os registros retornados pelo banco de dados.")
    explanation: Optional[str] = Field(None, description="Explicação em português do raciocínio analítico do LLM.")
