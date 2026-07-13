# Clew demo video — script + stage directions (~3:00)

_Rewritten after a full live walkthrough (onboarding → cards → war room → board).
Every beat below is something I actually drove in Slack; the stage directions are
the real clicks._

Target: Slack Agent Builder Challenge, "Agent for Good."
Judging (25% each): Technological Implementation, Design, Potential Impact, Quality of the Idea.

---

## ⏱️ Read this first — two timing realities that shape the edit

1. **Find Grants takes ~2–3 minutes live** (mandated full sweep: Grants.gov ×
   each program area, ProPublica + 990 checks, USAspending, workspace warm-path).
   You **cannot** show it in real time in a 3-min video. Plan:
   - Record the search once; in editing **speed-ramp the status-cycling to ~8 s**
     of B-roll (the live statuses — "🏛 Scanning USAspending awards…", "Checking
     your workspace for warm paths…", "Reading foundation 990 filings…" — are
     great sped up).
   - Have the **cards already generated** before the "reveal" shot so you cut
     straight from statuses → cards.
2. **The war-room brief takes ~1–2 min to generate** after you approve. Show
   Approve → war room **spawns instantly** + intro message → hard cut / speed-ramp
   → the pinned brief appears. Don't sit on the wait.

**Model:** set `CLEW_AGENT_MODEL=claude-opus-4-8` for the recording (brief/prose
quality is visibly better than Sonnet). Restart the bot after.

**Demo state is already seeded:** org = **TEL HI Neighborhood Center**, with
**2 cited qualified prospects** (Koret Foundation, HHS Head Start) waiting for a
live Approve. To re-record onboarding from scratch: stop bot → `rm clew.db` →
restart → repeat Beats 1–4.

**Record in a clean channel** — create a fresh `#demo` channel; the existing
`#grants` has old test chatter and old `#grant-…` rooms in the sidebar.

---

## The 3:00 arc — beats, verbatim VO, and stage directions

### 0:00–0:20 — The stake (no product yet)
**VO:** "A solo executive director at a small nonprofit does the job of five
people. Grant research — the thing that funds everything — is the first to fall
off. The tools that help start at two hundred dollars a month. This is Clew: a
grant agent that lives in Slack, built entirely on free public data."
**Screen:** title card, or the TEL HI website.

