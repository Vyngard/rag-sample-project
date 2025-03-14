from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import traceback

from app.core.config import settings
from app.core.database import get_db
from app.api.models import DocumentCreate, Document, Query, RAGResponse
from app.services import document_service, embedding_service, llm_service

router = APIRouter()


# Create a new document and queue it for embedding
@router.post("/documents/", response_model=Document)
def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    try:
        return document_service.create_document(db, document)
    except Exception as e:
        print(f"Error creating document: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document: {str(e)}"
        )

# Retrieve all documents with pagination
@router.get("/documents/", response_model=List[Document])
def read_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        documents = document_service.get_documents(db, skip=skip, limit=limit)
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

# Retrieve a specific document by ID
@router.get("/documents/{document_id}", response_model=Document)
def read_document(document_id: int, db: Session = Depends(get_db)):
    try:
        db_document = document_service.get_document(db, document_id=document_id)
        if db_document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return db_document
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving document: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )

# Query documents using RAG
@router.post("/query/", response_model=RAGResponse)
async def query_documents(query: Query, db: Session = Depends(get_db)):
    try:
        print(f"Processing query: '{query.query}'")
        print(f"Using embedding model: {settings.EMBEDDING_MODEL}")

        # Get embedding for the query
        query_embedding = await embedding_service.get_embedding(query.query)
        print(f"Generated embedding for query with {len(query_embedding)} dimensions")

        # Search for similar documents
        similar_docs = embedding_service.search_similar_documents(db, query_embedding, top_k=query.top_k)
        print(f"Found {len(similar_docs)} similar documents")

        # If no similar documents found
        if not similar_docs:
            print("No similar documents found")
            return RAGResponse(
                answer="I don't have enough information to answer that question.",
                sources=[]
            )

        # Extract content from similar documents
        contexts = [doc["content"] for doc in similar_docs]

        # Generate response using LLM
        print(f"Generating response using model: {query.model}")
        answer = await llm_service.generate_rag_response(query.query, contexts, model=query.model)

        # Get full document objects for the sources
        document_ids = [doc["id"] for doc in similar_docs]
        source_documents = document_service.get_documents_by_ids(db, document_ids)

        print(f"Returning response with {len(source_documents)} source documents")
        return RAGResponse(
            answer=answer,
            sources=source_documents
        )
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )