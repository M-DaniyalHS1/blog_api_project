# Task 6: Comments and reactions

Status: Implemented; awaiting manual deployment and user verification.

## Deployment
Run `uv run fastapi deploy` from the backend directory and wait for application startup to complete. The comments and likes migration has already been applied.

The reported cloud failure was a temporary DNS lookup failure for Supabase. The new startup code retries this specific error four times (2, 4, 8, and 16 seconds), then fails if connectivity has not recovered. Other database failures are not retried. This helps brief DNS failures; it cannot repair a persistent provider network problem.

## Verify
1. Refresh the frontend and open a published article. The discussion shows comments and a like count without login.
2. Choose Log in from the discussion. Sign in and confirm the app returns to the same story.
3. Add a comment, refresh/reopen the article, and verify it persists. Edit your comment; confirm the edited label. Try deleting it and cancel before confirming deletion.
4. Like the post, then unlike it. Log back in after refreshing to verify your stored reaction. Multiple likes from the same account must count only once.
5. Use a second account. It can add comments and its own like, but cannot edit/delete the first account's comments. Authors link to their profiles.
6. Verify comments are paginated after more than ten comments, with accurate totals after additions and deletions.
7. Move a test post to draft; its comments and reactions must not be publicly accessible. Republishing makes the retained discussion available again. Deleting the post removes its comments and likes.
8. Check narrow mobile layout and failure feedback. Invalid or expired authentication must reject writes. Failed saves keep the typed comment for retry while the article remains open.

Validation: 21 application tests and 3 startup tests passed; frontend lint and production build passed. Automated browser verification was unavailable. Mark Task 6 done only after live user confirmation.
