from typing import List, Dict, Any
from sqlalchemy import text
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)

def execute_read_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executa uma query SQL de leitura no banco de dados e retorna os resultados.
    
    Args:
        sql_query (str): A query SQL gerada pelo LLM.
        
    Returns:
        List[Dict[str, Any]]: Uma lista contendo os registros retornados.
    """
    try:
        # Abrimos uma conexão com o banco
        with engine.connect() as connection:
            # Utilizamos text() do SQLAlchemy para executar queries brutas de forma segura
            result = connection.execute(text(sql_query))
            
            # Extraímos os nomes das colunas devolvidas pela query
            columns = result.keys()
            
            # Montamos uma lista de dicionários combinando colunas e valores
            # Ex: [{"ProductName": "Chai", "TotalVendas": 1500}, ...]
            data = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return data
            
    except Exception as e:
        logger.error(f"Erro ao executar a query no banco de dados: {sql_query}")
        logger.error(f"Detalhe do erro: {str(e)}")
        # Propagamos o erro para ser tratado pela camada de roteamento (API)
        raise Exception(f"Falha na extração de dados: {str(e)}")