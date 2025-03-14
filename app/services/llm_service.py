import httpx
from typing import List
import traceback
from app.core.config import settings

# Generate a response using OpenAI with context from retrieved documents
async def generate_rag_response(query: str, context: List[str], model: str = None):
    try:
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key is required but not provided")

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # Combine context into a single string
        context_text = "\n\n".join(context)

        # Create system prompt for RAG
        system_prompt = """You are an AI assistant that answers questions based on the provided context.
        If the answer cannot be found in the context, acknowledge that you don't know rather than making up information.
        Provide a clear, concise answer that directly addresses the question, citing relevant information from the context."""

        # Create the message payload
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",
             "content": f"Context information is below:\n\n{context_text}\n\nQuestion: {query}\n\nAnswer:"}
        ]

        # Use gpt-3.5-turbo for reliable completion
        openai_model = "gpt-3.5-turbo"

        payload = {
            "model": openai_model,
            "messages": messages
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )

            print(f"Response status code: {response.status_code}")

            # Log response content (limited to first 500 chars to avoid huge logs)
            response_text = response.text[:500] + ("..." if len(response.text) > 500 else "")
            print(f"Response content: {response_text}")

            if response.status_code != 200:
                error_message = f"OpenAI API returned status code {response.status_code}"
                if response.text:
                    error_message += f": {response.text}"
                raise Exception(error_message)

            # Parse response
            data = response.json()

            # Validate response format
            if "choices" not in data or not data["choices"] or "message" not in data["choices"][0]:
                print(f"Unexpected response format: {data}")
                raise Exception(f"Unexpected response format from OpenAI API: {data}")

            answer = data["choices"][0]["message"]["content"]
            print(f"Successfully generated answer: {answer[:100]}...")
            return answer
    except Exception as e:
        print(f"Error generating RAG response: {str(e)}")
        traceback.print_exc()

        # Return a more helpful error message that includes the context
        if context:
            return f"I encountered an issue when generating a response. However, I found relevant information that might help: \n\n{context[0]}"
        else:
            return "I'm sorry, I encountered an issue while processing your query. Please try again later."