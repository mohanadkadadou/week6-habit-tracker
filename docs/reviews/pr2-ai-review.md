> **AI review of PR #2 (validation).** Reviewer: an independent Claude (Sonnet 5.5) subagent, read-only, given only the diff (not my PR description or notes). Graphite Diamond / CodeRabbit were not used because their GitHub apps are not installed on this account (see writeup.md).

**Summary:** The change is correct for the stated goal. Blank or whitespace-only names and malformed or impossible `day` values now return 422 before anything is written. The regex plus `fromisoformat` is a sound guard against the Python 3.11+ ISO variants and against Unicode digits. I found no critical or major issues. The points below are mostly scope, API design and test gaps.

**Findings**

1. **minor, main.py:51,66-67 (scope creep).** The 100-character name limit was not in the requirement ("reject empty names"). It is also a silent behaviour change for any client that sends longer names. Either call it out in the PR description or drop it. If you keep it, make it declarative so it shows up in the OpenAPI schema (`StringConstraints(strip_whitespace=True, min_length=1, max_length=...)`); note this changes the error text, so the message assertions would need updating.
2. **minor, main.py:60-68 (incomplete "blank" check).** `str.strip()` does not remove zero-width characters (`"​"`) or other invisible or control characters, so a visually empty habit name still passes. Use `value.isprintable()`/`unicodedata` and add the zero-width case to the blank-name test. Document that `POST /habits` now returns a name different from what was sent.
3. **minor, main.py:101-109 (API design, error precedence).** The body is validated before the habit lookup, so a malformed `day` on an unknown habit returns 422 rather than 404. Acceptable, but untested and undocumented. Add a test that pins the behaviour or note it.
4. **minor, main.py:74-83 (duplication and OpenAPI visibility).** `day` is parsed twice (regex, then `fromisoformat`) and the format rule is invisible to the generated docs. A `Field(pattern=...)` plus the `fromisoformat` check would put the format in the schema. The regex-then-parse approach itself is fine, because `strptime` would accept `2026-9-22`.
5. **minor, test_main.py:100 (weak assertion).** `assert "day" in r.text` would pass on almost any 422 body. Assert on the message (`"YYYY-MM-DD" in r.text` / `"not a valid calendar date" in r.text`), and split the format-error and calendar-error cases.
6. **minor, test_main.py:72-115 (test gaps).** Missing: `day` absent (`json={}`); non-string types (`{"name": null}`, `{"name": 123}`, `{"day": 20260922}`); boundary values 100 and 101 (only 101 is tested); a valid leap day (`2024-02-29`) and an invalid one (`2025-02-29`).
7. **minor, test_main.py (isolation).** The tests write to the real `habits.db` with no per-test fixture; `test_stripped_name_is_what_gets_listed` depends on shared state and would also pass if the name was stored twice.
8. **nit, main.py:34-35 and 48-49 (naming).** `name_not_blank` also enforces length; `validate_name` is more accurate.
9. **nit, test_main.py:78-82 and 95-99 (loop assertions).** The loops over `bad` values do not name the failing input; use `@pytest.mark.parametrize`.

**Out of scope, no action needed:** duplicate check-ins for the same day are still allowed.
