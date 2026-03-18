# FinTechX - Text-to-SQL LLM API

Este repositório contém a solução para o desafio técnico da **Laborit**, que consiste no desenvolvimento de uma API baseada em LLM capaz de traduzir perguntas analíticas em linguagem natural para consultas SQL otimizadas e seguras. A API se conecta ao banco de dados `northwind` e foi projetada com foco em escala, confiabilidade e custo operacional.

---

## Arquitetura da Solução

> O desenho de arquitetura é obrigatório conforme os critérios do desafio.

![Diagrama de Arquitetura](./docs/arquitetura.png)

Para mais detalhes sobre decisões técnicas, fluxo da requisição, estratégias de escalabilidade e segurança, consulte o [Documento de Arquitetura](./ARCHITECTURE.MD).

### Fluxo da Requisição

1. O usuário envia uma pergunta em linguagem natural (ex: *"Qual o ticket médio?"*) via endpoint `POST /api/v1/query`.
2. A aplicação verifica o **Cache em Memória**. Se houver um *Hit*, a query SQL em cache é executada diretamente no banco de dados.
3. Em caso de *Miss*, a pergunta passa pelo **RAG (ChromaDB)** para recuperar o contexto de negócios da FinTechX.
4. O prompt enriquecido é enviado ao LLM (OpenAI) utilizando **Function Calling** para garantir um retorno estruturado (JSON com SQL e Explicação).
5. A query gerada passa por **Guardrails de Segurança**, bloqueando comandos DDL/DML.
6. A query validada é executada no banco MySQL e os dados são retornados ao usuário com a explicação contextualizada.

### Decisões Técnicas e Justificativas

- **Function Calling:** Escolhido em detrimento do *prompt engineering* tradicional para garantir previsibilidade e evitar quebras de parsing no backend.
- **Cache Inteligente (Hash de SQL):** O cache armazena a string SQL atrelada à pergunta, e não os dados finais. Isso zera o custo de tokens e a latência de chamadas à API do LLM para perguntas repetidas, mantendo os dados de resposta sempre atualizados em tempo real.
- **Busca Vetorial (RAG):** Utilizada para injetar dicionários de dados e regras de negócio específicas da FinTechX (ex: cálculo de ticket médio) apenas quando necessário, economizando tokens no prompt e evitando alucinações.
- **Segurança e Guardrails:** Aplicação do princípio de defesa em profundidade. Mesmo utilizando o usuário `user_read_only`, a aplicação possui regex estrito para barrar comandos como `DROP` ou `UPDATE` e validar o escopo das tabelas do Northwind.
- **Processamento Assíncrono:** Requisições assíncronas para comunicação de rede (LLM) garantem alta concorrência, enquanto a comunicação com o banco utiliza pool de conexões otimizado via `SQLAlchemy`.

---

## Como Executar o Projeto Localmente

### Pré-requisitos

- Python 3.10+
- Conta na OpenAI (para a chave da API)

### Passo a Passo

1. **Clone o repositório:**

```bash
git clone https://github.com/alanmolter/laborit.git
cd laborit
```

2. **Crie e ative o ambiente virtual:**

```bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e insira sua chave da OpenAI:

```
LLM_API_KEY=sua_chave_openai_aqui
```

5. **Execute a aplicação:**

```bash
uvicorn app.main:app --reload
```

6. **Acesse a Documentação Interativa (Swagger):**

Abra o navegador em: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Testes

O projeto possui testes automatizados para os guardrails de segurança e o serviço de cache:

```bash
pytest tests/ -v
```

---

## CI/CD e Deploy na Nuvem

Como diferencial, este projeto possui uma esteira de CI/CD automatizada utilizando **GitHub Actions**.

Qualquer push na branch `main` dispara:

1. Verificação de ambiente e instalação de dependências.
2. Execução de testes automatizados com `pytest`.
3. Deploy contínuo via webhook no servidor de produção (Render).

---

## Estrutura do Projeto

```
laborit/
├── .github/workflows/deploy.yml    # CI/CD Pipeline
├── .env.example                    # Template de variáveis de ambiente
├── ARCHITECTURE.MD                 # Documento técnico de arquitetura
├── README.md                       # Este documento
├── requirements.txt                # Dependências Python
├── docs/
│   └── arquitetura.png             # Diagrama de arquitetura
├── app/
│   ├── __init__.py
│   ├── main.py                     # Entry point FastAPI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Configurações e env vars
│   │   └── security.py             # Guardrails de validação SQL
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py              # Engine SQLAlchemy
│   │   └── repository.py           # Execução de queries
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Modelos Pydantic
│   ├── routers/
│   │   ├── __init__.py
│   │   └── query.py                # Endpoints da API
│   └── services/
│       ├── __init__.py
│       ├── llm_service.py          # Integração OpenAI + Function Calling
│       ├── rag_service.py          # ChromaDB + Busca Vetorial
│       └── cache_service.py        # Cache inteligente em memória
├── tests/
│   ├── __init__.py
│   ├── test_security.py            # Testes dos guardrails
│   └── test_cache.py               # Testes do cache
└── Development Assessment (Dev Back).pdf
```

---

Feito com dedicação para o desafio do Círculo LAB.
