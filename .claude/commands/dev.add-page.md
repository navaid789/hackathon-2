# Add Frontend Page

Add a new page to the Next.js frontend.

## Arguments
- `$ARGUMENTS` - Description of the page (e.g., "settings page for user profile management")

## Steps

1. **Determine page details** from arguments:
   - Route path (e.g., `/settings`)
   - Whether it needs authentication
   - Key components and functionality

2. **Create the page file** at `frontend/src/app/<route>/page.tsx`:
   - Add `"use client"` if interactive
   - Import auth hooks if protected: `useSession`, `authClient` from `@/lib/auth-client`
   - Add redirect to `/sign-in` if unauthenticated
   - Use Tailwind CSS for styling (match existing design: gray-50 background, white cards with shadow, blue-600 primary)

3. **Create any required components** in `frontend/src/components/`:
   - Keep components focused and reusable
   - Use TypeScript interfaces for props

4. **Add navigation** if needed:
   - Update the main page header with a link to the new page
   - Add back navigation from the new page

5. **Add API client methods** if the page needs backend data:
   - Update `frontend/src/lib/api.ts` with new methods
   - Ensure JWT token is included in requests

6. **Verify**:
   - Page renders at the correct route
   - Auth protection works (redirects if not logged in)
   - Styling matches existing pages
