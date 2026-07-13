# Judge "start here" pin — paste-ready

Post this in the clean `#demo` channel and **pin it** before inviting
slackhack@salesforce.com and testing@devpost.com. (Checklist item 3 in
CONTEXT.md: invite judges as FULL members, *after* app hygiene + video.)

---

👋 **Welcome, judges! Here's the 3-minute path through Clew.**

Clew is a trust-first grant agent for small nonprofits: it finds *real,
currently-available* grants from free public data, cites every claim, and runs the
whole pipeline in Slack. The one rule: **nothing reaches the shortlist without a
real citation** — that's enforced in code, not a prompt.

**Try it (in this order):**

1️⃣ Open the **Clew** app → **Messages** tab. Click **Set Up Org Profile** and paste
the website `telhi.org` — Clew drafts the whole profile in ~10 seconds. (Or just
tell it about any nonprofit in chat.)

2️⃣ Click **Find Grants**. Clew sweeps Grants.gov, ProPublica 990s, and USAspending,
screens for fit, and posts a cited shortlist. *A full sweep takes ~2–3 minutes —
real government APIs.* Every card has a clickable source.

3️⃣ **Approve** a card → watch Clew spin up a `#grant-…` war room with a pinned,
fully-cited brief (anything it can't verify goes in the VERIFY list — it won't
guess). Inside the room, try: `help me apply`.

4️⃣ Open the app's **Home** tab: the pipeline funnel, the board, and the **"What
Clew can see"** transparency panel.

5️⃣ Bonus: ask Clew *"what federal grants has Mission Neighborhood Centers won?"* —
real award history from USAspending, cited.

**Where to talk to Clew:** the **Clew DM** is the personal cockpit (profile,
`clew briefing`, private searches — no @mention needed); **any channel** works for
team-visible asks (`@clew …`, grounded in that channel's history); each
**#grant-… war room** is grant-scoped — `@clew` inside one already knows which
grant you mean. No wrong door.

🧵 Why "Clew"? It's the root of the word *clue* — Ariadne's thread through the
labyrinth. A thread through the maze of funders to the ones that actually fit.

---

## Pre-invite checklist (for us, not the pin)

- [ ] Bot is live on Railway (it always is — do NOT run `run_clew.sh`; check by DMing Clew)
- [ ] DB re-seeded state: click **Find Grants** once so the pipeline/board isn't empty
- [ ] One lived-in war room: tasks designated + assigned (one ✅ done, one unassigned),
      brief pinned, `clew briefing` opted in
- [ ] Old app `A0BG7GBD4CX` deleted (the live one is `A0BGUBZF23E` — don't touch)
- [ ] Orphaned `#grant-…` channels from old runs archived
- [ ] `#demo` channel created, this message posted + pinned
- [ ] Judges invited as full members
