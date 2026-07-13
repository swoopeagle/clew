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
- **B0.1** `[~]` Confirm the running Railway build ≥ `bf2e07e` and a volume is mounted.
  Token now in `.env`; ran `npx @railway/cli status` + `variables`:
  **CONFIRMED** service `clew` is **Online**, volume **`clew-volume` mounted at `/app/data`**
  (`RAILWAY_VOLUME_MOUNT_PATH=/app/data`), app connected to Slack (healthy ping/pong).
  **NOT yet confirmed**: exact deployed git sha — runtime logs are heartbeats only. Prove
  the fix is actually live via **R1** (behavioral) or a one-line confirm from Jay that he
  deployed `bf2e07e`. NOTE: `railway variables` dumps live Slack secrets in cleartext —
  don't re-run casually; rotate Slack tokens post-submission (already on the Monday list).
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
- **B6 canvas draft** `[F]` Click **Draft Application** in a war room. Draft lands in the
  channel **canvas**, reply links "open the draft", leads with the real apply link — all
  PASS (see Finding B6-A: draft quality is excellent). BUT re-clicking Draft Application
  **created a SECOND canvas instead of refreshing in place** → FAIL on the refresh criterion.
  Root-caused + fixed in code (Finding B6-B). Quality: strong; refresh-in-place: was broken,
  now fixed pending deploy.
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

### Setup confirmed this session (Sun night)
- Live Railway org is now **PPH** (App Home: "Paws for Purple Hearts provides service and
  therapy dogs for wounded veterans…", US regional service areas / HQ Canyonville OR,
  program areas = service-dog training & placement / therapy dogs / canine-assisted
  services / puppy raising, grant range **$1,000–$500,000**). Pipeline = **3 approved**
  war rooms: Bob Woodruff Foundation (due 2026-07-20), Patterson Foundation — Assistance
  Dogs (due 2026-07-18), Petco Love — Helping Heroes. "Real-time workspace search
  connected" is showing → Finding #7 (warm-path auth) looks resolved. Sole-bot: one reply
  per action throughout, no duplicates.

### B6-A — Draft Application QUALITY: **STRONG** (this was the top-priority judgment call)
Tested in `#grant-bob-woodruff-foundation-3`. Read the full canvas from the prior run AND
drove a fresh Draft Application click; both drafts were high quality and consistent.
Verdict against the five criteria:
1. **Real apply link — YES.** Leads with `🔗 Apply here: https://bobwoodrufffoundation.my.site.com/s/`
   — the funder's actual Salesforce grant portal, with the note they migrated to it in
   2025. Not a guess. Fresh run independently re-derived the same URL and cited the BWF
   "Grants for Organizations" page as the source, noting the portal is a JS-loaded form
   that doesn't render on fetch (so you must create an account directly). Honest and correct.
2. **Grounding / zero hallucination — YES.** Every claim ties to either BWF's stated
   priorities (social determinants of health, decreasing barriers to mental healthcare) or
   PPH's own profile. It HEDGES exactly where it should: *"canine-assisted therapy isn't
   named as a category on their site — worth confirming with a program officer."* Caught a
   real **deadline discrepancy**: the auto-captured 2026-07-20 date couldn't be confirmed;
   three independent sources describe a rolling, year-round process — and it's transparent
   that the live criteria page 403'd so it used a cached listing. Eligibility checklist is
   real BWF criteria (501c3, 70% program-spend ratio, 2 yrs of 990s, audited financials,
   2 consecutive yrs >$50K gross receipts, contact grants@bobwoodrufffoundation.org). No
   fabricated programs, numbers, or eligibility claims.
3. **Structure — reads like a real application, not filler.** Apply link + deadline → Fit
   Summary → Eligibility Checklist → Application Outline (need statement / program
   description tied to PPH's service-dog + PTSD work / outcomes & evaluation with PCL-5
   appropriately hedged / budget-narrative bullets) → 3 Reusable Boilerplate paragraphs in
   PPH's voice. The ask sits inside BWF's $5K–$500K range. Concrete and funder-tailored.
4. **Canvas + refresh — canvas YES, refresh FAILED.** See B6-B.
5. **Tone/specificity — funder-tailored, not boilerplate.** Boilerplate paragraphs are
   specific to PPH (four regional service areas, Canyonville HQ, volunteer puppy-raiser
   pipeline). Strong.
Net: the drafts are genuinely good — the kind of output that sells the product. The only
quality nit is a chat-style sign-off (see B6-C).

### B6-B — HIGH: re-clicking Draft Application creates a DUPLICATE canvas (FIXED in code)
Evidence: after a second Draft Application click, the war room's tab bar showed **two
"Untitled" canvas tabs** — the first still holding the earlier draft, the second holding
the new one (verified by reading both: different apply-link wording, different deadline
phrasing). Intended behavior (B6 + the code's own comment) is ONE living canvas that a
re-draft refreshes in place.
- **Root cause:** `_try_canvas` used create-then-catch — it called
  `conversations.canvases.create` every time and only edited-in-place if Slack raised
  `channel_canvas_already_exists`. For canvases created via the API (user token) Slack does
  NOT reliably treat them as THE channel canvas, so the second `create` **succeeds and
  spawns a duplicate** instead of raising. The catch-path lookup (`_channel_canvas_id`) is
  never even reached.
- **Fix (committed):** persist the canvas id on the prospect and edit it on re-draft, so we
  don't depend on Slack's dedup. Added `prospects.canvas_id` column + migration
  (`storage/db.py`); new `_resolve_or_create_canvas` in `draft_application_action.py`:
  if a stored `canvas_id` exists → `canvases.edit` in place (falls back to create only if
  the canvas was deleted); otherwise create + persist the id. Kept the
  `channel_canvas_already_exists` adopt-and-track path as a secondary net. Tests:
  `tests/test_draft_application.py` (4 cases: redraft edits in place / first draft persists
  / deleted-canvas fallback / already-exists adopt). **74 pytest green.**
- **Deploy note:** fix is on local `main`, NOT yet on Railway. Until Jay deploys, a second
  Draft Application click still duplicates. Verify live after deploy.
- **Live cleanup:** my test click left a 2nd "Untitled" canvas in
  `#grant-bob-woodruff-foundation-3`. Same cleanup bucket as Finding #9 — will resolve on a
  `reset clew` + re-seed for the video, or delete the stray canvas manually. (Did NOT delete
  it — not confirming destructive actions.)

### B6-C — POLISH: canvas draft ends with a chat-style sign-off (FIXED in code)
Both drafts closed with *"Let me know if you'd like me to draft this directly into the war
room canvas, or start filling out the actual portal application questions…"* — confusing,
because the draft already IS the canvas. The agent didn't know its output gets placed there.
Fix (committed): `DRAFT_APPLICATION_PROMPT` now tells it the reply is saved verbatim into
the war-room canvas, to write it AS the finished document, and to end with the requirements
checklist (no sign-off / follow-up question). Prompt-only, low risk; verify wording live
after deploy.

### B6-D — POLISH (recommendation, NOT changed): canvas tab title is "Untitled"
The canvas body H1 is `Application draft — <funder>`, but the canvas's own title (the tab
label) stays "Untitled" / "Your canvas title" — Slack doesn't promote the markdown H1 to
the canvas title. Cosmetic, and the API path to set a title is uncertain; deliberately left
alone the night before judging. Recommend as a post-submission polish (set the canvas title
when creating, if the API supports it).
