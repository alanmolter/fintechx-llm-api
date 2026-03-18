import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.rag_service import retrieve_business_context

# Inicializa o client de forma assíncrona para melhor performance na API
client = AsyncOpenAI(api_key=settings.LLM_API_KEY)

# 1. Definição do Contexto (System Prompt)
# É fundamental informar o schema exato do banco Northwind para o modelo acertar as colunas
DB_SCHEMA_CONTEXT = """
Você é um assistente de dados avançado da FinTechX. Sua tarefa é traduzir perguntas analíticas feitas em linguagem natural para consultas SQL válidas e otimizadas para MySQL.

Você tem acesso ao banco de dados 'northwind', que contém as seguintes tabelas e relacionamentos principais:
- customers (CustomerID, CompanyName, ContactName, ContactTitle, City, Country)
- employees (EmployeeID, LastName, FirstName, Title, City)
- orders (OrderID, CustomerID, EmployeeID, OrderDate, ShipCity, ShipCountry)
- `order details` (OrderID, ProductID, UnitPrice, Quantity, Discount)
- products (ProductID, ProductName, SupplierID, CategoryID, UnitPrice, UnitsInStock)
- categories (CategoryID, CategoryName, Description)
- suppliers (SupplierID, CompanyName, ContactName, City, Country)
- shippers (ShipperID, CompanyName, Phone)

Relacionamentos:
- orders.CustomerID -> customers.CustomerID
- orders.EmployeeID -> employees.EmployeeID
- `order details`.OrderID -> orders.OrderID
- `order details`.ProductID -> products.ProductID
- products.CategoryID -> categories.CategoryID
- products.SupplierID -> suppliers.SupplierID

Regras de Ouro:
1. Gere APENAS consultas de leitura (SELECT). Nunca gere INSERT, UPDATE, DELETE, DROP ou ALTER.
2. Utilize boas práticas de SQL, como JOINs apropriados e aliases para as tabelas.
3. A tabela `order details` DEVE ser referenciada com backticks por conter espaço no nome.
4. Se a pergunta for ambígua, adote a interpretação mais lógica para o contexto de negócios da FinTechX.
"""

# 2. Definição da Ferramenta (Function Calling Schema)
# Este JSON Schema diz ao LLM os parâmetros exatos que nossa aplicação precisa receber.
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
        # 1. RAG: Recupera regras de negócio relevantes usando busca vetorial
        business_context = retrieve_business_context(question)
        
        # 2. Monta o Prompt Dinâmico unindo o Schema Base + Contexto RAG
        dynamic_system_prompt = f"{DB_SCHEMA_CONTEXT}\n{business_context}"
        
        # 3. Chama o LLM
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