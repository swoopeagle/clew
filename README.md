<p align="center">
  <img src="assets/clew-icon-512.png" alt="Clew logo: a red thread tracing a C through a grey labyrinth" width="128" height="128">
</p>

# Clew

**Grant prospecting for small nonprofit teams, right inside Slack.**

Clew is a Slack agent that finds real, currently-available grants and foundations that fit
your organization, screens each one for fit against your mission, geography, program areas,
and grant-size range, and hands your team a short, evidence-backed shortlist to approve or
pass on. Nothing reaches your shortlist without a real citation attached — no invented
funders, no fabricated grant sizes, no guessed deadlines.

Built for the small nonprofit teams who actually do this work: solo executive directors
writing grants themselves, volunteer-run organizations, and small (2–5 person) development
teams without dedicated grant-research staff. Because the same small team also handles what
happens *after* a prospect is approved, Clew stays with a grant through its whole lifecycle —
deadline tracking, a submission status board, reporting reminders, and a short org-learning
retro after every win or loss.

The name comes from "clew" — the literal root of the word "clue," the ball of thread Ariadne
gave Theseus so he could find his way back out of the labyrinth. Same idea: a thread through
a maze of funders to the ones that actually fit.

---

## 🚧 Project status — WIP (Slack Agent Builder Challenge, "Agent for Good")

This is an early hackathon build. The core loop works end-to-end and has been verified live in
a real Slack workspace, but it is not polished and there are known gaps.

**Built and verified live:**
- App runs in Slack (Bolt for Python, Socket Mode) and connects cleanly.
- The agent searches three real, free grant-data APIs (Grants.gov, ProPublica 990s,
  USAspending), screens results against an org profile, and posts a shortlist of qualified
  prospects as Block Kit cards with cited sources and Approve/Pass buttons.
- In a live test (an Oakland after-school STEM org profile), it correctly rejected
  university/research-scale federal grants as wrong-fit, surfaced two real Bay Area
  grantmakers with verifiable ProPublica citations, and *declined to fabricate* fit for a
  funder it had no evidence on — the trust behavior working as intended.
- SQLite persistence and the full lifecycle stage machine (qualified → approved → applied →
  submitted → awarded/declined, plus deadline, report-due, and org-learning retro) all work.

**Not yet verified / known gaps:**
- The button-click → modal round-trip (Approve → deadline modal, board transitions) is wired
  and unit-tested but not yet confirmed with a real click in Slack — that's the next test.
- App Home doesn't auto-refresh after new cards post (a Slack platform limitation); may add a
  manual Refresh affordance.
- Warm-path workspace search (Real-Time Search API) requires OAuth install; it degrades
  gracefully without it but hasn't been exercised live yet.
- No onboarding polish, no empty-state guidance beyond the basics, minimal error surfacing.

