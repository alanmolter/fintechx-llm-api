"""
security.py - Guardrails de validação SQL.

Implementa a camada de defesa em profundidade da aplicação.
Antes de qualquer query gerada pelo LLM ser executada no banco de dados,
ela passa por três validações:
  1. Deve iniciar com SELECT ou WITH (apenas leitura).
  2. Não pode conter palavras-chave destrutivas (DROP, DELETE, etc.).
  3. Deve referenciar pelo menos uma tabela permitida do Northwind.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Lista de comandos SQL que podem modificar ou destruir dados.
# Mesmo o banco usando um usuário read-only, esta validação adiciona
# uma segunda camada de proteção na aplicação.
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE", "CALL", "REPLACE"
]

# Tabelas válidas do banco Northwind que o LLM pode consultar.
# Qualquer query referenciando tabelas fora deste escopo será bloqueada.
ALLOWED_TABLES = [
    "customers", "employees", "orders", "order_details", "products",
    "suppliers", "shippers", "invoices", "purchase_orders",
    "purchase_order_details", "sales_reports"
]


def validate_sql_guardrails(sql_query: str) -> bool:
    """
    Valida uma query SQL gerada pelo LLM antes de executá-la no banco.

    Args:
        sql_query: A query SQL bruta gerada pelo modelo.

    Returns:
        True se a query for segura e válida, False caso contrário.
    """
    # Validação básica: query não pode ser vazia ou de tipo inválido
    if not sql_query or not isinstance(sql_query, str):
        logger.warning("Guardrail acionado: Query SQL vazia ou em formato inválido.")
        return False

    normalized_query = sql_query.upper().strip()

    # REGRA 1: Apenas leitura - deve começar com SELECT ou WITH (CTEs)
    if not (normalized_query.startswith("SELECT") or normalized_query.startswith("WITH")):
        logger.warning(f"Guardrail acionado: A query não inicia com SELECT ou WITH. Query: {sql_query}")
        return False

    # REGRA 2: Bloquear comandos destrutivos usando regex com word boundary (\b)
    # para evitar falsos positivos (ex: "DROPLET" não deve ser bloqueado por "DROP")
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized_query):
            logger.warning(f"Guardrail acionado: Comando proibido encontrado ({keyword}). Query: {sql_query}")
            return False

    # REGRA 3: A query deve referenciar pelo menos uma tabela do escopo Northwind
    query_lower = sql_query.lower()
    has_allowed_table = any(table in query_lower for table in ALLOWED_TABLES)

    if not has_allowed_table:
        logger.warning("Guardrail acionado: Nenhuma tabela do escopo (northwind) foi encontrada na query.")
        return False

    return True
