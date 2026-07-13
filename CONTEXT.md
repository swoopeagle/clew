# CONTEXT.md — Clew: current state & the road to submission

_Last updated: **Sunday July 12, 2026, LATE NIGHT** — tip commit `bf2e07e`; agent
sessions now persist across deploys; **Ian: your Monday checklist, bug-triage
results, and Railway token runbook are all in §5.** Read §0a then §5 FIRST —
§0 and §3 are Fri/Sat history and several details there are superseded._

---

## 0a. ☁️ SUNDAY UPDATE — Clew now runs on Railway. Laptops are retired.

Everything below this section that talks about laptops, tunnels, `run_clew.sh`,
or "Ian's machine is authoritative" is **obsolete**. Current truth:

- **Production host:** Railway (Jay's account, project `clew`), permanent URL
  **https://clew-production.up.railway.app** — one domain serves the Socket-Mode
  bot + OAuth (`/slack/install`, `/slack/oauth_redirect`) + the board API
  (`/api/board`). Dockerized (`Dockerfile` + `entrypoint.sh`); volume at
  `/app/data` holds `clew.db` + OAuth installs, so state survives every deploy.
  A non-root user is REQUIRED in the container — the agent CLI refuses
  bypassPermissions as root (this bit us; the entrypoint handles it).
- **⚠️ IAN: the app-level token was REGENERATED during cutover** to lock the
  sleeping laptop out cleanly. Your local `.env`'s `xapp-…` is dead and
  `run_clew.sh` will fail auth — expected, just stop it. **Do NOT regenerate any
  tokens to "fix" it** (that would kill the Railway host). Need local dev? Get
  the current values from Jay or the Railway dashboard.
- **OAuth / Real-Time Search re-installed onto the Railway volume** (Jay ran
  `/slack/install` against the Railway redirect URL — registered in the Slack
  app config). Warm path is live and now survives everything.
- **Web board fully live end-to-end:** Slack 🌐 button → signed org link →
  Vercel → Railway. Verified, including tampered-signature 403. No `:3001`
  tunnel exists or is needed, ever again. The old "Jay dependency" in §5 is gone.
- **Railway DB started fresh** — Ian's laptop `clew.db` (and its GIF-ready
  seed) is a dead artifact. Re-seed in ~4 min: DM `telhi.org` → confirm profile
  → Find Grants.
- **NEW: demo reset** — DM Clew `reset clew` → confirm → wipes profile +
  prospects, archives war rooms, App Home back to onboarding. Use freely
  between video takes.
