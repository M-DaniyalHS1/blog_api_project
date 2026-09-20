# Task 5: Categories, search, and pagination

Status: Implemented; awaiting manual deployment and live verification.

## Changes
- Categories: General, News, Technology, Sports, Lifestyle, Opinion, Culture.
- Existing posts receive General; authors can change this using My posts > Edit.
- Search matches title, summary, and full article, case-insensitively. Percent and underscore characters are treated literally.
- Search and category filters work together and exclude drafts.
- Homepage shows six posts per page and the total matching count. Changing filters resets to page one.
- Older pending searches are cancelled so stale responses cannot replace new results.

## Deploy and verify
1. Run `uv run fastapi deploy` from the backend folder and wait for successful startup. Migration 007 is already applied.
2. Refresh the frontend. Edit a published post and assign News or Technology. Verify its card and article display that category.
3. Choose a category filter and search a word from an article body or summary. Confirm results match both filters.
4. Search for an older post not initially displayed on page one; confirm it can be found.
5. With more than six matching posts, use Next/Previous and check there are no repeated items. Change a filter while on page two and confirm page one loads.
6. Try an unmatched search and Clear filters. Check mobile category controls and pagination.
7. Confirm saved drafts never appear in search or category results.

Validation: 17 API tests, lint, and production build passed. Live/browser confirmation is pending. Keep Task 5 unchecked until the user verifies it works.
