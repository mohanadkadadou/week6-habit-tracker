# My manual reviews (written before applying the AI review)

### My manual review of the streak diff (before fixing)
1. **Time zone / testability (design).** `date.today()` uses the *server's* local date: a user in another time zone sees a streak of 0 near midnight, and the tests (which also call `date.today()`) could straddle midnight. Fixed: optional `today` query parameter (ISO date; 422 if malformed) used by clients and by deterministic tests.
2. **Test helper swallows failures (test gap).** `_streak_habit` posted check-ins without asserting the response, so a broken POST would make the streak tests pass or fail for the wrong reason. Fixed: assert 200.
3. **Product rule worth stating (API shape).** A user who checked in yesterday but not yet today gets `streak: 0`. That is what the spec literally says ("up to and including today"), but it is surprising, so it is now stated in the docstring and has its own test.
4. **Cross-feature gap (correctness, not fixable in this PR).** Check-in `day` is not validated, so `"2026-9-22"` is stored and silently never matches `isoformat()`. That is exactly task 2 (validation), done in the second PR.
Not changed: loading the whole check-in history into a set (fine for a habit tracker; would be a `WHERE day >= ...` query at scale).

### My manual review of the validation diff (before fixing)
1. **Unrequested behaviour (scope).** The agent added a 100-character cap on names that the task did not ask for. Kept (a bound on stored text is reasonable) but called out in the PR as a tradeoff the reviewer can veto.
2. **Hidden dependency on the regex (correctness).** `date.fromisoformat()` on Python 3.11+ also accepts `20260922` and `2026-W39-2`, so the regex is what keeps stored days in one format. A later "simplification" removing it would silently allow other formats, so I added a comment explaining why it exists.
3. **`\d` matches non-ASCII digits (security/edge case).** I suspected `\d{4}` would accept `٢٠٢٦-٠٩-٢٢` or full-width digits and tested it by hand: they were already rejected (422) because `fromisoformat` refuses them, but only by accident. Replaced `\d` with `[0-9]` and added a test covering Unicode digits, ISO week dates, trailing newline and leading space.
4. **Test gap.** Nothing asserted that a trimmed name is what `GET /habits` lists. Added.
5. **Precedence (API shape).** A bad `day` on an unknown habit returns 422, not 404, because validation runs before the handler. Acceptable and consistent with FastAPI; noted in the PR.
6. **Not addressed:** days stored before this change are not re-validated (no migration); future dates are accepted because the task did not forbid them.
