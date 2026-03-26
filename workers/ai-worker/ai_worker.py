# worker/ai_worker.py
import os
import asyncio
from typing import Dict, Any
from arq.connections import RedisSettings
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from openai import AsyncOpenAI

# --- Configs ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-db:6333")
LLM_URL = os.getenv("LLM_URL", "http://host.docker.internal:1234/v1")
COLLECTION_NAME = "server_knowledge"

async def startup(ctx: Dict[Any, Any]) -> None:
    print("Starting AI RAG Worker. Initializing clients...")
    
    # Initialize Async Clients
    llm_client = AsyncOpenAI(base_url=LLM_URL, api_key="dummy-key-not-checked")
    qdrant_client = AsyncQdrantClient(url=QDRANT_URL)
    
    # Run setup once on boot
    if not await qdrant_client.collection_exists(COLLECTION_NAME):
        sample_response = await llm_client.embeddings.create(input="test", model="nomic-embed-text")
        sample_embedding = sample_response.data[0].embedding
        
        await qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=len(sample_embedding), distance=Distance.COSINE),
        )
    
    # Attach clients to context for reuse in tasks
    ctx['llm'] = llm_client
    ctx['qdrant'] = qdrant_client
    print("Worker initialization complete.")

async def shutdown(ctx: Dict[Any, Any]) -> None:
    print("Shutting down worker. Closing connections...")
    await ctx['llm'].close()
    # Qdrant async client handles its own cleanup natively

async def get_embedding(client: AsyncOpenAI, text: str) -> list:
    """Calls OpenAI to convert text into a numeric vector array."""
    response = await client.embeddings.create(
        input=text,
        model="nomic-embed-text"
    )
    return response.data[0].embedding

async def analyze_logs_with_rag(ctx: Dict[Any, Any], server_id: str, log_context: list, error_line: str):
    llm = ctx['llm']
    qdrant = ctx['qdrant']
    
    print(f"[{server_id}] Worker pulled RAG task from Redis. Trigger: {error_line}")
    
    # 1. RETRIEVAL
    error_vector = await get_embedding(llm, error_line)
    retrieved_docs_text = "No historical documentation found."

    if error_vector:
        search_results = await qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=error_vector,
            limit=3
        )
        if search_results.points:
            retrieved_docs_text = "\n\n".join([hit.payload["text"] for hit in search_results])

    # 2. GENERATION
    log_text = "\n".join(log_context)
    
    # OpenAI uses a strict System/User messaging structure
    messages = [
        {
            "role": "system", 
            "content": (
                "You are an expert game server administrator. Identify the root cause of the "
                "server crash and provide a short, actionable recommendation under 3 sentences."
            )
        },
        {
            "role": "user",
            "content": f"""
            Official documentation Context:
            {retrieved_docs_text}
            
            Server logs leading up to the crash:
            {log_text}
            
            Error line detected: "{error_line}"
            """
        }
    ]

    try:
        response = await llm.chat.completions.create(
            model="phi3",
            messages=messages,
            temperature=0.2 # Keep it analytical and factual
        )
        
        ai_recommendation = response.choices[0].message.content.strip()
        print(f"[{server_id}] AI generation complete. Returning result to broker.")
        
        return {
            "status": "success",
            "server_id": server_id,
            "error_line": error_line,
            "recommendation": ai_recommendation
        }
        
    except Exception as e:
        error_msg = f"Worker failed to process AI request: {str(e)}"
        print(f"[{server_id}] {error_msg}")
        return {
            "status": "error",
            "server_id": server_id,
            "error_line": error_line,
            "error_message": error_msg
        }

class WorkerSettings:
    functions = [analyze_logs_with_rag]
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown