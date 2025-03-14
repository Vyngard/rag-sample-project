# RAG System: Document Retrieval and Question Answering

A Retrieval Augmented Generation (RAG) system built with FastAPI, PostgreSQL with pgvector, RabbitMQ, and OpenAI. This system allows you to ingest documents, automatically embed them into vector representations, and query them with natural language to receive relevant answers backed by your document base.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setting Up PostgreSQL](#setting-up-postgresql)
  - [Setting Up RabbitMQ](#setting-up-rabbitmq)
  - [Project Setup](#project-setup)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [API Usage](#api-usage)
  - [Adding Documents](#adding-documents)
  - [Querying the System](#querying-the-system)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

This RAG system enhances language model capabilities by retrieving relevant information from a document knowledge base before generating answers. When a query is received, the system:

1. Converts the query to a vector embedding
2. Searches for similar documents in the vector database
3. Retrieves the most relevant documents
4. Provides these documents as context to a language model
5. Returns both the generated answer and the source documents

## Features

- Asynchronous document processing using message queues
- Vector similarity search for efficient document retrieval
- Integration with OpenAI embeddings and language models
- Stateless design allowing horizontal scaling
- API endpoints for document management and querying
- Transparent source attribution in responses

## Technology Stack

- **FastAPI**: Modern, high-performance web framework for building APIs
- **PostgreSQL + pgvector**: Database with vector search capabilities
- **RabbitMQ**: Message broker for asynchronous processing
- **OpenAI API**: For generating embeddings and responses
- **Python 3.8+**: Core programming language
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping
- **Pydantic**: Data validation and settings management
- **HTTPX**: Asynchronous HTTP client for Python

## System Architecture

The system consists of these main components:

1. **API Server**: FastAPI application that handles HTTP requests
2. **Worker Process**: Background service that processes document embedding
3. **Message Queue**: RabbitMQ for communication between API and worker
4. **Vector Database**: PostgreSQL with pgvector for document storage and retrieval
5. **Embedding Service**: Converts text to vector representations
6. **LLM Service**: Generates responses based on retrieved documents

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- RabbitMQ 3.8+
- OpenAI API key

### Setting Up PostgreSQL

1. Install PostgreSQL:
   ```bash
   # For Windows: Download installer from postgresql.org
   # For Ubuntu
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. Start PostgreSQL service:
   ```bash
   # Windows
   # Start from Services application
   
   # Ubuntu
   sudo systemctl start postgresql
   ```

3. Connect to PostgreSQL and create a database:
   ```bash
   psql -U postgres
   CREATE DATABASE ragdb;
   \c ragdb
   ```

4. Install pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

5. Create necessary tables:
   ```sql
   CREATE TABLE documents (
       id SERIAL PRIMARY KEY,
       content TEXT NOT NULL,
       meta_info JSONB,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   CREATE TABLE embeddings (
       id SERIAL PRIMARY KEY,
       document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
       embedding vector(1536),
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   ```

### Setting Up RabbitMQ

1. Install RabbitMQ:
   ```bash
   # For Windows: Download installer from rabbitmq.com
   # For Ubuntu
   sudo apt update
   sudo apt install rabbitmq-server
   ```

2. Start RabbitMQ service:
   ```bash
   # Windows
   # Start from Services application
   
   # Ubuntu
   sudo systemctl start rabbitmq-server
   ```

3. Enable the management plugin (optional but recommended):
   ```bash
   rabbitmq-plugins enable rabbitmq_management
   ```
   
   This provides a web interface at http://localhost:15672/ (default credentials: guest/guest)

### Project Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rag-system.git
   cd rag-system
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pika python-dotenv openai sentence-transformers pydantic typing python-multipart httpx
   ```

4. Create a `.env` file in the project root:
   ```
   # PostgreSQL
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=ragdb
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432

   # RabbitMQ
   RABBITMQ_HOST=localhost
   RABBITMQ_PORT=5672
   RABBITMQ_USER=guest
   RABBITMQ_PASSWORD=guest
   RABBITMQ_QUEUE=document_queue

   # OpenAI API
   OPENAI_API_KEY=your_openai_api_key
   ```

## Configuration

The main configuration is handled in `app/core/config.py`. Key settings include:

- Database connection details
- RabbitMQ connection details
- OpenAI API key
- Embedding model and dimensions

You can customize these settings by modifying the `.env` file or directly in `config.py`.

## Running the System

The system requires running two processes:

1. Start the API server:
   ```bash
   # From project root
   python run_api.py
   ```
   The API server will be available at http://localhost:8000

2. Start the worker in a separate terminal:
   ```bash
   # From project root
   python run_worker.py
   ```

For development, you can use the `--reload` flag with uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

The API provides endpoints for document management and querying.

### Adding Documents

To add a document to the system:

```bash
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "RAG (Retrieval-Augmented Generation) is a technique that enhances language model responses by retrieving relevant information from a knowledge base. This allows the model to provide more accurate and up-to-date information without having to retrain the entire model.",
    "meta_info": {
      "source": "RAG documentation",
      "author": "AI Expert"
    }
  }'
```

### Querying the System

To query the system and get relevant answers:

```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG and why is it useful?",
    "top_k": 3,
    "model": "gpt-3.5-turbo"
  }'
```

Example response:

```json
{
  "answer": "RAG (Retrieval-Augmented Generation) is a technique that enhances language model responses by retrieving relevant information from a knowledge base. It is useful because it allows the model to provide more accurate and up-to-date information without requiring the entire model to be retrained.",
  "sources": [
    {
      "content": "RAG (Retrieval-Augmented Generation) is a technique that enhances language model responses by retrieving relevant information from a knowledge base. This allows the model to provide more accurate and up-to-date information without having to retrain the entire model.",
      "meta_info": {
        "author": "AI Expert",
        "source": "RAG documentation"
      },
      "id": 2,
      "created_at": "2023-07-15T07:04:34.224788-08:00"
    }
  ]
}
```

## Development

### Project Structure

```
rag-system/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py
│   │   └── models.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── llm_service.py
│   │   └── queue_service.py
│   └── main.py
├── worker/
│   ├── __init__.py
│   └── worker.py
├── .env
├── run_api.py
├── run_worker.py
└── requirements.txt
```

### Adding New Features

- **New Document Types**: Extend the `Document` model in `app/api/models.py`
- **Custom Embedding Logic**: Modify `app/services/embedding_service.py`
- **Different LLM Providers**: Update `app/services/llm_service.py`

## Troubleshooting

### Common Issues

1. **PostgreSQL Vector Issues**:
   - Ensure pgvector extension is installed
   - Check that vector dimensions match your embedding model (1536 for text-embedding-3-small)

2. **RabbitMQ Connection Issues**:
   - Verify RabbitMQ is running: `rabbitmqctl status`
   - Check credentials in `.env` file

3. **OpenAI API Issues**:
   - Verify API key in `.env` file
   - Check API quota and billing status

4. **Worker Not Processing Documents**:
   - Check RabbitMQ management interface for queued messages
   - Verify worker logs for errors

### Debugging

- Enable debug logs in FastAPI: Add `--log-level debug` to the uvicorn command
- Check worker logs for embedding generation issues
- Verify database connections by connecting directly with psql