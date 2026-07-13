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

---

# Phase B — test plan for the untested new features
_Driven through Slack in the browser as Ian (workspace `T0BGGC4QGUB`), plus the public
web board. Status column: `[ ]` todo · `[~]` in progress · `[P]` pass · `[F]` fail ·
`[B]` blocked. Update inline as each is exercised. Ground rules from Phase 0 still hold:
one instance only, wait out long ops, screenshot before/after, never retry destructively._

## B0 — deploy gate (do FIRST; several B-cases and all fix-regressions depend on it)
- **B0.1** `[B]` Confirm the running Railway build ≥ `bf2e07e` and a volume is mounted at
  `/app/data`. **BLOCKED on `RAILWAY_TOKEN`** — once it's in `.env`:
  `set -a; source .env; set +a; npx @railway/cli variables` (look for the volume +
  `CLAUDE_CONFIG_DIR=/app/data/claude-home`) and `npx @railway/cli logs` (build sha).
- **B0.2** `[ ]` Sanity: one ping → exactly one reply, still English (watch for the #5
  Russian-word artifact recurring).

## Regression re-confirm of the 4 code-fixed findings (needs B0.1 green)
- **R1 session persistence** `[ ]` Draft an org profile conversationally in a DM, get the
  "say save it" prompt, **have Jay redeploy** (or wait for one), then reply "save it".
  PASS = it saves; no "I don't have a drafted profile visible."
- **R2 approve clarify** `[ ]` DM just "approve" with no prospect context. PASS = asks
  which prospect; does NOT replay an unrelated topic.
- **R3 home refresh** `[ ]` Run Find Grants; WITHOUT clicking Refresh, open App Home.
  PASS = board shows the new prospects.
- **R4 cfemail** `[ ]` Ask Clew for a funder's contact email on a Cloudflare-protected
  page. PASS = a real decoded address, never literal `[email protected]`.

## New features
- **B1 funder-research engine** `[ ]` Ask Clew to research a specific funder (e.g. "research
  the Bob Woodruff Foundation for us"). PASS = it web-searches + follows links, returns an
  eligibility-grade brief, and every factual claim carries a source link on an allowed host
  (grants.gov / propublica.org / usaspending.gov / the funder's own site). FAIL = any
  uncited claim or fabricated program.
- **B2 auto deadline + apply URL** `[ ]` Approve a prospect whose funder page states a
  deadline + apply link. PASS = Clew captures both automatically and only pops the Set
  Deadline modal when it can't find one. Verify the captured apply URL actually resolves
  to the application page.
- **B3 task designation** `[ ]` In a war room, click **Designate Tasks**. PASS = Clew turns
  the application requirements into a posted task board (discrete, ownable items grounded in
  that grant, not generic filler).
- **B4 assign + complete tasks** `[ ]` Assign a task to a user and mark another done. PASS =
  board updates in place; App Home "tasks in flight" strip + counts reflect the change.
- **B5 war-room 9am nudges** `[ ]` Time-gated (fires 09:00 PT). Can't wait — instead verify
  the pieces: a war room with an open task + near deadline appears in
  `build_war_room_nudges(team_id)` logic, and confirm the briefing loop is running in the
  Railway logs (needs B0.1). Note as "logic-verified, not observed live."
- **B6 canvas draft** `[ ]` Click **Draft Application** in a war room. PASS = draft lands in
  the channel **canvas** (not just a message), the reply links "open the draft", and the
  draft leads with the real apply link. Then click Draft Application AGAIN. PASS = the SAME
  canvas refreshes in place — no second canvas, no duplicate.
- **B7 morning briefing on demand** `[ ]` DM Clew `clew briefing`. PASS = a pipeline briefing
  posts (funnel, deadlines, tasks) and that DM is opted into the 9am run. Numbers match
  App Home.
- **B8 capability recitation** `[ ]` Ask "what can you do?" PASS = lists real capabilities and
  surfaces the `clew briefing` / `reset clew` phrases; no hallucinated features.
- **B9 reset clew (card only — do NOT confirm unless re-seeding)** `[ ]` DM `reset clew`.
  PASS = confirmation card states the right counts ("wipes profile + N prospects, archives
  M war-room channels"). **Dismiss it** — only confirm if we're deliberately wiping to
  re-seed PPH for the video.
- **B10 App Home impact panel** `[ ]` PASS = the "what Clew has done" block's numbers
  (prospects researched, citations, war rooms, tasks, ~hours) match the actual pipeline;
  hours is a labeled estimate, not asserted fact.
- **B11 teal web board** `[ ]` Open the Web Board (from App Home button). PASS = the teal
  redesign loads, shows the PPH pipeline by stage with deadlines + cited sources, and the
  task-progress chips + impact match Slack. Check it read-only (no write controls) and that
  it degrades gracefully if the API is briefly unreachable.

## Findings from Phase B
_(append here as they surface — same severity scheme: DEMO-BLOCKER / HIGH / POLISH)_
- _none logged yet_
