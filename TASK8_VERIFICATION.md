# Task 8: Ask Dani Blogs

Implemented on 2026-09-20; awaiting live verification. Task 7 is paused.

## Backend setup

### Gemini through OpenAI Agents SDK

To use Gemini, set these backend-only environment variables and manually redeploy:

```dotenv
GEMINI_API_KEY=your_private_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

Create the key in Google AI Studio. Never paste it into frontend code or chat. Gemini requests use Google's documented [OpenAI-compatible Chat Completions endpoint](https://ai.google.dev/gemini-api/docs/openai), with structured JSON answers. This path does not use the OpenAI Responses endpoint or the OpenAI key. There is no automatic provider fallback. Existing retrieval, citation checks, draft exclusion, and shared request limits apply. Gemini has its own provider quotas and billing rules; switching does not guarantee unlimited usage. Gemini output is capped at 4,096 tokens to allow room for model thinking; answers are still validated to the existing 6,000-character limit.

Gemini is now the only provider. `CHAT_PROVIDER`, `OPENAI_API_KEY`, and `OPENAI_MODEL` are no longer used by the chatbot.

Gemini now runs through the `openai-agents` package (`agents` Python module): `Agent` + `Runner` + `OpenAIChatCompletionsModel`, with an explicit `AsyncOpenAI` external client pointing to Google. `ModelAnswer` is the structured output type. Runs disable tracing, have no tools, allow one agent turn, and enforce a 35-second overall timeout. HTTP 502/503/504 get at most one retry; SDK client retries are disabled to avoid nested retries. The external client closes after each request. No OpenAI key is needed for Gemini.

Install dependencies with `uv sync` (the package and resolved dependencies are recorded in `pyproject.toml` and `uv.lock`). Redeploy the backend manually; this SDK migration requires no frontend or database changes. Provider responses in tests are simulated; live Gemini verification is still required. The SDK does not eliminate provider overload or quota errors.

SDK migration verification: all 36 backend tests passed. The Gemini integration test executes the real Agent/Runner/model adapter with a simulated client completion and checks structured output, citations, endpoint/key selection, disabled tracing, and the one-turn limit. A separate test checks bounded retries and redacted errors. No live provider call was made.

### Request limits

Optional backend settings: `CHAT_DAILY_LIMIT=100` and `CHAT_HOURLY_LIMIT=10`.

Cleanup verification: all 33 remaining backend tests passed. Legacy direct-HTTP tests were removed along with their implementation; SDK integration, error handling, draft privacy, source checks, and request-limit tests remain. No live Gemini request was made.

## What readers get

- Bottom-right closable chat panel, starter questions, loading status, recoverable errors, and Clear chat.
- Homepage questions search published posts by keywords in title, body, and category. Generic latest-post questions select the newest posts.
- On an article page, questions use that article only, including the Summarize this article starter.
- Answers include links to the selected source posts. Unknown citation IDs, absent sources, and insufficient evidence return a clear fallback.
- Drafts are excluded before provider calls. Source publication status is checked again before returning answers.
- The immediately previous user question supplies follow-up context; chat resets when changing article context. Conversations are kept only in page memory, with up to 20 displayed messages. No chat text is saved in our database.
- Questions and selected public excerpts go to Google Gemini. The UI discloses this and asks readers to check sources.

## Bounds and limitations

- Each question: 1,000 characters; previous question: 1,000 characters. Up to five posts, bounded excerpts, and 4,096 output tokens per provider request.
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
