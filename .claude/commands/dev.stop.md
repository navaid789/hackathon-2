# Stop Development Servers

Stop all running development servers for the Todo app.

## Steps

1. Find and kill processes on ports 3000, 3001, and 8000:
   ```bash
   lsof -ti:3000 -ti:3001 -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
   ```

2. Remove any stale Next.js lock file:
   ```bash
   rm -f /home/nm/hackathon-2/frontend/.next/dev/lock
   ```

3. Verify ports are free:
   ```bash
   ss -tlnp | grep -E '3000|3001|8000'
   ```

4. Report that servers have been stopped.
