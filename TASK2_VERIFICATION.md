# Task 2: Accounts verification

Status: Complete on 2026-09-20 based on user confirmation after manual deployment. The checks below are retained for regression testing; they were not all individually observed in the browser.

Database migration is already applied. Existing posts have been assigned to the configured admin. On startup, the app synchronizes that account with ADMIN_USERNAME and ADMIN_PASSWORD_HASH from the cloud environment. Keep those existing variables, SECRET_KEY, and ALGORITHM configured.

1. From D:\fast_api_tutorial\blog_api run `uv run fastapi deploy` and wait for application startup to succeed.
2. Refresh the cloud /docs page. Confirm POST /register, GET /me, and POST /logout exist.
3. Refresh the frontend to discard the old token. Sign up with a unique username (3–32 letters, numbers, underscores) and a password of 8–128 characters.
4. Confirm duplicate usernames and incorrect login passwords are rejected.
5. Publish a post and verify its author name appears.
6. Log out, then log back in. Logout invalidates all existing tokens for that account; refreshing the page also clears this version’s in-memory login.
7. Log in with the existing admin credentials and confirm existing posts retain their content and admin ownership.
8. With two test accounts, verify account B receives 403 when calling PUT or DELETE on account A’s post. The editor management UI is planned for Task 4.
9. Check the signup/login controls on a narrow mobile screen.

The old username-based admin JWTs are intentionally invalid under the new account system. Log in again after deployment. Task 2 is marked complete in PROJECT_TASKS.md based on user confirmation.
