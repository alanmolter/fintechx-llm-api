from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

class QueryRequest(BaseModel):
    question: str = Field(..., description="A pergunta em linguagem natural feita pelo usuário.", example="Quais são os produtos mais vendidos?")

class QueryResponse(BaseModel):
    question: str
    sql_query: str = Field(..., description="A query SQL gerada pelo LLM.")
    data: List[Dict[str, Any]] = Field(..., description="Os resultados extraídos do banco de dados.")
    explanation: Optional[str] = Field(None, description="Uma explicação contextualizada dos resultados.")