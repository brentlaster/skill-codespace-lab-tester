---
name: script-authenticity-fixer
description: >
  Fix AI-generated conference talk scripts containing fabricated personal experience claims.
  Finds fake anecdotes ("I've talked to teams...", "In my experience...", "A team I worked
  with...") and replaces them with verifiable alternatives: real research citations, runnable
  code demos, theoretical walkthroughs, or public case studies. Preserves SLIDE markers and
  produces a change log. Trigger on: "fix my script", "fake experiences", "make script
  authentic", "remove made-up anecdotes", "de-hallucinate the talk", "replace the anecdotes",
  "make this script honest", or any reference to AI-generated scripts with invented personal
  stories. Also trigger when reviewing talk scripts for authenticity or truthfulness.
---

# Script Authenticity Fixer

You are fixing AI-generated conference talk scripts that contain fabricated personal experience
claims. The speaker (Brent Laster, TechUpSkills) is presenting on AI/ML engineering topics he
has researched but hasn't necessarily worked on hands-on with real teams. The AI that generated
these scripts invented anecdotes and personal experiences that never happened. Your job is to
find every one of these fabrications and replace it with something real and verifiable.

## Why This Matters

When a speaker says "I was working with a team that tried this and..." the audience expects
that actually happened. If it didn't, and the speaker gets asked follow-up questions, they're
caught in a lie. That destroys credibility — the opposite of what a conference talk should do.
But the *point* being made by the fake anecdote is usually valid. So we don't want to just
delete it; we want to replace the fictional framing with something the speaker can stand behind
confidently.

## Before You Start

1. **Collect inputs from the user.** You need:

   | Input | Format | Purpose |
   |-------|--------|---------|
   | **Speaker script** | Text or .md file | The script to fix — must contain SLIDE markers |
   | **Topic context** | From user or filename | What the talk is about (guides research) |

   Optional but helpful:
   - The companion .pptx deck (so you can check if slides need updating too)
   - The talk abstract
   - Any notes about what the speaker *does* actually have experience with (so you don't
     flag legitimate claims)

   **Batch processing:** If the user provides multiple scripts, process them one at a time.
   Produce a separate revised script, change log, and set of code demos for each. Research
   from one script may be reusable for another if the topics overlap — that's fine.

2. **Understand the SLIDE marker format.** Scripts contain markers like `SLIDE 1`, `SLIDE 2`,
   etc. (or similar patterns — adapt to whatever format you find). These markers align the
   script to slides in a companion deck. They are sacred. Never remove, reorder, or renumber
   them. Your edits happen to the spoken text between markers.

## Phase 1: Scan for Fabricated Experience Claims

Read through the entire script and identify every instance where the text implies personal
experience, direct conversations, or firsthand observation that the speaker may not actually
have had. These fall into several categories:

### Detection Patterns

**Direct personal claims:**
- "I've worked with teams that..." / "I was working with a group..."
- "In my experience..." / "From what I've seen..."
- "I've talked to [people] who..." / "I had a conversation with..."
- "When I was consulting for..." / "At a company I worked with..."
- "I remember when..." / "There was this one time..."
- "I've personally found that..."

**Implied firsthand knowledge:**
- "What I've noticed is..." / "What I keep seeing is..."
- "Teams I've helped have found..."
- "A colleague of mine..." / "A friend who works at..."
- "One organization I know..."

**Fabricated social proof:**
- "Everyone I talk to says..." / "The consensus among practitioners is..."
- "After talking to dozens of..." / "In conversations with engineers..."
- "The teams that have adopted this tell me..."

**Invented case studies:**
- "One company saw a 40% improvement..." (with no citation)
- "A fintech startup I know switched to..."
- Specific-sounding stories with no attribution

Be thorough. Read every paragraph. These claims can be subtle — sometimes just a word or two
("I've found that X works well") embedded in an otherwise factual sentence.

**What NOT to flag — normal speaker language:**
Not every use of "I" is a fake experience claim. Leave these alone:
- Navigational/presenter language: "I'll show you", "I want to highlight", "Let me walk
  you through", "As I mentioned earlier"
- Opinions clearly framed as opinions: "I think this matters because...", "I'd argue that..."
- References to preparation: "When I was researching this talk...", "I put together this demo"
- Teaching framing: "I'll break this down into three parts"

The test: does the statement claim the speaker *did something* or *witnessed something* in
a professional context? If yes, flag it. If it's just the speaker guiding the audience through
the presentation, leave it.

**When the speaker might actually have the experience:**
If the user has told you about areas where they DO have real experience, don't flag claims
in those areas. If you're unsure, flag it but mark it with a note in the change log like
"⚠️ Flagged but you may actually have this experience — keep if so."

### Output of Phase 1

Create an internal inventory — a numbered list of every flagged passage with:
- The SLIDE it falls under
- The exact text being flagged
- The category of claim (from the patterns above)
- The underlying point the fabrication is trying to make

## Phase 2: Choose Replacement Strategies

For each flagged passage, decide on the best replacement strategy. The goal is to preserve
the rhetorical purpose (making the point concrete and memorable) while using something the
speaker can genuinely stand behind. Here are the strategies, ranked roughly by how compelling
they are:

### Strategy 1: Published Research or Industry Report
**Best for:** Statistics, trends, adoption rates, performance comparisons, best practices

Search the web for actual studies, surveys, reports, or blog posts from reputable sources
that support the same point. Good sources include:
- Academic papers (arXiv, ACL, NeurIPS proceedings)
- Industry reports (Gartner, McKinsey, Stack Overflow surveys, State of AI reports)
- Engineering blog posts from major companies (Google AI Blog, Meta AI, Netflix Tech Blog)
- Official documentation and benchmarks

When you find a source, the replacement text should cite it naturally:
> "According to Google's 2024 MLOps survey, teams that adopted feature stores saw a 35%
> reduction in time-to-production..."

The citation should feel like the speaker did their homework, not like they're reading a
bibliography.

### Strategy 2: Runnable Code Demo
**Best for:** Technical claims about how something works, performance characteristics,
comparing approaches, showing a workflow

Instead of "I worked with a team that found approach X faster than Y," write a small,
self-contained script that *demonstrates* it. The speaker can say:
> "Let me show you what this looks like in practice. Here's a simple example..."

Code demos should be:
- **Self-contained** — single file, runs with standard dependencies (Python preferred)
- **Quick to run** — under 30 seconds, ideally under 10
- **Clearly commented** — someone reading the code should understand the point
- **Focused** — demonstrate exactly the claim being made, nothing extra
- **Named descriptively** — e.g., `demo_feature_store_lookup.py`, `demo_prompt_caching.py`

Save each demo as a separate file. In the script, reference it:
> "I've put together a quick demo — let's take a look at what happens when we..."

### Strategy 3: Theoretical Walkthrough
**Best for:** Architecture decisions, design patterns, tradeoff analysis, "what would happen
if" scenarios

Replace the fake anecdote with a structured thought experiment that walks through the
reasoning:
> "Let's think through what happens when a team faces this decision. They have two options:
> [A] and [B]. If they choose A, they get [benefit] but face [tradeoff]. With B..."

This is honest — the speaker is reasoning through the problem rather than claiming to have
lived it. It can be just as compelling because the audience gets to think along with the
speaker.

### Strategy 4: Public Case Study
**Best for:** Company-specific examples, real-world adoption stories, lessons learned

Search for published case studies, conference talks, blog posts, or documentation where
companies describe their actual experience. Many large companies publish extensively:
> "Spotify's engineering team wrote about this exact challenge in their 2024 blog post
> on ML platform evolution. They found that..."

The key: the case study must be publicly available and attributable.

### Strategy 5: Reframe as General Knowledge
**Best for:** Claims that are widely accepted truths, common patterns, or consensus views
that don't need a personal anecdote to land

Sometimes the fake experience is just wrapping an obvious point in unnecessary narrative.
In that case, just state the point directly:

Before: "I've talked to many teams and they all agree that monitoring is crucial..."
After: "Monitoring is one of those things that every ML deployment guide puts at the top
of the list, and for good reason..."

### How to Choose

Apply this decision tree:
1. Is the claim about a measurable outcome or statistic? → **Research** first
2. Is the claim about how something technically works? → **Code demo** first
3. Is the claim about a decision-making process or tradeoff? → **Theoretical walkthrough**
4. Is the claim about a specific company's experience? → **Public case study** first
5. Is the claim just common knowledge dressed up as personal experience? → **Reframe**

If your first-choice strategy doesn't pan out (e.g., you can't find a good study), fall back
to the next most appropriate strategy. Every flagged passage must get a replacement — don't
leave any fake claims in the script.

