# ==============================================================================
# Script de Deploy dos 3 Contêineres no Google Cloud Run
# Projeto GCP: licenciamento-2026 | Região: southamerica-east1 (São Paulo)
# ==============================================================================

$PROJECT_ID = "licenciamento-2026"
$REGION = "southamerica-east1"

Write-Host ">>> Configurando projeto GCP ativo: $PROJECT_ID..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# 1. Contêiner 1: Módulo Ambiental & IA (Licenciamento + Desmatamento + Modelagem)
Write-Host "`n>>> [1/3] Fazendo Deploy do Contêiner Ambiental..." -ForegroundColor Green
gcloud run deploy brasil-ambiental `
    --source . `
    --dockerfile Dockerfile.ambiental `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2

# 2. Contêiner 2: Módulo Financeiro & IA (Benchmark Financeiro + BNDES + CNPJ)
Write-Host "`n>>> [2/3] Fazendo Deploy do Contêiner Financeiro..." -ForegroundColor Green
gcloud run deploy brasil-financeiro `
    --source . `
    --dockerfile Dockerfile.financeiro `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2

# 3. Contêiner 3: Módulo Geoespacial & GIS (MapBiomas + Licenças + Buffers)
Write-Host "`n>>> [3/3] Fazendo Deploy do Contêiner Geoespacial..." -ForegroundColor Green
gcloud run deploy brasil-geoespacial `
    --source . `
    --dockerfile Dockerfile.geoespacial `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2

Write-Host "`n>>> TODOS OS 3 CONTÊINERES FORAM DEPLOYADOS COM SUCESSO!" -ForegroundColor Yellow
