# TaxReady AI
**Organize Smarter. Verify Faster. File With Confidence.**

A working India-focused FinTech hackathon MVP: React/Vite/TypeScript frontend, FastAPI backend, SQLAlchemy database, real PDF/OCR extraction, user-confirmed financial records, deterministic comparison rules, personalized checklist, explainable readiness score, grounded assistant, and private downloadable PDF reports.

TaxReady AI prepares records; it does not file returns or provide definitive tax advice.

## Quick start on Windows (PowerShell)

Requirements: Python 3.11+, Node.js 20.19+ or 22.12+. This build was tested with Python 3.13 and Node 24 on Windows.

From the project folder:

```powershell
cd 'D:\Vs code\TRI\taxready-ai'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm.cmd ci
cd ..
```

No API key or environment file is needed for the local demo. Optional settings are in the root `.env.example` and `frontend/.env.example`. Copy them to `.env` in the corresponding folders only when you need custom configuration.

Start the backend in terminal 1:

```powershell
cd 'D:\Vs code\TRI\taxready-ai\backend'
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in terminal 2:

```powershell
cd 'D:\Vs code\TRI\taxready-ai\frontend'
npm.cmd run dev -- --port 5173
```

Open **http://127.0.0.1:5173/**. API documentation: **http://127.0.0.1:8000/docs**. Health check: **http://127.0.0.1:8000/health**.

Alternatively, after installing dependencies: `powershell -ExecutionPolicy Bypass -File scripts/start.ps1`. This starts hidden local service processes and opens your browser. Do not run it while the ports are already occupied. Terminal startup is preferable when you want visible logs and Ctrl+C shutdown.

On macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python` in place of the Windows Python path, and `npm` in place of `npm.cmd`.

## Demonstration workflow

1. Open the landing page, choose **Get started**, select **Start fresh**, and enter the explicitly labelled demo workspace.
2. Complete the financial questionnaire. Use salary from one employer and bank interest, financial year **2025-26**.
3. Upload `sample_documents/form16.pdf`, `form26as.pdf`, and `bank-interest.pdf`. Sample download buttons are also available in the upload center.
4. Open each document. Compare the fields and evidence with the authenticated source preview. Choose **Confirm reviewed fields**, then confirm your review.
5. Open **My checklist**. Form 16, Form 26AS and bank interest are complete; salary records and AIS are missing.
6. Open **Verification**. Annual TDS for the same employer and year is INR 45,000 versus INR 42,000: **INR 3,000** to review. This is not automatically a tax error.
7. Ask the assistant **Why does my TDS not match?**. Its answer includes source-document links and comparison context.
8. The reviewed three-document scenario calculates **59.0%**, from 60% document completeness, 100% field verification, 0% consistency and 100% questionnaire completion. Supported verified annual income is salary INR 850,000 and bank interest INR 12,500.
9. Open **Report center**, generate a report, and download the PDF. Its current-state score, inventory, checklist, amounts and unresolved findings match the dashboard.
10. Optionally upload and verify `salary-slip.pdf` and `ais.pdf`. These complete the five applicable checklist items. AIS interest matches the bank record. The TDS finding remains for review.
11. Resolve a finding only after reviewing the source records, with a meaningful explanation. Resolution does not alter source values or certify correctness. Corrections that change the comparison reopen it as a new finding.

Demo choices:
- **Start fresh:** empty isolated user session, full manual workflow.
- **Discrepancy demo:** three actual generated PDFs processed by the extraction pipeline; all fields require manual review.
- **Completed demo:** five explicitly pre-reviewed synthetic records; Form 26AS TDS matches INR 45,000. Score 100%.
- **Incomplete demo:** one unverified Form 16, unfinished profile and capital-gains guidance. Score 0%.

Each new demo login creates its own synthetic user and random server-validated session token, stored as a hash on the server and expiring after 24 hours. Sign out invalidates that token. Demo mode is not production authentication.

