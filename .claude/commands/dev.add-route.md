# Add API Route

Add a new API endpoint to both backend and frontend.

## Arguments
- `$ARGUMENTS` - Description of the new route (e.g., "GET /api/tasks/stats - return task statistics")

## Steps

1. **Parse the route description** from arguments to determine:
   - HTTP method (GET, POST, PUT, DELETE, PATCH)
   - URL path
   - Purpose/behavior
   - Request/response shape

2. **Backend - Add route handler** in `backend/app/routes/tasks.py` (or new route file):
   - Add the endpoint function with proper decorators
   - Include JWT auth dependency (`token: dict = Depends(verify_token)`)
   - Include session dependency (`session: Session = Depends(get_session)`)
   - Add user ownership validation if user-scoped
   - Add request/response schemas in `backend/app/schemas.py` if needed

3. **Frontend - Update API client** in `frontend/src/lib/api.ts`:
   - Add the corresponding method to the `api` object
   - Include proper typing for request/response

4. **Frontend - Update UI** if the route needs a UI component:
   - Add the UI element to the appropriate page
   - Wire up the API call with token auth

5. **Verify** the route works:
   - Test with curl using a valid JWT
   - Check both backend and frontend logs for errors
