$ErrorActionPreference = "Stop"

Write-Host "[1/4] Create .env files if missing..."
if (!(Test-Path "backend/.env")) {
    Copy-Item "backend/.env.example" "backend/.env"
    Write-Host "  - created backend/.env"
}
if (!(Test-Path "frontend/.env")) {
    Copy-Item "frontend/.env.example" "frontend/.env"
    Write-Host "  - created frontend/.env"
}
if (!(Test-Path "docker/.env")) {
    Copy-Item "docker/.env.example" "docker/.env"
    Write-Host "  - created docker/.env"
}

Write-Host "[2/4] Optional docker services (Postgres + Redis)"
Write-Host "  - run: docker compose --env-file .env up -d (inside docker/)"

Write-Host "[3/4] Backend install"
Write-Host "  - run: cd backend; pip install -e ."

Write-Host "[4/4] Frontend install"
Write-Host "  - run: cd frontend; npm install"

Write-Host "Bootstrap complete."

