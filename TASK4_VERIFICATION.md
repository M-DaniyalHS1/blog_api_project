# Task 4: Manage posts and drafts

Status: Implemented and locally tested; awaiting manual deployment and browser verification.

## Ready
- Migration 006 applied; all six pre-existing posts remain published.
- Fourteen isolated API tests passed. Frontend lint and production build passed.
- Public feed, search, direct articles, and author profiles exclude drafts.
- GET /me/posts retrieves only the authenticated author's posts and drafts.
- Publishing requires a title and article body. Drafts may be incomplete.
- First publication sets the date. Subsequent edits and republishing preserve it. Historical dates remain unchanged.

## Deploy
Run `uv run fastapi deploy` from the backend directory. Wait for successful startup. Confirm GET /me/posts appears in cloud /docs, then refresh the frontend and log in. Do not create drafts until the updated backend is fully deployed; the old API does not enforce draft privacy.

## Verify
1. Choose New Post, enter an unfinished draft, and choose Save draft. It should appear in My posts as PRIVATE DRAFT.
2. Refresh, log in again, open My posts, and edit the draft. Confirm saved text remains.
3. In a logged-out tab, confirm the draft is absent from the homepage/search and author page, and its direct article URL is unavailable.
4. Complete the title/body and choose Publish Post. Confirm the article becomes public with its publication date.
5. Edit a published post and choose Save changes. Confirm the public content updates.
6. Choose Move to draft. Confirm the article is private again.
7. Delete a test post. Cancel the first confirmation to keep it, then confirm deletion. Verify it disappears.
8. Log in with a different account. My posts must not show the first account's items. API ownership rejection is covered by automated tests.
9. Check these controls on a mobile viewport. Saved drafts survive refresh; unsaved typing does not. Logout clears unsaved editor state.

Only check off Task 4 after user confirmation. Task 5 remains unstarted.
