#!/usr/bin/env bash
# Provisions a FULLY FREE deployment of Agent Memory OS.
# - Qdrant: free-forever cloud tier (sign up manually at cloud.qdrant.io, no CLI for this part)
# - Backend: Azure Container Apps free monthly allowance (scale-to-zero)
# - Frontend: Azure Static Web Apps free tier
# - DB: Supabase free tier
# - Registry: Docker Hub free public repo (instead of paid Azure Container Registry)
# - Secrets: GitHub Actions secrets (instead of paid Key Vault, for now)
#
# Run once from the repo root: bash azure/provision-free.sh
# Requires: az cli logged in (az login), Docker running locally.

set -euo pipefail

RESOURCE_GROUP="agent-memory-rg"
LOCATION="francecentral"
ENV_NAME="agent-memory-env"
BACKEND_APP="agent-memory-backend"
DOCKERHUB_USER="${DOCKERHUB_USER:-yourdockerhubuser}"   # export this before running

echo "== STEP 0 — manual step first =="
echo "Go to https://cloud.qdrant.io, sign up, create a free cluster."
echo "Copy its URL and API key — you'll need them below."
read -p "Qdrant Cloud URL (e.g. https://xyz.cloud.qdrant.io): " QDRANT_URL
read -p "Qdrant Cloud API key: " QDRANT_API_KEY

echo "== 1. Resource group (free — Azure doesn't charge for empty RGs) =="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "== 2. Container Apps environment (free tier) =="
az extension add --name containerapp --upgrade -y
az provider register --namespace Microsoft.App -y
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "== 3. Build & push backend image to Docker Hub (free public repo) =="
docker build -t "$DOCKERHUB_USER/agent-memory-backend:latest" ./backend
docker push "$DOCKERHUB_USER/agent-memory-backend:latest"

echo "== 4. Deploy backend — scale to zero, free monthly allowance =="
az containerapp create \
  --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --environment "$ENV_NAME" \
  --image "$DOCKERHUB_USER/agent-memory-backend:latest" \
  --ingress external --target-port 8000 \
  --cpu 0.5 --memory 1Gi --min-replicas 0 --max-replicas 3 \
  --env-vars \
    QDRANT_URL="$QDRANT_URL" \
    QDRANT_API_KEY="$QDRANT_API_KEY" \
    SUPABASE_URL="$SUPABASE_URL" \
    SUPABASE_KEY="$SUPABASE_KEY" \
    OPENAI_API_KEY="$OPENAI_API_KEY"

echo ""
echo "Done — entirely free except OpenAI embedding calls (a few cents/month at MVP volume)."
echo "Backend URL:"
az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv
