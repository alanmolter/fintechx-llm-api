# Documento de Arquitetura - FinTechX Text-to-SQL API

## 1. Visão Geral e Fluxo da Requisição

A solução foi desenhada para atuar como uma ponte inteligente e segura entre usuários de negócios da FinTechX e o banco de dados relacional. O fluxo da requisição segue uma pipeline estrita:

1. **Ingestão:** A API (FastAPI) recebe a pergunta em linguagem natural.
2. **Verificação de Cache:** O hash da pergunta é consultado. Em caso de hit, o SQL correspondente é recuperado imediatamente.
3. **Recuperação de Contexto (RAG):** Regras de negócios específicas da FinTechX são recuperadas do banco vetorial (ChromaDB) para enriquecer o prompt.
4. **Geração Determinística (LLM):** Utiliza-se Function Calling para garantir que o LLM retorne um objeto JSON contendo exclusivamente a query SQL e uma explicação lógica, evitando alucinações de texto livre.
5. **Defesa em Profundidade (Guardrails):** O SQL gerado passa por validações semânticas na aplicação antes de tocar no banco de dados.
6. **Execução e Retorno:** A query é executada no MySQL e os dados são empacotados na resposta.

```
┌──────────┐     ┌─────────────────────────────────────────────────────────┐     ┌───────────┐
│  Usuário │────▶│                   FastAPI Application                   │────▶│  Response  │
└──────────┘     │                                                         │     └───────────┘
                 │  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌───────┐ │
                 │  │  Cache   │──▶│   RAG   │──▶│   LLM    │──▶│Guards │ │
                 │  │ (MD5)   │   │(ChromaDB)│  │ (OpenAI) │   │ rails │ │
                 │  └─────────┘   └─────────┘   └──────────┘   └───────┘ │
                 │                                                  │      │
                 │                                           ┌──────▼────┐ │
                 │                                           │   MySQL   │ │
                 │                                           │(Northwind)│ │
                 │                                           └───────────┘ │
                 └─────────────────────────────────────────────────────────┘
```

## 2. Decisões Técnicas e Justificativas

### Cache Inteligente (Semantic/Hash Caching)

Optou-se por cachear a **query SQL gerada** em vez dos dados finais. Isso garante que a latência e o custo das chamadas ao LLM sejam mitigados para perguntas frequentes, sem comprometer a atualização em tempo real dos dados transacionais da FinTechX.

- **Chave:** Hash MD5 da pergunta normalizada (lowercase, sem espaços extras).
- **TTL:** 24 horas, configurável.
- **Evolução:** Em produção, o cache em memória pode ser substituído por um cluster **Redis** para persistência e compartilhamento entre instâncias.

### RAG (Busca Vetorial)

A injeção dinâmica de dicionários de dados permite que o LLM entenda conceitos subjetivos (ex: "clientes corporativos" ou "ticket médio") sem poluir o System Prompt com todo o conhecimento da empresa, mantendo o consumo de tokens eficiente.

- **Banco vetorial:** ChromaDB (in-memory para o escopo do teste).
- **Embeddings:** OpenAI `text-embedding-3-small`.
- **Top-K:** 2 documentos mais relevantes por consulta.

### Processamento Síncrono vs Assíncrono

A arquitetura utiliza rotas assíncronas (`async def`) no FastAPI para a comunicação de I/O de rede com o provedor do LLM, evitando o bloqueio da main thread e permitindo alta concorrência. A execução no banco de dados é tratada de forma a garantir a estabilidade do pool de conexões.

## 3. Estratégias de Mitigação de Riscos e Segurança

Para garantir a integridade dos dados e prevenir ataques de injeção:

- **Isolamento de Credenciais:** O acesso ocorre via um usuário estritamente de leitura (`user_read_only`).
- **Validação na Camada de Aplicação:** Implementação de Guardrails baseados em expressões regulares que bloqueiam palavras-chave destrutivas (`DROP`, `DELETE`, `ALTER`, etc.) e verificam se as tabelas acessadas pertencem ao escopo do negócio (`customers`, `orders`, `order_details`, `products`, `employees`, `suppliers`, `shippers`, `invoices`, `purchase_orders`).
- **Function Calling contra Prompt Injection:** Forçar o LLM a operar através de uma ferramenta (`tool_choice`) reduz drasticamente a superfície de ataque para comandos maliciosos disfarçados de perguntas de negócios.

## 4. Escalabilidade e Custo Operacional

A aplicação é **stateless** (com exceção do cache, que pode ser externalizado para um cluster Redis), tornando-a perfeitamente adequada para:

- **Conteinerização** (Docker) e orquestração horizontal (Kubernetes/AWS ECS).
- **Previsibilidade de custos (FinOps):** A estratégia combinada de Function Calling rigoroso com Cache de Queries garante previsibilidade nos custos operacionais do provedor de LLM.
- **Pool de conexões:** SQLAlchemy com `pool_size=5` e `max_overflow=10` para gerenciar conexões ao banco de forma eficiente.
