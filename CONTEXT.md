# CONTEXT.md — Where Clew is at, and what's left

_Last updated: Friday July 11, 2026, evening (Jay's session). For Ian (or anyone)
continuing development. Read this top to bottom before touching code._

---

## The competition

- **Slack Agent Builder Challenge**, **"Slack Agent for Good"** track — $8,000 first / $4,000 second.
- **Deadline: Sunday, July 13, 2026, 5:00 PM PDT.**
- Judging criteria (equally weighted): Technological Implementation, Design, Potential Impact, Quality of the Idea.
- Tech requirement: use at least one of **Slack AI capabilities / MCP server integration / Real-Time Search API**. We have a **custom MCP server** (✓ satisfied) and are going for the **Real-Time Search API** as a second (see "Remaining work").
- **Submission requires:** text description, architecture diagram (`docs/architecture.svg` — needs a check that it still matches), **~3-minute demo video of the working app**, and a sandbox workspace shared with **slackhack@salesforce.com** and **testing@devpost.com**.

## Current state (short version)

The core loop is verified live in the `slackathon` workspace: DM/@mention → Claude
agent → three real grant APIs → cited prospect cards. Today added ~10 commits of
integration fixes, a full design pass, an agent security lockdown, chat-first
onboarding, website autofill, and live progress UX. All 24 tests pass; ruff clean.

**Not yet verified live:** the Approve → deadline-modal → board round-trip and the
lifecycle transitions (wired + unit-tested, just needs clicks), and the whole
OAuth/warm-path (Real-Time Search) flow.

## What changed today (commit by commit, oldest first)

1. **`398a3d7` Fix integration blockers** —
   - `pyproject.toml`: dev extra referenced `bolt-python-support-agent-claude[test]` (template artifact, not on PyPI) → `pip install -e ".[dev]"` was broken on any fresh machine. Now `clew[test]`. Also added missing `storage*` to packages.
   - `agent/agent.py`: model now pinned via `CLEW_AGENT_MODEL` env (default `claude-opus-4-8`).
   - `listeners/actions/prospect_actions.py`: Approve/Pass now republish App Home (board used to go stale); deadline modal opens **before** other calls (3-second `trigger_id` window); warm-path client respects `SLACK_API_URL`.
   - App Home got a manual **Refresh** button (`clew_refresh_home`).
   - **`app_oauth.py` was fundamentally broken**: it served OAuth over HTTP but never opened a Socket Mode connection, so with `socket_mode_enabled: true` in the manifest it completed installs but **never received a single event**. Now it runs both in one asyncio loop (aiohttp for `/slack/install` + `/slack/oauth_redirect`, Socket Mode for events). **Run exactly one of `app.py` / `app_oauth.py`, never both** — each opens its own socket, so both running = every event handled twice.
2. **`bb20264` Org profile modal v2 + board polish** — program areas are a `multi_static_select` over 14 curated areas (`CURATED_PROGRAM_AREAS` in `org_profile_builder.py`, value==label) plus a free-text "Other" input; grant sizes are `number_input`s; inline validation via `ack(response_action="errors")` (min≤max, ≥1 program area) in `parse_org_profile_values()` (`org_profile_submission.py`). Board: stage emojis, ⏰ marker for deadlines within 7 days, warmer empty state. **Slack API landmines encoded in tests:** never send empty `initial_value` on number_input, never send `initial_options` not byte-identical to `options`.
3. **`5ea851d` App Home v2 + card polish** — hero, 1️⃣2️⃣3️⃣ onboarding when no profile, two-column profile summary fields, 📊 pipeline summary, trust footer; prospect cards got "Why it fits", fields meta, evidence links labeled by domain.
4. **`584756b` ⚠️ SECURITY: agent tool lockdown** — the SDK agent ran with `permission_mode="bypassPermissions"` and an `allowed_tools` list of **bare names that matched nothing** (SDK MCP tools are namespaced `mcp__clew-grant-tools__<name>`). Net effect: the agent had Claude Code's built-in Read/Bash/Grep and, when asked "open the org profile," **read its own source code and described it to the user**. It could have read `.env`. Fixed: corrected namespaced allowlist + `disallowed_tools` blocking all filesystem/shell/web built-ins + system-prompt persona ("you live inside Slack; never discuss code"). **If you add a tool, add it to BOTH the `create_sdk_mcp_server(tools=[...])` list and `AGENT_TOOLS` in `agent/agent.py`.**
5. **`d1f6c7c` Home-tab deep link** — superseded by #6; the `slack://` link proved unreliable (showed a raw URL popup) and the injection was removed again in #6.
6. **`a78d256` Chat-first setup** — a **Set Up Org Profile button now appears under agent replies whenever no profile exists** (`listeners/views/setup_prompt_builder.py`; message buttons carry a trigger_id, so the modal opens straight from chat). New `save_org_profile` agent tool (`agent/tools/org_profile_tool.py`) lets users set up conversationally. Find Grants with no profile short-circuits to the setup prompt.
7. **`e860976` Website autofill** — `fetch_org_website` tool (`agent/tools/website.py`): user pastes their site URL, agent fetches (10 s timeout, 200 KB cap, http/https only, stdlib HTML→text), drafts the profile, confirms, saves.
8. **`84d4246` Profile confirmation card** — after save (either path), a card with the summary + Find Grants/Edit buttons posts in chat (`profile_saved_builder.py`).
9. **`b900b44` Live search progress** — `run_agent(..., on_tool_use=cb)` fires per tool call; DM/mention paths update assistant status ("🔍 Searching Grants.gov…"); Find Grants button path `chat_update`s its progress message. Labels: `listeners/events/tool_status.py`.
10. **`18a5892` Welcome + board links** — empty @mention gets a real welcome (`welcome_builder.py`); Grant Board rows link to each prospect's original card (workspace URL cached from `auth.test` in `home_refresh.py`).

## Architecture cheat sheet

- **Entry points:** `app.py` (Socket Mode only — the proven path) or `app_oauth.py` (Socket Mode + OAuth HTTP server — needed for user tokens / Real-Time Search / remote Slack MCP). One at a time.
- **Agent:** `agent/agent.py`, Claude Agent SDK (`ClaudeSDKClient`), custom in-process MCP server `clew-grant-tools` with 8 tools: `search_grants_gov`, `search_propublica_orgs`, `get_990_filings`, `search_usaspending`, `search_workspace`, `save_qualified_prospect`, `save_org_profile`, `fetch_org_website`. Trust boundary: prospects only reach the shortlist via `save_qualified_prospect`, which requires real citations.
- **State:** single SQLite file `clew.db` (`storage/db.py`): `org_profile` + `prospects` (stage machine: qualified → approved → applied → submitted → awarded/declined/passed). Sessions (thread → SDK session id) are in-memory (`thread_context/store.py`).
- **Views:** everything Block Kit lives in `listeners/views/`; actions in `listeners/actions/`; events in `listeners/events/`.
- **Tests/lint:** `pytest` (24 tests), `ruff check .`, `ruff format .`. Run both before every commit — several tests encode Slack API constraints that will crash `views.open` live if violated.

## Environment (no secrets in this file — ask Jay)

`.env` (gitignored) needs: `ANTHROPIC_API_KEY`, `SLACK_BOT_TOKEN` (xoxb, from Install App page), `SLACK_APP_TOKEN` (xapp, app-level token with `connections:write`). For OAuth also: `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET`, `SLACK_REDIRECT_URI` (must exactly match a redirect URL registered in the Slack app config). Optional: `CLEW_AGENT_MODEL`.

Setup: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/python app.py`.

## ⚠️ Cleanup task: duplicate Slack apps

The workspace has TWO Clew apps — an older one (bot username `clew`) and the one
Jay's tokens belong to (bot username `clew2`, app `A0BGUBZF23E`). **Delete the one
we're not using and rename the survivor to "Clew"** (api.slack.com/apps → Basic
Information → Delete App / Display Information). Judges clicking a dead duplicate
is an avoidable UX fail. App icons are ready in `assets/icon/` (three variants +
flat versions) — upload one under Display Information while you're there.

## The web board (added late Friday)

**https://clew-board.vercel.app** — a read-only Next.js board (in `web/`) showing the
live pipeline: org profile, stat tiles, kanban by stage, deadlines, citations. It polls
`GET /api/board` (served by the Python process on port 3001, `webapi.py`) through a
Cloudflare quick tunnel. Architecture story: the agent writes through MCP tools; the
web board renders the same SQLite state live. **Operational chain that must ALL be
running for the public board to work:** `app.py` (bot + API) → `cloudflared tunnel
--url http://localhost:3001` → the tunnel URL set as `CLEW_API_URL` in the Vercel
project (jays-projects/clew-board). ⚠️ Quick-tunnel URLs change on every cloudflared
restart — if it restarts, update `CLEW_API_URL` on Vercel (`vercel env`) and redeploy
(`cd web && vercel deploy --prod`). All writes stay in Slack; the web app has no write
endpoints.

## Remaining work, in priority order

1. **Finish live verification** (30 min of clicking): Approve → deadline modal →
   Save → board shows Approved with deadline; Pass; Applied → Submitted → Awarded
   (report-due + retro modal) → Reported; Declined (retro). Also: paste a website
   URL → draft profile → confirm → card; Find Grants live statuses. Screenshot the
   good moments for the Devpost gallery as you go.
2. **OAuth / Real-Time Search API** (the second required technology, ~1-2 h):
   `ngrok http 3000` → add `https://<sub>.ngrok-free.app/slack/oauth_redirect` to
   the app's redirect URLs AND `SLACK_REDIRECT_URI` in `.env` → set client
   ID/secret/signing secret in `.env` → run `app_oauth.py` (instead of `app.py`) →
   visit `/slack/install` → approve. Expect: installation file under
   `./data/installations/`, green "workspace search connected" line on App Home,
   agent uses `search_workspace`, warm-path hints in awarded/declined modals.
3. **Submission package** (protect at least half a day):
   - **Demo video (~3 min)** — suggested beats: (1) paste website URL → profile
     drafts itself, (2) Find Grants with live statuses, (3) a cited card — click
     the citation on camera, (4) the trust moment: point out it REJECTED a
     wrong-fit grant / declined to fabricate, (5) Approve → deadline → board,
     (6) warm-path mention. Lead with the problem: solo EDs doing grant research
     by hand vs $200+/mo tools.
   - **Devpost text** — lead with impact + the no-fabrication trust boundary;
     name the tech: custom MCP server, Real-Time Search API, Claude Agent SDK.
   - **Check `docs/architecture.svg`** still matches (OAuth runner changed).
   - **Invite judges** to the workspace: slackhack@salesforce.com, testing@devpost.com.
   - **Keep the process running during judging** — Socket Mode means the bot is
     only alive while someone's laptop runs it. Decide who hosts it Sunday+.
   - Update README's "Project status" section — several "not yet verified" items
     are now done.
4. **Nice-to-have if time remains:** deadline-reminder DM (schema already stores
   deadlines; a small daily check would prove the lifecycle story), a smoke test
   for the agent-tool layer with mocked HTTP.

## Working agreements

- Commit small and often; every commit leaves pytest+ruff green. All of today's
  work is on `main` as 11 atomic commits — `git log --oneline` reads as a
  changelog.
- Don't rename `action_id`s / `callback_id`s / storage columns without checking
  `tests/test_view_builders.py` and `listeners/*/__init__.py` registrations.
- The agent must never get filesystem/shell tools back. If a new capability needs
  data, wrap it in a narrow MCP tool like `fetch_org_website`.
