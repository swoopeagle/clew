# Clew — the grant agent that lives in your Slack

**Tagline:** A trust-first grant-finding agent for small nonprofits. It learns your
org once, finds *real, currently-available* grants from free public data, cites
every one, and runs the whole pipeline — right inside Slack.

---

## Inspiration

A solo executive director at a small nonprofit does the job of five people. Grant
research — the thing that funds everything else — is the first task that falls off
the desk. And the tools that help start at **$200–600 a month**: Instrumentl,
Candid/Foundation Directory, GrantStation. So the orgs that most need help finding
funding are the ones priced out of the tools that find it.

We wanted to flip that: put a capable grant researcher **inside the Slack a small
team already uses**, built entirely on **free, public data**, that a non-technical
ED can run by typing a sentence — and that they can *trust*, because in the
nonprofit world a made-up funder or a wrong deadline isn't a cute hallucination,
it's a wasted week they didn't have.

## What it does

**Learn the org once.** Paste your website and Clew drafts your whole profile —
mission, geography, program areas, grant-size range — in about ten seconds. Or
just tell it about your org in chat.

**Find real, cited grants.** Ask "find grants" and Clew runs a full sweep across
three free public sources — **Grants.gov**, **ProPublica's 990 filings**, and
**USAspending** — screens every result against your profile, and posts a short
shortlist. Every card carries a **real citation** you can click. It says what it
*can't* verify instead of guessing, and it's honest when a big federal award is
"not a starter grant."

**Approve → a war room.** Approve a grant and Clew spins up a dedicated
`#grant-<name>` channel, invites you, and pins an AI **brief** — funder, amount,
deadline, requirements — with everything cited and anything unverifiable quarantined
in a VERIFY list. Inside that room, Clew already knows the grant: "help me apply"
just works (fit summary, application outline, boilerplate in your voice, a
requirements checklist).

**Run the pipeline in Slack.** A stage funnel and board live on the App Home tab and
in-channel — qualified → approved → applied → submitted → awarded — with deadline
flags. A live **web board** mirrors it for board members who don't have Slack.

**Know your history.** Ask what any org (yours, a peer, a grantee) has won and Clew
pulls its **real federal award history from USAspending**, cited, and flags the
recurring funders.

## The one thing that makes Clew different: the trust boundary is *enforced*

Every "AI grant tool" promises it won't make things up. Clew makes that a
**mechanism, not a marketing line.** The only way a prospect reaches your shortlist
is through one tool — `save_qualified_prospect` — and that tool **rejects any
prospect whose citations aren't real URLs from a source we actually queried**
(grants.gov, propublica.org, usaspending.gov). No citation, no shortlist. The agent
*cannot* hand you an uncited grant even if it tries. That guarantee is the product.

## How we built it

- **Claude Agent SDK** (`ClaudeSDKClient`, Opus 4.8) drives the reasoning and tool
  use, with per-thread sessions for continuity.
- **A custom in-process MCP server** (`clew-grant-tools`, 9 tools) is Clew's hands:
  the four data-source tools, workspace search, the award-history tool, the enforced
  `save_qualified_prospect` trust gate, plus profile save and website fetch.
- **Slack Real-Time Search API** (via OAuth user token) powers "warm-path" detection
  — Clew checks whether your team has already discussed a funder before surfacing it,
  and can answer questions from your workspace history.
- **Bolt for Python** (Socket Mode + OAuth) with **Block Kit** for every surface:
  cards, the scannable brief, the App Home funnel/board, war-room briefs, the
  transparency panel.
- **Next.js on Vercel** for the public web board, fed by a bearer-auth JSON API,
  reachable only through **signed per-org HMAC links** — real multi-tenant isolation.
- **SQLite** holds the org profile and the prospect pipeline.
- **Security lockdown:** the agent's built-in filesystem/shell/web tools are
  disallowed; only the namespaced `clew-grant-tools` are allowed — so the agent can
  research grants and nothing else.

## Challenges we ran into

- **Making "no fabrication" real.** It started as a prompt instruction. We turned it
  into enforced citation validation on the save path — the differentiator had to be
  code, not a promise.
- **Trust vs. resilience.** Free government APIs are slow and occasionally return
  HTML error pages. Every source call is now timeout-bounded and degrades to a clean
  "unavailable" instead of freezing a live search — without ever letting a failure
  become a fabricated result.
- **Grounding the agent in the *channel*, not just its own memory.** Clew reads a
  war room's recent history so it answers from what the team actually discussed, not
  a blank context.
- **Meeting people where they work.** Onboarding had to survive a non-technical ED:
  paste-a-URL AI drafting, conversational setup, or a guided form — all three land in
  the same profile.

## Accomplishments we're proud of

- A grant agent a solo ED can actually run — and **trust** — end to end, on **free
  public data**, without leaving Slack.
- The **enforced-citation trust boundary**: structurally incapable of shortlisting a
  grant it can't cite.
- Deep Slack-native design: war-room channels, App Home pipeline funnel, a live
  "what Clew can see" transparency panel, and a signed multi-tenant web board.

## What we learned

Restraint is a feature. The moments that made Clew feel trustworthy were the ones
where it *declined* — "verify this on the funder's site," "this is a big operating
award, not a starter grant," "your org has no federal awards on record." For the
people Clew serves, an honest *no* is worth more than a confident *maybe*.

## What's next

- **Full funding history.** Federal wins are live today; next we reconstruct
  *foundation* funding history from public **990-PF grantee filings** — a funder
  graph where every edge is an IRS filing.
- **Salesforce Nonprofit Cloud sync.** Import an org's existing pipeline and push
  awarded grants back — Clew as the system of *action* in Slack alongside the system
  of record. (Salesforce owns Slack; the grants/development team is a natural
  beachhead.)
- **More Slack-native surfaces:** the pipeline as a Slack List, war-room briefs as
  living Canvases.
- **Deadline chasing:** scheduled reminders in the war room as a deadline nears.

## Built with

`Claude Agent SDK` · `Model Context Protocol (custom MCP server)` · `Claude Opus 4.8`
· `Slack Real-Time Search API` · `Bolt for Python` · `Slack Block Kit` · `OAuth`
· `Next.js` · `Vercel` · `SQLite` · `Grants.gov API` · `ProPublica Nonprofit
Explorer API` · `USAspending API`

## Try it

Judges: you have workspace access. Start in the Clew app's **Messages** tab —
`@clew` and click **Set Up Org Profile** (try website `telhi.org`), then **Find
Grants**, approve a card to watch a war room spawn, and open the **Home** tab for
the pipeline board. Every claim links to its source.
