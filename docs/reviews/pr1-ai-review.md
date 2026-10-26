> **AI review of PR #1 (streak).** Reviewer: an independent Claude (Sonnet 5.5) subagent, read-only, given only the diff (not my PR description or notes). Graphite Diamond / CodeRabbit were not used because their GitHub apps are not installed on this account (see writeup.md).

**PR review: feature/streak (GET /habits/{id}/streak)**

**Summary:** The endpoint is small and mostly correct. It returns 404 for an unknown habit, dedupes days with a set, and gives 0 when there is no check-in today. The loop is bounded by the number of distinct stored days. The main risk is that it matches strings against a column that is never validated as ISO. Test coverage is decent but has a few gaps.

**Findings**

1. **major** main.py:55 and :79 (existing code, but this PR depends on it). `CheckinIn.day` is a free `str`, and streak matching is an exact string compare against `date.isoformat()`. A check-in stored as `"2026-9-22"`, `"2026-09-22T10:00"`, or `" 2026-09-22"` is accepted by POST but silently never counts. The user sees a wrong streak with no error.
   Suggested change: type `day: date` in `CheckinIn` and store `checkin.day.isoformat()`. At minimum, normalise or validate in this PR, and add a test that POSTs a non-ISO day.
2. **minor** main.py:94 and :106. `today` is a public, unauthenticated client parameter, so any caller can pass a future or arbitrary date. It does no harm, but it makes the "current streak" definition client-controlled and invites inconsistent results across clients.
   Suggested change: bound it with something like `if today > date.today() + timedelta(days=1): raise HTTPException(422, ...)` (the +1 day covers UTC+14), or rename the parameter `as_of` and document it.
3. **minor** main.py:108. `today - timedelta(...)` raises `OverflowError` (a 500) if a row exists for `0001-01-01` and `today` is at the lower limit. Unreachable once finding 1 is fixed.
4. **minor** main.py:95 (API design). A user who has not yet checked in today sees 0, even with a 30-day streak ending yesterday. That matches the stated spec, but it makes the number misleading during the day.
   Suggested change: also return `"checked_in_today": bool` (or the last check-in day) so clients can show "streak at risk" instead of 0.
5. **minor** main.py:93. The response model is untyped, and the new endpoint repeats the habit-existence check that appears in `add_checkin`.
   Suggested change: add a `StreakOut(BaseModel)` for the OpenAPI schema, and extract a `_require_habit(conn, habit_id)` helper.
6. **minor** test_main.py:56. `_streak_habit` and the first four tests use `date.today()`. They can run across midnight and compare against the server's `date.today()`, which makes them flaky.
   Suggested change: pass `params={"today": ...}` in all streak tests, as the later tests already do, or freeze time.
7. **minor** test_main.py. Missing cases: a streak that crosses a month or year boundary (2029-12-31 to 2030-01-01); a habit with check-ins only in the future relative to `today`; an isolation check showing another habit's check-ins are not counted; a non-ISO stored day (see finding 1).
8. **nit** main.py:104. `SELECT DISTINCT` is redundant because the set already dedupes.
9. **nit** test_main.py:90-91. The tests use shared, un-reset `habits.db` state across tests and runs; a per-test temp DB fixture would be more robust.