**How to run it yourself:** see [Setup](#setup) below. You'll need a Slack workspace you can
install apps into and an Anthropic API key.

### 🙏 Feedback wanted

Genuinely early, so poke holes. A few specific things I'd love a second opinion on:

1. **Fit quality** — set up an org profile for a nonprofit you know and run *Find Grants*. Are
   the prospects it surfaces actually plausible fits? Where does its judgment feel off?
2. **The trust framing** — the whole pitch is "sourced, no fabrication, five good leads over
   fifty long shots." Does that land as genuinely different from paid tools, or is it too
   subtle to matter to a real user?
3. **Scope** — is prospecting-plus-light-lifecycle the right cut, or should the demo lean
   harder on one thing? (See the [Roadmap](#roadmap) for what's deliberately deferred.)
4. **The data-source gap** — Grants.gov/ProPublica/USAspending skew federal + larger
   foundations. Small local/community grants are the hardest to surface. Ideas for free
   sources that cover *small* opportunities are the single most valuable input right now.

---

## What it does

- **Find Grants** — searches [Grants.gov](https://grants.gov) (open federal opportunities),
  [ProPublica's Nonprofit Explorer](https://projects.propublica.org/nonprofits/) (foundation
  990 data), and [USAspending.gov](https://www.usaspending.gov) (real historical grant
  awards — useful evidence for smaller/local funding) and screens results against your org
  profile before anything reaches your shortlist.
- **Shortlist cards** — each qualified prospect is posted as a Block Kit card with its fit
  rationale, cited sources, and **Approve / Pass** buttons — the human-approval gate, made
  visible as UI.
- **Grant Board** — every prospect, grouped by stage (qualified → approved → applied →
  submitted → awarded/declined/passed), right on the App Home tab.
- **Lifecycle follow-through** — approving a prospect prompts for a deadline; marking a
  grant awarded prompts for a report-due date and a short retro note; declined prospects get
  the same retro prompt so the team remembers why next time.
- **Warm-path detection** — when installed with OAuth, Clew checks the workspace's own
  message history for prior mentions of a funder before qualifying it, and surfaces that at
  retro time too. Degrades gracefully (never fabricates a "no mentions" claim) when
  unavailable.

## Architecture

Slack (Bolt for Python, Socket Mode) → an agent built on the **Claude Agent SDK**, with a
custom **MCP server** exposing the grant-data tools (`search_grants_gov`,
`search_propublica_orgs`, `get_990_filings`, `search_usaspending`, `search_workspace`,
`save_qualified_prospect`) → free public APIs. All state — org profile and every prospect
through every lifecycle stage — lives in a single SQLite file (`storage/db.py`); the
shortlist cards, Grant Board, and lifecycle reminders are all views or transitions on that
one table, not separate systems.

The agent may only add something to the shortlist by calling `save_qualified_prospect`,
which requires a real cited source for every claim — this is Clew's trust boundary, not a
suggestion in a prompt.

## Setup

### Prerequisites

- A Slack workspace where you can install apps
- The [Slack CLI](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-mac-and-linux/)
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- Python 3.12+

### Install and run

```sh
git clone <this-repo> clew
cd clew
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

slack login
cp .env.sample .env
# add your ANTHROPIC_API_KEY to .env

slack run
```

On first run, `storage/db.py` creates `clew.db` in the project root automatically.

### Using it

Open the app's **Home** tab in Slack:

1. Click **Set Up Org Profile** and fill in your mission, geography, program areas, and
   grant-size range.
2. Click **Find Grants**. Clew searches, screens, and posts qualified prospects as cards in
   a DM thread with you.
3. **Approve** or **Pass** on each card. Approving prompts for a deadline.
4. Track everything on the **Grant Board** section of App Home — mark prospects Applied,
   Submitted, Awarded, or Declined as they move through your process.

You can also just DM the agent or @mention it in a channel — "find grants for us" works the
same way as clicking the button.

### Optional: warm-path detection (Real-Time Search API)

Workspace search requires OAuth (not just Socket Mode). See `app_oauth.py` and the
`SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET` / `SLACK_REDIRECT_URI` variables in `.env.sample`
for that setup. Without it, Clew works fully — it just skips the warm-path check rather than
guessing.

`app_oauth.py` serves the OAuth endpoints (`/slack/install`, `/slack/oauth_redirect`) over
HTTP while still receiving events over Socket Mode, so it fully replaces `app.py` — run
exactly one of the two, never both (each opens its own Socket Mode connection, so running
both double-handles every event). The redirect URL registered in the Slack app config must
match `SLACK_REDIRECT_URI` exactly (e.g. your `ngrok http 3000` URL +
`/slack/oauth_redirect`).

## Project structure

- **`storage/`** — SQLite schema and CRUD for `org_profile` and `prospects` (the single
  source of truth for the whole grant lifecycle).
- **`agent/`** — Claude Agent SDK configuration (`agent.py`), the grant-data and
  qualification tools (`tools/`), and org-profile context injection (`org_context.py`).
- **`listeners/events`** — App Home, DM, and @mention entry points.
- **`listeners/actions`** — button handlers: org profile, Find Grants, Approve/Pass, and
  every Grant Board stage transition.
- **`listeners/views`** — every Block Kit surface: the App Home, the Grant Board, the
  shortlist card, the org profile modal, and the deadline/awarded/declined modals.

## Roadmap

Clew is deliberately scoped to prospecting and light lifecycle tracking for this build. The
natural next chapter — application drafting assistance, a fuller submission workflow, and
deeper evaluation/reporting support — follows the same pattern (a tool the agent calls, a
stage on the same `prospects` table) but isn't built here.

## Development

```sh
ruff check .
ruff format .
pytest
```
