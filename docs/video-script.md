# Clew demo video — script + shot list (~3:00)

Target: Slack Agent Builder Challenge, "Agent for Good" track.
Recording setup: `CLEW_AGENT_MODEL=claude-opus-4-8` in `.env` (flip back after).
Fresh state for the take: stop bot, `rm clew.db`, restart — or record from an
already-seeded pipeline and skip the onboarding beat's save step.
Do NOT restart the bot mid-take (in-memory sessions drop the thread).

Rule of thumb: the two beats judges will remember are the **live citation click**
and the **war room spawning itself**. If over 3:00, cut anywhere but there.

---

## 0:00–0:20 — The stake (no product on screen)

Visual: title card or a real small-nonprofit website (TEL HI).

> "A solo executive director at a small nonprofit does the job of five people.
> Grant research — the thing that funds everything — is the first thing that
> falls off. The tools that help start at two hundred dollars a month.
> This is Clew: a grant agent that lives in Slack, built on free public data."

## 0:20–0:45 — Teach it your org once

Visual: Slack. @mention Clew → welcome card → click **Set Up Org Profile** →
"✨ Draft with AI" → paste `telhi.org` → Draft with AI → form returns prefilled →
Save.

> "You teach Clew your org once. Paste your website — it drafts the whole
> profile. Review, tweak, save. That's onboarding."

## 0:45–1:25 — Find grants, and the trust beat

Visual: click **Find Grants** → live statuses cycle ("🔍 Searching Grants.gov…",
ProPublica, USAspending) → prospect cards land → **click a citation, show the
real funder page in the browser**.

> "Clew sweeps three free public sources — Grants.gov, ProPublica's foundation
> filings, USAspending — and screens every result against your profile.
> Here's the part that matters: every card is cited. Click the evidence — that's
> the real funder, the real program. Clew is structurally incapable of inventing
> a grant: the only way anything reaches this list is through a tool that
> requires real citations. No fabricated funders, amounts, or deadlines. Ever."

## 1:25–2:20 — The wow: approve → war room

Visual: click **Approve** → deadline modal → save → "📂 Opened #grant-…" → cut
into the channel → live statuses → the pinned brief posts (point at the VERIFY
list) → type "@clew help me apply to this grant" → it dives in without asking
which grant.

> "Approve a grant and Clew opens a war room — a channel for that one grant.
> It researches and pins a brief: amount, deadline, requirements — everything
> cited, and anything it couldn't verify goes in a VERIFY list instead of being
> guessed. And inside this room, Clew already knows the grant. 'Help me apply' —
> and it drafts the outline and boilerplate in your organization's voice."

## 2:20–2:45 — Pipeline + live web board

Visual: App Home board (stage emojis, ⏰ deadline flags) → click 🌐 Web Board →
kanban in browser → change a stage in Slack → board updates in place (~15 s).

> "The whole pipeline lives on a board — in Slack, and on a live web view your
> board members can see without a Slack account. Signed per-org links,
> multi-tenant. Change a stage in Slack; the web updates in seconds."

*(If OAuth/Real-Time Search is live, insert 10 s here: ask Clew something that
requires workspace search — "what did we say about the deadline for X?")*

> *"And with workspace search connected, Clew remembers everything your team
> has ever said about every grant — a second brain for the development office."*

## 2:45–3:00 — Roadmap + mission close

Visual: one simple slide — **Find → Manage → Salesforce Nonprofit Cloud**.

> "Next: import your full funding history automatically from public 990 filings,
> manage every application end to end, and sync with Salesforce Nonprofit
> Cloud — the system of record, with Clew as the system of action in Slack.
> Grant seeking is how small nonprofits survive. Clew gives them their hours
> back — for the mission."

---

## Pre-flight checklist (do in order, ~15 min before recording)

1. `.env`: `CLEW_AGENT_MODEL=claude-opus-4-8`; restart bot.
2. Bot + `:3001` tunnel up; web board loads via a fresh 🌐 link (not a stale one).
3. Do one full dry run of the E2E workflow (CONTEXT.md §6) — surprises happen
   off camera, not on it.
4. Slack sidebar clean: hide unrelated channels/DMs from the recording window.
5. Browser: log out of anything personal; bookmark bar hidden.
6. Record at 1920×1080; Slack at ~110% zoom so Block Kit text is legible.
7. Have the funder citation page pre-vetted (know it loads and looks credible).
