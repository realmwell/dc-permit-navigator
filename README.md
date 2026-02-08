# DC Permit Navigator

An AI-powered chatbot that helps DC residents, businesses, and visitors navigate the District's 103+ permits, licenses, and certifications across 16 government agencies.

Ask questions like:
- "What permits do I need to open a restaurant in DC?"
- "How do I get a building permit for a home renovation?"
- "What's the process for getting a sidewalk cafe permit?"
- "I want to host a block party on my street - what do I need?"
- "How much does a food truck license cost?"

## Why This Exists

Washington DC has **103+ different permits** spread across **16 different agencies**, each with its own application portal, fee structure, and process. A restaurant owner might need to navigate DOB (building permit), DC Health (food service license), ABCA (alcohol license), DDOT (sidewalk cafe permit), FEMS (fire safety), and DLCP (business license) — all separately.

This project exists because **government should be making it easier, not harder, to get permits**. Every day a permit is delayed is a day a business can't open, a homeowner can't renovate, or a community event can't happen. The first step toward fixing this is making the information accessible and understandable.

## What It Does

- Answers natural language questions about DC permits using RAG (Retrieval-Augmented Generation)
- Provides direct links to application portals for each agency
- Explains requirements, fees, processing times, and related permits
- Covers all major categories: building, business, food, alcohol, cannabis, environmental, events, professional licenses, parking, zoning, historic preservation, and more

## What It Doesn't Do

- Does not submit permit applications on your behalf
- Does not guarantee accuracy — always verify with the issuing agency
- Does not provide legal advice
- Information is manually curated and may not reflect the very latest changes

## Architecture

Fully serverless, AWS-native, designed to cost under $5/month:

```
User → CloudFront → S3 (static chat UI)
                  → Lambda Function URL (RAG query engine)
                       → FAISS index (pre-computed, in-memory)
                       → Bedrock Titan Embeddings v2 (query embedding)
                       → Bedrock Claude Haiku (answer generation)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

**Key cost decisions:**
- Lambda Function URL instead of API Gateway (free vs $1/M requests)
- FAISS in Lambda memory instead of managed vector DB ($0 vs $43-691/month minimum)
- Pre-computed embeddings at deploy time (one-time ~$0.01 cost)
- Reserved Lambda concurrency of 1 + daily query cap

## The Permit Database

The `data/permits.json` file contains a manually curated database of 103 DC permits across 16 categories:

| Category | Count |
|----------|-------|
| Building & Construction | 15 |
| Alcohol & Cannabis | 13 |
| Professional & Occupational Licenses | 13 |
| Public Space & Transportation | 11 |
| Parking & Driving | 8 |
| Environmental | 8 |
| Events & Entertainment | 6 |
| Food & Health | 6 |
| Animal Permits | 5 |
| Business Licenses | 4 |
| Vital Records | 4 |
| Fire & Safety | 3 |
| Historic Preservation | 2 |
| Zoning | 2 |
| Health Professions | 1 |
| Firearms | 1 |

**Agencies covered:** DOB, DLCP, DDOT, ABCA, DC Health, DOEE, FEMS, MPD, DMV, DPR, Office of Planning, Office of Zoning, HSEMA, DC Film Office, DC Courts, Mayor's Office of LGBTQ Affairs.

## Insights

Some things we learned compiling this database:

1. **16 agencies, 16 portals** — There is no single place to find all DC permits. Each agency has its own website, its own application system, and its own process. DDOT uses TOPS. DOB uses Permit Wizard and Citizen Access. DLCP uses a different portal. ABCA uses Quickbase. DC Health has its own Food Division portal. This fragmentation is the core problem.

2. **Agency name changes create confusion** — DCRA was split into DOB (Department of Buildings) and DLCP (Department of Licensing and Consumer Protection), but many URLs and forms still reference "DCRA." ABRA was renamed ABCA when cannabis was added. DDOE became DOEE. These name changes make it hard for the public to find the right agency.

3. **The permit web is deeply interconnected** — Opening a restaurant requires coordinating across 6+ agencies. A demolition permit needs DOB + DOEE (asbestos) + HPO (historic) + potentially WMATA review. Nobody tells you about ALL the permits you need — you discover them one by one, often after delays.

4. **Processing times are rarely published** — Most agencies say "varies" for processing time. This lack of transparency makes it impossible for applicants to plan. The few that do publish times (e.g., 15 business days for parade permits, same day for marriage licenses) stand out as exceptions.

5. **Fees range from $0 to $8,000** — A First Amendment assembly notification is free. A medical cannabis retailer license application costs $8,000. Many permits don't publish their fees online at all.

6. **Digital adoption is uneven** — DDOT's TOPS system and DOB's Permit Wizard are relatively modern. But many agencies still require in-person visits, paper forms, or email submissions. DC Health stopped accepting paper applications for food permits (good!), but ABCA still accepts applications by mail.

7. **"Permits you didn't know you needed"** — Did you know you need a permit to keep pigeons in DC? Or that removing a tree on the sidewalk strip requires DDOT Urban Forestry approval? Or that a retaining wall over 4 feet needs a building permit? The system assumes you know what to ask for.

## Setup & Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Python 3.12
- Bedrock model access enabled for Titan Embeddings v2 and Claude Haiku

### Build the FAISS Index

```bash
pip install -r requirements.txt
python scripts/build_index.py
```

### Deploy

```bash
sam build
sam deploy --guided  # first time
sam deploy           # subsequent deploys
```

### Upload Frontend

```bash
./scripts/upload-site.sh
```

## Development

```
dc-permit-navigator/
├── data/
│   └── permits.json              # Curated permit database (103 permits)
├── lambda/
│   ├── handler.py                # RAG query Lambda
│   └── requirements.txt          # Lambda dependencies
├── scripts/
│   ├── build_index.py            # Vector index builder (Bedrock Titan v2)
│   ├── generate_site_data.py     # Generate JS from permits.json
│   └── upload-site.sh            # S3 frontend sync + CloudFront invalidation
├── site/
│   ├── index.html                # Chat UI + permit directory + about page
│   ├── css/style.css             # Styles
│   └── js/
│       ├── app.js                # Frontend controller
│       └── permits-data.js       # Auto-generated permit data (do not edit)
├── template.yaml                 # SAM/CloudFormation (all AWS resources)
├── ARCHITECTURE.md               # Detailed architecture doc
├── blog-post.md                  # Substack blog post draft
└── README.md                     # This file
```

### Updating the permit database

1. Edit `data/permits.json`
2. Run `python scripts/generate_site_data.py` to regenerate the frontend data
3. Run `python scripts/build_index.py` to rebuild the vector index
4. Deploy with `sam deploy` and `./scripts/upload-site.sh`

## Contributing

The permit database (`data/permits.json`) is manually curated. If you notice a missing permit, incorrect information, or a broken link, please open an issue or PR.

## Disclaimer

This is an informational tool only. Always verify permit requirements directly with the issuing DC government agency. This project is not affiliated with or endorsed by the DC government.

## License

MIT