## Processing and financial rules

- Content inspection validates PDF/image signatures, parsability, file size, PDF page count, encryption and image dimensions. Files receive random stored names inside user-specific private paths.
- Digital PDFs use PyMuPDF. Images and scanned pages use Pillow preprocessing and Tesseract with a timeout. Missing OCR yields a visible, actionable failure and permits reprocessing.
- Rules recognize Form 16, Form 26AS, AIS, bank-interest statements and salary slips. Exact labelled values are extracted with source page, method, evidence and review state. Conflicting occurrences are left unextracted rather than arbitrarily choosing one.
- Monetary normalization and comparisons use Python `Decimal`; currency fields also have database `Numeric(18,2)` columns. Financial comparison uses the exact normalized decimal strings. Frontend total aggregation uses integer paise (`BigInt`); chart coordinates are converted to numbers for visualization only.
- Checklists are configurable preparation guidance in `backend/app/services/rules.py`. Not-applicable items are excluded from the denominator. For multiple employers, duplicate records from the same employer do not count as additional employers.
- TDS and interest comparisons require matching financial years, explicit annual scope and employer/bank context. Incompatible periods or ambiguous multiple annual values produce **Needs Review**, rather than a definitive discrepancy.
- Findings cover TDS differences, interest differences, inconsistent financial years, duplicates, missing declared records and missing critical extraction fields. Resolution notes persist for an unchanged finding; changed source amounts invalidate the old resolution.
- Verified income only summarizes unambiguous annual Form 16 salary and bank-interest records. Salary slips, tax-credit statements and AIS are not added again. Other income categories can be organized manually but are not included in this supported income subtotal.
- Readiness weights: documents 40%, financial-field verification 25%, comparable consistency checks 25%, completed questionnaire 10%.
- With no applicable requirements, empty components score 100. With applicable requirements, zero extracted fields or zero comparable checks score 0 in those components. User-resolved comparisons count as reviewed consistency checks. The numerical score does not certify the correctness of source values.
- High-severity unresolved issues remain prominently displayed at any score.
- Reports are immutable historical snapshots. Generate a new report after updating records.

## OCR and optional AI

**Local OCR:** install Tesseract and add it to PATH, or set `TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe` in the backend environment. Digital sample PDFs do not require OCR. The backend Docker image includes Tesseract.

**Optional structured extraction:** set `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` for an API supporting chat-completions strict JSON schemas. The pipeline sends only selected labelled financial/year lines, excludes PAN and person/employer/bank names, validates the response with Pydantic, and independently checks evidence and reparses each accepted value. Provider failures visibly fall back to deterministic extraction.

The assistant uses useful deterministic templates grounded in the live profile, checklist, verified supported income and findings. It identifies provisional comparison values and references their source records. Chat does not call an external LLM. Tax-law questions outside supported guidance link to the official Income Tax Department.

## Database and migrations

Local development automatically creates the schema in `backend/data/taxready.db`. Private files are in `backend/data/private`; both are excluded from the source archive.

For a fresh database, optionally run migrations **before** starting the backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

If this exact initial schema was already created by the development app, use `alembic stamp head` once instead of replaying the initial create-table migration. Production does not auto-create tables: the Docker startup applies migrations.

Use `DATABASE_URL=postgresql+psycopg://...` to use PostgreSQL. Supabase pooled PostgreSQL URLs can be used with SSL configured in the URL. Schema includes all requested entities, session storage, relationships, foreign keys, ownership indexes and a frozen initial Alembic migration.

## Environment configuration

