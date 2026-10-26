# Week 6 Writeup: AI Code Review & Testing (Habit Tracker)

**Mohanad Kadadou (2309115218).** Implementation agent: Claude Code (one-shot prompt per feature, via a subagent). **AI reviewer: an independent Claude (Sonnet 5.5) subagent, not Graphite Diamond or CodeRabbit.** Those need their GitHub app installed on the repo owner's account, which an agent cannot do, so I used a read-only Claude reviewer that saw only the diff (not my PR description or notes). Its review is posted as a visible comment on each PR. If you install CodeRabbit on this repo, commenting `@coderabbitai review` on the PRs adds the "official" review.

## The two PRs
| PR | Task | Commits |
|---|---|---|
| [#1 streak](https://github.com/mohanadkadadou/week6-habit-tracker/pull/1) | `GET /habits/{id}/streak` | agent one-shot, my manual-review fixes, AI-review fixes |
| [#2 validation](https://github.com/mohanadkadadou/week6-habit-tracker/pull/2) | reject empty names and malformed `day` | agent one-shot, my manual-review fixes, AI-review fixes, an import repair |

Each PR description follows problem / approach / manual review / testing / tradeoffs and shows the AI review comment. They are left open (not merged) so the review is visible.

## Guardrails (Part I)
```bash
scripts/check.sh      # black --check, ruff check (E,F,I,B,UP,SIM), pytest -q; exits non-zero on the first failure
```
CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the same script on every push and PR. What each catches (real output in [`docs/evidence/guardrails.txt`](docs/evidence/guardrails.txt)): a flipped assertion fails pytest (`2 failed, 1 passed`); un-formatted code fails `black --check`; an unused import fails ruff (`I001`/`F401`). **A failing test fails the build** in CI too: run [40315284806](https://github.com/mohanadkadadou/week6-habit-tracker/actions/runs/40315284806) on branch `demo/failing-test` ended `failure`, while both PR branches are green. Honest slip: while applying review fixes I corrupted an import in `test_main.py` with a scripted edit and pushed it; `scripts/check.sh` flagged it on my next run and `fix: repair test imports...` repaired it. The guardrail did its job, but I had read a truncated output too quickly.

## My manual review vs. the AI's ([my notes](docs/reviews/manual-reviews.md), AI reviews: [#1](docs/reviews/pr1-ai-review.md), [#2](docs/reviews/pr2-ai-review.md))
**PR #1 (streak)**
| Topic | Me | AI | Who was better |
|---|---|---|---|
| Unvalidated `day` strings silently never count | noted, deferred to PR #2 | **major**, suggests `day: date` | tie (same finding; AI ranked it higher) |
| Server clock / time zone | added optional `today` parameter | flagged the same dependence but wanted `today` **bounded** (arguably over-engineering) | me (found it first); AI's bound not adopted |
| Flaky tests near midnight | fixed the helper only | spotted that the first four tests **still** used `date.today()` | **AI**: I had missed my own incomplete fix |
| Missing tests (year boundary, other habit's check-ins, future days) | not covered | listed all three | **AI** (adopted: 2 new tests) |
| Streak is 0 until you check in today | kept per spec, documented | suggested adding `checked_in_today` for the API | AI had the better UX idea; not adopted (scope) |
| Refactors (`StreakOut` model, `_require_habit` helper), `OverflowError` on year 1, redundant `DISTINCT` | not seen | nits and a nearly unreachable crash | AI thorough but low value; I took only `DISTINCT` |

**PR #2 (validation)**
| Topic | Me | AI | Who was better |
|---|---|---|---|
| Unrequested 100-char cap | flagged, kept | flagged scope creep | tie |
| `\d` matches non-ASCII digits | **tested it by hand** (`٢٠٢٦-٠٩-٢٢`): already rejected, but by accident; switched to `[0-9]` | said the regex is "a sound guard against Unicode digits" (static review, did not run it) | **me**: running it showed the guard was luck |
| Zero-width / invisible-only names (`"​"`) pass `strip()` | missed | found, with the fix | **AI** (adopted, tested with 5 invisible characters) |
| Weak assertion `"day" in r.text` | missed | found | **AI** (adopted) |
| Test gaps: missing `day`, wrong types, length 100/101, leap day | partial | complete list | **AI** (adopted all) |
| 422 vs 404 precedence; shared `habits.db` | noted both | noted both | tie |
| `regex` is load-bearing (`fromisoformat` accepts `20260922`, `2026-W39-2`) | found, documented in code | found duplication concern | me |

**Pattern:** the AI was better at breadth and at spotting what my own fixes left behind (tests, edge-case tables, invisible characters); I was better where something had to be **run** (it reviewed statically and could not know the `\d` result) and where product intent mattered. Its severity labels were uneven (the "major" was a pre-existing issue; a "minor" was an unreachable overflow). I adopted about two thirds of its findings and rejected the rest as out of scope.

## What I learned
Guardrails and LLM review catch different things: black, ruff and pytest give instant, deterministic, zero-argument verdicts on formatting, lint and known behaviour, while the AI reviewer found what no rule knows to look for (an invisible-character name, an assertion that proves nothing, a test I only half-fixed). I would trust an AI review as a second reader whose every finding comes with a reproducible example I can check in a minute, but not as an approver: it was static, it missed that a guard worked by accident, and it cannot decide product intent. My heuristic now: run the guardrails first, then treat each AI finding as a hypothesis to verify, and weight it by whether it points at something I can actually reproduce.
