Flora Focus Stage 2 - PostgreSQL Migration
==========================================

Goal
----
Replace the temporary SQLite production database with a real hosted PostgreSQL database.

Chosen provider
---------------
Supabase Postgres

Important connection choice
---------------------------
Use the Supabase pooler session mode connection string for Render.

Why
---
- Supabase documents direct connections as IPv6-first.
- Supabase documents pooler session mode as suitable for persistent backend services and for environments that need IPv4 support.

What code now expects
---------------------
Set this environment variable on Render:
- DATABASE_URL

If DATABASE_URL is set:
- backend uses PostgreSQL
- SQLite is ignored

If DATABASE_URL is not set:
- backend falls back to local SQLite

Exact Supabase steps
--------------------
1. Create a Supabase account.
2. Create a new project.
3. Set and save a strong database password.
4. Wait for the database to finish provisioning.
5. Open the Connect panel.
6. Copy the Postgres pooler session mode connection string.
7. Replace the password placeholder with your actual database password.

Exact Render steps
------------------
1. Open the Render service flora-focus-api.
2. Go to Environment.
3. Add DATABASE_URL with the Supabase pooler session mode connection string.
4. Save changes.
5. Trigger a manual redeploy.
6. Watch the logs.

Success criteria
----------------
After redeploy, backend logs should show:
- Database ready (postgres): ...

Then verify:
- GET /api/health returns 200
- signup works
- login works
- task creation works
- friends/family endpoints still work

Notes
-----
- This does not yet migrate existing SQLite data automatically.
- That is acceptable if Stage 1 was only a temporary public backend test.
