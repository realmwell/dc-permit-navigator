# Claude Code Handoff: DC Permit Navigator

## What we built (in Claude Code, before deployment)

A complete RAG chatbot project for navigating DC's 103+ permits across 16 agencies. The repo at `/Users/maxmac/dc-permit-rag` (GitHub: `realmwell/dc-permit-navigator`) contains:

- `data/permits.json` — Hand-curated database of 103 DC permits with agencies, fees, requirements, application URLs
- `lambda/handler.py` — RAG query Lambda (Bedrock Titan v2 embeddings + Claude Haiku for answers)
- `scripts/build_index.py` — Builds vector index from permits.json via Bedrock Titan Embeddings v2
- `scripts/generate_site_data.py` — Generates `site/js/permits-data.js` from permits.json (for offline directory)
- `scripts/upload-site.sh` — Syncs frontend to S3 + invalidates CloudFront
- `site/index.html` — 3-tab frontend: Chat, Full Permit Directory, About
- `site/css/style.css` — Responsive styles
- `site/js/app.js` — Frontend controller (chat, directory search/filter, tab navigation)
- `site/js/permits-data.js` — Auto-generated 65KB JS file with all 103 permits inline
- `template.yaml` — SAM/CloudFormation (S3, CloudFront, OAC, Lambda, Budget alarm)
- `ARCHITECTURE.md` — Full technical architecture doc
- `blog-post.md` — Substack blog post draft
- `README.md` — Project README

## What happened during deployment (in CloudShell)

### Problem 1: SAM crashed with `NoneType has no attribute 'get'`

`sam validate` and `sam deploy` failed because `template.yaml` had been corrupted during editing:
- Empty resource stubs under `Resources:` (keys with no body): `CloudFrontUrl:`, `QueryFunctionUrl:`, `DistributionId:`
- Stray `Value:` lines that belonged in `Outputs:` but ended up under `Resources:`
- SAM iterates over `Resources:` expecting each value to be a dict; `None` values crash it

**Fix:** Deleted the empty stubs so `Resources:` only contained real resources with `Type:` and `Properties:`. Also removed an empty `Policies:` line under `QueryFunction` that had no policy list.

### Problem 2: Lambda reserved concurrency rejected

CloudFormation failed with: *"Specified ReservedConcurrentExecutions for function decreases account's UnreservedConcurrentExecution below its minimum value of [10]."*

The template set `ReservedConcurrentExecutions: 1` on the Lambda, but the account's unreserved concurrency floor is 10.

**Fix:** Removed `ReservedConcurrentExecutions` from the Lambda resource entirely.

### Problem 3: Stack stuck in failed state

The failed stack entered `CREATE_FAILED` / rollback. Could not update while in this state. Had to wait for full deletion before redeploying.

**Fix:** Waited until `describe-stacks` returned "does not exist", then ran `sam deploy` again.

### Problem 4: AccessDenied on CloudFront URL

After successful stack creation, visiting the CloudFront URL returned AccessDenied because S3 had no `index.html` at the root.

**Fix:** Uploaded a placeholder `index.html` to the S3 bucket. Had to discover the actual bucket name via:
```bash
aws cloudformation describe-stack-resources --stack-name dc-permit-navigator --logical-resource-id SiteBucket
```

### Current state after deployment

- **Infrastructure works.** Stack is deployed: S3, CloudFront, OAC, Lambda, IAM role, Budget alarm.
- **CloudFront URL is live:** `https://d3nt8hiz2zlgo5.cloudfront.net`
- **BUT:** Only a placeholder HTML page is being served. The real frontend from the repo (`site/`) has NOT been uploaded yet. The Lambda exists but has no Function URL or API Gateway event wired up to expose it publicly.

---

## INSTRUCTIONS: Build out the public-facing frontend

The goal is to make `https://d3nt8hiz2zlgo5.cloudfront.net` serve the actual interactive app (chat + permit directory) from the repo.

### Step 1: Upload the real frontend to S3

The frontend already exists in `site/`. It does NOT need React or Vite — it's vanilla HTML/CSS/JS by design (matching the bus tracker pattern). Upload it:

```bash
# Get the actual bucket name
BUCKET=$(aws cloudformation describe-stack-resources \
  --stack-name dc-permit-navigator \
  --logical-resource-id SiteBucket \
  --query "StackResources[0].PhysicalResourceId" \
  --output text)

# First regenerate the permits data JS
cd /Users/maxmac/dc-permit-rag
python3 scripts/generate_site_data.py

# Sync the site directory to S3
aws s3 sync site/ "s3://$BUCKET/" --delete

# Invalidate CloudFront cache
DIST_ID=$(aws cloudformation describe-stack-resources \
  --stack-name dc-permit-navigator \
  --logical-resource-id Distribution \
  --query "StackResources[0].PhysicalResourceId" \
  --output text)

aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

After this, `https://d3nt8hiz2zlgo5.cloudfront.net` should serve the full 3-tab UI with the browsable permit directory working immediately (it uses inline JS data, no API needed).

