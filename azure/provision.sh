#!/usr/bin/env bash
# Provisions every Azure resource for Agent Memory OS, in order.
# Run once from the repo root: bash azure/provision.sh
# Requires: az cli logged in (az login), Docker running locally.

set -euo pipefail

RESOURCE_GROUP="agent-memory-rg"
LOCATION="francecentral"          # France Central — good for EU data residency story
ACR_NAME="agentmemoryacr"
ENV_NAME="agent-memory-env"
KEYVAULT_NAME="agent-memory-kv"
BACKEND_APP="agent-memory-backend"
QDRANT_APP="agent-memory-qdrant"
STORAGE_ACCOUNT="agentmemorystorage"

echo "== 1. Resource group =="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "== 2. Container Registry =="
az acr create --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --sku Basic --admin-enabled false

echo "== 3. Container Apps environment =="
az extension add --name containerapp --upgrade -y
az provider register --namespace Microsoft.App -y
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "== 4. Key Vault =="
az keyvault create --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" --location "$LOCATION"

echo "   -> Add your real secrets now, e.g.:"
echo "   az keyvault secret set --vault-name $KEYVAULT_NAME --name supabase-key --value <value>"
echo "   az keyvault secret set --vault-name $KEYVAULT_NAME --name qdrant-api-key --value <value>"
echo "   az keyvault secret set --vault-name $KEYVAULT_NAME --name openai-api-key --value <value>"

echo "== 5. Storage account + file share for Qdrant persistence =="
az storage account create --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" --location "$LOCATION" --sku Standard_LRS
STORAGE_KEY=$(az storage account keys list --account-name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" --query "[0].value" -o tsv)
az storage share create --name qdrant-storage --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY"
az containerapp env storage set \
  --name "$ENV_NAME" --resource-group "$RESOURCE_GROUP" \
  --storage-name qdrant-storage --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" --azure-file-share-name qdrant-storage --access-mode ReadWrite

echo "== 6. Build & push backend image =="
az acr build --registry "$ACR_NAME" --image agent-memory-backend:latest ./backend

echo "== 7. Deploy Qdrant container app (internal only) =="
az containerapp create \
  --name "$QDRANT_APP" --resource-group "$RESOURCE_GROUP" --environment "$ENV_NAME" \
  --image qdrant/qdrant:v1.12.0 --ingress internal --target-port 6333 \
  --cpu 1.0 --memory 2Gi --min-replicas 1 --max-replicas 1

echo "== 8. Deploy backend container app =="
az containerapp create \
  --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --environment "$ENV_NAME" \
  --image "$ACR_NAME.azurecr.io/agent-memory-backend:latest" \
  --ingress external --target-port 8000 \
  --registry-server "$ACR_NAME.azurecr.io" \
  --cpu 0.5 --memory 1Gi --min-replicas 0 --max-replicas 5

echo "== 9. Grant backend's managed identity access to Key Vault =="
az containerapp identity assign --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --system-assigned
PRINCIPAL_ID=$(az containerapp identity show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query principalId -o tsv)
az keyvault set-policy --name "$KEYVAULT_NAME" --object-id "$PRINCIPAL_ID" --secret-permissions get list

echo ""
echo "Done. Backend URL:"
az containerapp show --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv
