# Task 8: Ask Dani Blogs

Implemented on 2026-09-20; awaiting live verification. Task 7 is paused.

## Backend setup

Add these settings to your existing backend `.env` for local development, and to the backend deployment's environment/secrets for production:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
CHAT_DAILY_LIMIT=100
CHAT_HOURLY_LIMIT=10
```

Replace the placeholder privately. Never add the key to frontend files or any `VITE_` variable. The real `.env` is ignored by Git. An OpenAI API account with API billing/access is required. Local key presence was checked without displaying secrets: not configured.

Deploy the backend and frontend manually as usual. No new Python dependencies are needed. Migration `migrations/009_chat_usage.sql` was applied to the configured database and the table was verified. Normal startup also creates the new table if it is absent in another environment.

The implementation uses the OpenAI Responses API with structured output and `store: false`. References: [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).

## What readers get

- Bottom-right closable chat panel, starter questions, loading status, recoverable errors, and Clear chat.
- Homepage questions search published posts by keywords in title, body, and category. Generic latest-post questions select the newest posts.
- On an article page, questions use that article only, including the Summarize this article starter.
- Answers include links to the selected source posts. Unknown citation IDs, absent sources, and insufficient evidence return a clear fallback.
- Drafts are excluded before provider calls. Source publication status is checked again before returning answers.
- The immediately previous user question supplies follow-up context; chat resets when changing article context. Conversations are kept only in page memory, with up to 20 displayed messages. No chat text is saved in our database.
- Questions and selected public excerpts go to OpenAI. The UI discloses this and asks readers to check sources.

## Bounds and limitations

- Each question: 1,000 characters; previous question: 1,000 characters. Up to five posts, bounded excerpts, and 900 output tokens per provider request.
- Database counters enforce 100 requests per UTC day across the site and 10 per client IP per clock hour by default. They survive restarts and are shared across workers. Set either limit to 0 to disable requests. Failed/no-match requests also count; these are request caps, not exact currency budgets.
- Client addresses are HMAC-hashed before storage. Application code does not trust arbitrary forwarded headers; the hosting server must configure trusted proxy forwarding correctly. Shared IPs share the hourly cap; verify this behavior on your host. The global cap still applies across all clients.
- Provider failures/timeouts return a generic 503, limits return 429 with Retry-After, and missing configuration does not stop the blog. Provider errors and API keys are not returned to readers.
- Retrieval is keyword-based, not semantic or internet search. Long articles use excerpts, so answers can miss details. Instructions and validated source IDs reduce mistakes but do not prove that every AI claim is supported. Check real answer quality before marking complete.

## Automated verification

- `python -m unittest discover -s tests`: 31 tests passed (24 existing plus 7 chatbot tests).
- Chat checks cover public citation links, draft exclusion, unrelated questions, invalid source IDs, insufficient evidence, posts unpublished during a reply, daily/hourly limits, missing keys, validation, provider request format, timeout/errors, and incomplete responses.
- `npm run lint` and `npm run build`: passed.
- Provider responses were mocked; no paid OpenAI calls were made. Automated browser verification was not performed.

## Manual checks after deployment

1. Open Ask Dani Blogs on the homepage and choose latest posts. Follow a source link and verify it opens the correct full article.
2. On that article, choose Summarize this article. Compare the answer with the stored body, then ask a follow-up.
3. Ask about a topic absent from your posts. Expect an insufficient-information answer rather than invented news.
4. Make a uniquely named draft. Search for its name in chat; confirm no draft content is returned.
5. Test close/reopen, Escape, keyboard focus, Clear chat, and the panel on a narrow phone screen.
6. Verify friendly errors with a missing/invalid key and a low hourly limit in a test environment; restore normal settings afterward.
7. Confirm real answer quality and source accuracy, then mark Task 8 complete in PROJECT_TASKS.md.