### Step 2: Expose the Lambda as a public HTTP endpoint

The Lambda needs a public URL so the chat feature can call it. Two options:

**Option A (simplest): Add Lambda Function URL back to template.yaml**

Under `QueryFunction` in `template.yaml`, add:

```yaml
      FunctionUrlConfig:
        AuthType: NONE
        Cors:
          AllowOrigins:
            - '*'
          AllowMethods:
            - POST
            - OPTIONS
          AllowHeaders:
            - Content-Type
```

And add an Output:

```yaml
  QueryFunctionUrl:
    Description: Lambda Function URL for RAG queries
    Value: !GetAtt QueryFunctionUrl.FunctionUrl
```

Then redeploy: `sam build && sam deploy`

**Option B: Add API Gateway via SAM Events**

Under `QueryFunction`, add:

```yaml
        Events:
          QueryApi:
            Type: Api
            Properties:
              Path: /query
              Method: POST
```

And add CORS globals:

```yaml
Globals:
  Api:
    Cors:
      AllowMethods: "'POST,OPTIONS'"
      AllowHeaders: "'Content-Type'"
      AllowOrigin: "'*'"
```

Option A (Function URL) is free. Option B (API Gateway) costs $1/million requests but gives you better control. For a PoC under $5/month, Option A is recommended.

### Step 3: Connect the frontend to the Lambda endpoint

After deploying the Lambda URL, get it from the stack outputs:

```bash
aws cloudformation describe-stacks --stack-name dc-permit-navigator \
  --query "Stacks[0].Outputs[?OutputKey=='QueryFunctionUrl'].OutputValue" \
  --output text
```

Then update `site/js/app.js` — find this line near the top:

```javascript
const API_URL = window.PERMIT_NAV_API_URL || '';
```

Replace with the actual Lambda Function URL:

```javascript
const API_URL = window.PERMIT_NAV_API_URL || 'https://XXXXXXX.lambda-url.us-east-1.on.aws/';
```

Re-upload the site to S3 and invalidate CloudFront (same commands as Step 1).

### Step 4: Build and upload the vector index

The Lambda needs the FAISS index in S3 to answer questions. Build it:

```bash
cd /Users/maxmac/dc-permit-rag
pip install boto3
python scripts/build_index.py --upload $BUCKET
```

This will:
1. Chunk all 103 permits into text documents
2. Embed them via Bedrock Titan Embeddings v2 (~$0.01 one-time cost)
3. Write `data/embeddings/permits.index` (binary vectors) and `data/embeddings/chunks.json`
4. Upload both to S3

**Prerequisite:** Bedrock model access must be enabled in the AWS console for:
- `amazon.titan-embed-text-v2:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

### Step 5: Verify the full flow

1. Visit `https://d3nt8hiz2zlgo5.cloudfront.net`
2. The **Permit Directory** tab should show all 103 permits, searchable and filterable
3. The **Chat** tab should accept a question, call the Lambda, and return an AI-generated answer
4. If the Lambda isn't connected yet, the chat falls back to local keyword search (functional but less intelligent)

### Step 6: Cost protection verification

Confirm these safeguards are in place:
- Lambda has no reserved concurrency set (removed due to account limits) — consider adding it back if account concurrency increases
- Lambda handler has a daily query cap of 200 (`MAX_DAILY_QUERIES` in handler.py)
- AWS Budget alarm is set at $5 (via the `Budget` resource in template.yaml)
- Lambda timeout is 30s, memory is 512MB

### Known issues to watch for

1. **S3 upload permissions:** If `aws s3 sync` fails with AccessDenied, your IAM principal needs `s3:PutObject` on the site bucket. Do NOT make the bucket public — keep OAC-only.
2. **Bedrock access:** If the Lambda returns errors about model access, enable Titan Embeddings v2 and Claude Haiku in the Bedrock console (Model access → Request access).
3. **Cold starts:** First Lambda invocation after idle will take 5-10s to download the FAISS index from S3 to `/tmp`. Subsequent warm invocations are fast.
4. **CORS:** If the frontend can't reach the Lambda, check that the Function URL CORS config allows the CloudFront domain.
