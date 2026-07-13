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
- **R1 session persistence** `[B]` DEFERRED — needs a real deploy event to test
  save-across-redeploy. Do it as part of tomorrow's Jay deploy.
- **R2 approve clarify** `[P]` DM'd bare "approve" (10:38 PM). Reply: *"I want to make sure
  I approve the right one — could you tell me which prospect… (check the shortlist on the
  Home tab or ask me to re-list)."* Asks which, doesn't guess, doesn't replay an unrelated
  topic. Finding #2 confirmed fixed + live.
- **R3 home refresh** `[P]` (evidenced) The Finding #3 fix (`save_qualified_prospect_tool`
  → `publish_home` after every save) is in the deployed build, and the Home board is
  populated with the auto-published prospects. Fresh live observation (run Find Grants →
  watch Home update without Refresh) folds into the shoot-day reseed.
- **R4 cfemail** `[P]` (evidenced) The deployed #grant-bob-woodruff brief rendered the
  correctly-decoded `grants@bobwoodrufffoundation.org` — the fetch-path decode works live.
  The only leak path is the WebSearch-snippet fallback (seen in the local harness), now
  covered by the new prompt guard (committed `69791e1`, pending deploy). See Finding R4-A.

## New features
- **B1 funder-research engine** `[P]` (evidenced) Every live brief this session (BWF,
  Patterson, Petco) was an eligibility-grade brief with real cited sources (propublica,
  funder's own criteria/portal pages, ProPublica card) and honest Confirmed/Verify splits —
  no uncited claims or fabricated programs observed. Fresh on-demand run folds into reseed.
- **B2 auto deadline + apply URL** `[P]` (evidenced) The 3 existing approved prospects show
  auto-captured deadlines + apply URLs (BWF 2026-07-20 + Salesforce portal; Patterson
  2026-07-18) while **Petco correctly carries no deadline** (its page states none) — exactly
  the "capture when stated, skip when absent" behavior. NOT freshly observed: the Set
  Deadline modal only-pops-when-absent path (needs a fresh approve → do at reseed).
- **B3 task designation** `[P]` The #grant-bob-woodruff task board is grounded, discrete,
  ownable items tied to BWF's real requirements (501c3 letter, 990s, audited financials,
  board list, canine-services fit, need statement), assigned to real users — plus the "No
  tasks yet — click Designate Tasks" empty state. Not generic filler.
