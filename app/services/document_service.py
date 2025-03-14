from sqlalchemy.orm import Session
from app.core.database import Document
from app.api.models import DocumentCreate
from app.services.queue_service import publish_document

# Create a document and send it to the processing queue
def create_document(db: Session, document: DocumentCreate):
    db_document = Document(
        content=document.content,
        meta_info=document.meta_info
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # Publish to queue for processing
    publish_document(
        document_id=db_document.id,
        content=db_document.content,
        metadata=db_document.meta_info
    )

    return db_document

# Get a document by ID
def get_document(db: Session, document_id: int):
    return db.query(Document).filter(Document.id == document_id).first()

# Get all documents with pagination
def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Document).offset(skip).limit(limit).all()

# Get documents by list of IDs
def get_documents_by_ids(db: Session, document_ids: list):
    return db.query(Document).filter(Document.id.in_(document_ids)).all()