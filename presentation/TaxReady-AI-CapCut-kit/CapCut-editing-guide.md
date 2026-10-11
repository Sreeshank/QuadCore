# TaxReady AI — CapCut editing guide
From Tax Confusion to Confidence | Arjun | 16:9 | 1920 × 1080 | 30 fps

Import all PNGs. Put scene 01 through 07 on the main video track. The screenshots contain text already: use small zooms to keep it visible. Optional transparent PNGs can be put on overlay tracks and moved independently; a flattened screenshot's individual objects cannot be animated separately.

## Suggested 115-second timeline
These are editing targets. Adjust cuts to the actual narration; transitions must not hide important text.

| Time | Image | Animation to add | Transition into next scene |
|---|---|---|---|
| 00:00–00:15 | 01-tax-season.png | Fade in 0.6s. Scale 100% → 104% over the clip. Add "Meet Arjun" as a text overlay fading in. | Dissolve 0.4s |
| 00:15–00:29 | 02-document-confusion.png | Slow pan toward documents. Optional question overlays appear one at a time with a 0.3s upward slide. Use a brief gentle shake on the document overlay only. | Dissolve 0.6s |
| 00:29–00:45 | 03-private-workspace.png | Scale 100% → 103%. Overlay document PNGs slide upward into the workspace one after another, 0.4s each. Cut to 09-real-app-documents.png for the last 4s. | Dissolve 0.4s |
| 00:45–01:00 | 04-review-fields.png | Slow zoom toward the reviewed values. Add a checkmark text overlay with scale 80% → 110% → 100% over 0.4s. Cut to 10-real-app-review.png for 4s. | Direct cut |
| 01:00–01:17 | 05-tds-difference.png | Hold the two amounts still. Add an outlined amber rectangle around the difference as an overlay; fade in 0.3s, hold, fade out. Optional scale pulse 100% → 104% → 100%. Cut to 11-real-app-findings.png for 4s. | Dissolve 0.5s |
| 01:17–01:34 | 06-readiness-dashboard.png | Scale 100% → 103%. Add "59% preparation readiness" as a gentle fade-in overlay. Cut to 08-real-app-dashboard.png for 4s. | Dissolve 0.6s |
| 01:34–01:55 | 07-confidence-report.png | Slow zoom out 104% → 100%. Add arjun-happy.png as an optional character overlay. Show 12-real-app-reports.png briefly, then return to the story frame. Fade the final frame out over 1s. | End fade 1s |

For a simpler edit, use the 7 scene screenshots only. For more motion, use the transparent characters/documents over a plain #F1F5FC background instead of placing them on top of their identical baked-in objects.

## Keyframes
Select a clip. Add the diamond keyframe for Scale at the start (100%). Move to the end and add Scale 103% or 104%. CapCut interpolates between them. Use Position keyframes for gentle pans or document movement. Use Opacity 0% → 100% over 0.4s for fades if a suitable preset is unavailable. Preset names and availability vary by version.
Official guide: https://www.capcut.com/resource/how-to-add-keyframes-in-capcut

## Narration and sound
The seven supplied narration WAVs are in order. Put them on the narration track and set playback speed to 1.25×; enable pitch preservation if available. Leave approximately 1s between scenes. This gives roughly 1 minute 55 seconds. Or record the supplied script yourself.
Use gentle piano or ambient music underneath. Start music around -26 dB and voice around -6 dB; adjust by listening so every word is clear. Fade music in 1s and out 2s. Add soft paper rustling early, subtle upload whooshes, one quiet notification at the discrepancy, and a soft confirmation sound after review.
Keep the discrepancy unresolved in the story: the sample records still differ by INR 3,000.

## Captions and export
Use white or navy captions with clear contrast, no more than two lines, and a consistent sans-serif font. Screenshot frames already have a caption near the bottom; use screenshots as-is or crop/cover the existing caption before adding different captions.
Real app screenshots use the synthetic demo account named Sammer; the animated story character is Arjun. Label the app footage "Synthetic demo workspace" so the name change is clear.
Export 1080p, 30 fps, H.264 MP4, high quality. Final card: "TaxReady AI — Organize Smarter. Verify Faster. File With Confidence." Include "Preparation guidance, not tax advice."



## Updated kit ? current project features
All current app screenshots use a fresh Sammer Demo workspace with the three supported records reviewed: 59% readiness, 3 of 5 checklist items complete, and an unresolved INR 3,000 TDS difference. Story character Arjun remains separate from the synthetic account. Images 01?21 are 1920?1080; 22 is a portrait mobile screenshot. The five PDF preview images are portrait document assets.

### Suggested new feature inserts
Keep the main story around 1:55 by replacing existing app cutaways, or add this optional 15-second montage before the final card:
- 0?3s: 20-moving-beginner-guide.png ? 21-guide-next-position.png. Cross-dissolve 0.4s. Overlay: "A guide that moves with you". These are still screenshots; animate a crop or use a dissolve to illustrate the guide movement.
- 3?6s: 14-ai-assistant-answer.png ? 15-own-api-key-settings.png. Dissolve 0.3s. Overlay: "Built-in help. Optional own API key." This screenshot shows the setting, not a live provider connection.
- 6?9s: 16-privacy-and-activity.png. Slow zoom 100% ? 103%. Overlay: "Export your data. Control your workspace."
- 9?12s: 13-report-snapshot.png. Fade in 0.4s. Overlay: "An explainable report snapshot."
- 12?15s: 19-dark-dashboard.png ? 22-mobile-guide.png. Use the mobile shot centered over a plain navy background, rather than stretching it. Overlay: "Desktop, mobile, light and dark."
Optional montage narration: "A moving guide explains each step. Choose built-in help or your own API key. Export your records, view report snapshots, and prepare wherever you work."

### New document assets
The five PDFs include issuer headers, references, structured summaries, supporting breakdowns and synthetic sample markings. Use the corresponding preview PNG as a paper overlay: rotate from -3? to 0?, scale from 85% to 100% over 0.5s, then hold. Keep sample markings visible. Never present these as official government or bank-issued records.

### Captions and narration timing
Import Arjun-captions.srt as captions when supported. Its timing is an approximate sentence-level alignment for the supplied narration clips at 1.25? speed, with a 1s gap after each clip. Keep pitch preservation enabled where available and fine-tune by listening. Timeline.csv gives the exact calculated clip boundaries, including gaps. No soundtrack is included; choose a suitable licensed track from your editing library.

Open Preview-gallery.html to browse the images offline. All media paths are relative, so extract the ZIP before opening it. The kit contains no real API key, account token, or private customer documents.