| Variable | Default / purpose |
| --- | --- |
| APP_ENV | development; production enables fail-closed configuration checks |
| DEMO_MODE | true locally; must be false in production |
| DATABASE_URL | SQLite fallback; PostgreSQL via postgresql+psycopg:// |
| STORAGE_BACKEND | local or supabase; production requires supabase |
| STORAGE_DIR | backend/data/private, for local files |
| CORS_ORIGINS | localhost:5173 and 127.0.0.1:5173; exact comma-separated allowed origins |
| MAX_UPLOAD_MB / MAX_PDF_PAGES | 10 / 30 |
| RATE_LIMIT | 120 API requests per minute per local process/client bucket |
| TESSERACT_CMD | Optional absolute OCR executable path |
| SUPABASE_URL / SUPABASE_ANON_KEY | Supabase authentication configuration |
| SUPABASE_SERVICE_ROLE_KEY | Backend-only private-storage credential |
| SUPABASE_BUCKET | taxready-private |
| LLM_API_KEY / LLM_BASE_URL / LLM_MODEL | Optional structured extraction provider |
| VITE_API_URL | Frontend API URL including /api/v1; unset uses local proxy |
| VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY | Frontend public authentication settings |

No service-role key or LLM secret belongs in frontend environment variables.

## Optional deployment

**Local Docker with PostgreSQL and OCR:**

```sh
docker compose up --build
```

Open http://localhost:5173. This Compose configuration is a local synthetic-data demo, with service ports bound to localhost. Do not use its demo database password for deployment.

**Supabase + Render/Railway + Vercel:**
1. Provision Supabase PostgreSQL and configure email/password authentication with permitted frontend and recovery redirect URLs.
2. Run Alembic migrations against the deployed database. Then run `scripts/supabase_security.sql` to deny direct browser Data API access to financial tables and create a private storage bucket.
3. Deploy the backend using `backend/Dockerfile` or the supplied `render.yaml`. Set `APP_ENV=production`, `DEMO_MODE=false`, `STORAGE_BACKEND=supabase`, database URL, Supabase credentials and exact frontend CORS origin.
4. Backend startup verifies that the configured Supabase bucket is private. Public bucket configuration is rejected.
5. Deploy `frontend/` to Vercel: build command `npm run build`, output `dist`. Configure `VITE_API_URL=https://your-backend/api/v1` and the public Supabase authentication variables before building. `vercel.json` provides SPA route fallback.
6. Test sign up, confirmation, sign in, password recovery and cross-user isolation using your deployed Supabase configuration.

