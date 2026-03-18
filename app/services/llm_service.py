import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.rag_service import retrieve_business_context

client = AsyncOpenAI(api_key=settings.LLM_API_KEY)

DB_SCHEMA_CONTEXT = """
Você é um assistente de dados avançado da FinTechX. Sua tarefa é traduzir perguntas analíticas feitas em linguagem natural para consultas SQL válidas e otimizadas para MySQL.

Você tem acesso ao banco de dados 'northwind', que contém as seguintes tabelas e colunas:

- customers (id, company, last_name, first_name, email_address, job_title, business_phone, city, state_province, country_region)
- employees (id, company, last_name, first_name, email_address, job_title, business_phone, city, state_province, country_region)
- orders (id, employee_id, customer_id, order_date, shipped_date, shipper_id, ship_name, ship_address, ship_city, ship_state_province, ship_country_region, shipping_fee, taxes, payment_type, paid_date, tax_rate, status_id)
- order_details (id, order_id, product_id, quantity, unit_price, discount, status_id, date_allocated, purchase_order_id, inventory_id)
- products (id, product_code, product_name, description, standard_cost, list_price, reorder_level, target_level, quantity_per_unit, discontinued, minimum_reorder_quantity, category, supplier_ids)
- suppliers (id, company, last_name, first_name, email_address, job_title, city, country_region)
- shippers (id, company, last_name, first_name, email_address, job_title, business_phone)
- invoices (id, order_id, invoice_date, due_date, tax, shipping, amount_due)
- purchase_orders (id, supplier_id, created_by, submitted_date, creation_date, status_id, expected_date, shipping_fee, taxes, payment_date, payment_amount, payment_method)
- purchase_order_details (id, purchase_order_id, product_id, quantity, unit_cost, date_received, posted_to_inventory, inventory_id)

Relacionamentos:
- orders.customer_id -> customers.id
- orders.employee_id -> employees.id
- orders.shipper_id -> shippers.id
- order_details.order_id -> orders.id
- order_details.product_id -> products.id
- invoices.order_id -> orders.id
- purchase_orders.supplier_id -> suppliers.id
- purchase_order_details.purchase_order_id -> purchase_orders.id
- purchase_order_details.product_id -> products.id

Regras de Ouro:
1. Gere APENAS consultas de leitura (SELECT). Nunca gere INSERT, UPDATE, DELETE, DROP ou ALTER.
2. Utilize boas práticas de SQL, como JOINs apropriados e aliases para as tabelas.
3. A coluna de categoria em products é 'category' (texto direto, não há tabela separada de categorias).
4. O preço de venda nos order_details é 'unit_price'. O preço de lista do produto é 'list_price'.
5. Se a pergunta for ambígua, adote a interpretação mais lógica para o contexto de negócios da FinTechX.
"""

sql_generation_tool = {
    "type": "function",
    "function": {
        "name": "execute_data_extraction",
        "description": "Extrai dados do banco MySQL da FinTechX formatando a string SQL necessária para responder à pergunta do usuário.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "A query SQL otimizada, validada e sintaticamente correta para MySQL.",
                },
                "explanation": {
                    "type": "string",
                    "description": "Uma breve explicação em português do raciocínio analítico utilizado para montar essa query.",
                }
            },
            "required": ["sql_query", "explanation"],
        },
    }
}

async def generate_sql_from_text(question: str) -> dict:
    """
    Recebe a pergunta, busca contexto corporativo (RAG), e gera a query SQL via Function Calling.
    """
    try:
        business_context = retrieve_business_context(question)

        dynamic_system_prompt = f"{DB_SCHEMA_CONTEXT}\n{business_context}"

        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": dynamic_system_prompt},
                {"role": "user", "content": question}
            ],
            tools=[sql_generation_tool],
            tool_choice={"type": "function", "function": {"name": "execute_data_extraction"}},
            temperature=0.0
        )

        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        return arguments

    except Exception as e:
        raise Exception(f"Erro ao gerar SQL via LLM: {str(e)}")
