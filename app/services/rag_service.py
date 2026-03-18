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
        "text": "O 'ticket médio' é calculado somando o valor total de todas as vendas (UnitPrice * Quantity da tabela `order details`) e dividindo pelo número total de pedidos distintos (OrderID). Use: SELECT AVG(subtotal) FROM (SELECT od.OrderID, SUM(od.UnitPrice * od.Quantity) AS subtotal FROM `order details` od GROUP BY od.OrderID) t.",
        "metadata": {"topic": "métricas financeiras"}
    },
    {
        "id": "rule_clientes_corporativos",
        "text": "Um 'cliente corporativo' é definido como qualquer registro na tabela `customers` onde o campo `CompanyName` não seja nulo e possua um `ContactTitle` de gerência ou diretoria (ex: Manager, Owner, Sales Representative).",
        "metadata": {"topic": "segmentação de clientes"}
    },
    {
        "id": "rule_melhores_vendedores",
        "text": "Os 'melhores vendedores' são os funcionários (employees) que geraram a maior receita total em vendas. Junte employees -> orders -> `order details` e some UnitPrice * Quantity para cada EmployeeID.",
        "metadata": {"topic": "kpi funcionários"}
    },
    {
        "id": "rule_produtos_mais_vendidos",
        "text": "Os 'produtos mais vendidos em quantidade' são obtidos juntando `products` com `order details` e somando a coluna Quantity por ProductName. ORDER BY SUM(Quantity) DESC.",
        "metadata": {"topic": "análise de produtos"}
    },
    {
        "id": "rule_volume_vendas_cidade",
        "text": "O 'volume de vendas por cidade' é calculado juntando `orders` com `order details`, somando UnitPrice * Quantity e agrupando por ShipCity da tabela orders.",
        "metadata": {"topic": "análise geográfica"}
    },
    {
        "id": "rule_clientes_mais_compraram",
        "text": "Os 'clientes que mais compraram' são identificados juntando `customers` com `orders` e `order details`, somando UnitPrice * Quantity por CompanyName.",
        "metadata": {"topic": "análise de clientes"}
    },
    {
        "id": "rule_vendas_por_ano",
        "text": "O 'valor total de vendas por ano' é obtido extraindo o ano de OrderDate (YEAR(o.OrderDate)), juntando orders com `order details` e somando UnitPrice * Quantity agrupado por ano.",
        "metadata": {"topic": "análise temporal"}
    },
    {
        "id": "rule_vendas_por_categoria",
        "text": "O 'valor total de vendas por categoria' requer juntar `categories` com `products` e `order details`. Agrupe por CategoryName e some UnitPrice * Quantity.",
        "metadata": {"topic": "análise por categoria"}
    },
    {
        "id": "rule_fornecedores_frequentes",
        "text": "Os 'fornecedores mais frequentes nos pedidos' são obtidos juntando `suppliers` com `products` e `order details`. Conte o número de OrderIDs distintos por supplier CompanyName.",
        "metadata": {"topic": "análise de fornecedores"}
    },
    {
        "id": "rule_produtos_mais_caros",
        "text": "Os 'produtos mais caros' são simplesmente obtidos da tabela `products` ordenando por UnitPrice DESC. SELECT ProductName, UnitPrice FROM products ORDER BY UnitPrice DESC.",
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
