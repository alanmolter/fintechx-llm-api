import chromadb
from chromadb.utils import embedding_functions
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

chroma_client = chromadb.Client()

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.LLM_API_KEY,
    model_name="text-embedding-3-small"
)

collection = chroma_client.get_or_create_collection(
    name="fintechx_business_rules",
    embedding_function=openai_ef
)

BUSINESS_RULES = [
    {
        "id": "rule_ticket_medio",
        "text": "O 'ticket médio' é calculado somando o valor total de todas as vendas (unit_price * quantity da tabela order_details) e dividindo pelo número total de pedidos distintos (order_id). Use: SELECT AVG(subtotal) FROM (SELECT od.order_id, SUM(od.unit_price * od.quantity) AS subtotal FROM order_details od GROUP BY od.order_id) t.",
        "metadata": {"topic": "métricas financeiras"}
    },
    {
        "id": "rule_clientes_corporativos",
        "text": "Um 'cliente corporativo' é definido como qualquer registro na tabela customers onde o campo 'company' não seja nulo e possua um 'job_title' de gerência ou diretoria (ex: Manager, Owner, Purchasing Manager).",
        "metadata": {"topic": "segmentação de clientes"}
    },
    {
        "id": "rule_melhores_vendedores",
        "text": "Os 'melhores vendedores' são os funcionários (employees) que geraram a maior receita total em vendas. Junte employees -> orders -> order_details e some unit_price * quantity para cada employee_id. Use CONCAT(e.first_name, ' ', e.last_name) para o nome.",
        "metadata": {"topic": "kpi funcionários"}
    },
    {
        "id": "rule_produtos_mais_vendidos",
        "text": "Os 'produtos mais vendidos em quantidade' são obtidos juntando products com order_details e somando a coluna quantity por product_name. ORDER BY SUM(quantity) DESC.",
        "metadata": {"topic": "análise de produtos"}
    },
    {
        "id": "rule_volume_vendas_cidade",
        "text": "O 'volume de vendas por cidade' é calculado juntando orders com order_details, somando unit_price * quantity e agrupando por ship_city da tabela orders.",
        "metadata": {"topic": "análise geográfica"}
    },
    {
        "id": "rule_clientes_mais_compraram",
        "text": "Os 'clientes que mais compraram' são identificados juntando customers com orders e order_details, somando unit_price * quantity por customers.company.",
        "metadata": {"topic": "análise de clientes"}
    },
    {
        "id": "rule_vendas_por_ano",
        "text": "O 'valor total de vendas por ano' é obtido extraindo o ano de order_date (YEAR(o.order_date)), juntando orders com order_details e somando unit_price * quantity agrupado por ano.",
        "metadata": {"topic": "análise temporal"}
    },
    {
        "id": "rule_vendas_por_categoria",
        "text": "O 'valor total de vendas por categoria' requer juntar products com order_details. A coluna de categoria é products.category (texto direto, não há tabela separada). Agrupe por p.category e some od.unit_price * od.quantity.",
        "metadata": {"topic": "análise por categoria"}
    },
    {
        "id": "rule_fornecedores_frequentes",
        "text": "Os 'fornecedores mais frequentes nos pedidos' são obtidos juntando suppliers com products (via supplier_ids) e order_details. Conte o número de order_ids distintos por suppliers.company. Nota: products.supplier_ids pode conter IDs separados por ponto-e-vírgula.",
        "metadata": {"topic": "análise de fornecedores"}
    },
    {
        "id": "rule_produtos_mais_caros",
        "text": "Os 'produtos mais caros' são obtidos da tabela products ordenando por list_price DESC. SELECT product_name, list_price FROM products ORDER BY list_price DESC.",
        "metadata": {"topic": "análise de preços"}
    }
]

try:
    collection.add(
        documents=[rule["text"] for rule in BUSINESS_RULES],
        metadatas=[rule["metadata"] for rule in BUSINESS_RULES],
        ids=[rule["id"] for rule in BUSINESS_RULES]
    )
    logger.info("Base vetorial do RAG populada com sucesso.")
except Exception as e:
    logger.warning(f"Coleção já populada ou erro ao inserir: {e}")


def retrieve_business_context(question: str, top_k: int = 2) -> str:
    """
    Busca as regras de negócio mais relevantes no banco vetorial com base na pergunta do usuário.
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
