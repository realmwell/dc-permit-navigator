#!/usr/bin/env python3
"""
Build FAISS-compatible vector index from the DC permit database.

Reads data/permits.json, chunks each permit into semantic documents,
embeds them via Bedrock Titan Embeddings v2, and writes:
  - data/embeddings/permits.index (binary vector index)
  - data/embeddings/chunks.json (chunk text + metadata)

Run locally before deployment. One-time cost: ~$0.01 for 103 permits.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --upload BUCKET_NAME
"""

import argparse
import json
import os
import struct
import sys
import time
from pathlib import Path

import boto3

# Titan Embeddings v2 config
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIMENSIONS = 256  # smallest option, plenty for ~100 docs
BATCH_DELAY = 0.1  # seconds between API calls to be polite


def load_permits(permits_path="data/permits.json"):
    """Load the permit database."""
    with open(permits_path) as f:
        data = json.load(f)

    # Build agency lookup
    agencies = {a["id"]: a for a in data["agencies"]}
    return data["permits"], agencies


def chunk_permit(permit, agencies):
    """
    Turn a single permit into one or more text chunks for embedding.

    For our ~103 permit dataset, one chunk per permit is sufficient.
    Each chunk contains all searchable information about the permit.
    """
    agency = agencies.get(permit.get("agency", ""), {})
    agency_name = agency.get("name", "Unknown Agency")
    formerly = agency.get("formerly", "")

    parts = []
    parts.append(f"Permit: {permit['name']}")
    parts.append(f"Category: {permit.get('category', 'N/A')}")
    parts.append(f"Agency: {agency_name}")
    if formerly:
        parts.append(f"(Formerly: {formerly})")
    parts.append(f"Description: {permit.get('description', 'N/A')}")

    if permit.get("requirements"):
        parts.append(f"Requirements: {permit['requirements']}")

    if permit.get("fees"):
        parts.append(f"Fees: {permit['fees']}")

    if permit.get("processing_time"):
        parts.append(f"Processing Time: {permit['processing_time']}")

    if permit.get("how_to_apply"):
        parts.append(f"How to Apply: {permit['how_to_apply']}")

    if permit.get("apply_url"):
        parts.append(f"Application URL: {permit['apply_url']}")

    if permit.get("notes"):
        parts.append(f"Notes: {permit['notes']}")

    if permit.get("related_permits"):
        parts.append(f"Related Permits: {', '.join(permit['related_permits'])}")

    text = "\n".join(parts)

    return [
        {
            "text": text,
            "permit_id": permit["id"],
            "permit_name": permit["name"],
            "category": permit.get("category", ""),
            "agency": agency_name,
        }
    ]


def embed_text(bedrock, text):
    """Embed a single text string via Bedrock Titan Embeddings v2."""
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(
            {
                "inputText": text,
                "dimensions": EMBEDDING_DIMENSIONS,
                "normalize": True,
            }
        ),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def build_index(permits_path="data/permits.json", output_dir="data/embeddings"):
    """Build the vector index from the permit database."""
    print(f"Loading permits from {permits_path}...")
    permits, agencies = load_permits(permits_path)
    print(f"Loaded {len(permits)} permits from {len(agencies)} agencies")

    # Chunk all permits
    print("Chunking permits...")
    all_chunks = []
    for permit in permits:
        chunks = chunk_permit(permit, agencies)
        all_chunks.extend(chunks)
    print(f"Created {len(all_chunks)} chunks")

    # Embed all chunks
    print(f"Embedding {len(all_chunks)} chunks via Bedrock Titan v2...")
    bedrock = boto3.client("bedrock-runtime")

    vectors = []
    for i, chunk in enumerate(all_chunks):
        if i > 0 and i % 10 == 0:
            print(f"  Embedded {i}/{len(all_chunks)}...")

        vec = embed_text(bedrock, chunk["text"])
        vectors.append(vec)
        time.sleep(BATCH_DELAY)

    print(f"  Embedded {len(all_chunks)}/{len(all_chunks)} - Done!")

    # Save index and chunks
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save binary vector index
    # Format: 4 bytes num_vectors, 4 bytes dimensions, then float32 vectors
    index_path = output_path / "permits.index"
    with open(index_path, "wb") as f:
        f.write(struct.pack("I", len(vectors)))
        f.write(struct.pack("I", EMBEDDING_DIMENSIONS))
        for vec in vectors:
            f.write(struct.pack(f"{EMBEDDING_DIMENSIONS}f", *vec))

    index_size = index_path.stat().st_size
    print(f"Saved index: {index_path} ({index_size:,} bytes)")

    # Save chunks JSON (text + metadata, no vectors)
    chunks_path = output_path / "chunks.json"
    with open(chunks_path, "w") as f:
        json.dump(all_chunks, f, indent=2)

    chunks_size = chunks_path.stat().st_size
    print(f"Saved chunks: {chunks_path} ({chunks_size:,} bytes)")

    # Cost estimate
    total_tokens = sum(len(c["text"].split()) * 1.3 for c in all_chunks)  # rough estimate
    cost = (total_tokens / 1000) * 0.00002
    print(f"\nEstimated embedding cost: ~${cost:.4f}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Vector dimensions: {EMBEDDING_DIMENSIONS}")

    return index_path, chunks_path


def upload_to_s3(bucket_name, index_path, chunks_path):
    """Upload index and chunks to S3."""
    s3 = boto3.client("s3")

    print(f"\nUploading to s3://{bucket_name}/...")

    s3.upload_file(
        str(index_path),
        bucket_name,
        "data/embeddings/permits.index",
        ExtraArgs={"ContentType": "application/octet-stream"},
    )
    print(f"  Uploaded {index_path}")

    s3.upload_file(
        str(chunks_path),
        bucket_name,
        "data/embeddings/chunks.json",
        ExtraArgs={"ContentType": "application/json"},
    )
    print(f"  Uploaded {chunks_path}")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build vector index for DC Permit Navigator")
    parser.add_argument("--permits", default="data/permits.json", help="Path to permits.json")
    parser.add_argument("--output", default="data/embeddings", help="Output directory")
    parser.add_argument("--upload", metavar="BUCKET", help="Upload to S3 bucket after building")
    args = parser.parse_args()

    index_path, chunks_path = build_index(args.permits, args.output)

    if args.upload:
        upload_to_s3(args.upload, index_path, chunks_path)
