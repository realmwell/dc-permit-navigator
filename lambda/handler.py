"""
DC Permit Navigator - RAG Query Lambda

Handles natural language questions about DC permits by:
1. Loading pre-built FAISS index from S3 (cached in /tmp)
2. Embedding the user's query via Bedrock Titan Embeddings v2
3. Searching FAISS for top-k most relevant permit chunks
4. Generating a natural language answer via Bedrock Claude Haiku
"""

import json
import os
import struct
import tempfile
import time
import traceback
from pathlib import Path

import boto3

# Lazy-loaded globals (persist across warm invocations)
_faiss_index = None
_chunks = None
_bedrock = None
_s3 = None

BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
INDEX_KEY = os.environ.get("INDEX_KEY", "data/embeddings/permits.index")
CHUNKS_KEY = os.environ.get("CHUNKS_KEY", "data/embeddings/chunks.json")

EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
LLM_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"

TOP_K = 5
MAX_DAILY_QUERIES = 200  # Cost protection

# Simple daily counter file in /tmp
COUNTER_FILE = "/tmp/query_counter.json"


def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def get_bedrock():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime")
    return _bedrock


def load_index():
    """Load FAISS index and chunks from S3, caching in /tmp."""
    global _faiss_index, _chunks

    if _faiss_index is not None and _chunks is not None:
        return

    s3 = get_s3()

    # Download chunks
    chunks_path = "/tmp/chunks.json"
    if not Path(chunks_path).exists():
        s3.download_file(BUCKET_NAME, CHUNKS_KEY, chunks_path)

    with open(chunks_path) as f:
        _chunks = json.load(f)

    # Download FAISS index (stored as raw float32 vectors + metadata)
    index_path = "/tmp/permits.index"
    if not Path(index_path).exists():
        s3.download_file(BUCKET_NAME, INDEX_KEY, index_path)

    # Load our simple vector index (no faiss dependency needed for small datasets)
    with open(index_path, "rb") as f:
        data = f.read()

    # Format: 4 bytes num_vectors, 4 bytes dimensions, then float32 vectors
    num_vectors = struct.unpack("I", data[:4])[0]
    dimensions = struct.unpack("I", data[4:8])[0]

    vectors = []
    offset = 8
    for i in range(num_vectors):
        vec = struct.unpack(f"{dimensions}f", data[offset : offset + dimensions * 4])
        vectors.append(vec)
        offset += dimensions * 4

    _faiss_index = {"vectors": vectors, "dimensions": dimensions}
    print(f"Loaded {num_vectors} vectors with {dimensions} dimensions")


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_index(query_vector, top_k=TOP_K):
    """Search the vector index for most similar chunks."""
    if _faiss_index is None:
        return []

    similarities = []
    for i, vec in enumerate(_faiss_index["vectors"]):
        sim = cosine_similarity(query_vector, vec)
        similarities.append((i, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def embed_text(text):
    """Embed text using Bedrock Titan Embeddings v2."""
    bedrock = get_bedrock()

    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text, "dimensions": 256, "normalize": True}),
    )

    result = json.loads(response["body"].read())
    return result["embedding"]


def generate_answer(question, context_chunks):
    """Generate answer using Bedrock Claude Haiku."""
    bedrock = get_bedrock()

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are the DC Permit Navigator, a helpful assistant that answers questions about Washington DC government permits, licenses, and certifications.

You have access to a database of 103+ DC permits across 16 agencies. Use ONLY the provided context to answer questions. If the context doesn't contain enough information to fully answer the question, say so and suggest which agency to contact.

Rules:
- Be specific: include permit names, agencies, fees, requirements, and application URLs when available
- If multiple permits might be needed, list all of them
- Always mention the issuing agency by full name
- Include direct links to apply when available
- If you're not sure, say so — don't guess about government requirements
- Be concise but thorough
- Format your response with markdown for readability

Context from permit database:
{context}

User question: {question}"""

    response = bedrock.invoke_model(
        modelId=LLM_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def check_rate_limit():
    """Simple daily rate limiter using a file in /tmp."""
    today = time.strftime("%Y-%m-%d")

    try:
        with open(COUNTER_FILE) as f:
            counter = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        counter = {"date": today, "count": 0}

    if counter.get("date") != today:
        counter = {"date": today, "count": 0}

    if counter["count"] >= MAX_DAILY_QUERIES:
        return False

    counter["count"] += 1
    with open(COUNTER_FILE, "w") as f:
        json.dump(counter, f)

    return True


def cors_response(status_code, body):
    """Return a response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """Main Lambda handler."""

    # Handle CORS preflight
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return cors_response(200, {"message": "OK"})

    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))
        question = body.get("question", "").strip()

        if not question:
            return cors_response(400, {"error": "Question is required"})

        if len(question) > 500:
            return cors_response(400, {"error": "Question too long (max 500 characters)"})

        # Rate limit check
        if not check_rate_limit():
            return cors_response(
                429,
                {
                    "error": "Daily query limit reached. Try again tomorrow.",
                    "answer": "I've reached my daily query limit to keep costs manageable. This is a free, open-source project. Please try again tomorrow, or browse the permit directory on the main page for the information you need.",
                },
            )

        # Load index (cached after first invocation)
        load_index()

        # Embed the question
        query_vector = embed_text(question)

        # Search for relevant chunks
        results = search_index(query_vector)

        # Get the text of matching chunks
        context_chunks = []
        source_permits = []
        for idx, score in results:
            if idx < len(_chunks):
                chunk = _chunks[idx]
                context_chunks.append(chunk["text"])
                if chunk.get("permit_id") not in [s.get("permit_id") for s in source_permits]:
                    source_permits.append(
                        {
                            "permit_id": chunk.get("permit_id"),
                            "permit_name": chunk.get("permit_name"),
                            "agency": chunk.get("agency"),
                            "score": round(score, 3),
                        }
                    )

        # Generate answer
        answer = generate_answer(question, context_chunks)

        return cors_response(
            200,
            {
                "answer": answer,
                "sources": source_permits,
                "query": question,
            },
        )

    except Exception as e:
        traceback.print_exc()
        return cors_response(
            500,
            {
                "error": "Something went wrong. Please try again.",
                "detail": str(e),
            },
        )
