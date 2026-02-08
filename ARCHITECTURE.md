# DC Permit Navigator - Architecture

## Overview

A serverless RAG (Retrieval-Augmented Generation) chatbot that helps people navigate DC's 103+ permits, licenses, and certifications across 16 agencies. Users ask natural language questions like "What permit do I need to open a restaurant?" and get accurate, sourced answers with direct links to apply.

## Design Principles

1. **Near-zero idle cost** - No always-on resources. Everything is pay-per-use.
2. **$5/month spending cap** - Hard cost ceiling via AWS Budgets + in-code rate limiting.
3. **AWS-native** - No external dependencies beyond AWS services.
4. **Simple** - Minimal moving parts. One Lambda, one S3 bucket, one CloudFront distribution.

## Architecture Diagram

```
                    ┌──────────────────────┐
                    │    CloudFront CDN     │
                    │  (static site cache)  │
                    └──────┬───────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌──────────────┐         ┌──────────────────┐
    │  S3 Bucket   │         │  Lambda Function │
    │ (static site │         │  (Function URL)  │
    │  + FAISS     │         │                  │
    │  index)      │         │  1. Load FAISS   │
    └──────────────┘         │     from S3/tmp  │
                             │  2. Embed query  │
                             │     (Bedrock     │
                             │      Titan v2)   │
                             │  3. Search FAISS │
                             │  4. Generate     │
                             │     answer       │
                             │     (Bedrock     │
                             │      Haiku)      │
                             └──────────────────┘
```

## Component Details

### 1. Data Layer (`data/`)

- **`permits.json`** - Manually curated database of 103 DC permits across 16 agencies
- **`embeddings/`** - Pre-computed FAISS index (built at deploy time, not runtime)
- Each permit is chunked into ~200-word documents covering: description, requirements, fees, how to apply, related permits

### 2. Embedding Pipeline (`scripts/build_index.py`)

- Runs locally or in CI at deploy time (NOT at query time)
- Uses Amazon Bedrock Titan Embeddings v2 ($0.00002/1K tokens)
- Chunks each permit into semantic documents
- Builds FAISS index and uploads to S3
- One-time cost: ~$0.01 for 103 permits

### 3. Query Lambda (`lambda/handler.py`)

- **Runtime**: Python 3.12
- **Memory**: 512MB (enough for FAISS index in memory)
- **Timeout**: 30s
- **Concurrency**: 1 (cost protection)
- **Trigger**: Lambda Function URL (FREE - no API Gateway needed)

Query flow:
1. Download FAISS index from S3 to `/tmp` on cold start (cached for warm invocations)
2. Embed user query using Bedrock Titan Embeddings v2
3. Search FAISS for top-5 most relevant permit chunks
4. Send retrieved context + user question to Bedrock Claude Haiku
5. Return structured answer with permit names, links, and next steps

### 4. Frontend (`site/`)

- Static HTML/CSS/JS on S3 behind CloudFront
- Simple chat interface (no framework needed)
- Calls Lambda Function URL directly
- Streaming responses via Lambda response streaming

### 5. Cost Controls

| Control | Mechanism |
|---------|-----------|
| Lambda concurrency | Reserved = 1 |
| Daily query cap | In-code counter (DynamoDB atomic counter or S3 object) |
| Monthly budget | AWS Budgets alarm at $4 |
| Billing alarm | CloudWatch alarm at $5 |
| No idle cost | All services are purely pay-per-use |

### 6. Cost Estimates

| Scenario | Monthly Cost |
|----------|-------------|
| Idle (zero traffic) | < $0.01 |
| 10 queries/day (Haiku) | ~$0.40 |
| 50 queries/day (Haiku) | ~$2.00 |
| 100 queries/day (Haiku) | ~$4.00 |

Breakdown per query (Claude Haiku):
- Titan embedding: ~$0.000004
- FAISS search: $0 (in-memory)
- Haiku input (~2K tokens context): ~$0.0005
- Haiku output (~300 tokens): ~$0.000375
- Lambda compute (~5s): ~$0.00004
- **Total per query: ~$0.001**

## Infrastructure (SAM/CloudFormation)

```yaml
Resources:
  # S3 bucket for static site + FAISS index
  SiteBucket:
    Type: AWS::S3::Bucket

  # CloudFront for CDN + HTTPS
  Distribution:
    Type: AWS::CloudFront::Distribution

  # Lambda for RAG queries
  QueryFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      MemorySize: 512
      Timeout: 30
      ReservedConcurrentExecutions: 1
      FunctionUrlConfig:
        AuthType: NONE
        Cors:
          AllowOrigins: ["*"]

  # Budget alarm
  BudgetAlarm:
    Type: AWS::Budgets::Budget
    Properties:
      Budget:
        BudgetLimit:
          Amount: 5
```

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Frontend | HTML/CSS/JS on S3 + CloudFront | ~$0/month |
| API | Lambda Function URL | FREE |
| Embeddings | Bedrock Titan Embeddings v2 | $0.00002/1K tokens |
| LLM | Bedrock Claude Haiku | $0.25/$1.25 per 1M tokens |
| Vector Search | FAISS (in Lambda memory) | $0 |
| Storage | S3 | < $0.01/month |
| Infra-as-Code | SAM/CloudFormation | FREE |

## Key Decisions

1. **Lambda Function URLs over API Gateway** - Saves $1/million requests. For a PoC under 100 queries/day, this is the single biggest cost saving.

2. **FAISS over managed vector DB** - Aurora Serverless v2 has a $43/month minimum. OpenSearch Serverless is $691/month minimum. FAISS in Lambda memory is $0.

3. **Pre-computed embeddings** - The permit database is static and manually curated. Embedding at deploy time means zero embedding cost at query time (only the user's question needs embedding).

4. **Claude Haiku over Nova Micro** - Haiku is ~5x more expensive but much better at nuanced permit Q&A. At 50 queries/day it's still only ~$2/month. Quality matters for government information.

5. **No database at all** - Daily query counter can use a simple S3 object or CloudFront log analysis. No DynamoDB needed.
