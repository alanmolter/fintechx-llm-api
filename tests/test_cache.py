import time

from app.services.cache_service import (
    get_cached_sql,
    set_cached_sql,
    _generate_cache_key,
    _IN_MEMORY_CACHE,
    CACHE_TTL,
)


class TestCacheKeyGeneration:
    """Testes para a geração de chaves de cache."""

    def test_same_question_same_key(self):
        key1 = _generate_cache_key("Qual o ticket médio?")
        key2 = _generate_cache_key("Qual o ticket médio?")
        assert key1 == key2

    def test_case_insensitive(self):
        key1 = _generate_cache_key("Qual o ticket médio?")
        key2 = _generate_cache_key("QUAL O TICKET MÉDIO?")
        assert key1 == key2

    def test_extra_spaces_ignored(self):
        key1 = _generate_cache_key("Qual o ticket médio?")
        key2 = _generate_cache_key("  Qual   o   ticket   médio?  ")
        assert key1 == key2

    def test_different_questions_different_keys(self):
        key1 = _generate_cache_key("Qual o ticket médio?")
        key2 = _generate_cache_key("Quais os produtos mais vendidos?")
        assert key1 != key2


class TestCacheOperations:
    """Testes para as operações de set e get do cache."""

    def setup_method(self):
        _IN_MEMORY_CACHE.clear()

    def test_cache_miss_returns_none(self):
        result = get_cached_sql("pergunta nova")
        assert result is None

    def test_cache_set_and_get(self):
        question = "Quais são os produtos mais vendidos?"
        sql = "SELECT ProductName FROM products"
        explanation = "Lista os produtos."

        set_cached_sql(question, sql, explanation)
        result = get_cached_sql(question)

        assert result is not None
        assert result["sql_query"] == sql
        assert "Via Cache" in result["explanation"]

    def test_cache_hit_after_set(self):
        set_cached_sql("teste", "SELECT 1 FROM orders", "teste")
        result = get_cached_sql("teste")
        assert result is not None

    def test_cache_expired_returns_none(self):
        question = "pergunta expirada"
        set_cached_sql(question, "SELECT 1 FROM customers", "exp")

        key = _generate_cache_key(question)
        _IN_MEMORY_CACHE[key]["timestamp"] = time.time() - CACHE_TTL - 1

        result = get_cached_sql(question)
        assert result is None
