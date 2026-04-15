$ErrorActionPreference = "Stop"

Write-Host "[1/4] Create .env files if missing..."
if (!(Test-Path "src/backend/.env")) {
    Copy-Item "src/backend/.env.example" "src/backend/.env"
    Write-Host "  - created src/backend/.env"
}
if (!(Test-Path "src/frontend/.env")) {
    Copy-Item "src/frontend/.env.example" "src/frontend/.env"
    Write-Host "  - created src/frontend/.env"
}
if (!(Test-Path "docker/.env")) {
    Copy-Item "docker/.env.example" "docker/.env"
    Write-Host "  - created docker/.env"
}

Write-Host "[2/4] Optional docker services (Postgres + Redis)"
Write-Host "  - run: docker compose --env-file .env up -d (inside docker/)"

Write-Host "[3/4] Backend install"
Write-Host "  - run: cd src/backend; pip install -e ."

Write-Host "[4/4] Frontend install"
Write-Host "  - run: cd src/frontend; npm install"

Write-Host "Bootstrap complete."

