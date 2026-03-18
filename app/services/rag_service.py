"""
rag_service.py - Serviço de RAG (Retrieval-Augmented Generation).

Utiliza ChromaDB como banco vetorial para armazenar regras de negócio
da FinTechX. Quando o usuário faz uma pergunta, as regras mais relevantes
são recuperadas via busca semântica e injetadas no prompt do LLM.

Isso permite que o LLM entenda conceitos subjetivos como "ticket médio"
ou "clientes corporativos" sem poluir o system prompt com todo o
conhecimento da empresa, economizando tokens e evitando alucinações.
"""

import chromadb
from chromadb.utils import embedding_functions
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# 1. INICIALIZAÇÃO DO BANCO VETORIAL (ChromaDB)
# =============================================================================
# Usamos ChromaDB em memória (Client()) para o escopo deste desafio.
# Em produção, seria substituído por ChromaDB persistente ou Pinecone/Weaviate.
chroma_client = chromadb.Client()

# Função de embedding que converte texto em vetores numéricos usando a API da OpenAI.
# O modelo text-embedding-3-small é otimizado para custo e performance.
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.LLM_API_KEY,
    model_name="text-embedding-3-small"
)

# Cria (ou recupera) a coleção vetorial que armazena as regras de negócio
collection = chroma_client.get_or_create_collection(
    name="fintechx_business_rules",
    embedding_function=openai_ef
)

# =============================================================================
# 2. DICIONÁRIO DE REGRAS DE NEGÓCIO (Seed Data)
# =============================================================================
# Em produção, essas regras viriam de um Confluence, Notion ou banco de dados.
# Cada regra explica ao LLM como interpretar um conceito de negócio específico
# e quais tabelas/colunas utilizar para gerar o SQL correto.
BUSINESS_RULES = [
    {
        "id": "rule_ticket_medio",
        "text": (
            "O 'ticket médio' é calculado somando o valor total de todas as vendas "
            "(unit_price * quantity da tabela order_details) e dividindo pelo número "
            "total de pedidos distintos (order_id). "
            "Use: SELECT AVG(subtotal) FROM (SELECT od.order_id, SUM(od.unit_price * od.quantity) "
            "AS subtotal FROM order_details od GROUP BY od.order_id) t."
        ),
        "metadata": {"topic": "métricas financeiras"}
    },
    {
        "id": "rule_clientes_corporativos",
        "text": (
            "Um 'cliente corporativo' é definido como qualquer registro na tabela customers "
            "onde o campo 'company' não seja nulo e possua um 'job_title' de gerência ou "
            "diretoria (ex: Manager, Owner, Purchasing Manager)."
        ),
        "metadata": {"topic": "segmentação de clientes"}
    },
    {
        "id": "rule_melhores_vendedores",
        "text": (
            "Os 'melhores vendedores' são os funcionários (employees) que geraram a maior "
            "receita total em vendas. Junte employees -> orders -> order_details e some "
            "unit_price * quantity para cada employee_id. "
            "Use CONCAT(e.first_name, ' ', e.last_name) para o nome completo."
        ),
        "metadata": {"topic": "kpi funcionários"}
    },
    {
        "id": "rule_produtos_mais_vendidos",
        "text": (
            "Os 'produtos mais vendidos em quantidade' são obtidos juntando products com "
            "order_details e somando a coluna quantity por product_name. ORDER BY SUM(quantity) DESC."
        ),
        "metadata": {"topic": "análise de produtos"}
    },
    {
        "id": "rule_volume_vendas_cidade",
        "text": (
            "O 'volume de vendas por cidade' é calculado juntando orders com order_details, "
            "somando unit_price * quantity e agrupando por ship_city da tabela orders."
        ),
        "metadata": {"topic": "análise geográfica"}
    },
    {
        "id": "rule_clientes_mais_compraram",
        "text": (
            "Os 'clientes que mais compraram' são identificados juntando customers com orders "
            "e order_details, somando unit_price * quantity por customers.company."
        ),
        "metadata": {"topic": "análise de clientes"}
    },
    {
        "id": "rule_vendas_por_ano",
        "text": (
            "O 'valor total de vendas por ano' é obtido extraindo o ano de order_date "
            "(YEAR(o.order_date)), juntando orders com order_details e somando "
            "unit_price * quantity agrupado por ano."
        ),
        "metadata": {"topic": "análise temporal"}
    },
    {
        "id": "rule_vendas_por_categoria",
        "text": (
            "O 'valor total de vendas por categoria' requer juntar products com order_details. "
            "A coluna de categoria é products.category (texto direto, não há tabela separada). "
            "Agrupe por p.category e some od.unit_price * od.quantity."
        ),
        "metadata": {"topic": "análise por categoria"}
    },
    {
        "id": "rule_fornecedores_frequentes",
        "text": (
            "Os 'fornecedores mais frequentes nos pedidos' são obtidos juntando suppliers "
            "com products (via supplier_ids) e order_details. Conte o número de order_ids "
            "distintos por suppliers.company. "
            "Nota: products.supplier_ids pode conter IDs separados por ponto-e-vírgula."
        ),
        "metadata": {"topic": "análise de fornecedores"}
    },
    {
        "id": "rule_produtos_mais_caros",
        "text": (
            "Os 'produtos mais caros' são obtidos da tabela products ordenando por list_price DESC. "
            "SELECT product_name, list_price FROM products ORDER BY list_price DESC."
        ),
        "metadata": {"topic": "análise de preços"}
    }
]

# =============================================================================
# 3. POPULAÇÃO DO BANCO VETORIAL (executada na inicialização da aplicação)
# =============================================================================
# Insere todas as regras de negócio no ChromaDB. O embedding é gerado
# automaticamente pela OpenAIEmbeddingFunction configurada acima.
try:
    collection.add(
        documents=[rule["text"] for rule in BUSINESS_RULES],
        metadatas=[rule["metadata"] for rule in BUSINESS_RULES],
        ids=[rule["id"] for rule in BUSINESS_RULES]
    )
    logger.info("Base vetorial do RAG populada com sucesso.")
except Exception as e:
    # Se a coleção já foi populada (reinício da app), o ChromaDB retorna erro de ID duplicado
    logger.warning(f"Coleção já populada ou erro ao inserir: {e}")


# =============================================================================
# 4. FUNÇÃO DE BUSCA SEMÂNTICA
# =============================================================================
def retrieve_business_context(question: str, top_k: int = 2) -> str:
    """
    Busca as regras de negócio mais relevantes para a pergunta do usuário.

    Utiliza busca vetorial (similaridade de cosseno) para encontrar os
    documentos mais próximos semanticamente da pergunta feita.

    Args:
        question: A pergunta em linguagem natural do usuário.
        top_k: Quantidade de regras mais relevantes a retornar (default: 2).

    Returns:
        String formatada com o contexto de negócios para injetar no prompt do LLM.
    """
    try:
        results = collection.query(
            query_texts=[question],
            n_results=top_k
        )

        documents = results.get("documents", [[]])[0]

        if documents:
            context_str = "\n".join([f"- {doc}" for doc in documents])
            return f"\nContexto de Negócios Relevante:\n{context_str}\n"
        return ""

    except Exception as e:
        logger.error(f"Erro na busca vetorial (RAG): {e}")
        return ""