### 0:20–0:40 — Teach it once (onboarding)
**VO:** "You teach Clew your org once. Paste your website — it drafts the whole
profile."
**Stage directions:**
1. In `#demo`, type `@clew` (select the in-channel Clew), send with **no other
   text** → **welcome card** appears in a thread. *(Note the trust line: "🔒
   Every prospect comes with real citations — I never invent a funder, grant
   size, or deadline.")*
2. Click **Set Up Org Profile** → modal opens.
3. In **Your website**, type `telhi.org` → click **✨ Draft with AI**.
4. ~10 s later the form returns **fully prefilled** (mission, geography SF,
   program areas, grant range $5k–$50k). Scroll it so the fill is visible.
5. Click **Save Profile** → confirmation card in the DM: *"✅ Org profile saved!
   Here's what Clew will screen every grant against:"*

### 0:40–1:25 — Find grants + the trust beat
**VO:** "Now it sweeps three free public sources — Grants.gov, ProPublica's
foundation filings, USAspending — and screens every result against your profile.
Here's what matters: every card is cited. Click the evidence — that's the real
funder, the real filing. Clew is *structurally incapable* of inventing a grant:
the tool that saves a prospect **rejects anything without a real citation.**"
**Stage directions:**
1. Click **Find Grants** (on the confirmation card).
2. **[B-roll, sped up]** live statuses cycle in the thread: "🏛 Scanning
   USAspending awards…" → "Checking your workspace for warm paths…" → "Reading
   foundation 990 filings…".
3. Cut to the **cited cards**. Land on **Koret Foundation** (SF, ProPublica-
   cited) or the **HHS Head Start** card — the Head Start one is stronger: it
   shows a *real SF peer (Mission Neighborhood Centers) winning Head Start
   awards*, cited to usaspending.gov, **with an honest caveat** ("big operating
   awards, not a starter grant").
4. **Click a citation link** → the real ProPublica/USAspending page opens. Say
   the trust line here.

### 1:25–2:20 — The wow: approve → war room
**VO:** "Approve a grant and Clew opens a war room — a dedicated channel for that
one grant. It researches and pins a brief: amount, deadline, requirements —
everything cited, and anything it can't verify goes in a VERIFY list instead of
being guessed. And in this room, Clew already knows the grant."
**Stage directions:**
1. Click **Approve** on a card → **Set Deadline** modal opens → pick a date ~5
   days out → **Save**.
2. A **`#grant-…` channel appears in the sidebar instantly** + a "📂 Opened
   #grant-…" note posts where you approved.
3. **[speed-ramp the ~1–2 min]** → the **pinned brief** posts. Point at the
   layout: **💰 Amount / 📅 Deadline side-by-side** (both "Verify" here — nothing
   invented), then **✅ Confirmed / ⚠️ Verify before applying / ▶️ Next steps**,
   **📎 Sources**.
4. In the war room, type: `@clew based on the brief, draft our application` →
   it dives in **without being told which grant** (fit summary, outline,
   boilerplate, checklist — rendered as clean markdown).

### 2:20–2:45 — Pipeline + trust surface + web view
**VO:** "The whole pipeline lives on a board in Slack — a funnel from review to
awarded. Clew even shows you exactly which channels it can see; it only reads
what you invite it to. And for board members without Slack, the same pipeline is
a live web view."
**Stage directions:**
1. Open the Clew app → **Home** tab. Show the **funnel header** (`🔍 → ✅ → ✍️ →
   📬 → 🏆` with counts) and the board with the ⏰ due badge.
2. Scroll to **🔒 What Clew can see** (the trust/observability section).
3. *(Optional, only if the tunnel + Vercel are live)* click **🌐 Web Board**.

### 2:45–3:00 — Roadmap + mission close
**VO:** "It already reconstructs your *federal* funding history — ask it what any
peer has won and it pulls the real, cited awards and spots the recurring funders.
Next: foundation history from public 990 filings, and a two-way sync with
Salesforce Nonprofit Cloud. Grant seeking is how small nonprofits survive. Clew
gives them their hours back — for the mission."
**Screen:** one slide — **Find → Manage → Import & sync (Salesforce NPC).**

### OPTIONAL day-to-day beat (~10s) — "know your history"
Real capability, verified live. Drop in during the day-to-day section if you have
room:
- DM Clew: `what federal grants has Mission Neighborhood Centers won?` → it replies
  with the **real cited USAspending history** ($20M / $30.6M / $22.5M Head Start…)
  and calls out the **recurring Head Start stream**. Proves "start day one with
  your funders already tagged, not an empty board."
- Note: for TEL HI itself this correctly returns *nothing* (small org, no federal
  money) — so demo it against a **peer/grantee that has history**.

---

## The two "holy-grail" beats — do not cut these
1. **The citation click** (0:40–1:25) — proves the no-fabrication guarantee.
2. **The war room spawning itself** (1:25–2:20) — the moment judges remember.
If you're over time, cut onboarding detail and the web-board shot, never these.

## Devpost headline to mirror the video
"Clew's shortlist tool **rejects any prospect without a real citation** — the
no-fabrication guarantee is enforced in code, not just prompted." (Tech + Idea.)

---

## Pre-flight checklist (~15 min before recording)
1. `.env`: `CLEW_AGENT_MODEL=claude-opus-4-8`; run `bash scripts/run_clew.sh`.
2. Confirm demo state: TEL HI profile + 2 qualified prospects present (Home tab).
3. Fresh `#demo` channel; hide/scroll away old `#grant-…` channels.
4. Slack at ~110% zoom (Block Kit text legible at 1080p); dark or light — pick one.
5. Browser: logged out of anything personal; bookmarks hidden.
6. Pre-vet the citation page you'll click (know it loads and looks credible).
7. Do one silent dry-run of Beats 1–5 so nothing surprises you on camera.

---

# 🔮 Alternate cut — the "reuse engine" demo (north-star)

_This is the demo that sells the actual moat: Clew as **compounding org memory**, not a
one-shot draft tool. Architecture + rationale live in
[draft-application-reuse-engine.md](draft-application-reuse-engine.md). It is a **forward
cut** — it needs the seed below built first; it is NOT recordable today._

## The demo problem this cut solves
The value is a **derivative** — the rate at which each application gets faster and better —
but a demo only shows a point on the curve. **You can't show time passing, so show the
accumulated *result* of time having passed, prove the mechanism live once, and make the
compounding legible as something on screen that moves.** Show the flywheel already spun up,
give it one visible push, let the audience feel the momentum.

## Build-first dependencies (be honest — none of this is recordable yet)
- [ ] **Seeded PPH fact library** — ~25 confirmed facts w/ provenance (the F1–F9 set + more:
  dogs placed, retention, waitlist, Purdue evidence, ADI/IGDF gap, financials).
- [ ] **Competitive-draft template deployed to Railway** — now in the prompts
  (`SYSTEM_PROMPT` APPLICATION HELP), needs deploy + a live test.
- [ ] **Provenance chips** on canvas facts + a **capture line** ("✓ Saved — will auto-fill N
  questions across your M active grants").
- [ ] **Grant-readiness score** on the Home tab (a number that visibly ticks up on capture).
- [ ] Two war rooms for two funders that reframe the *same* facts differently (Bob Woodruff +
  Patterson is the proven pair — Patterson's ADI/IGDF rule is the gap-spotting "save").

## The 3:00 spine — beats, VO, stage directions

### 0:00–0:25 — Lived-in cold open (start in the future, not at zero)
**VO:** "This is Paws for Purple Hearts — a small nonprofit that's been using Clew for a few
months. Three grants in flight, and a library of everything that makes them fundable —
dogs placed, retention, the research behind their work — each fact captured once, from
real work they were already doing."
**Screen:** PPH **Home tab** — 3 war rooms, a **grant-readiness score** ("78% ready"), a
fact count. The judge should feel they're looking at an org with history.

### 0:25–1:00 — New grant → competitive draft → ONE live capture
**VO:** "A new funder lands. Clew researches it live and drafts a *competitive* application —
not a template. It leads with the real apply link, positions PPH against who this funder
actually funds, and asks for the few facts it still needs."
**Stage:** In `#grant-bob-woodruff`, click **Draft Application** → [speed-ramp the research]
→ the **canvas** draft: 🔗 apply link, ⭐ why-fund-us, `✅ USE AS-IS` prose with **provenance
chips**, `✏️ NEEDS`. The ED fills **one** live: "92% retention."
**On-screen copy (the compounding made legible):** *"✓ Saved — this fact will auto-fill 6
open questions across your 3 active grants."*

### 1:00–2:00 — THE MONEY SHOT: the second funder (reuse) + the save
**VO:** "Here's what nobody else does. A second funder — completely different questions.
Watch: you don't re-enter anything."
**Stage:** Open the second war room (Patterson), click **Draft Application** → the **same
facts** (340 placements, 92% retention, the Purdue study) **pour into the new draft**,
reworded to Patterson's actual questions, provenance chips glowing. Point at one fact
appearing in *both* drafts.
**VO (the save — the beat that pays off NOW, not later):** "Same facts, different
application. And Clew just caught that Patterson only funds ADI/IGDF members — flagging it
*before* the team sank twenty hours into an application they're not even eligible for."

### 2:00–2:30 — Make the compounding legible (the number that moves)
**VO:** "Every fact entered once now works everywhere. The more PPH uses Clew, the faster
and stronger every application gets."
**Screen:** the **readiness score ticks up** (78% → 82%) as the fact lands; "N facts
powering M applications."

### 2:30–3:00 — Credibility + mission close
**VO:** "And this isn't tuned for one org."
**Screen:** the **four-org slide** — Paws for Purple Hearts · Homeboy Industries · Rocking
the Boat · First Descents — *"Four real nonprofits. Real funders. Real facts. No per-org
setup."* (This is the answer to "did you cherry-pick one org?")
**VO close:** "Clew turns the knowledge trapped in one person's head into an asset that
compounds — so every grant a small nonprofit writes is more competitive than their last.
Grant seeking is how they survive. Clew helps them win."

## Holy-grail beats for this cut — do not cut these
1. **The second-funder reuse shot** (1:00–2:00) — same facts, different competitive app. The
   moment that proves it's not mad-libs.
2. **The gap-spotting save** — the one benefit that lands *in the room*, not in the future.
3. **The "will auto-fill 6 questions" capture line** — turns invisible future value into a
   present, on-screen consequence.

## The trap to avoid
Do **not** try to show it "getting better" across three live drafts — the deltas are too
subtle and it's too slow; you'll bore them proving a curve. Show the **after-state + one
push**, not the climb.
