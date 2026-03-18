import re
import logging

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE", "CALL", "REPLACE"
]

ALLOWED_TABLES = [
    "customers", "employees", "orders", "order_details", "products",
    "suppliers", "shippers", "invoices", "purchase_orders",
    "purchase_order_details", "sales_reports"
]

def validate_sql_guardrails(sql_query: str) -> bool:
    """
    Analisa a query SQL gerada pelo LLM para aplicar guardrails e validação semântica.
    Garante que seja uma operação de leitura segura e dentro do escopo.
    """
    if not sql_query or not isinstance(sql_query, str):
        logger.warning("Guardrail acionado: Query SQL vazia ou em formato inválido.")
        return False

    normalized_query = sql_query.upper().strip()

    if not (normalized_query.startswith("SELECT") or normalized_query.startswith("WITH")):
        logger.warning(f"Guardrail acionado: A query não inicia com SELECT ou WITH. Query: {sql_query}")
        return False

    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized_query):
            logger.warning(f"Guardrail acionado: Comando proibido encontrado ({keyword}). Query: {sql_query}")
            return False

    query_lower = sql_query.lower()
    has_allowed_table = any(table in query_lower for table in ALLOWED_TABLES)

    if not has_allowed_table:
        logger.warning("Guardrail acionado: Nenhuma tabela do escopo (northwind) foi encontrada na query.")
        return False

    return True
