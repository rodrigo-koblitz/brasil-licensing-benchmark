# Deploy to Google Cloud Run
# Run this script in PowerShell from within G:\Meu Drive\UFMG\auxiliary\app

param(
    [string]$ProjectId = "",
    [string]$Region = "southamerica-east1",  # Sao Paulo, Brazil (or us-central1)
    [string]$ServiceName = "acre-licensing-benchmark"
)

if (-not $ProjectId) {
    $ProjectId = Read-Host "Digite o seu Google Cloud Project ID (GCP Project ID)"
}

Write-Host "Configurando projeto: $ProjectId..." -ForegroundColor Cyan
gcloud config set project $ProjectId

Write-Host "Habilitando APIs necessarias no Google Cloud..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

Write-Host "Iniciando build e deploy no Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 2

Write-Host "Deploy finalizado com sucesso!" -ForegroundColor Green
