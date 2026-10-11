param([switch]$SkipCapture,[switch]$SkipNarration,[switch]$Stills)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
function Check-Command { if($LASTEXITCODE -ne 0){throw "Command failed with exit code $LASTEXITCODE"} }
if(-not(Test-Path 'node_modules/@remotion/renderer')){npm.cmd ci --no-audit --no-fund;Check-Command}
if(-not $SkipCapture){
 $projectRoot=Split-Path $PSScriptRoot -Parent
 try{Invoke-WebRequest 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 3 | Out-Null}catch{
  Start-Process -FilePath (Join-Path $projectRoot '.venv/Scripts/python.exe') -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden
 }
 try{Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 3 | Out-Null}catch{
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm.cmd run dev -- --port 5173' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden
 }
 Start-Sleep -Seconds 3
 node node_modules/@playwright/test/cli.js install ffmpeg;Check-Command
 node capture.mjs;Check-Command
}
if(-not $SkipNarration){& "$PSScriptRoot/narrate.ps1"}
node prepare-media.mjs;Check-Command
if($Stills){node render.mjs --stills;Check-Command}else{node render.mjs;Check-Command;node validate.mjs;Check-Command}
