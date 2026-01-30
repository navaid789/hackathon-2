# Start Development Servers

Start both backend and frontend development servers for the Todo app.

## Steps

1. Kill any existing processes on ports 3000, 3001, and 8000
2. Remove any stale Next.js lock files at `frontend/.next/dev/lock`
3. Start the backend:
   ```bash
   cd /home/nm/hackathon-2/backend && .venv/bin/uvicorn app.main:app --reload --port 8000
   ```
   Run this in the background.

4. Start the frontend:
   ```bash
   cd /home/nm/hackathon-2/frontend && npm run dev
   ```
   Run this in the background.

5. Wait 5 seconds, then verify both servers:
   - `curl -s http://localhost:8000/health` should return `{"status":"ok"}`
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` should return `200`

6. Report status of both servers.

## Troubleshooting
- If port 3000 is in use: `lsof -ti:3000 | xargs kill -9`
- If Turbopack cache is corrupted: `rm -rf frontend/.next`
- If backend DB connection fails: check `.env` DATABASE_URL and Neon dashboard
