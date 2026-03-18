import re
import logging

# Configuração básica de log para registrar tentativas de injeção ou falhas
logger = logging.getLogger(__name__)

# 1. Lista de comandos DDL e DML estritamente proibidos
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE", "CALL", "REPLACE"
]

# 2. Tabelas do escopo do desafio Northwind
ALLOWED_TABLES = [
    "customers", "employees", "orders", "products",
    "order details", "categories", "suppliers", "shippers"
]

def validate_sql_guardrails(sql_query: str) -> bool:
    """
    Analisa a query SQL gerada pelo LLM para aplicar guardrails e validação semântica.
    Garante que seja uma operação de leitura segura e dentro do escopo.
    
    Args:
        sql_query (str): A query SQL bruta gerada pelo modelo.
        
    Returns:
        bool: True se a query for segura e válida, False caso contrário.
    """
    if not sql_query or not isinstance(sql_query, str):
        logger.warning("Guardrail acionado: Query SQL vazia ou em formato inválido.")
        return False

    # Normalizar a query para facilitar a análise
    normalized_query = sql_query.upper().strip()

    # REGRA 1: Obrigar que seja uma query de leitura
    # Consultas complexas podem começar com WITH (CTEs), então permitimos ambos
    if not (normalized_query.startswith("SELECT") or normalized_query.startswith("WITH")):
        logger.warning(f"Guardrail acionado: A query não inicia com SELECT ou WITH. Query: {sql_query}")
        return False

    # REGRA 2: Bloquear palavras-chave destrutivas (Regex para exatidão)
    # Usamos \b para garantir que estamos buscando a palavra inteira e não parte de uma string (ex: "DROP" vs "DROPLET")
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized_query):
            logger.warning(f"Guardrail acionado: Comando proibido encontrado ({keyword}). Query: {sql_query}")
            return False

    # REGRA 3: Validação Semântica de Contexto (Tabelas)
    # Verifica se a query menciona pelo menos uma das tabelas permitidas no schema
    query_lower = sql_query.lower()
    has_allowed_table = any(table in query_lower for table in ALLOWED_TABLES)
    
    if not has_allowed_table:
        logger.warning("Guardrail acionado: Nenhuma tabela do escopo (northwind) foi encontrada na query.")
        return False

    # Se passou por todas as barreiras, a query é considerada segura para execução
    return True