- **Deploys now:** `git push` then `npx @railway/cli up -d` from repo root
  (CLI currently authed on Jay's machine; `railway logs` for prod logs).
- **Sunday-evening wow bundle (all live — SHOW THESE IN THE VIDEO):**
  1. **Proactive morning briefing** — DM Clew `clew briefing` → instant pipeline
     briefing (⏰ deadlines ≤7d with war-room links, 🔍 awaiting review, 📮 awaiting
     funder, 📄 reports due) AND that DM becomes the daily 9am PT home (background
     loop in the Railway process). This is the "agent that works while you sleep"
     beat — fire it on demand for the camera.
  2. **War-room channel topics** — every grant channel shows `📅 Due … · 💰 … ·
     brief pinned` in its topic, refreshed when the deadline is set.
  3. **Canvas application drafts** — "Help me apply" now writes the outline into
     the war room's channel canvas (living doc, team-editable) when OAuth's user
     token is available; falls back to a chat message otherwise.
- **Sunday-afternoon bundle #2 (from Jay's live-test feedback — all shipped, 4 commits):**
  1. **Deadlines auto-captured** — `save_qualified_prospect` now takes
     `deadline_date` (grants.gov close dates land automatically, normalized to
     ISO) + `application_url` (citation-gated). The Approve deadline popup only
     appears when Clew genuinely couldn't find a deadline; the war-room brief
     backfills one it researches (row + channel topic + Home board).
  2. **Real apply links** — new `fetch_webpage` agent tool (any funder page;
     fetched content pinned as untrusted data in the system prompt). "Help me
     apply" output must START with `🔗 Apply here:` + confirmed deadline;
     "VERIFY on the funder's site" is only allowed after an actual fetch
     attempt. Briefs put the apply link first in sources ("Apply here").
  3. **Task designation engine** — new `grant_tasks` table. In a war room:
     🧩 Designate Tasks (agent proposes 3-6 action items from the requirements)
     → each row has an *Assign to…* people picker → assignee gets a threaded
     @-ping → ✅ Done strikes it through. Conversational too: "@Clew have @sam
     pull our audited financials" creates an owned task (`assign_grant_task`
     tool, war-room-scoped). Board rebuilds from DB on every touch.
  4. **Grant-scoped war-room buttons** — replies inside a `#grant-…` channel now
     carry ✍️ Draft Application / 🧩 Designate Tasks / 📋 Tasks / 🌐 Grant
     Website / 📅 Set Deadline (only while unknown) instead of the org-wide
     nav; a "Quick actions" message posts under the pinned brief. Org-wide
     buttons (Find Grants / Saved Grants / Edit Profile / Web Board) stay in
     DMs + general channels. Fixed: app_mention was stripping ALL `<@U…>`
     mentions, which would have eaten task assignees.
  5. **Real funder research (the big one — from Jay's Bob Woodruff live test:
     briefs were "VERIFY everything + a ProPublica link")** — root cause was
     structural: the agent had no web search (couldn't FIND a funder's site)
     and fetched pages had their links stripped (couldn't navigate one).
     Now: the built-in **WebSearch is enabled** for the agent (untrusted-data
     rule extended to search results; everything else stays disallowed);
     `fetch_webpage` output lists the page's LINKS incl. mailto contacts so
     the agent crawls homepage → grants page → application portal; war-room
     briefs are REQUIRED to run the research loop and now carry `apply_url`
     (the real portal), `criteria_url`, `contact`, who's-eligible bullets,
     and an **AI eligibility analysis** cross-referencing the org profile —
     all rendered prominently in the pinned brief, and the portal URL is
     persisted so 🌐 Grant Website opens where you actually apply, not
     ProPublica. 403-blocked sites (Cloudflare TLS fingerprinting — e.g.
     bobwoodrufffoundation.org) fall back to targeted WebSearch queries;
     fetch sends browser-like headers. Draft-application uses the same loop.
  6. **Canvas draft fix (Jay: "I DONT see any channel canvas")** — the canvas
     existed but Slack hides channel canvases; the success message now
     deep-links straight to the canvas doc (workspace `/docs/` URL) and names
     the canvas icon as the manual path. A re-draft REPLACES the existing
     canvas via `canvases.edit` instead of silently dumping to chat
     (channels only allow one canvas). War-room topics truncate long
     free-text grant sizes.
  7. **Web board premium teal makeover (live on Vercel, same URL)** — brand
     unified to the teal logo family: animated spiral logo that draws itself
     in, Fraunces serif wordmark, count-up stat tiles, staggered card
     entrances, deadline/source pill chips, stage-tinted column headers,
     shimmer skeleton while loading, pulsing Live indicator, full dark mode,
     `prefers-reduced-motion` respected, tagline removed. Zero new deps;
     web/ only (no bot deploy involved).
  8. **Final wow bundle (Sun evening, from the rubric deep-dive)** — tasks now
     surface EVERYWHERE: the morning briefing lists each grant's open/unassigned
     task counts with war-room links; App Home shows a "🧩 N tasks in flight"
     line under the funnel; and the 9am pass (plus on-demand `clew briefing`)
     posts **nudges INTO war rooms** when a deadline is ≤3 days or tasks sit
     unowned — channel @-mentions ping the assignees (DMs can't). App Home also
     gained a "📊 What Clew has done for you" impact panel computed live from
     the DB (prospects researched, citations verified, war rooms opened, tasks
     handed off, est. staff-hours saved). The web board renders 🧩 done/total
     task chips per card (board API now ships per-prospect task counts).
     **VIDEO NOTE: fire `clew briefing` on camera — briefing lands in the DM
     AND nudges pop into war rooms simultaneously. Best cold open we have.**
  9. **Discoverable commands** — ask @clew "what can you do" and it recites the
     full capability list including the two magic DM phrases (`clew briefing`,
     `reset clew`), which are intercepted before the agent and were previously
     unknown to it.
  10. **Session persistence (Ian's Blocker — Sunday night)** — agent sessions now
      survive deploys: `agent_sessions` table on the volume + the agent CLI's
      state dir moved to the volume (`CLAUDE_CONFIG_DIR`) + stale-session
      retry-as-fresh. Plus: App Home republishes after every prospect save,
      Cloudflare `data-cfemail` decodes to real contact emails, ambiguous
      prospect references get a clarifying question. Full triage in §5.
- Tests: **70 green.**

## 0. TL;DR

The build is **done and live-verified end to end**. What's left is almost entirely
**submission logistics** (video, judge access, hosting) — not code.

**This second session (July 11 late night):** refreshed the README to match the real
product (it still claimed "WIP, approve flow unverified, 6 tools"), added a paste-ready
**judge "start here" pin** (`docs/judge-start-here.md`), tracked the previously-untracked
`scripts/run_clew.sh`, and shipped **5 hardening fixes** from a pre-judging code review:
(1) Approve is now an **atomic DB claim** — a double-click can't spawn a duplicate war
room; (2) removed the unused **Slack-MCP server** (was arbitrary "act as the user" prompt-
injection surface); (3) Find Grants no longer leaves "Searching…" frozen on error; (4)
board bearer check is now **timing-safe**; (5) the citation gate now enforces **provenance**
(a URL a tool actually returned), not just the host — so the trust-boundary pitch is now
literally true. **Tests: 39 green** (was 33; **now 70** after Sunday's work — §0a).

**First session (earlier July 11):** fixed a wrong-app bug, stood up **OAuth + Real-Time
Search live**, shipped the enforced-citation trust boundary, redesigned the war-room brief,
added the **award-history tool**, an **App Home trust surface** + **pipeline funnel**, fixed
markdown rendering, and produced the **Devpost draft, a redrawn architecture diagram, a
walkthrough-grounded video script, and 5 reference GIFs**.

## 1. The competition

- **Slack Agent Builder Challenge — "Agent for Good"**, $8k first / $4k second.
- **Deadline: Monday July 13, 2026, 5:00 PM PDT — that is TOMORROW.** (It is now
  late Sunday night 7/12; code is frozen and everything is live on Railway.) Aim
  to submit by ~2 PM Monday, not at the wire.
- Judging (25% each): Technological Implementation, Design, Potential Impact, Quality of the Idea.
- Submission needs: text (draft ready → `docs/devpost.md`), architecture diagram
  (`docs/architecture.svg`, freshly redrawn), **~3-min demo video** (script ready →
  `docs/video-script.md`, NOT yet recorded), and workspace access for
  slackhack@salesforce.com + testing@devpost.com.

## 2. ⚠️ Critical gotchas (read these first)

- **The live app is `A0BGUBZF23E`** ("clew2"). There is an OLD duplicate,
  `A0BG7GBD4CX`, that Ian's machine was mistakenly running earlier — it lacks the
  war-room scopes. `.env` now points at `A0BGUBZF23E` (correct). **When cleaning up
  duplicate apps, delete `A0BG7GBD4CX`, NOT `A0BGUBZF23E`.**
- ~~Run app_oauth.py / tunnels / laptop DB~~ — **superseded by §0a: everything runs
  on Railway now.** Never start a local bot while Railway is up (split-brain: Socket
  Mode round-robins events across connections). Real-Time Search remains LIVE, now
  persisted on the Railway volume. Old `#grant-…` channels from laptop-era DBs are
  orphans — archive by hand or ignore.
- **Full Find Grants sweep takes ~2–3 min** (6 program areas × 3 sources + warm-path
  + 990 checks); the war-room **brief takes ~1–2 min**. The video script speed-ramps
  both — do NOT show them real-time.
- **Demo reset:** DM Clew `reset clew` → confirmation card → wipes the org profile +
  all prospects and ARCHIVES the war-room channels (bots can't hard-delete channels).
  Perfect for re-running the onboarding demo from scratch.

## 3. What changed SATURDAY night (historical — Sunday's much larger changes live in §0a)

- **App fix:** switched `.env` from the old app to `A0BGUBZF23E` (restores
  `channels:manage`/`pins:write` → war rooms work).
- **OAuth + Real-Time Search LIVE:** installed via `app_oauth.py` + a cloudflared
  `:3000` tunnel; verified `search.messages` returns real results; warm-path
  detection fires in Find Grants.
- **Enforced trust boundary:** `save_qualified_prospect` now REJECTS any prospect
  whose `fit_sources` aren't real URLs on grants.gov/propublica.org/usaspending.gov.
  Promise → mechanism. (+ dedup guard, dropped bogus `sam` source enum.)
- **Resilience:** 15s timeouts + error handling on all grant APIs + workspace search
  (no more frozen "Searching…").
- **Channel awareness:** the agent reads recent channel history and grounds replies
  in the team's actual discussion.
- **New tool `get_org_award_history`:** an org's OWN federal award history from
  USAspending (by recipient) — verified live (Mission Neighborhood Centers → 5 cited
  awards + recurring-funder insight). 9 MCP tools as of Saturday (**now 11 +
  built-in WebSearch** — fetch_webpage and assign_grant_task landed Sunday, §0a).
- **Brief redesign:** agent emits JSON → scannable Block Kit (Amount/Deadline
  side-by-side, Confirmed/Verify/Next, telegraphic bullets). Falls back to plain
  text if JSON parse fails.
- **App Home:** pipeline **funnel** header + per-stage counts; **"What Clew can see"**
  trust/observability section (live channel list).
- **Markdown rendering fix:** "Help me apply" draft + Find Grants summary now render
  as Slack `markdown` blocks (no more literal `**`).
- **Demo polish:** on-brand loading copy, friendly errors, deadline shows on Applied
  rows, approve survives a dead trigger_id.
- **Deliverables:** `docs/devpost.md`, `docs/architecture.svg` (redrawn),
  `docs/video-script.md` (walkthrough-grounded), and 5 reference GIFs in Ian's
  Downloads (onboarding, approve→war room, brief, board, award-history).

## 4. Ops runbook — ☁️ THE BOT NOW RUNS ON RAILWAY (Sunday cutover, supersedes laptops)

**Production host: Railway** (Jay's account, project `clew`, service `clew`).
Permanent URL: **https://clew-production.up.railway.app** — serves Socket Mode bot +
OAuth (`/slack/install`, `/slack/oauth_redirect`) + board API (`/api/board`) on one
domain. Persistent volume at `/app/data` holds `clew.db` + OAuth installs — state
survives every restart/deploy. Vercel's `CLEW_API_URL` points here permanently:
**no more tunnels, no more laptops, no run_clew.sh.**

⚠️ **IAN: your local runner is intentionally locked out.** The app-level token was
regenerated during the migration, so `run_clew.sh` on your machine now fails auth —
that's expected, just stop it. Do NOT regenerate tokens to get back in; that would
kill the Railway host. All laptop instructions below/above in this doc are obsolete.

```sh
# deploy a change (from repo root, after git push):
npx @railway/cli up -d                  # rebuild + deploy to Railway
npx @railway/cli logs                   # tail production logs
npx @railway/cli variables              # inspect env (set with --set "K=V")
# Railway CLI is authed on Jay's machine; Ian: `railway login` w/ Jay's ok, or ask Jay.

# for the video recording: better prose on Opus
#   railway variables --set "CLEW_AGENT_MODEL=claude-opus-4-8" (then redeploy)

# checks (local dev)
.venv/bin/python -m pytest              # 70 green
.venv/bin/ruff check . && .venv/bin/ruff format .
```

Secrets live in `.env` (gitignored): `A0BGUBZF23E` bot+app tokens, the three OAuth
creds, `ANTHROPIC_API_KEY`, **plus the two web-board values: `CLEW_BOARD_SECRET`
and `CLEW_API_TOKEN`** — these must be byte-identical to the values in the Vercel
project env (jays-projects/clew-board), or the 🌐 Web Board button emits unsigned
links that Vercel 403s ("link isn't valid"). Get them from Jay. **All of these were
pasted in chat during setup — rotate the Anthropic key + regenerate Slack tokens
right after submitting.**

## 5. Ian's submission-day checklist (Monday) — REWRITTEN Sunday night, supersedes every earlier version of this section

### Hosting: NOTHING TO DO. Seriously.

The bot runs **24/7 on Railway** (Jay's account, project `clew`) and has been verified
live all weekend. The web board is permanently wired to it — **no tunnels exist
anymore, anywhere**. Explicitly:

- ❌ Do **NOT** run `scripts/run_clew.sh` — a second connected instance splits Socket
  Mode events with production (and your old xapp token is dead anyway; auth will fail).
- ❌ Do **NOT** regenerate any Slack token "to fix" that auth failure — a regen kills
  the Railway host mid-judging.
- ❌ Do **NOT** touch Railway, Vercel, or cloudflared. There is nothing to keep alive,
  no laptop that must stay awake, no URL that rotates.

### Does Ian need Railway access? Not required — but a project token is set up for you.

Nothing on the Monday list needs Railway. For debugging/deploying independently, Jay
is issuing you a **project token** (Railway dashboard → project `clew` → Settings →
Tokens; scoped to `production`, revocable after the hackathon — no account sharing).
Use it as an env var with the CLI, no login needed:

```sh
export RAILWAY_TOKEN=<token from Jay>
npx @railway/cli logs          # tail prod logs
npx @railway/cli variables     # inspect env
npx @railway/cli up -d         # deploy (from repo root, after git pull)
```

Deploy etiquette: `git pull` first, run `pytest` (70 green) before `up -d`, never
deploy while the video is being recorded, and never touch the Slack tokens.

### Ian's Sunday-night bug triage — status after fixes (all deployed)

1. **Session amnesia (Blocker) — FIXED, your diagnosis was right.** Two layers: the
   session map was in-memory (every deploy wiped it — there were ~6 deploys while you
   tested), and the agent CLI's session transcripts lived on the ephemeral container
   FS. Now: sessions persist to an `agent_sessions` table on the volume, the CLI's
   state dir moved to the volume (`CLAUDE_CONFIG_DIR=/app/data/claude-home`), and a
   stale session id degrades to a fresh conversation instead of an error. The
   conversational "say save it" flow survives deploys now.
2. **Bare "approve" misfire — same root cause** (a wiped session losing the thread);
   also added a prompt rule: ambiguous prospect references get a clarifying question,
   never a guess.
3. **App Home stale after Find Grants — FIXED**: the board republishes after every
   prospect save (Slack never refreshes App Home on its own).
4. **`[email protected]` — FIXED**: that's Cloudflare's email obfuscation; the fetcher
   now decodes `data-cfemail` so the real address (usually the grants contact) shows.
5. **Stray Russian word** — one-off sampling artifact on sonnet-5; no code lever worth
   touching the night before judging. Recording on Opus makes it even less likely.
6. **Sig visible in board URL** — by design: the HMAC link IS the auth (documented).
7. **Warm-path not connected** — expected: needs one visit to
   https://clew-production.up.railway.app/slack/install (persists to the volume).
8. **Vague-ask clarifying question** — deliberately NOT changed: the full-sweep-
   without-asking behavior was an explicit fix after earlier feedback; reverting it
   the night before judging risks the "agent asks permission" regression.
9. **Duplicate `-3` channels** — yours to archive (or `reset clew` + re-seed).

### Monday, priority order

1. **Record the ~3-min video** — THE long pole. `docs/video-script.md` + GIFs ready.
   **New best cold open:** DM `clew briefing` on camera — the briefing lands AND
   nudges pop into the war rooms in the sidebar simultaneously ("It's 9am. Nobody
   asked Clew for anything."). Get a citation click into the first 45 seconds. For
   best prose, ask Jay to set `CLEW_AGENT_MODEL=claude-opus-4-8` on Railway first.
2. **Stage the workspace BEFORE judge invites** — populated board (one Find Grants
   run), one lived-in war room: 🧩 Designate Tasks → assign two via the people picker,
   mark one ✅ done, leave one unassigned (so briefing rollup + nudges have content);
   `clew briefing` opted in; brief pinned with the apply link visible.
3. **Devpost** — paste `docs/devpost.md`, upload `assets/devpost-thumbnail.png` (3:2
   card) + `docs/architecture.pdf`, tag technologies (Claude Agent SDK, custom MCP
   server, Real-Time Search API), add the video URL. Sandbox URL:
   https://slackathon-hny7616.slack.com. Save as draft early.
4. **App hygiene** — delete OLD app `A0BG7GBD4CX` (**NOT** `A0BGUBZF23E` — verify the
   ID before clicking); archive orphaned `#grant-…` channels from old test runs
   (or DM `reset clew` + re-seed for a pristine pipeline).
5. **Judge access** — invite slackhack@salesforce.com + testing@devpost.com as FULL
   members, AFTER #2–4. Clean `#demo` channel with `docs/judge-start-here.md` pinned.
6. **Submit by ~2 PM** (deadline 5 PM PDT — leave buffer for Devpost hiccups).
7. **AFTER submission: rotate secrets with Jay** — Anthropic key, Slack tokens/secrets,
   CLEW_BOARD_SECRET/CLEW_API_TOKEN (several were pasted in chats during the build).

## 6. Roadmap (for Devpost "What's next")

- **Full funding history:** federal wins shipped (`get_org_award_history`); next,
  reconstruct **foundation** wins from public **990-PF grantee filings** (funder
  graph — every edge an IRS filing).
- **Salesforce Nonprofit Cloud** two-way sync (import pipeline, push awards). Salesforce
  owns Slack; the grants/development team is the beachhead.
- **Slack-native surfaces:** pipeline → Slack List, briefs → war-room Canvas (needs
  scopes → a reinstall; post-hackathon so it doesn't disturb the live OAuth install).
- **Deadline chasing:** scheduled reminders in the war room as a deadline nears.
