# Dani Blogs project checklist

Work through these phases in order. Mark a task `[x]` only after its behavior has been tested and works correctly. Code being written alone does not mean a task is done.

For each phase: agree on behavior, implement, test locally, apply any required database changes, deploy, and verify. Record verification evidence and the completion date below the phase before checking it off. Keep unfinished or blocked items unchecked.

## 1. Individual post pages
- [x] Phase complete and verified
- [x] Give each post a shareable URL and full article page.
- [x] Display its picture, publication date, and optional source link.
- [x] Show short previews on homepage cards that link to the full article.
- [x] Handle loading, missing posts, and request errors.
- [x] Verify direct links, browser refresh, and mobile reading.

Verification: Complete. User confirmed “task one is working” after choosing to deploy manually.

- Frontend lint and production build passed.
- Three isolated API integration tests passed.
- Article metadata migration was applied and verified.
- Final working-behavior confirmation came from the user; automated browser verification was unavailable.

### Task 1 refinement: homepage summary and full article
- [x] User verifies the refinement after manual deployment.

User confirmed the refinement is working.

Implemented separate optional summary and full-article fields, paragraph layout on article pages, and fallback excerpts for existing posts. Four API tests, frontend lint, and production build passed. Migration 003 applied and verified. User will deploy manually. Existing posts with only a short paragraph require full article text to be added; source links do not import article text.

## 2. User accounts
- [x] Phase complete and verified
- [x] Add registration, login, and logout.
- [x] Store hashed passwords and handle invalid credentials and expired sessions.
- [x] Assign existing posts to the admin account without losing data.
- [x] Enforce authentication on protected backend actions.
- [x] Verify separate users and access permissions.

Verification / completion date: 2026-09-20. Complete based on user confirmation after manual deployment.

- User confirmed the account changes work after resolving missing deployed routes.
- Nine isolated API tests passed, including registration, duplicate names, hashing, login failures, ownership, logout revocation, expiry, and admin migration.
- Frontend lint and build passed.
- Account migration applied and verified: existing posts preserved and assigned to admin.
- Live confirmation came from the user; automated browser checks were not performed.

## 3. Author profiles
- [x] Phase complete and verified
- [x] Add an author name, picture, and short bio.
- [x] Create profile pages listing the author's published posts.
- [x] Link articles to their authors.
- [x] Allow users to edit only their own profiles.

Verification / completion date: 2026-09-20. User confirmed profiles work after manual deployment. All 12 API tests, lint, and build passed.

## 4. Manage posts and drafts
- [x] Phase complete and verified
- [x] Allow authors to create, edit, and delete their own posts.
- [x] Add draft saving and publishing.
- [x] Keep drafts private and excluded from public feeds and search.
- [x] Enforce ownership in the backend, not only in the interface.
- [x] Verify draft persistence, publishing, editing, and deletion.

Verification / completion date: 2026-09-20. User confirmed Task 4 is working after manual deployment.

- Fourteen API tests, frontend lint, and production build passed.
- Draft migration applied; existing posts preserved as published.
- Live working-behavior confirmation came from the user; browser checks were not individually observed through automation.

## 5. Categories, search, and pagination
- [x] Phase complete and verified
- [x] Assign categories to posts and provide working category filters.
- [x] Search all published posts, not just the loaded page.
- [x] Add pagination or a load-more control with consistent ordering.
- [x] Verify combined filters, empty results, and page boundaries.

Verification / completion date: 2026-09-20. Marked complete at the user's explicit request.

- All 17 API tests, frontend lint, and production build passed.
- Category migration applied and verified; existing posts preserved.
- Completion confirmed by the user; live browser checks were not independently observed.

## 6. Comments and reactions
- [ ] Phase complete and verified
- [ ] Allow logged-in users to comment and react to posts.
- [ ] Allow users to manage their own comments and undo reactions.
- [ ] Enforce permissions and prevent duplicate reactions.
- [ ] Verify counts and persistence after refresh.

Verification / completion date: Pending.

## 7. Reporting and moderation
- [ ] Phase complete and verified
- [ ] Allow users to report posts and comments.
- [ ] Build an admin report-review interface.
- [ ] Allow admins to remove inappropriate content and resolve reports.
- [ ] Verify that ordinary users cannot access moderation actions.
- [ ] Complete moderation before opening public registration widely.

Verification / completion date: Pending.

## 8. Reader chatbot: Ask Dani Blogs
- [ ] Phase complete and verified
- [ ] Add a closable chat panel with starter questions.
- [ ] Find posts, summarize articles, and answer questions from published content.
- [ ] Link answers to the source articles used.
- [ ] Explain when published content does not contain enough information.
- [ ] Exclude private drafts and treat article text as content, not instructions.
- [ ] Keep AI credentials on the FastAPI backend and add usage limits.
- [ ] Verify citations, unavailable answers, and service errors.

Verification / completion date: Pending.

## 9. Writing assistant
- [ ] Phase complete and verified
- [ ] Suggest titles, draft improvements, and summaries in the editor.
- [ ] Show suggestions for author review before applying them.
- [ ] Never publish automatically or overwrite drafts without approval.
- [ ] Verify author permissions, draft preservation, and error handling.

Verification / completion date: Pending.

## 10. Launch checks and deployment
- [ ] Phase complete and verified
- [ ] Check mobile layouts and accessibility.
- [ ] Verify permissions, validation, and error handling.
- [ ] Test registration through publishing, reading, and interaction.
- [ ] Run appropriate frontend and backend checks.
- [ ] Apply required database migrations and deploy frontend and backend.
- [ ] Verify the deployed site, direct article URLs, and chatbot.

Verification / completion date: Pending.

## Current next task

Step 6: Comments and reactions. Not started.
