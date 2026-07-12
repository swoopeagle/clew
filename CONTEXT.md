# CONTEXT.md — Clew: current state & the road to submission

_Last updated: **Sunday July 12, 2026, afternoon** (Jay + Claude — cloud cutover).
Read §0a FIRST — it changes several things stated lower in this doc._

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
- Tests: **57 green.**

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
literally true. **Tests: 39 green** (was 33).

**First session (earlier July 11):** fixed a wrong-app bug, stood up **OAuth + Real-Time
Search live**, shipped the enforced-citation trust boundary, redesigned the war-room brief,
added the **award-history tool**, an **App Home trust surface** + **pipeline funnel**, fixed
markdown rendering, and produced the **Devpost draft, a redrawn architecture diagram, a
walkthrough-grounded video script, and 5 reference GIFs**.

## 1. The competition

- **Slack Agent Builder Challenge — "Agent for Good"**, $8k first / $4k second.
- **Deadline: Monday July 13, 2026, 5:00 PM PDT.** (July 13 is a *Monday* — the prior
  handoff mislabeled it Sunday.) Today is Sat July 11, so there are **two full days
  left** (Sun + Mon). Aim to submit by ~2 PM Monday, not at the wire.
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

## 3. What changed tonight (all committed + pushed to `main`)

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
  awards + recurring-funder insight). 9 MCP tools total now.
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
.venv/bin/python -m pytest              # 39 green
.venv/bin/ruff check . && .venv/bin/ruff format .
```

Secrets live in `.env` (gitignored): `A0BGUBZF23E` bot+app tokens, the three OAuth
creds, `ANTHROPIC_API_KEY`, **plus the two web-board values: `CLEW_BOARD_SECRET`
and `CLEW_API_TOKEN`** — these must be byte-identical to the values in the Vercel
project env (jays-projects/clew-board), or the 🌐 Web Board button emits unsigned
links that Vercel 403s ("link isn't valid"). Get them from Jay. **All of these were
pasted in chat during setup — rotate the Anthropic key + regenerate Slack tokens
right after submitting.**

## 5. Ian's action items (Sunday) + the Jay dependency

### Does Ian's list block Jay? — mostly NO. One coupling.

Jay owns the **web board / Vercel**. For Jay to do anything with the live board he needs:
(a) the bot running on Ian's machine, (b) a public tunnel to **`:3001`** (the board API),
and (c) that tunnel URL set as `CLEW_API_URL` on Vercel. Right now **only the `:3000`
OAuth tunnel is up — there is no `:3001` tunnel** — so the live board can't reach Ian's
machine, and Jay is blocked until Ian provides a `:3001` URL.

- **If Jay might touch the board Sunday → do this TONIGHT so you don't block him:**
  ```sh
  cloudflared tunnel --url http://localhost:3001   # separate tab from the :3000 one
  ```
  Grab the printed `https://<random>.trycloudflare.com` URL and send it to Jay (he sets
  it as `CLEW_API_URL` on Vercel). While app_oauth.py is running, `:3001` already serves
  `GET /api/board`, so the tunnel is all that's missing.
- **Everything else Ian does is independent of Jay** — video, Devpost, judge invites,
  deleting the old app, secret rotation. None of it touches Jay's work.

### Tomorrow (Sunday), priority order — all Ian unless noted

1. **Record the ~3-min video** — _Ian (+ video guy)._ THE long pole. Script +
   5 reference GIFs ready. First run `bash scripts/run_clew.sh`, click **Find Grants**
   once (~2–3 min) to repopulate the reseeded demo pipeline, and confirm `.env` has
   `CLEW_AGENT_MODEL` unset or `=claude-opus-4-8` (code already defaults to Opus).
2. **Devpost** — _Ian._ Create project, paste `docs/devpost.md` section-by-section,
   upload `docs/architecture.svg`, add "Built with" tags, then the video URL. Save as
   draft; submit by ~2 PM **Monday**.
3. **App hygiene** — _Ian, fresh eyes._ Delete OLD app `A0BG7GBD4CX` (**NOT**
   `A0BGUBZF23E` — verify the ID before clicking); confirm name "Clew" + icon (assets/);
   archive orphaned `#grant-…` channels from old runs.
4. **Judge access** — _Ian._ Invite slackhack@salesforce.com + testing@devpost.com as
   FULL members — AFTER #1–3 (they poke immediately). Create a clean `#demo` channel and
   pin the copy in `docs/judge-start-here.md`.
5. **Hosting through Mon 5 PM** — _Ian._ `bash scripts/run_clew.sh` on a plugged-in,
   awake machine. Add the `:3001` board tunnel (above) if the web board must stay up.
6. **Web board / Vercel** — _Jay + Ian._ Jay re-points `CLEW_API_URL` whenever the
   trycloudflare URL rotates, or the board 403s/502s. Unblocked once Ian shares `:3001`.
7. **Rotate secrets** — _Ian, AFTER submission Monday._ Anthropic key + Slack tokens
   (pasted in chat during setup).

### Do-tonight decision
The only thing worth doing tonight instead of tomorrow is the **`:3001` tunnel URL for
Jay** — and only if Jay plans to work on the board Sunday. If he's waiting on you either
way, stand it up now (2 min) and drop him the URL. Otherwise everything can wait for
tomorrow.

## 6. Roadmap (for Devpost "What's next")

- **Full funding history:** federal wins shipped (`get_org_award_history`); next,
  reconstruct **foundation** wins from public **990-PF grantee filings** (funder
  graph — every edge an IRS filing).
- **Salesforce Nonprofit Cloud** two-way sync (import pipeline, push awards). Salesforce
  owns Slack; the grants/development team is the beachhead.
- **Slack-native surfaces:** pipeline → Slack List, briefs → war-room Canvas (needs
  scopes → a reinstall; post-hackathon so it doesn't disturb the live OAuth install).
- **Deadline chasing:** scheduled reminders in the war room as a deadline nears.
