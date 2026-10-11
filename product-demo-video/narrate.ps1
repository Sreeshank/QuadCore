$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
$speaker=New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.SelectVoice('Microsoft David Desktop')
$speaker.Rate=0
$scenes=Get-Content (Join-Path $PSScriptRoot 'scenes.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'public/voice') | Out-Null
for($i=0;$i -lt $scenes.Count;$i++){
 $speaker.SetOutputToWaveFile((Join-Path $PSScriptRoot "public/voice/$i.wav"))
 $speaker.Speak($scenes[$i].text)
 $speaker.SetOutputToNull()
}
$speaker.Dispose()
