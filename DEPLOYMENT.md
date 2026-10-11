# Vercel deployment

Production site: https://taxready-ai.vercel.app

Video player: https://taxready-ai.vercel.app/product-demo/Watch-demo.html

Subtitle download: https://taxready-ai.vercel.app/product-demo/subtitles.srt

The React frontend and cinematic product video are public. No backend has been hosted yet. The `/api/*` routes deliberately return HTTP 503 with a setup message until a persistent backend is connected. The online workspace therefore does not yet support sign-in, uploads, dashboard records, the assistant, or report generation. The local app remains available with its existing backend.

## Connect the backend

Deploy the existing FastAPI service with persistent PostgreSQL and private document storage. The project's `render.yaml`, backend Dockerfile, environment examples, and main README describe production configuration, including Supabase authentication, migrations, and private storage.

Once the backend is healthy, replace the first rewrite in `frontend/vercel.json`:

```json
{"source":"/api/:path*","destination":"https://YOUR-BACKEND-HOST/api/:path*"}
```

Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in the Vercel project to enable production sign-in. Keep database credentials and the Supabase service-role key on the backend. If using a direct `VITE_API_URL` instead of the rewrite, configure the backend's CORS origins to include `https://taxready-ai.vercel.app`.

Redeploy from `frontend` with Vercel CLI: `vercel deploy --prod --scope quad-core7`. The linked project is `taxready-ai`; local `.vercel` files are ignored by Git. This deployment was published through the CLI; automatic GitHub deployments have not been configured.

The Vercel source upload excludes local builds, dependencies, credentials, and test output through `frontend/.vercelignore`.
