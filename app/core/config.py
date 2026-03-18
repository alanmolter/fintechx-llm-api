"""
config.py - Configurações centralizadas da aplicação.

Carrega variáveis de ambiente do arquivo .env e disponibiliza
todas as configurações necessárias (banco de dados, LLM, etc.)
através de um objeto singleton 'settings'.
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente do sistema operacional.
# Isso permite que os segredos (senhas, API keys) fiquem fora do código-fonte.
load_dotenv()


class Settings:
    """Classe que centraliza todas as configurações da aplicação."""

    PROJECT_NAME: str = "FinTechX Text-to-SQL API"

    # --- Banco de Dados MySQL (Northwind) ---
    # As credenciais são lidas do .env. Não há valores default para evitar
    # exposição acidental de senhas no código-fonte.
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")

    # URL de conexão no formato exigido pelo SQLAlchemy + driver PyMySQL
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # --- Provedor LLM (OpenAI) ---
    LLM_API_KEY = os.getenv("LLM_API_KEY")


# Instância única utilizada em toda a aplicação
settings = Settings()
