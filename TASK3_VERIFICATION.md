# Task 3: Author profiles

Status: Implemented; live user verification pending.

## What changed
- Public author pages at `/#/authors/<id>` with display name (username fallback), picture (initial fallback), bio, and newest-first posts with pagination.
- Author names on homepage cards and article pages link to profiles.
- Logged-in users can choose Edit profile on the homepage; their username also links to their public profile.
- PATCH /me/profile only changes the authenticated user's profile. IDs, roles, passwords, and usernames cannot be changed with this endpoint.
- GET /authors/{id} returns public profile information and the author's posts. All current posts are published; draft filtering must be added with Task 4.

## Database
Migration 005 has already added nullable display_name, bio, and avatar_url columns to users. No existing content or accounts were replaced.

## Deploy and check
1. From the backend directory run `uv run fastapi deploy` and wait for successful startup.
2. Confirm GET /authors/{author_id} and PATCH /me/profile appear in cloud /docs.
3. Refresh the frontend, log in, and choose Edit profile.
4. Save a display name, short bio, and public HTTP/HTTPS picture URL. Open your profile through your username link.
5. Confirm the details persist after refreshing and only your posts appear. Profile pages can be read while logged out.
6. Follow an author link from a homepage card and a full article. Check direct profile URLs and browser Back/Forward.
7. Clear the picture or use a broken image URL: your initial should appear. Clear the display name: your username should appear. Check a user with no posts and a nonexistent author ID.
8. Check the profile and editor at a mobile viewport. Backend permission and pagination checks are covered by automated tests.

Validation: 12 API tests passed; frontend lint and production build passed. Browser behavior still requires manual verification.
