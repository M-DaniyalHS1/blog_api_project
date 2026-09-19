# Task 1: Verification record

Status: Complete based on the user’s confirmation that Task 1 is working after manual deployment. The checks below are retained as a regression checklist; they were not individually observed through browser automation.

The database migration has already been applied. The local code passes lint, production build, and three isolated API integration tests.

## Deploy and start

1. In the backend folder, run `uv run fastapi deploy` and wait for a successful startup.
2. In `frontend`, run `npm run dev` (or refresh the existing development server).

## Browser checks

- Open a story from its homepage title or Read full story link. Confirm the homepage only shows an excerpt, while the article shows all content and paragraph breaks.
- Copy its `/#/posts/<id>` URL into a new browser tab, then refresh. It should load the same article.
- Use browser Back and Forward, then Back to posts. Confirm navigation works and the login session is retained within the same tab.
- Create a post with an optional image and an HTTPS source link. Confirm its publication date appears and the source link opens the original source. Older posts correctly show Publication date unavailable.
- Open `/#/posts/999999999` to check the missing-post message. Open `/#/posts/invalid` to check the invalid-link message.
- With browser networking offline, reload an article. Confirm an error appears; reconnect and choose Try again.
- Check at a narrow mobile viewport: no horizontal overflow, readable paragraphs, fitting images and accessible navigation.

Task 1 is marked complete in PROJECT_TASKS.md based on user confirmation. Task 2 remains unstarted.
