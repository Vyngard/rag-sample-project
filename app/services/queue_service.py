import pika
import json
from app.core.config import settings


def get_connection():
    credentials = pika.PlainCredentials(
        username=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )

    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials
    )

    return pika.BlockingConnection(parameters)

# Publish document to the queue for processing
def publish_document(document_id: int, content: str, metadata=None):
    if metadata is None:
        metadata = {}

    connection = get_connection()
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)

    # Prepare message
    message = {
        "document_id": document_id,
        "content": content,
        "metadata": metadata
    }

    # Publish message
    channel.basic_publish(
        exchange='',
        routing_key=settings.RABBITMQ_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )

    print(f"Document {document_id} sent to queue")
    connection.close()