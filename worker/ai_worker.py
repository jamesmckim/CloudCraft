# worker/ai_worker.py
import os
from celery import Celery
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from openai import OpenAI

# --- Configs ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-db:6333")
LLM_URL = os.getenv("LLM_URL", "http://host.docker.internal:1234/v1")

# Initialize the OpenAI Client to point to your local machine
client = OpenAI(
    base_url=LLM_URL, 
    api_key="dummy-key-not-checked"
)

# --- Initialize ---
celery_app = Celery("ai_worker", broker=REDIS_URL, backend=REDIS_URL)
qdrant = QdrantClient(url=QDRANT_URL)

COLLECTION_NAME = "server_knowledge"

def get_embedding(text: str) -> list:
    """Calls OpenAI to convert text into a numeric vector array."""
    response = client.embeddings.create(
        input=text,
        model="nomic-embed-text"
    )
    return response.data[0].embedding

def setup_collection():
    if not qdrant.collection_exists(COLLECTION_NAME):
        sample_embedding = get_embedding("test")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=len(sample_embedding), distance=Distance.COSINE),
        )

# --- THE CELERY TASK ---
@celery_app.task(name="analyze_logs_with_rag")
def analyze_logs_with_rag_task(server_id: str, log_context: list, error_line: str):
    setup_collection()
    print(f"[{server_id}] Worker pulled RAG task from Redis. Trigger: {error_line}")
    
    # 1. RETRIEVAL
    error_vector = get_embedding(error_line)
    retrieved_docs_text = "No historical documentation found."

    if error_vector:
        search_results = qdrant.query_points(
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
        response = client.chat.completions.create(
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