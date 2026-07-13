# 🧵 Clew: the grant office that lives in your Slack

**Clew** (noun, archaic): *a ball of thread, the root of the word "clue." Ariadne's thread through the labyrinth.*

Clew is a trust-first grant agent for small nonprofits. It finds real, currently open funding, proves every claim with a citation, researches how to actually apply, drafts a competitive application, hands the work to your teammates, and chases the deadlines. All of it inside the Slack workspace your team already uses, built entirely on free public data.

---

## 💸 The problem

There are **1.8 million nonprofits in the US**, and most are tiny. Roughly **88% run on budgets under $500K a year**, and about **61% pursue grants with a team of one or two people** doing the work of entire departments. Grant research, the thing that funds everything else, is the first task that falls off the desk.

The tools that help start at **$200 to $600 a month** (Instrumentl, Candid's Foundation Directory, GrantStation). The organizations that most need funding are priced out of the tools built to find it.

And the deeper issue is not search. Funding intelligence is scattered across silos: Grants.gov, foundation 990 filings, USAspending, each funder's own website, and the org's institutional memory. An overstretched ED has to stitch those together by hand, then still write the application. **The gap between data and action is where small nonprofits lose.**

## 🧶 Our solution

Clew collapses that gap. A non-technical executive director pastes their website into Slack, and minutes later has a cited shortlist of open opportunities screened against their mission, geography, and capacity. One click of **Approve** and Clew opens a war room where the annoying work is already done: the real application portal link, the guidelines page, a contact email, and an honest analysis of whether the org is eligible. From there it drafts, delegates, and reminds.

The one rule that makes it trustworthy: **nothing reaches the shortlist without a real citation, and that rule is enforced in code, not in a prompt.**

## ⚙️ What Clew does

| Stage | What Clew does | Where |
| ----------- | ----------- | ----------- |
| 🧵 Onboard | Paste your website, Clew drafts the whole org profile for review (or use the ✨ AI form-fill modal) | DM |
| 🔍 Find | Full sweep of Grants.gov, ProPublica 990s, and USAspending with live progress statuses; every prospect posted as a cited card | DM or any channel |
| ✅ Approve | Human gate: Approve or Pass buttons on every card. Approving spawns a dedicated war room | Prospect cards |
| 📂 Research | Pinned brief with the real apply link, criteria page, contact, who the funder already funds, and an eligibility analysis against your profile | War room |
| ✍️ Draft | A competitive application draft written into the shared channel canvas, positioned against the funder's actual grantees, every section tagged ✅ use as is or ✏️ needs a specific number from you | War room canvas |
| 🧩 Delegate | Clew proposes the action items (financials, board list, narrative sections) and each one gets handed to a teammate with a people picker; "have @sam pull our financials" works too | War room |
| ⏰ Watch | Unprompted 9am briefing plus nudges into any war room with a deadline inside 3 days or unowned work, mentioning the owners | DM + war rooms |
| 📊 Track | Pipeline funnel and grant board on the App Home, plus a live web dashboard for board members who are not in Slack | App Home + web |

There is no wrong door: Clew answers wherever it is asked. The DM is the personal cockpit, channels are for team-visible decisions, and each war room already knows which grant it is for.

## 🔒 Honesty enforced by architecture

Most agent demos promise accuracy. Clew enforces it. The **only** way anything reaches the shortlist is one tool call, and that tool **rejects any prospect whose citation is not a URL a search tool actually returned in this run**. Provenance-checked, not just format-checked. No citation, no recommendation.

The same discipline runs through everything downstream: briefs mark unverified facts for follow-up instead of guessing, drafts never invent the org's numbers (every gap is a named ✏️ blank), and the App Home carries a transparency panel showing exactly which channels Clew can see.

Why it matters here: for a two-person nonprofit, a fabricated funder or a wrong deadline is not a quirky hallucination. It is a wasted week they did not have.

## 🏗️ How we built it

- **Slack Bolt for Python** (async), Socket Mode plus OAuth, every surface in Block Kit: App Home dashboard, modals, cards, task boards, canvases, channel topics
- **Claude Agent SDK** driving the agent, with per-thread sessions that survive redeploys
- **Custom MCP server** ("clew-grant-tools", 11 tools): three grant data sources, org award history, workspace search, website fetching with link crawling, profile and prospect persistence with the citation gate, and task designation
- **Slack Real-Time Search API** for warm-path detection: has your team already talked about this funder?
- Built-in **web search plus a crawling loop** that walks a funder's site to the actual application portal, criteria page, and contact email, with all fetched content treated as untrusted data
- **SQLite on a persistent volume**: one table of truth renders as cards, board, briefing, and web dashboard
- **Docker on Railway**, running 24/7 with no laptops involved, and a **Next.js web board on Vercel** locked behind signed per-org HMAC links handed out only inside that org's Slack
- **76 automated tests** across storage, view builders, parsing, and the trust boundary

## 🧪 Does it generalize? We checked.

The same engine, with **zero per-org tuning**, produced real funders, live portals, and honestly flagged gaps for four real organizations in four different domains:

1. 🐕 Service dogs for wounded veterans (Paws for Purple Hearts)
2. 🕊️ Gang rehabilitation and reentry (Homeboy Industries)
3. 🚣 Bronx youth development (Rocking the Boat)
4. 🏔️ Young adults impacted by cancer (First Descents)

## 📈 The impact math

Clew's App Home shows each org a live receipt of prospects researched, citations verified, war rooms opened, and tasks handed off, with an honest estimate of staff time returned:

$$\text{hours returned} \approx 2.5 \times \text{prospects researched}$$

For a typical week that is **10 to 15 hours of development-staff work and hundreds of dollars a month** returned to food banks, after-school programs, and neighborhood centers. Multiply across the long tail of 1.8M organizations and the addressable impact is enormous, because the marginal cost of Clew's research is near zero: the data was always free, it just was not actionable.

## 🔭 What's next

- **Foundation funding graphs** from public 990-PF grantee filings, where every edge is an IRS record
- **The reuse engine**: Clew as compounding org memory, capturing each fact an application surfaces so no ED ever answers the same question twice
- **Salesforce Nonprofit Cloud sync**: import an existing pipeline, push awarded grants back
- Deeper Slack-native surfaces: the pipeline as a Slack List, briefs as living canvases

## 🚀 Try it in 60 seconds

1. Open **Clew** in the sandbox workspace and DM it: `clew briefing` (instant pipeline rundown, plus nudges into any war room that needs attention)
2. Ask it: *"what can you do?"*
3. Open a `#grant-` war room and click **✍️ Draft Application**, then open the channel canvas
4. Click **🌐 Web Board** on the App Home for the live dashboard

Every number you see came from a real API call, and every funder has a link to prove it. 🧵
