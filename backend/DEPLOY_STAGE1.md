Flora Focus Stage 1 Deployment Prep
===================================

What Stage 1 does
-----------------
- Deploy the FastAPI backend to a public URL.
- Move secrets into environment variables.
- Make CORS explicit instead of open to everything.
- Keep SQLite only for temporary smoke testing.

What Stage 1 does NOT solve
---------------------------
- Real multi-device production data safety.
- Shared production database for many users.
- App Store / Google Play packaging.

SQLite on a hosted web service is only acceptable for a temporary test backend.
Stage 2 should replace it with PostgreSQL before real public use.

Chosen host
-----------
Render web service

Why Render
----------
- Simple FastAPI deployment flow.
- Clear support for monorepos via rootDir.
- Easy environment variable management.

Files added or changed
----------------------
- render.yaml
- backend/server.py

Environment variables
---------------------
- FLORA_ENV=production
- JWT_SECRET_KEY=<long random secret>
- ALLOWED_ORIGINS=<comma-separated frontend origins>
- FLORA_DB_PATH=<optional path override; local/dev only for now>

Recommended ALLOWED_ORIGINS values for early testing
----------------------------------------------------
- Desktop local app only: leave unset in local development.
- Public test frontend later: set to the exact frontend origins, for example:
  https://florafocus.app,https://www.florafocus.app

Exact Render steps
------------------
1. Put this project in a GitHub repository.
2. Create a Render account.
3. In Render, choose New > Blueprint.
4. Connect the GitHub repository.
5. Render should detect render.yaml at the repo root.
6. Create the service from the blueprint.
7. When prompted:
   - keep FLORA_ENV as production
   - accept generated JWT_SECRET_KEY
   - enter ALLOWED_ORIGINS only if you already have a hosted frontend origin
8. Wait for deploy to finish.
9. Open:
   https://<your-render-domain>/api/health
10. Confirm the response is:
   {"status":"ok"}

Important warning
-----------------
If you keep plan: free and SQLite, Render's filesystem is not suitable for real user data.
Use this only to prove the backend can run publicly.
Before inviting real users, move to Stage 2 and migrate to PostgreSQL.
