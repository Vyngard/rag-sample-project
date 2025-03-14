from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, MetaData, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    meta_info = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default="CURRENT_TIMESTAMP")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    # We don't define a real SQLAlchemy type for vector, we'll handle it with raw SQL
    # But keep the column for schema reflection
    embedding = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default="CURRENT_TIMESTAMP")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()