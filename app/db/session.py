from sqlalchemy import create_engine
from app.core.config import settings

# Criamos a engine do SQLAlchemy usando a DATABASE_URL definida nas configurações.
# A URL já contém o host, usuário, senha e banco fornecidos no desafio.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True, # Verifica se a conexão está ativa antes de usá-la (evita erros de "MySQL server has gone away")
    pool_size=5,        # Tamanho do pool de conexões (ajustável para escala)
    max_overflow=10
)