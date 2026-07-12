# CONTEXT.md — Clew: current state, features, and how to test everything

_Last updated: Saturday July 12, 2026, night — Jay's final handoff. This is the
single authoritative picture of the project. Read top to bottom before touching
anything._

---

## 1. The competition

- **Slack Agent Builder Challenge**, **"Slack Agent for Good"** track — $8,000 first / $4,000 second.
- **Deadline: Sunday, July 13, 2026, 5:00 PM PDT.**
- Judging criteria (equally weighted): Technological Implementation, Design, Potential Impact, Quality of the Idea.
- Tech requirement (≥1 of): Slack AI capabilities / **MCP server integration** (✓ we have a custom MCP server) / Real-Time Search API (designed, never exercised live — optional stretch).
- **Submission requires:** text description, architecture diagram (`docs/architecture.svg` — VERIFY it still matches; the web board and war rooms aren't on it), **~3-minute demo video**, and workspace access for **slackhack@salesforce.com** and **testing@devpost.com**.

## 2. What Clew is (elevator version)

A Slack-native grant agent for small nonprofits. It learns the org once, then finds
real, currently-available grants from three free public data sources, screens them
for fit, and posts a cited shortlist for human approval. Approved grants get their
own Slack "war room" channel with an AI brief, application-drafting help, and a
lifecycle board (Slack App Home + a live web board). **Trust boundary:** the agent
can only shortlist through the `save_qualified_prospect` tool, which requires real
citations — no invented funders, amounts, or deadlines, ever.

## 3. Complete feature inventory (all live-verified unless noted)

**Onboarding / org profile — three ways in:**
- Conversational: tell @clew about your org in chat → it gathers, confirms, saves (`agent/tools/org_profile_tool.py`).
- Website autofill in chat: paste your site URL → agent fetches + drafts the profile (`agent/tools/website.py`).
- Form with AI assist: "Set Up Org Profile" button (in chat replies AND App Home) opens a modal with a "✨ Draft with AI" section — website/notes in, every field prefilled for review (`listeners/views/org_profile_builder.py`, `listeners/actions/org_profile_actions.py`, `agent/profile_draft.py`). Structured inputs: 14-area multi-select + "other", number inputs, inline validation (`listeners/views/org_profile_submission.py`).
- After any save: confirmation card in chat with Find Grants / Edit buttons (`listeners/views/profile_saved_builder.py`) + App Home refresh.

**Grant discovery:**
- "Find Grants" (button or plain chat ask) runs a mandated full sweep: Grants.gov per program area, ProPublica foundations + 990 checks, USAspending award history — never stops after one source, never asks permission mid-search (SEARCH STRATEGY in `agent/agent.py`).
- Live progress statuses while it works ("🔍 Searching Grants.gov…") — assistant status in DMs, message updates for button runs (`listeners/events/tool_status.py`, `on_tool_use` in `agent/agent.py`).
- Qualified prospects post as cards: "Why it fits", meta fields, **evidence links labeled by source domain**, warm-path note, Approve/Pass (`listeners/views/prospect_card_builder.py`).

**Approval → war room (the flagship flow):**
- Approve → deadline modal → prospect moves to Approved → **a `#grant-<name>` channel is created**, approver invited, and the agent researches + posts a **grant brief** (summary, amount, deadline, requirements — cited, unknowns in a VERIFY list, pinned) (`listeners/grant_channel.py`). A link to the channel posts where you approved.
- **Inside a war room the agent knows the grant**: every message gets a [GRANT WAR ROOM] context block, so "help me apply to this grant" just works; in normal channels it plays the master-list role (`agent/channel_context.py`, `storage.get_prospect_by_grant_channel`).
- "✍️ Help me apply" button on approved cards → fit summary, full application outline, boilerplate paragraphs in the org's voice, VERIFY checklist (`listeners/actions/draft_application_action.py`).

**Pipeline management:**
- Lifecycle: qualified → approved → applied → submitted → awarded/declined (+ passed), with deadline, report-due, reported, and retro-note capture via modals (`listeners/views/lifecycle_builders.py`, `lifecycle_submissions.py`, `listeners/actions/prospect_actions.py`).
- App Home: hero, profile summary, 📊 pipeline stats, board with stage emojis, ⏰ due-within-7-days flags, rows linked to their original cards AND their war rooms, Refresh button, trust footer (`listeners/views/app_home_builder.py`, `board_builder.py`).
- Chat nav row under every reply (once a profile exists): 🔍 Find Grants · 📋 Saved Grants (renders the board right in chat) · Edit Org Profile · 🌐 Web Board. **All button replies land in the channel/thread where clicked** (`listeners/actions/origin.py`, `saved_grants_action.py`).

**Web board (frontend):**
- **https://clew-board.vercel.app** — Next.js 16 app in `web/` (Vercel project `clew-board`, on Jay's Vercel account): profile card, stat tiles, kanban by stage, deadlines, citations; polls every 15 s; light/dark.
- **Access is via signed per-org links only**: the 🌐 button carries `?org=<team>&sig=<hmac>` (`board_link()` in `webapi.py`); the Next proxy (`web/app/api/board/route.ts`) verifies the HMAC and 403s anything else — the bare URL does NOT open. Data flows: SQLite → `GET /api/board` on :3001 (bearer-token-protected, `webapi.py`) → cloudflared tunnel → Vercel proxy → page.

**Agent guts:**
- Claude Agent SDK (`ClaudeSDKClient`), model from `CLEW_AGENT_MODEL` (currently `claude-sonnet-5` for cost; default `claude-opus-4-8` — consider Opus for the video run).
- Custom in-process MCP server `clew-grant-tools`, 9 tools: `search_grants_gov`, `search_propublica_orgs`, `get_990_filings`, `search_usaspending`, `search_workspace`, `save_qualified_prospect`, `save_org_profile`, `fetch_org_website` (+ remote Slack MCP attaches only under OAuth).
- **Security lockdown (do not undo):** `disallowed_tools` blocks all filesystem/shell/web built-ins; allowlist uses the namespaced `mcp__clew-grant-tools__*` names. Before this, the bot could read its own source and `.env`. If you add a tool: register it in BOTH `create_sdk_mcp_server(tools=[...])` and `AGENT_TOOLS` in `agent/agent.py`.

## 4. Environment & secrets (names only — get values from Jay, never commit)

| Var | What |
|---|---|
| `ANTHROPIC_API_KEY` | agent inference (key was pasted in chats — rotate after the hackathon) |
| `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` | xoxb + xapp (Socket Mode) for the clew2 app `A0BGUBZF23E` |
| `CLEW_AGENT_MODEL` | currently `claude-sonnet-5` |
| `CLEW_BOARD_SECRET` | HMAC secret for signed board links — must match Vercel env |
| `CLEW_API_TOKEN` | bearer for `/api/board` — must match Vercel env |
| `CLEW_BOARD_URL` / `CLEW_WEB_API_PORT` | optional overrides (defaults: vercel URL, 3001) |
| `SLACK_CLIENT_ID/SECRET`, `SLACK_SIGNING_SECRET`, `SLACK_REDIRECT_URI` | only for the never-exercised OAuth path (`app_oauth.py`) |

Bot scopes already installed (after Saturday's reinstall): includes `channels:manage`, `channels:read`, `pins:write` — war rooms depend on these.

## 5. Ops runbook

```sh
# one-time
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.sample .env   # then fill values from Jay

# run the bot (EXACTLY ONE of these — both open Socket Mode; two = double-handling)
.venv/bin/python app.py         # normal: bot + board API on :3001
.venv/bin/python app_oauth.py   # only for the OAuth/warm-path experiment

# public web board (both must be running on the same machine as the bot)
cloudflared tunnel --url http://localhost:3001
# ⚠️ the trycloudflare URL CHANGES on every restart. When it does:
cd web && npx vercel env rm CLEW_API_URL production -y \
        && printf "<new-url>" | npx vercel env add CLEW_API_URL production \
        && npx vercel deploy --prod --yes

# checks
.venv/bin/python -m pytest      # 33 tests, must stay green
.venv/bin/ruff check . && .venv/bin/ruff format .
cd web && npm run build         # Next build must pass
```

**During judging the bot + tunnel must be running on someone's machine.** Decide
whose. The Vercel project is on Jay's account — he must run the redeploy (or add
you as a member).

## 6. THE end-to-end test workflow (run this exact sequence after any change)

Prep: to test onboarding fresh, clear state first: stop the bot, `rm clew.db`,
restart (or just skip steps 1–3 if a profile already exists).

1. **Welcome:** @mention Clew in a channel with no other text → welcome card with trust line + Set Up Org Profile button.
2. **AI form fill:** click Set Up Org Profile → modal shows "✨ Draft with AI" → enter a real nonprofit website (e.g. `telhi.org`) → Draft with AI → "drafting…" view → form returns fully prefilled → tweak → Save Profile. Expect: confirmation card in DM with Find Grants button; App Home shows the profile. (Also test the modal's validation: min $50k / max $5k must show an inline error.)
3. **Conversational alternative:** in a DM, "our geography is actually Oakland too" → agent confirms → saves → confirmation card.
4. **Find Grants:** click Find Grants (from the confirmation card or a channel nav row) → progress message updates through Grants.gov / ProPublica / USAspending → several prospect cards with domain-labeled citations → summary reply, nav row beneath. Verify the reply landed in the channel/thread you clicked in. Click a citation — must be a real page.
5. **Approve → war room:** click Approve on a card → deadline modal opens instantly → pick a date, Save → card flips to ✅ Approved with "✍️ Help me apply" → "📂 Opened #grant-…" message → the channel exists, you're in it, intro cycles live statuses, then the **brief** posts (check: amounts/deadlines either cited or in the VERIFY list — nothing invented) and is pinned.
6. **War-room context:** in that channel, "@clew can you help me apply to this grant?" → it must dive in WITHOUT asking which grant. Ask "when's the deadline?" → answers from the stored date.
7. **Pass:** Pass another card → flips to ❌, no channel created, board updates.
8. **Lifecycle:** on App Home, walk the approved grant: Mark Applied → Submitted → Awarded (modal: report due + retro) → board shows 🏆 with report date; Mark Reported afterward. Verify the board refreshed in place at each step.
9. **Saved Grants:** click 📋 in a channel nav row → board renders in that channel thread, rows link to cards and war rooms.
10. **Web board:** click 🌐 Web Board → opens `clew-board.vercel.app?org=…&sig=…` showing the same pipeline; change a stage in Slack → board updates within ~15 s. Negative tests: open the bare URL and a tampered `sig` → both must show the invalid-link message (proxy returns 403).
11. **Suite:** `pytest` (33 green) + `ruff check .` + `cd web && npm run build`.

## 7. Known gaps & rough edges (honest list)

- **OAuth / Real-Time Search API never exercised live.** `app_oauth.py` is believed correct (combined Socket-Mode + OAuth HTTP runner) but untested. Standing it up = ngrok/tunnel on :3000, redirect URL in the Slack config matching `SLACK_REDIRECT_URI`, client id/secret in `.env`, visit `/slack/install`. Would light up warm-path workspace search + a second required technology. Optional — MCP already satisfies the requirement.
- **Duplicate Slack apps:** the workspace has an older `clew` and ours (`clew2`, `A0BGUBZF23E`). Delete the old one and rename ours to "Clew" (api.slack.com → Basic Information). Icons ready in `assets/`.
- **Tunnel URL rotation** (see runbook) — the #1 way the web board silently dies.
- **Sessions are in-memory** (`thread_context/store.py`) — bot restart forgets conversation threads (DB state is safe). Fine for demo.
- **Model quality:** running Sonnet 5 for cost. The brief/outline prose is noticeably better on Opus — one-line `.env` flip for the video run.
- **`docs/architecture.svg` is stale** (predates web board + war rooms).
- **Board link on old messages:** nav buttons render at post time; old messages keep old buttons. Fresh interactions have the current row.

## 8. Remaining submission checklist (in order)

1. ~3-min demo video. Suggested arc: paste website → AI-drafted profile → Find Grants (live statuses) → cited card, click the citation → Approve → **war room spawns with the brief** → ask @clew for application help in the room → web board updating live. Lead with the problem (solo EDs, $200+/mo tools) and the trust line.
2. Devpost text: impact-first; name the tech (Claude Agent SDK, custom MCP server, Block Kit, Next.js/Vercel, signed multi-tenant links); the no-fabrication trust boundary is the differentiator.
3. Invite slackhack@salesforce.com + testing@devpost.com to the workspace.
4. Update/redraw `docs/architecture.svg`; refresh README's status section.
5. Duplicate-app cleanup + set the app icon.
6. Decide judging-weekend hosting (bot + tunnel) and keep it alive.