- **B4 assign + complete tasks** `[P]` (evidenced) Tasks carry real assignees (@Ian, @Jay)
  and Done states (5 done / 1 open), and the Home strip "1 task in flight" reconciles exactly
  with the board's "1 open" — counts reflect task state across surfaces. Live reactive toggle
  not exercised (avoided mutating Jay's task).
- **B5 war-room 9am nudges** `[P]` (logic-verified) `build_war_room_nudges` nudges
  approved/applied war rooms with a deadline ≤3 days OR unassigned open tasks;
  `_seconds_until_next_briefing` fires 09:00 PT and rolls forward; `briefing_loop` starts at
  app startup and never dies. The same `post_briefing` path is proven live via the on-demand
  `clew briefing` (B7). Not observed firing at 9am (time-gated), as expected.
- **B6 canvas draft** `[F]` Click **Draft Application** in a war room. Draft lands in the
  channel **canvas**, reply links "open the draft", leads with the real apply link — all
  PASS (see Finding B6-A: draft quality is excellent). BUT re-clicking Draft Application
  **created a SECOND canvas instead of refreshing in place** → FAIL on the refresh criterion.
  Root-caused + fixed in code (Finding B6-B). Quality: strong; refresh-in-place: was broken,
  now fixed pending deploy.
- **B7 morning briefing on demand** `[P]` DM'd `clew briefing`. PASS — posted "Your morning
  grant briefing": BWF due in 7 days → its war room, Patterson due in 5 days → its war room,
  "#grant-bob-woodruff-foundation-3 — 1 task open", opts DM into daily 9am ("Clew checks your
  pipeline every morning"). Petco (no deadline) correctly omitted from deadline lines. Numbers
  match App Home. Minor: "N days" countdown computed in UTC (7/5) vs PT calendar (8/6) — see
  Finding B7-A.
- **B8 capability recitation** `[P]` Asked "what can you do?". PASS — recites the full real
  capability list (Find grants w/ sources, org profile, Approve→war room, Draft
  Application→canvas, Designate tasks, Saved Grants/Home/Web Board) and both backticked
  phrases `clew briefing` + `reset clew`; references the live PPH profile; no hallucinated
  features. Matches SYSTEM_PROMPT "WHAT YOU CAN DO" exactly.
- **B9 reset clew (card only — do NOT confirm unless re-seeding)** `[B]` DELIBERATELY
  SKIPPED. Typing the `reset clew` trigger was auto-blocked by the safety classifier —
  consistent with the ground rule to never risk a reset before the video. Card-copy check
  isn't worth any wipe risk; trivially confirmable at the shoot-day reseed.
- **B10 App Home impact panel** `[P]` "What Clew has done for you": *researched 3 prospects,
  verified 3 citations, opened 3 war rooms, handed off 24 tasks — roughly **~8 hours** (est.
  2.5 hrs per researched prospect)*. Numbers reconcile with the pipeline (3/3/3); **hours is
  explicitly a labeled estimate**, not asserted fact. PASS. (Aside: the "What Clew can see"
  panel still lists stale TEL HI channels + a `#grant-metta-fund` → Finding #9 reseed
  cleanup.)
- **B11 teal web board** `[P]` Opened from App Home (`clew-board.vercel.app/?org=…&sig=…`,
  per-org HMAC). PASS — teal board loads ("Live · updated …"), KPI tiles correct (**3 Active ·
  3 Approved · 0 Awaiting · 0 Awarded**), stage columns Qualified 0 / Approved 3 / Applied 0 /
  Submitted 0 / Awarded 0. All 3 approved cards show deadline + "Nd left", grant size,
  geography, full fit rationale WITH honest caveats (ADI/IGDF status for Patterson, Petco
  invitation-only), warm-path note where relevant, and a cited source (propublica). Task chip
  "🧩 5/6 tasks" on BWF matches the war room (1 open). Read-only confirmed ("Actions happen in
  Slack… This board is the live, read-only view") — no write controls. Impact/org header
  matches Slack. NOT tested: graceful API-down degradation (couldn't safely simulate).
  (Caution when reading via text-extraction: the KPI tiles' numbers/labels interleave — the
  SCREENSHOT is authoritative, tiles are correct.)

# Phase C — remaining features (Sun night, live on Railway)
Sweep of every control/feature not yet freshly exercised. Wave 1 = risk-free; Wave 2 =
mutates demo state (cleaned by the shoot-day reseed); Wave 3 = deploy-gated (tomorrow).

## Wave 1 — risk-free, ALL PASS
- **C1 ping** `[P]` "hello" → exactly ONE reply, English, references live PPH profile. Sole-bot
  confirmed, no duplicates (#5 Russian artifact did not recur).
- **C2 Saved Grants** `[P]` Posts funnel + all 3 approved cards (BWF/Patterson/Petco) with fit
  rationale, "Approved" status, "Help me apply" action, source-thread links.
- **C3 Grant Website** `[P]` Opens `bobwoodrufffoundation.my.site.com/s/` — the REAL BWF grant
  portal (= the captured application_url, not a guess).
- **C4 Refresh** `[P]` Board re-publishes cleanly, all numbers unchanged.
- **C5 Edit Org Profile modal** `[P]` Opens prefilled with live PPH (mission/geography/programs);
  cancelled without saving.
- **C6 award-history table** `[P]` Graded the 4:17 PM thread: clean Block Kit table, 3 real DoD
  awards (HU00011810072 $316,793; HU00012010024 $316,792; HU00012210020 $306,430) each cited to
  usaspending.gov, recurring-funder insight, honest caveats, no fabrication.
- **C7 feedback 👍/👎** `[P]` Thumbs-up registers a filled/selected state, no error.
- **C8 Tasks button** `[P]` Re-posts the current board exactly (1 open + 5 done, right assignees).

## Wave 2 — mutating (on a throwaway test prospect; Jay's 3 stay untouched)
- **C9 B1 fresh research** `[P]` "research the Gary Sinise Foundation… add if a fit." EXCELLENT:
  followed real links (official site, First Responder Grant Guidelines PDF, ProPublica 990s),
  found GSF's only open grant lane is restricted to law-enforcement/fire/EMS depts, correctly
  concluded PPH doesn't qualify → did NOT save it. Honest non-fit, real citations, no `[email
  protected]`, recalled the prior conclusion. (Quality-over-quantity discipline, live.)
- **C10 R3 live / Find Grants** `[P]` Full sweep first returned an HONEST NULL ("No new
  prospects to save… Nothing padded onto the list just to show something new"), ruling out 8
  named funders each with a reason — a strong re-validation of the search strategy +
  no-fabrication guarantee. Then a targeted save (DAV CST, below) drove the R3 observation:
  on save, App Home auto-updated to "1 to review" + a new "Qualified — awaiting review [1]"
  row + impact bumped to 4 prospects — all WITHOUT clicking Refresh. `publish_home`-on-save
  works live.
- **C11 B2 / approve** `[P]` Approved DAV (whose exact deadline Clew couldn't confirm) → the
  Set Deadline modal POPPED (the "only when absent" path; BWF/Patterson had captured dates and
  didn't need it). Set 2026-07-31 → saved → war room `#grant-dav-charitable-service-trust`
  opened with a full brief: **apply URL captured** (`dav.smartsimple.com`), criteria
  (`cst.dav.org/grants/`), **real contact `cst@dav.org` (no [email protected])**, honest
  Amount="Verify", nuanced eligibility analysis, cited DAV sources. Channel topic → "Due
  2026-07-31".
- **C12 Designate Tasks (fresh)** `[P]` Grounded, DAV-SPECIFIC board: pull 501c3 letter,
  financials, board list, "draft need statement citing veteran wounds/rehabilitation",
  "program narrative on canine-assisted THERAPEUTIC activities" (the eligibility framing),
  "budget narrative EXCLUDING capital/pilot costs" (DAV's stated exclusions). Not filler; each
  with an Assign-to picker.
- **C13 B4 live toggle** `[P]` Assigned task 1 to @Ian (people picker: clew/Jay/Ian/Slackbot)
  → a green "Done" button appeared → clicked Done → board updated in place (task struck +
  reordered, counter 6 open/0 done → 5/1). App Home strip → "6 tasks in flight across 2 war
  rooms · 5 unassigned"; impact → 4 prospects / 30 tasks. Web board task chip → "1/6 tasks".
  Full cross-surface reactivity.
- **C14 Mark Applied** `[P]` Clicked Mark Applied → a prospect moved approved→applied (funnel
  "3 approved · 1 applied"), an "Applied — in progress" section appeared with a "Mark
  Submitted" button, and the web board reflected it (that prospect left Approved). Stage
  transition + cross-surface sync work. NOTE: board reflowed between find→click so it applied
  **Bob Woodruff** instead of DAV — an execution slip, not a product bug; UI is forward-only
  (Mark Submitted) so not cleanly revertible → reseed fixes it.

**Reseed cleanup added this session:** DAV prospect + `#grant-dav-charitable-service-trust`
war room (with 1 done/1 assigned task), Bob Woodruff now in "Applied" stage, a stray re-posted
BWF task board (from C8), the stray 2nd BWF "Untitled" canvas — all cleared by `reset clew`.

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

### R4-A — HIGH: `[email protected]` placeholder can leak into drafts (FIXED in code)
Finding #4 (cfemail) recurred in the local SDK harness draft — a literal `[email protected]`
landed in the application ("Portal/technical contact — [email protected]"). Root cause is
NOT the decoder (`_decode_cfemail` is correct and works on the live fetch path — the live
BWF brief correctly shows `grants@bobwoodrufffoundation.org`). It's that when a funder's
contact page **403s the fetch**, the agent falls back to **WebSearch snippets**, which carry
Cloudflare's visible `[email protected]` placeholder and never pass through the decoder — and
the agent copies it verbatim. Fix (committed `69791e1`): a FUNDER RESEARCH LOOP rule — never
output the literal `[email protected]`; if that's all you have, drop the email or say "see the
funder's contact page." Covers every path (search snippets + failed fetches). Pending deploy.

### Session 2 — Sun night deploy-free pass (summary)
Everything testable without a deploy, done tonight. **Code shipped to `main`** (all pending
tomorrow's Jay deploy): B6 duplicate-canvas fix + `canvas_id` persistence (`c5eb672`),
competitive-draft template in the prompts (`e972248`), cfemail guard (`69791e1`), plus the
reuse-engine one-pager and the north-star demo cut. **Live re-confirms (on the current
Railway build):** R2 ✅, R4 ✅ (fetch-path), B3 ✅, B4 ✅, B5 ✅ (logic), B10 ✅; B1/B2/R3
✅ (evidenced by existing live state). **Deferred to the deploy + reseed:** R1 (needs a
deploy event), the fresh Find-Grants-dependent observations (live R3, B2 modal path), B9
(reset — intentionally not risked), and the live test of the new template + canvas fix.
**Cleanup for reseed:** stale TEL HI `#grant-…` channels + `#grant-metta-fund` + the stray
2nd BWF "Untitled" canvas (Finding #9 bucket).

### B7-A — POLISH: deadline countdown disagreed across surfaces (FIXED in code)
Same deadlines, different "days left": for BWF (2026-07-20) the **Slack briefing** said "due
in 7 days" while the **web board** said "8d left"; Patterson "5" vs "6d". Root cause was two
differences: the briefing (`_days_until`) used `date.today()` = the SERVER's local date (UTC
on Railway), while the board (`daysUntil`) used `Math.ceil` on an instant-diff in the
VIEWER's browser TZ. Fix (committed): both now compute a **calendar-day difference anchored
to America/Los_Angeles** (the TZ the briefing already uses for the 9am run) — briefing via
`datetime.now(_BRIEFING_TZ).date()`, board via `Intl.DateTimeFormat(timeZone:
"America/Los_Angeles")` + UTC-midnight subtraction. Verified they now agree: BWF 8, Patterson
6, DAV 19. Test: `tests/test_briefing.py`. 76 pytest green. (Board change lives in
`web/app/page.tsx` — needs the Vercel deploy to go live, same as the Railway deploy.)

### B8/B10 cross-check — App Home + board + briefing agree
App Home: 3 approved, "1 task in flight across 1 war room". Web board: 3 Approved, BWF "5/6
tasks" (= 1 open). Briefing: "1 task open". All consistent. B10 impact-panel numbers not
separately audited this session but the three surfaces reconcile.

### B6-D — POLISH (recommendation, NOT changed): canvas tab title is "Untitled"
The canvas body H1 is `Application draft — <funder>`, but the canvas's own title (the tab
label) stays "Untitled" / "Your canvas title" — Slack doesn't promote the markdown H1 to
the canvas title. Cosmetic, and the API path to set a title is uncertain; deliberately left
alone the night before judging. Recommend as a post-submission polish (set the canvas title
when creating, if the API supports it).
