# Database Migration

Run database migrations for the Todo application.

## Arguments
- `$ARGUMENTS` - Optional: "better-auth" | "backend" | "all" (default: "all")

## Steps

### Better Auth Migration (frontend tables)
1. Read DATABASE_URL from `frontend/.env.local`
2. Run:
   ```bash
   cd /home/nm/hackathon-2/frontend && DATABASE_URL="<url>" npx @better-auth/cli migrate --yes
   ```
3. Verify success message

### Backend Migration (tasks table)
1. Backend auto-creates tables on startup via `SQLModel.metadata.create_all`
2. If backend is running, it will pick up model changes on reload
3. If not running, start it briefly to trigger table creation

### Verification
```bash
DATABASE_URL="<url>" node -e "
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
pool.query(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\")
  .then(r => { console.log('Tables:', r.rows.map(x => x.table_name)); pool.end(); });
"
```

Report which tables exist after migration.
