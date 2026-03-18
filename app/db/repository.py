"""
repository.py - Camada de acesso ao banco de dados.

Responsável por executar as queries SQL geradas pelo LLM no banco MySQL.
Utiliza SQLAlchemy para gerenciamento seguro de conexões e execução.
"""

from typing import List, Dict, Any
from sqlalchemy import text
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)


def execute_read_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executa uma query SQL de leitura no banco de dados Northwind.

    Abre uma conexão do pool, executa a query, e retorna os resultados
    como uma lista de dicionários (cada dict = uma linha do resultado).

    Args:
        sql_query: A query SQL validada pelos guardrails.

    Returns:
        Lista de dicionários no formato [{"coluna": valor, ...}, ...].

    Raises:
        Exception: Se a execução falhar (query inválida, timeout, etc.).
    """
    try:
        with engine.connect() as connection:
            # text() do SQLAlchemy encapsula a string SQL para execução segura
            result = connection.execute(text(sql_query))

            # Extrai os nomes das colunas retornadas pela query
            columns = result.keys()

            # Converte cada linha em um dicionário {coluna: valor}
            data = [dict(zip(columns, row)) for row in result.fetchall()]

            return data

    except Exception as e:
        logger.error(f"Erro ao executar query: {sql_query}")
        logger.error(f"Detalhe: {str(e)}")
        raise Exception(f"Falha na extração de dados: {str(e)}")