## Phase 3: Research and Build Replacements

Work through each flagged passage and build the replacement content.

### For Research Citations
- Use web search to find actual sources
- Verify the source exists and actually says what you think it says — fetch the URL and
  confirm. An invented citation is worse than the fake anecdote it replaced.
- Extract the specific finding, statistic, or conclusion
- Note the author/organization, year, and title for natural citation in speech
- Don't include formal academic citation format — this is spoken text. The speaker should
  name-drop the source naturally: "a 2024 Stanford study found..." or "according to
  Hugging Face's model card..."

### For Code Demos
- Write the code and ensure it's syntactically correct
- Add clear comments explaining what each section does
- Include a brief docstring at the top explaining what the demo shows
- Use realistic but simple data/examples
- Actually run the code to verify it works — don't just eyeball it. Fix any errors before
  saving. If a demo requires a paid API key or special hardware, note that in a comment at
  the top and make it work with mock data as a fallback.
- Save to the output directory alongside the revised script

### For Theoretical Walkthroughs
- Structure as a clear narrative: setup → options → tradeoffs → conclusion
- Use concrete (but hypothetical) numbers where they help: "say you have 10,000 training
  examples and..." — this is honest because it's explicitly hypothetical
- Keep it conversational — this is spoken text, not a whitepaper

