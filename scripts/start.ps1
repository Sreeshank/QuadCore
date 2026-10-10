# Run from the repository root. Opens hidden local services and your browser.
$ErrorActionPreference = 'Stop'
$taxreadyRoot = Split-Path $PSScriptRoot -Parent
$taxreadyPython = Join-Path $taxreadyRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taxreadyPython)) {
    throw 'Create .venv and install backend requirements first; see README.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $taxreadyRoot 'frontend/node_modules'))) {
    throw 'Run npm install in frontend first; see README.md.'
}
Start-Process -FilePath $taxreadyPython -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $taxreadyRoot 'backend') -WindowStyle Hidden
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm.cmd run dev -- --port 5173' -WorkingDirectory (Join-Path $taxreadyRoot 'frontend') -WindowStyle Hidden
Start-Sleep -Seconds 3
Start-Process 'http://127.0.0.1:5173/'

