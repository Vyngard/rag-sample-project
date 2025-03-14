import sys
import os
import json
import asyncio
import pika
import traceback
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.embedding_service import get_embedding, save_embedding
from app.core.database import Base

# Create database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Process a document by generating and saving its embedding
async def process_document(document_id, content, metadata):
    print(f"Processing document ID {document_id}")

    try:
        # Get embedding vector for the document
        print(f"Generating embedding using {settings.EMBEDDING_MODEL}")
        embedding_vector = await get_embedding(content)

        # Verify embedding dimensions
        dimensions = len(embedding_vector)
        print(f"Generated embedding with {dimensions} dimensions")

        # Save the embedding to the database
        db = SessionLocal()
        try:
            save_embedding(db, document_id, embedding_vector)
            print(f"Successfully processed document ID {document_id}")
        except Exception as e:
            print(f"Database error processing document ID {document_id}: {str(e)}")
            traceback.print_exc()
            raise
        finally:
            db.close()
    except Exception as e:
        print(f"Error processing document ID {document_id}: {str(e)}")
        traceback.print_exc()
        raise

# Callback function for processing messages from RabbitMQ
def callback(ch, method, properties, body):
    try:
        # Parse message
        message = json.loads(body)
        document_id = message["document_id"]
        content = message["content"]
        metadata = message.get("metadata", {})

        print(f"Received message for document {document_id}")

        # Process document asynchronously
        asyncio.run(process_document(document_id, content, metadata))

        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Successfully processed message for document {document_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding message: {str(e)}")
        print(f"Message body: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        traceback.print_exc()
        # Negative acknowledgment - message will be requeued
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# Start the worker to consume messages from RabbitMQ
def start_worker():
    try:
        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )

        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare queue
        channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)

        # Set quality of service
        channel.basic_qos(prefetch_count=1)

        # Set up consumer
        channel.basic_consume(
            queue=settings.RABBITMQ_QUEUE,
            on_message_callback=callback
        )

        print("Worker started. Waiting for messages...")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Worker error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        start_worker()
    except KeyboardInterrupt:
        print("Worker stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting worker: {str(e)}")
        traceback.print_exc()
        sys.exit(1)