# CONTEXT.md — Clew: current state & the road to submission

_Last updated: **Saturday July 11, 2026, late night** (Ian + Claude session). This
supersedes the prior handoff. Read top to bottom before touching anything._

---

## 0. TL;DR of tonight

The build is **done and live-verified end to end**. What's left is almost entirely
**submission logistics** (video, judge access, hosting) — not code.

Tonight we: fixed a wrong-app bug, stood up **OAuth + Real-Time Search live**,
shipped the **enforced-citation trust boundary** + a batch of hardening (from a
Fable audit), redesigned the war-room brief, added a new **award-history tool**, an
**App Home trust surface** + **pipeline funnel**, fixed markdown rendering, and
produced the **Devpost draft, a redrawn architecture diagram, a walkthrough-grounded
video script, and 5 reference GIFs**.

## 1. The competition

- **Slack Agent Builder Challenge — "Agent for Good"**, $8k first / $4k second.
- **Deadline: Sunday July 13, 2026, 5:00 PM PDT.** Aim to submit by ~2 PM Sunday.
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
- **Run `app_oauth.py`, NOT `app.py`.** OAuth is installed; `app_oauth.py` is the
  runner that serves the Socket-Mode bot + OAuth + the board API on :3001. Running
  both = double-handling.
- **OAuth install is persisted** to `data/installations/` — warm-path/Real-Time
  Search survives restarts and tunnel death. The `:3000` tunnel is only needed to
  (re)install OAuth, not for normal running.
- **DB was re-seeded** tonight for a clean onboarding GIF. Current `clew.db` =
  **TEL HI profile only, no prospects.** Click **Find Grants** once (~2–3 min) to
  repopulate before recording. (Ian's local DB is now authoritative; Jay's older DB
  is NOT synced, and the old `#grant-…` channels in the sidebar are orphaned
  leftovers — ignore or archive.)
- **Full Find Grants sweep takes ~2–3 min** (6 program areas × 3 sources + warm-path
  + 990 checks); the war-room **brief takes ~1–2 min**. The video script speed-ramps
  both — do NOT show them real-time.

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

## 4. Ops runbook

```sh
# run the bot (EXACTLY ONE; app_oauth.py is the one — OAuth is installed)
.venv/bin/python app_oauth.py           # bot + OAuth + board API :3001
# OR, for judging weekend (auto-restart + caffeinate):
bash scripts/run_clew.sh

# OAuth (re)install only if needed — tunnel on :3000, visit <tunnel>/slack/install
cloudflared tunnel --url http://localhost:3000

# for the video recording: better prose on Opus
#   set CLEW_AGENT_MODEL=claude-opus-4-8 in .env, restart

# checks
.venv/bin/python -m pytest              # 33 green
.venv/bin/ruff check . && .venv/bin/ruff format .
```

Secrets live in `.env` (gitignored): `A0BGUBZF23E` bot+app tokens, the three OAuth
creds, `ANTHROPIC_API_KEY`. **These were pasted in chat during setup — rotate the
Anthropic key + regenerate Slack tokens right after submitting Sunday.**

## 5. Remaining checklist (in priority order, with owners)

1. **Record the ~3-min video** — _Ian + video guy._ Script + 5 reference GIFs ready.
   Re-seed reminder: click Find Grants first to repopulate the demo pipeline. Flip to
   Opus for the take. (THE long pole — worth more than any feature.)
2. **Devpost** — _Ian._ Create project, paste `docs/devpost.md`, fill fields, upload
   video. (Can scaffold everything except the video tonight.)
3. **Judge access** — _Ian._ Invite slackhack@salesforce.com + testing@devpost.com as
   FULL members. Do AFTER cleanup + video (they poke immediately). Pin a "start here"
   in a clean #demo channel.
4. **App hygiene** — _Ian, morning/fresh eyes._ Delete OLD app `A0BG7GBD4CX` (NOT
   `A0BGUBZF23E`); confirm name "Clew" + icon (assets/).
5. **Hosting through Sun 5 PM** — _Ian._ `bash scripts/run_clew.sh` on a plugged-in,
   awake machine. The `:3001` board tunnel + Vercel re-point is the web-board risk.
6. **Web board / Vercel** — _Jay + Ian._ Decide ownership; if the trycloudflare URL
   rotates, re-point `CLEW_API_URL` on Vercel (see prior notes) or the board 403s.
7. **Rotate secrets** — _Ian, after submission._

## 6. Roadmap (for Devpost "What's next")

- **Full funding history:** federal wins shipped (`get_org_award_history`); next,
  reconstruct **foundation** wins from public **990-PF grantee filings** (funder
  graph — every edge an IRS filing).
- **Salesforce Nonprofit Cloud** two-way sync (import pipeline, push awards). Salesforce
  owns Slack; the grants/development team is the beachhead.
- **Slack-native surfaces:** pipeline → Slack List, briefs → war-room Canvas (needs
  scopes → a reinstall; post-hackathon so it doesn't disturb the live OAuth install).
- **Deadline chasing:** scheduled reminders in the war room as a deadline nears.
