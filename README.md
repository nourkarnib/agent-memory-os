# Agent Memory OS

A persistent memory layer for AI agents. Captures, stores, and semantically searches every decision your agents make.

## Architecture

```
agent-memory-os/
├── backend/          # FastAPI + Supabase + Qdrant, Dockerized
├── sdk/               # Python SDK (pip install agentmemory)
├── frontend/          # React dashboard, Vite
├── azure/             # provisioning scripts (free + paid versions)
└── .github/workflows/ # CI/CD pipeline
```

## Local development

```bash
# Backend
cd backend
cp .env.example .env   # fill in Supabase/Qdrant/OpenAI keys
pip install -r requirements.txt
uvicorn app.main:app --reload

# Qdrant (local, for dev only)
docker run -p 6333:6333 qdrant/qdrant

# Frontend
cd frontend
npm install
npm run dev
```

## Deploying with Render

The repository includes `render.yaml` for a simple two-service deployment:

1. Push `agent-memory-os` to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Enter the backend values when Render prompts for environment variables:
    `SUPABASE_URL`, `SUPABASE_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`,
    `OPENAI_API_KEY`, and `ALLOWED_ORIGINS`.
4. After the frontend service is created, set `VITE_API_URL` to the backend
    HTTPS URL and redeploy the frontend.
5. Run `backend/schema.sql` in Supabase before storing the first memory.

`ALLOWED_ORIGINS` must contain the frontend URL, for example:
`["https://agent-memory-frontend.onrender.com"]`.

---

## Deploying for free

The whole stack can run at **$0/month**, with one small exception: OpenAI
embedding calls, which cost a few cents at MVP volume (a few thousand
memories/month). Everything else has a genuine free tier.

| Component | Service | Free tier limit |
|---|---|---|
| FastAPI backend | Azure Container Apps | 2M requests + 180k vCPU-sec/month free, scale-to-zero |
| Vector DB | Qdrant Cloud (not self-hosted) | 1GB RAM / 4GB disk, permanently free, ~1M vectors |
| React dashboard | Azure Static Web Apps | 100GB bandwidth/month free |
| Relational DB | Supabase | 500MB DB, 50k monthly active users free |
| Container registry | Docker Hub (public repo) | free, instead of paid Azure Container Registry |
| Secrets | GitHub Actions secrets | free, instead of paid Azure Key Vault |

### Why Qdrant Cloud instead of self-hosting on Azure
Self-hosting Qdrant on Container Apps requires minReplicas of 1 because the
vector index needs to stay warm in memory — it can't scale to zero like the
backend, so you'd pay roughly $15-25/month for an always-on container.
Qdrant Cloud's free tier removes that cost entirely. The trade-off: free
clusters suspend after 1 week of inactivity and delete after 4 weeks — fine
while actively building, just reactivate if you've been away.

### One-time setup

1. Qdrant Cloud — sign up at cloud.qdrant.io, create a free cluster, copy the URL and API key.
2. Supabase — create a free project, run backend/schema.sql in the SQL editor.
3. Docker Hub — create a free account for your-username/agent-memory-backend.
4. Run the provisioning script:

```bash
az login
export DOCKERHUB_USER=your-dockerhub-username
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-supabase-service-role-key
export OPENAI_API_KEY=sk-...
bash azure/provision-free.sh
```

It prompts for your Qdrant Cloud URL and API key, then provisions the
resource group, Container Apps environment, and deploys the backend — all
on free tiers.

### Upgrading later (once you have paying customers)

azure/provision.sh (the paid version) adds Azure Container Registry, Key
Vault, and an optional self-hosted Qdrant Container App — useful once you
need private networking, secret rotation without redeploys, or data
residency guarantees beyond what Qdrant Cloud's region options offer.

### CI/CD

.github/workflows/deploy.yml runs on every push to main:
- Backend changes trigger a build, push to Docker Hub, a new revision on Container Apps, then a health check
- Frontend changes are built and deployed to Static Web Apps

Required GitHub secrets: AZURE_CREDENTIALS, DOCKERHUB_USERNAME,
DOCKERHUB_TOKEN, AZURE_STATIC_WEB_APPS_API_TOKEN.

### Database schema

Run backend/schema.sql in the Supabase SQL editor before first deploy.

## SDK usage

```python
from agentmemory import MemoryOS, remember

memory = MemoryOS(api_key="mem_sk_...", agent_id="pricing-agent",
                   base_url="https://agent-memory-backend.example.azurecontainerapps.io")

@remember(memory, tags=["pricing"])
def decide_discount(customer, order):
    return {"decision": "approve", "discount": 0.15}
```
