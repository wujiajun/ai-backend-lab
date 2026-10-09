from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_backend_lab.config import load_settings

settings = load_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)

session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
