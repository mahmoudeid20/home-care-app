Set-Location -Path "$PSScriptRoot\backend"
Write-Host "Starting Sanad FastAPI Backend..." -ForegroundColor Green
& ".\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000 --reload

