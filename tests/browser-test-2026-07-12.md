# Browser test record — Sat July 12, 2026 (Ian + Claude)

Manual end-to-end test of Jay's Railway build, driven through Slack in the browser.
Demo org: **Paws for Purple Hearts** (https://www.pawsforpurplehearts.org/).
This is the raw findings log so we can re-check before judging. Companion automated
suite: `pytest` (70 green as of `20c9abe`).

## Setup at test time
- Live instance: Jay's build on **Railway** (`clew-production.up.railway.app`), sole
  bot in workspace `T0BGGC4QGUB`. Ian's local `app_oauth.py` was stopped at 3:47 PM so
  events didn't double-handle; a ping got exactly one reply → Railway confirmed sole.
- Local DB backed up first: `clew.db.bak-telhi-2026-07-12` (not the live DB — Railway
  has its own volume).
- Tested code was whatever Railway was running Sat afternoon (pre-`bf2e07e`).

## What Jay had already built (feature inventory, all verified present in the UI)
1. App Home **Refresh** button (manual board re-pull).
2. App Home **Web Board** button → external teal dashboard (`clew-board.vercel.app`).
3. **Real-time workspace search / warm-path** status + "Connect workspace search" link.
4. **"What Clew has done for you" ROI/impact block** (prospects, citations, war rooms,
   tasks → est. staff-hours saved).
5. War-room **quick-actions row**: Draft Application, Designate Tasks, Tasks, Grant
   Website, Set Deadline.
6. **Set Deadline** modal on Approve (optional, skippable).
7. **Saved Grants** button.
8. **Org Profile modal** ("Draft with AI" + manual fields) — worked when the chat
   confirmation path didn't.
9. Federal **award history** as a formatted Block Kit table.

## Findings (9) and resolution after Jay's Sunday push (`bf2e07e` + follow-ups)

| # | Sev | Finding | Status | Evidence |
|---|-----|---------|--------|----------|
| 1 | Blocker | Conversational "save it" onboarding lost all context ("I don't have a drafted profile visible") | **FIXED IN CODE — needs live re-test** | Root cause was two-layer: in-memory session map + agent-CLI transcripts on ephemeral FS, both wiped every deploy. Now `agent_sessions` table on the volume, `CLAUDE_CONFIG_DIR=/app/data/claude-home`, stale session degrades to fresh instead of erroring. Tests: `test_session_store_survives_process_restart`, `test_agent_sessions_persist_and_expire`. |
| 2 | High | Bare "approve" with no context misfired into unrelated reply | **FIXED IN CODE** | Same session-wipe root cause + new agent prompt rule 5b: ambiguous prospect reference → clarifying question, never a guess. |
| 3 | High | App Home didn't auto-refresh after Find Grants | **FIXED IN CODE** | `save_qualified_prospect_tool` now calls `publish_home` after every save (`agent/tools/qualify.py`). |
| 4 | High | Literal `[email protected]` in a live reply | **FIXED IN CODE** | Cloudflare `data-cfemail` obfuscation; fetcher now decodes it (`website.py::_decode_cfemail`). Test: `test_cfemail_decode_and_extraction`. |
| 5 | High | One-off stray Russian word ("Здесь") | **WONTFIX (accepted)** | Judged a one-off sonnet-5 sampling artifact; recording on Opus lowers likelihood further. No code lever the night before judging. Re-flag only if it recurs. |
| 6 | Polish | org id + sig visible in Web Board URL | **BY DESIGN** | The HMAC signature IS the per-org auth (documented). Not a leak. |
| 7 | Polish | Warm-path / real-time search not authenticated on Railway | **IAN ACTION** | Needs one visit to `https://clew-production.up.railway.app/slack/install` (persists to the volume). |
| 8 | Polish | Vague "find me money" burns a full research cycle instead of clarifying | **WONTFIX (deliberate)** | Full-sweep-without-asking was an explicit earlier fix; reverting risks an "agent asks permission" regression the night before judging. |
| 9 | Polish | Numbered duplicate war-room channels (`…-foundation-3`) | **IAN ACTION** | Archive the stale duplicates, or `reset clew` + re-seed. |

## Still to verify / test tonight (NOT yet exercised)
- **Deploy proof**: confirm Railway is actually running `bf2e07e`+ (not an older
  container), and that `/app/data` is a mounted volume — the session fix is inert
  without the volume. Then re-run the real blocker repro: draft profile → deploy →
  "save it" survives.
- **Untested net-new features** from the rest of Sunday's push: task-designation
  engine + task board + 9am nudges, proactive morning briefing, canvas application
  drafts (link + refresh-in-place), the funder-research engine (web search + crawling),
  auto-captured deadlines/apply URLs, `reset clew`, the animated teal web board +
  task-progress chips + impact panel.
