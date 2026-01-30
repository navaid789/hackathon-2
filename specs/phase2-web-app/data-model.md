# Data Model: Phase II - Full-Stack Todo Web Application

**Date**: 2026-01-29 | **Status**: Implemented

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐
│    user       │ 1───N │   session    │
│ (Better Auth) │       │ (Better Auth)│
└──────┬───────┘       └──────────────┘
       │
       │ 1───N
       │
┌──────┴───────┐       ┌──────────────┐
│   account     │       │ verification │
│ (Better Auth) │       │ (Better Auth)│
└──────────────┘       └──────────────┘
       │
       │ user.id = tasks.user_id
       │
┌──────┴───────┐       ┌──────────────┐
│    tasks      │       │    jwks      │
│ (Application) │       │ (Better Auth)│
└──────────────┘       └──────────────┘
```

## Entities

### User (Better Auth Managed)

**Table**: `user`
**Column Convention**: camelCase
**Managed by**: Better Auth (DO NOT modify directly)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | text | NO | auto-generated UUID | Primary key |
| name | text | NO | - | Display name |
| email | text | NO | - | Unique email address |
| emailVerified | boolean | NO | false | Email verification status |
| image | text | YES | null | Profile image URL |
| createdAt | timestamp | NO | now() | Record creation time |
| updatedAt | timestamp | NO | now() | Last update time |
| hashed_password | text | YES | null | Legacy Phase I column (unused by Better Auth) |

**Indexes**: Unique on `email`

### Session (Better Auth Managed)

**Table**: `session`
**Column Convention**: camelCase
**Managed by**: Better Auth

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | text | NO | auto-generated | Primary key |
| expiresAt | timestamp | NO | - | Session expiry |
| token | text | NO | - | Session token (unique) |
| createdAt | timestamp | NO | now() | Creation time |
| updatedAt | timestamp | NO | now() | Update time |
| ipAddress | text | YES | null | Client IP |
| userAgent | text | YES | null | Client user agent |
| userId | text | NO | - | FK → user.id |

### Account (Better Auth Managed)

**Table**: `account`
**Column Convention**: camelCase
**Managed by**: Better Auth

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | text | NO | auto-generated | Primary key |
| accountId | text | NO | - | Provider account ID |
| providerId | text | NO | - | Auth provider (e.g., "credential") |
| userId | text | NO | - | FK → user.id |
| accessToken | text | YES | null | OAuth access token |
| refreshToken | text | YES | null | OAuth refresh token |
| idToken | text | YES | null | OIDC ID token |
| accessTokenExpiresAt | timestamp | YES | null | Token expiry |
| refreshTokenExpiresAt | timestamp | YES | null | Refresh expiry |
| scope | text | YES | null | OAuth scope |
| password | text | YES | null | Hashed password (for credential provider) |
| createdAt | timestamp | NO | now() | Creation time |
| updatedAt | timestamp | NO | now() | Update time |

### Verification (Better Auth Managed)

**Table**: `verification`
**Column Convention**: camelCase
**Managed by**: Better Auth

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | text | NO | auto-generated | Primary key |
| identifier | text | NO | - | Verification target (email) |
| value | text | NO | - | Verification token |
| expiresAt | timestamp | NO | - | Expiry time |
| createdAt | timestamp | YES | now() | Creation time |
| updatedAt | timestamp | YES | now() | Update time |

### JWKS (Better Auth Managed)

**Table**: `jwks`
**Column Convention**: camelCase
**Managed by**: Better Auth

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | text | NO | auto-generated | Primary key |
| publicKey | text | NO | - | EdDSA public key (JSON) |
| privateKey | text | NO | - | EdDSA private key (JSON) |
| createdAt | timestamp | NO | now() | Key creation time |

### Task (Application Managed)

**Table**: `tasks`
**Column Convention**: snake_case
**Managed by**: SQLModel (backend)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | integer | NO | auto-increment | Primary key |
| user_id | text | NO | - | Owner user ID (indexed) |
| title | text | NO | - | Task title |
| description | text | NO | "" | Task description |
| completed | boolean | NO | false | Completion status |
| created_at | timestamp | NO | now() (UTC) | Creation time |
| updated_at | timestamp | NO | now() (UTC) | Last update time |

**Indexes**: Index on `user_id`

## Validation Rules

### Task
- `title`: Required, non-empty string
- `description`: Optional, defaults to empty string
- `user_id`: Must match authenticated user's JWT `sub` claim
- `completed`: Boolean, toggled via PATCH endpoint

### User (Better Auth)
- `email`: Required, valid email format, unique
- `name`: Required, non-empty
- `password`: Required at sign-up (min length handled by Better Auth)

## State Transitions

### Task Lifecycle
```
Created (completed=false) → Toggle → Completed (completed=true) → Toggle → Incomplete
     │                                        │
     └──── Delete ────────────────────────────┘
     │
     └──── Update (title, description) ──── Same state
```

### Session Lifecycle (Better Auth)
```
Sign-Up → Session Created → Active → Sign-Out → Destroyed
Sign-In → Session Created → Active → Expired → Auto-cleanup
```
