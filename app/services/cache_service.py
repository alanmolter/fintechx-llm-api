"""
cache_service.py - Serviço de cache inteligente.

Armazena em memória as queries SQL já geradas pelo LLM, evitando chamadas
repetidas à API da OpenAI para perguntas idênticas.

Estratégia: cacheia a query SQL (não os dados), de modo que os dados
retornados ao usuário sejam sempre frescos (execução real no banco),
mas o custo/latência do LLM seja eliminado para perguntas repetidas.

Em produção, este cache em memória pode ser substituído por Redis
para persistência e compartilhamento entre múltiplas instâncias.
"""

import time
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Dicionário em memória simulando um Redis.
# Chave: hash MD5 da pergunta normalizada.
# Valor: {"sql": "SELECT...", "explanation": "...", "timestamp": epoch}
_IN_MEMORY_CACHE = {}

# TTL (Time-To-Live): tempo máximo em segundos antes do cache expirar (24 horas)
CACHE_TTL = 86400


def _generate_cache_key(question: str) -> str:
    """
    Gera uma chave de cache determinística a partir da pergunta.

    Normaliza a pergunta (lowercase, remove espaços extras) para garantir
    que variações irrelevantes ("Qual o ticket?" vs "  qual  o  ticket?  ")
    resultem na mesma chave.

    Args:
        question: A pergunta original do usuário.

    Returns:
        Hash MD5 da pergunta normalizada (32 caracteres hex).
    """
    normalized_q = " ".join(question.lower().strip().split())
    return hashlib.md5(normalized_q.encode('utf-8')).hexdigest()


def get_cached_sql(question: str) -> Optional[dict]:
    """
    Verifica se já existe uma query SQL cacheada para esta pergunta.

    Args:
        question: A pergunta do usuário.

    Returns:
        Dict com 'sql_query' e 'explanation' se houver cache válido, None caso contrário.
    """
    cache_key = _generate_cache_key(question)
    cached_item = _IN_MEMORY_CACHE.get(cache_key)

    if cached_item:
        if time.time() - cached_item["timestamp"] < CACHE_TTL:
            logger.info(f"Cache HIT para a pergunta: '{question}'")
            return {
                "sql_query": cached_item["sql"],
                "explanation": cached_item["explanation"]
            }
        else:
            logger.info("Cache EXPIRED.")
            del _IN_MEMORY_CACHE[cache_key]

    return None


def set_cached_sql(question: str, sql_query: str, explanation: str) -> None:
    """
    Armazena no cache a query SQL gerada pelo LLM para uma pergunta.

    Na próxima vez que a mesma pergunta for feita, o LLM não será chamado;
    a SQL cacheada será executada diretamente no banco.

    Args:
        question: A pergunta original do usuário.
        sql_query: A query SQL gerada pelo LLM.
        explanation: A explicação gerada pelo LLM.
    """
    cache_key = _generate_cache_key(question)
    _IN_MEMORY_CACHE[cache_key] = {
        "sql": sql_query,
        "explanation": f"[Via Cache] {explanation}",
        "timestamp": time.time()
    }
    logger.info(f"Cache SET para a pergunta: '{question}'")
