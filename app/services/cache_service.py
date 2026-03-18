import time
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Dicionário em memória para simular o Redis
# Formato: { "hash_da_pergunta": {"sql": "SELECT...", "timestamp": 1690000000} }
_IN_MEMORY_CACHE = {}

# Tempo de vida do cache em segundos (ex: 24 horas)
CACHE_TTL = 86400 

def _generate_cache_key(question: str) -> str:
    """
    Normaliza a pergunta (remove espaços extras e deixa minúscula) 
    e gera um hash MD5 para usar como chave de busca rápida.
    """
    normalized_q = " ".join(question.lower().strip().split())
    return hashlib.md5(normalized_q.encode('utf-8')).hexdigest()

def get_cached_sql(question: str) -> Optional[dict]:
    """
    Verifica se a pergunta já foi feita recentemente e retorna o SQL correspondente.
    """
    cache_key = _generate_cache_key(question)
    cached_item = _IN_MEMORY_CACHE.get(cache_key)
    
    if cached_item:
        # Verifica se o cache expirou
        if time.time() - cached_item["timestamp"] < CACHE_TTL:
            logger.info(f"Cache HIT para a pergunta: '{question}'")
            return {
                "sql_query": cached_item["sql"],
                "explanation": cached_item["explanation"]
            }
        else:
            # Remove se estiver expirado
            logger.info("Cache EXPIRED.")
            del _IN_MEMORY_CACHE[cache_key]
            
    return None

def set_cached_sql(question: str, sql_query: str, explanation: str) -> None:
    """
    Salva o SQL gerado pelo LLM no cache para futuras consultas idênticas.
    """
    cache_key = _generate_cache_key(question)
    _IN_MEMORY_CACHE[cache_key] = {
        "sql": sql_query,
        "explanation": f"[Via Cache] {explanation}", # Marcador para o usuário saber que veio do cache
        "timestamp": time.time()
    }
    logger.info(f"Cache SET para a pergunta: '{question}'")