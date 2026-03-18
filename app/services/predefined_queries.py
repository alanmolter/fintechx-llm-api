import re
from typing import Optional

PREDEFINED = [
    {
        "keywords": ["produtos", "populares", "corporativ"],
        "question": "Quais são os produtos mais populares entre os clientes corporativos?",
        "sql": """
            SELECT p.product_name AS produto, SUM(od.quantity) AS total_quantidade
            FROM order_details od
            JOIN products p ON od.product_id = p.id
            JOIN orders o ON od.order_id = o.id
            JOIN customers c ON o.customer_id = c.id
            WHERE c.company IS NOT NULL
            GROUP BY p.product_name
            ORDER BY total_quantidade DESC
            LIMIT 10
        """,
        "explanation": "Consulta os produtos com maior volume de vendas (quantidade) para clientes que possuem empresa cadastrada (clientes corporativos), ordenando do mais popular para o menos popular."
    },
    {
        "keywords": ["produtos", "vendidos", "quantidade"],
        "question": "Quais são os produtos mais vendidos em termos de quantidade?",
        "sql": """
            SELECT p.product_name AS produto, SUM(od.quantity) AS total_quantidade
            FROM order_details od
            JOIN products p ON od.product_id = p.id
            GROUP BY p.product_name
            ORDER BY total_quantidade DESC
            LIMIT 10
        """,
        "explanation": "Soma a quantidade vendida de cada produto através da tabela order_details e retorna os 10 produtos com maior volume de vendas."
    },
    {
        "keywords": ["volume", "vendas", "cidade"],
        "question": "Qual é o volume de vendas por cidade?",
        "sql": """
            SELECT o.ship_city AS cidade,
                   ROUND(SUM(od.unit_price * od.quantity), 2) AS total_vendas
            FROM orders o
            JOIN order_details od ON o.id = od.order_id
            WHERE o.ship_city IS NOT NULL
            GROUP BY o.ship_city
            ORDER BY total_vendas DESC
        """,
        "explanation": "Calcula o valor total de vendas (preço unitário x quantidade) agrupado pela cidade de envio dos pedidos."
    },
    {
        "keywords": ["clientes", "mais", "compraram"],
        "question": "Quais são os clientes que mais compraram?",
        "sql": """
            SELECT c.company AS cliente,
                   ROUND(SUM(od.unit_price * od.quantity), 2) AS total_compras
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            JOIN order_details od ON o.id = od.order_id
            GROUP BY c.company
            ORDER BY total_compras DESC
            LIMIT 10
        """,
        "explanation": "Identifica os 10 clientes com maior valor total em compras, juntando as tabelas customers, orders e order_details."
    },
    {
        "keywords": ["produtos", "caros"],
        "question": "Quais são os produtos mais caros da loja?",
        "sql": """
            SELECT product_name AS produto, list_price AS preco
            FROM products
            WHERE list_price IS NOT NULL AND list_price > 0
            ORDER BY list_price DESC
            LIMIT 10
        """,
        "explanation": "Retorna os 10 produtos com maior preço de lista (list_price) cadastrado no catálogo."
    },
    {
        "keywords": ["fornecedores", "frequentes"],
        "question": "Quais são os fornecedores mais frequentes nos pedidos?",
        "sql": """
            SELECT s.company AS fornecedor,
                   COUNT(DISTINCT od.order_id) AS total_pedidos
            FROM suppliers s
            JOIN products p ON FIND_IN_SET(s.id, p.supplier_ids) > 0
            JOIN order_details od ON od.product_id = p.id
            GROUP BY s.company
            ORDER BY total_pedidos DESC
            LIMIT 10
        """,
        "explanation": "Conta o número de pedidos distintos em que cada fornecedor aparece, relacionando suppliers com products e order_details."
    },
    {
        "keywords": ["melhores", "vendedores"],
        "question": "Quais os melhores vendedores?",
        "sql": """
            SELECT CONCAT(e.first_name, ' ', e.last_name) AS vendedor,
                   ROUND(SUM(od.unit_price * od.quantity), 2) AS total_vendas
            FROM employees e
            JOIN orders o ON e.id = o.employee_id
            JOIN order_details od ON o.id = od.order_id
            GROUP BY e.id, e.first_name, e.last_name
            ORDER BY total_vendas DESC
        """,
        "explanation": "Identifica os vendedores (employees) que geraram a maior receita total, somando o valor de todas as vendas associadas a cada um."
    },
    {
        "keywords": ["valor", "vendas", "ano"],
        "question": "Qual é o valor total de todas as vendas realizadas por ano?",
        "sql": """
            SELECT YEAR(o.order_date) AS ano,
                   ROUND(SUM(od.unit_price * od.quantity), 2) AS total_vendas
            FROM orders o
            JOIN order_details od ON o.id = od.order_id
            WHERE o.order_date IS NOT NULL
            GROUP BY YEAR(o.order_date)
            ORDER BY ano
        """,
        "explanation": "Agrupa todas as vendas por ano (extraído da data do pedido) e soma o valor total de cada período."
    },
    {
        "keywords": ["vendas", "categoria"],
        "question": "Qual é o valor total de vendas por categoria de produto?",
        "sql": """
            SELECT p.category AS categoria,
                   ROUND(SUM(od.unit_price * od.quantity), 2) AS total_vendas
            FROM products p
            JOIN order_details od ON p.id = od.product_id
            WHERE p.category IS NOT NULL AND p.category != ''
            GROUP BY p.category
            ORDER BY total_vendas DESC
        """,
        "explanation": "Calcula o valor total de vendas agrupado pela categoria do produto, utilizando a coluna 'category' da tabela products."
    },
    {
        "keywords": ["ticket", "medio", "médio"],
        "question": "Qual o ticket médio por compra?",
        "sql": """
            SELECT ROUND(AVG(subtotal), 2) AS ticket_medio
            FROM (
                SELECT od.order_id, SUM(od.unit_price * od.quantity) AS subtotal
                FROM order_details od
                GROUP BY od.order_id
            ) t
        """,
        "explanation": "Calcula o ticket médio somando o valor de cada pedido (unit_price x quantity) e tirando a média entre todos os pedidos distintos."
    },
]


def find_predefined_query(question: str) -> Optional[dict]:
    """
    Busca uma query predefinida que corresponda à pergunta do usuário.
    Retorna o dict com sql_query e explanation, ou None se não encontrar.
    """
    q_lower = question.lower().strip()
    q_normalized = re.sub(r"[^\w\s]", "", q_lower)

    for entry in PREDEFINED:
        match_count = sum(1 for kw in entry["keywords"] if kw in q_normalized)
        if match_count >= 2:
            return {
                "sql_query": entry["sql"].strip(),
                "explanation": entry["explanation"],
            }

    return None


def get_all_example_questions() -> list:
    """Retorna a lista de todas as perguntas de exemplo disponíveis."""
    return [entry["question"] for entry in PREDEFINED]
