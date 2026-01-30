# End-to-End Test

Run a full end-to-end test of the Todo application: auth flow + CRUD operations.

## Prerequisites
- Backend running on port 8000
- Frontend running on port 3000

## Steps

1. **Verify servers are running**:
   - `curl -s http://localhost:8000/health`
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`
   - If either fails, suggest running `/dev.start`

2. **Test Sign-Up** (use unique email with timestamp):
   ```bash
   EMAIL="e2e-$(date +%s)@test.com"
   curl -s -X POST http://localhost:3000/api/auth/sign-up/email \
     -H "Content-Type: application/json" \
     -d "{\"name\":\"E2E Test\",\"email\":\"$EMAIL\",\"password\":\"testpassword123\"}"
   ```
   Verify: response contains `token` and `user.id`

3. **Test Sign-In + Get JWT**:
   ```bash
   curl -s -c /tmp/e2e-cookies.txt -X POST http://localhost:3000/api/auth/sign-in/email \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"$EMAIL\",\"password\":\"testpassword123\"}"
   ```
   Then fetch JWT:
   ```bash
   curl -s -b /tmp/e2e-cookies.txt http://localhost:3000/api/auth/token
   ```
   Verify: response contains JWT token string

4. **Test Create Task** (POST):
   Verify: 201 status, response has task with id

5. **Test List Tasks** (GET):
   Verify: array containing the created task

6. **Test Toggle Complete** (PATCH):
   Verify: `completed: true`

7. **Test Update Task** (PUT):
   Verify: updated title in response

8. **Test Delete Task** (DELETE):
   Verify: 204 status

9. **Test Auth Rejection** (no token):
   Verify: 403 status

10. **Report results** as a table:
    | Test | Status | Details |
    |------|--------|---------|
    | Sign-Up | PASS/FAIL | ... |
    | ... | ... | ... |
