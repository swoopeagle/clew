# Clew Draft Application → Reuse Engine (brainstorm capture)

_Session: Ian + Claude, 2026-07-12 (pre-judging). Status: design locked in-session; the
two-funder value test passed on paper; nothing below is built yet except where noted._

## Thesis (one line)
Competitiveness isn't a better draft template — it's **reusing the org's accumulated facts
across grant applications that all ask the questions differently.** The draft is the visible
tip of a compounding org-memory system.

## The job (reframe)
Draft Application looks like a **generation** feature; the real job is **memory**:

> _"Help me never answer the same question twice — and make each answer better than my last."_

Small nonprofits have nothing for this today: the knowledge lives in the ED's head and walks
out the door when she does. If Clew becomes the org's memory, generation is just its proof.

## Architecture — the decisions we locked
1. **The unit is a fact, not an answer.** Atomic, provenance-tracked facts are the reusable
   asset. **Reuse the truth, regenerate the prose** per funder. (Funders smell boilerplate;
   reusing narrative is a competitiveness *liability*.)
2. **Curated library, agent-proposed / human-confirmed.** Raw workspace search is demoted to
   the *discovery* arm — it **proposes** candidate facts; it is never the reuse mechanism.
   No forms, ever.
3. **Capture is a byproduct of drafting.** Filling a `✏️ NEEDS: <exact fact>` blank *is*
   confirming a fact. Channel mentions get *proposed* ("update placements 340 → 400?"), never
   silently ingested. **If it ever feels like a CRM, we've lost.**
4. **Freshness = use-but-flag-inline, modulated by fact half-life.** Identity facts (EIN,
   mission) never decay → silent. Metrics (placements, budget) decay fast → age flag fires
   loudly. The freshness flag *is* the re-capture surface — accuracy improves through use.
5. **Question-as-query for answering; archetypes for gap-spotting.** Each funder question is
   a retrieval query over (fact library + funder research); the model assembles + regenerates
   prose. Archetypes are NOT a brittle router — they're the org's **grant-readiness coverage
   map** → a readiness score ("70% ready; missing an evaluation-plan fact and a
   lived-experience answer").
6. **Never blend funders.** Org facts reuse across funders; funder *requirements* stay
   strictly per-funder.

### The governing principle (why it's accurate/robust)
> **Apply the same discipline inward that already makes funder research trustworthy: cite it
> or flag it, never assert it.** Every reused fact carries provenance + date + confidence;
> anything stale or unconfirmed degrades to a confirm prompt, never a silent claim.

## The flow
```
funder's ACTUAL application questions (Clew already fetches these)
        │
        ▼  each question = a query
  ┌─────────────────────────────────────────────┐
  │  retrieve: fact library  +  funder research  │
  └─────────────────────────────────────────────┘
        │
        ▼  assemble + REGENERATE prose per funder
  answer, with:  ✅ USE-AS-IS (cited provenance)   ✏️ NEEDS (exact fact)   ⚠️ stale-flag
        │
        ▼  team fills a ✏️ NEEDS  ──►  fact enters library (confirmed)  ──►  reused next time
```

## The demo (validated in-session, zero key, zero build)
Hand-seed PPH's ~10 facts, then click Draft on **Bob Woodruff** *and* **Patterson** and show
the **same facts re-worded to each funder's actual questions, with provenance chips**. What
lands hardest (lead with this):
- **A fact's competitive weight shifts by funder.** "Raises its own puppies" is a throwaway
  clause for Bob Woodruff and the **entire eligibility centerpiece** for Patterson. Same
  fact, reframed — that's the grant-consultant move.
- **Gap-spotting fires on a real requirement.** ADI/IGDF membership is irrelevant to Bob
  Woodruff (silent) and a **blocking `✏️ NEEDS`** for Patterson. The readiness model earning
  its keep.
- Enter a number once (340 placements), reused in both with the same provenance + age flag.

The literal "340 appears twice" is table-stakes; the **weight-shift + gap-firing** is the wow.

## Build map — what exists vs. what's net-new
**Already live (reuse it):**
- OAuth user token → Slack `search.messages` plumbing, authenticated on the Railway volume
  (`agent/tools/workspace_search.py`, `listeners/actions/prospect_actions.py`). Today its
  aperture is one string (funder name) → one flag (warm path). The discovery arm just
  **widens the same aperture** to fact-shaped queries. Not a from-scratch build.
- Draft Application flow + war-room canvas, incl. refresh-in-place fix
  (`listeners/actions/draft_application_action.py`).
- Funder research loop (WebSearch + fetch), org profile, and it already fetches the funder's
  **actual application-questions doc** — the unlock for question-as-query.

**Designed but not yet shipped (this session's draft-quality work):**
- The competitive template: `✅ USE-AS-IS` / `✏️ NEEDS` signposting, a "why fund us"
  differentiator, a "proof points we need from you" list, an outcomes
  baseline→target→instrument→timeline framework, and a cost-effectiveness line. Validated by
  rewrite; not yet encoded into `SYSTEM_PROMPT` / `DRAFT_APPLICATION_PROMPT`.

**Net-new (the real, defensible asset):**
- **Fact library**: storage schema — `value, type, provenance(source+who+when), confidence,
  half-life`. Per-org.
- **Propose→confirm capture loop**: fill-a-`NEEDS` = silent confirm; channel mention =
  proposed confirm.
- **Freshness/decay logic** + inline age flags (per fact type).
- **Question-as-query assembly** over library + funder research.
- **Archetype coverage / readiness model** (gap-spotting + score).

## Riskiest assumption (and its status)
That "same facts → visibly different, visibly *better* prose per funder, with provenance"
reads as magic, not mad-libs. **Tested on paper in-session (Bob Woodruff vs. Patterson) — it
lands, on the strength of the weight-shift + gap-firing.** Next validation is live, in Slack,
once wired.

## Open questions (parked, not now)
- Where exactly does the confidence bar sit for silent reuse vs. forced confirm?
- Passive channel-extraction pipeline: how aggressive before accuracy erodes?
- Readiness score as its own surface (App Home panel?).
- Ever reuse *narrative*, not just facts? (Deliberately set down for now.)

## Suggested next steps
1. **Now / pre-judging:** encode the competitive template into the two prompts (in-session,
   no key) and dry-run a second funder to confirm the shape holds live.
2. **Demo build:** hand-seed the PPH fact library + surface provenance chips on the canvas so
   the two-funder side-by-side is real, not narrated.
3. **Post-judging:** the fact library schema + propose→confirm loop (the compounding asset).
