"""
session.py - Configuração da engine de conexão com o banco de dados.

Cria a engine do SQLAlchemy que gerencia o pool de conexões com o
banco MySQL Northwind. A engine é reutilizada em toda a aplicação
para garantir eficiência e estabilidade nas conexões.
"""

from sqlalchemy import create_engine
from app.core.config import settings

# A engine gerencia um pool de conexões com o MySQL.
# - pool_pre_ping: testa se a conexão está ativa antes de usá-la
#   (evita erros "MySQL server has gone away" em conexões ociosas).
# - pool_size: número de conexões mantidas no pool (5 simultâneas).
# - max_overflow: conexões extras permitidas além do pool_size em picos de uso.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)
