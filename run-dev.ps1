# Run InterviewCoachAI (PowerShell)
# Starts backend (uvicorn) and frontend (python http.server) in background processes.
# Usage: .\run-dev.ps1

# Get the current directory
$rootDir = Get-Location

# Start backend (new window)
$backendCmd = "cd '$rootDir\backend\fastapi_ai'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "Launched backend on http://localhost:8000" -ForegroundColor Green

# Start frontend (new window)
$frontendCmd = "cd '$rootDir\frontend'; python -m http.server 3000"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $frontendCmd
Write-Host "Launched frontend on http://localhost:3000" -ForegroundColor Green

Write-Host "`nApplication is starting... Open http://localhost:3000 in your browser" -ForegroundColor Cyan
Write-Host "To stop: Close the PowerShell windows or run: Get-Process python | Stop-Process -Force`n" -ForegroundColor Yellow