### For Public Case Studies
- Search for the actual published source
- Confirm it's publicly accessible (not behind a paywall the audience can't reach)
- Summarize accurately — don't embellish what the company said

## Phase 4: Rewrite the Script

Now apply all the replacements to produce a revised script. Rules:

1. **Preserve ALL SLIDE markers** exactly as they appear in the original
2. **Maintain the script's voice and flow** — the replacement text should feel natural in
   context, not like a jarring insert. Read the sentences before and after each replacement
   to make sure the transitions work.
3. **Keep roughly the same length** — if you replace a 3-sentence anecdote, the replacement
   should be about 3 sentences too. Speakers budget time per slide; big length changes
   throw off pacing.
4. **Don't touch text that isn't flagged** — if a passage doesn't contain a fabricated
   experience claim, leave it exactly as-is. This includes factual statements, definitions,
   explanations, and legitimate rhetorical devices.
5. **Make it speakable** — read each replacement aloud in your head. Does it sound like
   natural speech? Would a real human say this at a podium? Avoid overly formal or written-
   sounding constructions.

Save the revised script with the same filename plus a `_authentic` suffix (e.g.,
`my_talk_script_authentic.md`).

## Phase 5: Generate Change Log

Produce a markdown change log documenting every replacement. This is how the speaker reviews
what you did and decides if they're comfortable with the changes. Format:

```markdown
# Script Authenticity Fixes — [Talk Title]

## Summary
- **Total claims flagged:** N
- **Replacements by strategy:**
  - Research citations: N
  - Code demos: N
  - Theoretical walkthroughs: N
  - Public case studies: N
  - Reframed as general knowledge: N
- **Code demos generated:** [list of filenames]

## Changes by Slide

### SLIDE X — [Slide topic if known]

**Original:**
> [exact original text]

**Issue:** [what was fabricated — e.g., "Claims personal experience working with teams on
feature stores, but speaker has not done this"]

**Strategy:** [which strategy was used]

**Replacement:**
> [the new text]

**Source:** [citation URL or "N/A — theoretical walkthrough" or "demo: filename.py"]

---
[repeat for each change]
```

Save as `change_log.md` alongside the revised script.

## Output Checklist

When you're done, you should have produced:
- [ ] The revised script (with `_authentic` suffix) — all SLIDE markers intact
- [ ] A change log (`change_log.md`) documenting every replacement
- [ ] Any code demo files (named descriptively, saved alongside the script)

Present these to the user with a brief summary: how many claims were flagged, what strategies
were used, and any flagged passages where you want the speaker's input (e.g., "this one I
wasn't sure about — you might actually have this experience, so check it").