Supabase authentication is verified server-side using its [authenticated user endpoint](https://supabase.com/docs/reference/python/auth-getuser). Storage setup follows [private-bucket guidance](https://supabase.com/docs/guides/storage/buckets/fundamentals). Tailwind uses its [PostCSS integration](https://tailwindcss.com/docs/installation/using-postcss).

## Tests and verification

Backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

Browser acceptance tests (start both services first):

```powershell
cd frontend
npm.cmd run test:e2e
```

Playwright uses installed Microsoft Edge by default. Set `PLAYWRIGHT_CHANNEL=chrome` to use installed Chrome. Tests cover the entire manual upload-to-report browser workflow and mobile navigation. Screenshots and a downloaded PDF are saved under `frontend/test-results/`.

Backend tests cover classification, digital PDF extraction, scanned/image OCR behavior and missing Tesseract, validated fields, decimal comparisons, year/period matching, duplicates, multiple employers, checklist personalization, zero denominators, scores, report content, schema migration, authentication, ownership, private previews, deletion, reprocessing, CORS, request limits and issue-resolution invalidation.

See `VERIFICATION.md` for the final results and remaining limits.

## Scope and limitations

- Financial extraction is strongest for the supplied labelled templates. Real-world multi-table Form 26AS/AIS layouts require additional parsers and careful aggregation. Unsupported or conflicting fields remain incomplete; values are never fabricated.
- Processing runs synchronously in bounded worker requests. Production-scale use needs a background queue, resource isolation for document parsers, distributed rate limiting, monitoring, retention controls and an independent security review.
- Local demo files are plaintext on the local filesystem, protected by OS access and authenticated API routes. Demo sessions should contain synthetic records only.
- Generic freelancer/business/capital-gains/rental/deduction records can be manually categorized. The MVP does not calculate these income amounts, tax liabilities, filing forms or statutory entitlement.
- Generated reports retain historical financial snapshots, even if a source document is later deleted. Current inventory and extraction are deleted. Saved reports can be viewed and permanently deleted in Report center. Privacy & activity provides complete workspace erasure with typed confirmation; automated production retention remains future work.
- Optional Supabase and paid LLM integrations need your own credentials and were not live-tested in this workspace.
- OCR availability depends on Tesseract. Its success/error paths are covered in tests; the local digital workflow works without it. Docker bundles it.
- Docker/PostgreSQL and hosted deployment configuration are supplied; verification in this workspace uses SQLite, local services and the installed Edge browser.

## Project layout

```text
frontend/src/{components,pages,layouts,hooks,services,context,types,utils}
backend/app/{api,models,schemas,services,core,db,utils}
backend/alembic/versions/0001_initial.py
backend/tests/
frontend/e2e/
sample_documents/
scripts/
docker-compose.yml
render.yaml
```

A distributable source ZIP is included beside this project folder. It excludes dependencies, private files, local databases, secrets, traces and generated runtime data.


## Additional workspace controls

- Transcribe missing source fields with page number and quoted evidence; entries remain unverified until reviewed. Remove incorrect fields or mark verified fields for another review.
- Select and delete multiple documents with confirmation.
- Search verification findings and filter by severity and review status.
- View immutable report snapshots and delete saved reports and their PDFs.
- Export masked workspace JSON or spreadsheet-safe field CSV from Privacy & activity.
- Review a metadata-only activity history and erase workspace records, originals and reports with typed confirmation. Sign-in remains available.
- Apply migration `0002_audit_events` to existing deployments, then rerun the updated Supabase security SQL. Development startup creates the new table automatically.

## Beginner walkthrough

Click **Beginner tour** (the book icon) in the workspace top bar. The 33-step guide opens the real pages, highlights relevant controls, and explains each workflow in plain language. Next and Back move through the guide; the chapter selector jumps between Overview, Documents, Field review, Checklist, Findings, Assistant, Reports, Privacy, and Profile. Skip, Close, or Escape exits. The walkthrough respects reduced-motion preferences and does not submit changes. Finish unsaved edits before starting because the guide navigates between pages.

## Your own assistant API key

Open **AI assistant > Assistant settings**, select **OpenAI**, enter your API key and an available Responses-compatible model, then allow the displayed context sharing. Choose **Done** and send a question. OpenAI usage is billed to your API account. Built-in guidance remains available without a key.

The key exists only in the assistant page state and the current request header. It is not written to local/session storage, the database, exports, or activity records. Leaving/reloading the page clears it; **Clear key & use built-in** clears it immediately. Requests go through the authenticated backend to the fixed HTTPS OpenAI Responses endpoint with `store: false`, no redirects, and a timeout. This setting does not override the provider's data policies. Deploy behind HTTPS and configure any external proxy/APM to redact `X-Assistant-Api-Key` and `Authorization` headers.

Only the current question and selected preparation context are sent: financial year, score components, verification counts, checklist status, supported income and numerical findings. Profile names, raw document contents, free-text resolution notes and originals are excluded automatically. User-typed questions may contain personal information. Generated answers need source review; source links are selected by the existing deterministic assistant.

Implementation follows the [official OpenAI Responses documentation](https://developers.openai.com/api/docs/guides/migrate-to-responses). The default model is editable because access varies by API account.

## Realistic synthetic documents

The five sample PDFs now include issuer headers, document references, structured summaries, supporting quarterly/account breakdowns, page numbering and clear synthetic markings. They retain the same example amounts and extraction labels. Start a new sample demo, or download/upload the refreshed files from `sample_documents/`, to see the redesigned originals. Existing uploaded originals and historical reports are preserved.
