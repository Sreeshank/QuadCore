-- Run after Alembic migrations in Supabase's SQL editor.
-- Backend uses a privileged DATABASE_URL; application authorization scopes every query.
-- Prevent direct unauthenticated Data API access to the financial tables.
alter table public.users enable row level security;
alter table public.demo_sessions enable row level security;
alter table public.tax_profiles enable row level security;
alter table public.documents enable row level security;
alter table public.extracted_fields enable row level security;
alter table public.checklist_items enable row level security;
alter table public.validation_issues enable row level security;
alter table public.readiness_reports enable row level security;
-- No browser Data API policies: all application data goes through the FastAPI API.
revoke all on public.users, public.demo_sessions, public.tax_profiles, public.documents,
  public.extracted_fields, public.checklist_items, public.validation_issues,
  public.readiness_reports from anon, authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('taxready-private','taxready-private',false,10485760,array['application/pdf','image/png','image/jpeg'])
on conflict (id) do update set public=false, file_size_limit=10485760,
  allowed_mime_types=array['application/pdf','image/png','image/jpeg'];
-- Do not add public/select-all storage policies. Only backend service-role requests are used.


alter table public.audit_events enable row level security;
revoke all on public.audit_events from anon, authenticated;
