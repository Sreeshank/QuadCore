# TaxReady AI cinematic demo

Final deliverable: **TaxReady_AI_Cinematic_Demo.mp4** — 1920×1080, 30 fps, 120 seconds, H.264 video and AAC stereo audio.

Open `Watch-demo.html` for the local video player and download links.

This separate production directory contains a React/TypeScript Remotion composition, real Playwright browser captures, local Windows narration, animated captions, and an original synthesized electronic score with transition effects. No commercial music or stock media is used. Motion depth uses CSS perspective and SVG; a Three.js runtime is unnecessary for this design.

## Reproduce on this Windows workstation

Install the app's existing frontend/backend dependencies first (see parent README). Node.js, Microsoft Edge, and Windows System.Speech with Microsoft David Desktop are used.

```powershell
cd 'D:\Vs code\TRI\taxready-ai\product-demo-video'
npm.cmd ci --no-audit --no-fund
powershell -ExecutionPolicy Bypass -File render-video.ps1
```

The script starts missing local services, installs Playwright's recording helper, captures an isolated synthetic workflow, synthesizes narration, creates media, renders, and validates the MP4. Services are left running for the user. It does not change application source code or use a real user's records. It does create synthetic demo sessions through the app.

Reuse existing media: `powershell -ExecutionPolicy Bypass -File render-video.ps1 -SkipCapture -SkipNarration`. Render review frames: `node render.mjs --stills`. Preview interactively: `npx remotion studio src/index.tsx`. Set `CHROME_EXECUTABLE` if Edge is installed elsewhere.

## Contents

- `scenes.json`, `narration_script.txt`, `storyboard.md`: complete editorial plan and narration.
- `voiceover.wav`: timed narration only, useful for CapCut editing.
- `subtitles.srt`: scene-timed caption chunks; also animated in the MP4.
- `public/clips`: six actual app recordings, fitted to editorial scene lengths.
- `public/raw`: original unedited browser recordings, including additional field reviews.
- `public/voice`: original and tempo-adjusted local narration takes.
- `public/original-score.wav`, `public/soundtrack.wav`: original music/effects and final mix.
- `public/readiness-report.pdf`: actual synthetic report downloaded through the app.
- `capture-validation.json`, `validation.json`: UI checks and final media checks.
- `review`: representative rendered frames for visual review.

The source clips use all-intra H.264 encoding for reliable frame seeking with a bounded Remotion cache. `node render.mjs --test` renders a three-second browser segment to check the renderer before a full run. `capture-finding.mjs` can optionally record a focused TDS pickup through the actual High-severity filter; the complete capture script uses that filter too.

Voice disclosure: Microsoft David Desktop is a local synthesized English voice, not a premium neural Indian English voice. Caption chunks use proportional timing within the measured speech. Synthetic TDS figures and 59% readiness are checked against the real UI. TaxReady AI prepares records; it does not file returns or verify government databases.

Rendering API reference: https://www.remotion.dev/docs/renderer/render-media and https://www.remotion.dev/docs/options/browser-executable . Dependencies are isolated and locked in this directory; Remotion's own licensing terms apply to use of its tooling.
