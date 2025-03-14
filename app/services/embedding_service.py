import httpx
import json
from sqlalchemy.orm import Session
import traceback
from app.core.config import settings

# Get embedding vector from OpenAI's text-embedding-3-small model
async def get_embedding(text: str):
    try:
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key is required for embeddings but not provided")

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": text
        }

        url = "https://api.openai.com/v1/embeddings"

        print(f"Getting embedding using {settings.EMBEDDING_MODEL} for: '{text[:50]}...'")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload
            )

            print(f"Response status: {response.status_code}")

            if response.status_code != 200:
                error_message = f"OpenAI API returned status code {response.status_code}"
                if response.text:
                    error_message += f": {response.text}"
                raise Exception(error_message)

            # Parse response
            data = response.json()

            # Validate response format
            if "data" not in data or not data["data"] or "embedding" not in data["data"][0]:
                raise Exception(f"Unexpected response format from OpenAI API: {data}")

            embedding_vector = data["data"][0]["embedding"]
            dimensions = len(embedding_vector)
            print(f"Successfully retrieved embedding vector with {dimensions} dimensions")

            # Verify dimensions match expected
            if dimensions != settings.EMBEDDING_DIMENSION:
                print(
                    f"Warning: Retrieved embedding has {dimensions} dimensions, but config expected {settings.EMBEDDING_DIMENSION}")

            return embedding_vector
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        traceback.print_exc()
        raise

# Save embedding using raw connection execution
def save_embedding(db: Session, document_id: int, embedding_vector):
    try:
        # Convert embedding vector to a string representation
        vector_str = json.dumps(embedding_vector)
        dimensions = len(embedding_vector)

        # Get a raw connection from the session
        connection = db.connection()

        # Execute using psycopg2 directly
        cursor = connection.connection.cursor()
        cursor.execute(
            "INSERT INTO embeddings (document_id, embedding) VALUES (%s, %s::vector)",
            (document_id, vector_str)
        )

        db.commit()
        print(f"Saved embedding for document ID {document_id} with {dimensions} dimensions")
    except Exception as e:
        print(f"Error saving embedding: {str(e)}")
        traceback.print_exc()
        db.rollback()
        raise

# Search for similar documents using raw connection execution (same as save_embedding)
def search_similar_documents(db: Session, query_embedding, top_k=3):
    try:
        # Convert embedding vector to a string representation
        vector_str = json.dumps(query_embedding)

        # Get a raw connection from the session
        connection = db.connection()

        # Execute using psycopg2 directly
        cursor = connection.connection.cursor()
        cursor.execute(
            """
            SELECT 
                d.id, 
                d.content, 
                d.meta_info,  
                d.created_at,
                1 - (e.embedding <=> %s::vector) AS similarity
            FROM 
                embeddings e
            JOIN 
                documents d ON e.document_id = d.id
            ORDER BY 
                similarity DESC
            LIMIT %s
            """,
            (vector_str, top_k)
        )

        # Fetch all results
        rows = cursor.fetchall()

        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]

        # Format the results into a list of dictionaries
        documents = []
        for row in rows:
            doc = {}
            for i, col_name in enumerate(column_names):
                doc[col_name] = row[i]
            documents.append(doc)

        print(f"Found {len(documents)} similar documents")
        return documents
    except Exception as e:
        print(f"Error searching for similar documents: {str(e)}")
        traceback.print_exc()
        raise