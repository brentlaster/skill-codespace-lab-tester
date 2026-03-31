# Talk Expander Skill — User Guide

## What This Skill Does

You have a conference talk with a slide deck (.pptx) and a speaker script (.md) synced by SLIDE delimiters. The problem: some slides have dense script sections with stats, case studies, and lists that are hard to memorize. This skill analyzes your talk, identifies the hardest sections to deliver from memory, and inserts new slides that display the key talking points visually — so you can reference what's on screen instead of memorizing everything.

The result: more slides, same timing, same content, far less memorization.

## What You Need

Two files in the same folder:

1. **A .pptx slide deck** — your polished presentation
2. **A .md speaker script** — with SLIDE delimiters marking where each slide's script begins

The script's SLIDE delimiter format can vary. Common formats the skill handles:

    ## [SLIDE 5 — The Test That Passed]
    ## SLIDE 5: THE TEST THAT PASSED
    ## **SLIDE 5 — The Test That Passed**

The skill auto-detects whichever format your script uses.

## How to Use It

Tell Claude something like:

- "Expand my slides — I can't memorize all this"
- "Use the talk-expander skill on these files"
- "Add more slides from my script so I don't have to memorize as much"
- "Break up the dense slides in my talk"

Claude will:

1. **Analyze** your deck and script, rating each section's memorization difficulty
2. **Propose an expansion plan** showing which slides to expand and why
3. **Ask for your approval** before making changes
4. **Build the expanded deck** with new slides matching your deck's visual style
5. **Update the script** with new SLIDE delimiters so it stays in sync
6. **Verify alignment** — deck slide count must exactly match script section count
7. **Produce a change report** summarizing what was added and delivery tips

## What You Get Back

Three new files (originals are never modified):

- `yourfile_expanded.pptx` — the expanded deck with new slides inserted
- `yourfile_expanded.md` — the updated script with new SLIDE sections
- `yourfile_expansion-report.md` — a summary of changes and delivery tips

## How New Slides Are Numbered

New slides use letter suffixes to avoid renumbering your entire deck. If slide 14 gets expanded, the new slide becomes 14b (and 14c if there's a second). Your existing slide numbers stay the same, so your mental map of the talk isn't disrupted.

## What Makes a Good Expansion Candidate

The skill looks for sections that are hardest to deliver from memory:

- **Specific statistics** — numbers, percentages, research citations
- **Case studies or examples** — detailed scenarios with multiple steps
- **Ordered lists of 4+ items** — processes, frameworks, checklists
- **Technical details** — code patterns, configuration specifics
- **Before/after comparisons** — where the details matter

It leaves alone sections that are easy to deliver naturally: narrative transitions, audience interactions, Q&A slides, section dividers, and content that's already well-represented on the existing slide.

## Tips for Best Results

- **Let the skill propose first.** Review the expansion plan before approving — you might want more or fewer expansions than it suggests.
- **Check the script flow after expansion.** The script sections get redistributed across more slides. Read through the expanded script to make sure transitions between sections feel natural.
- **The deck and script must stay in sync.** If you later edit one, edit the other to match. The slide count and section count must always be equal.
- **New slides match your deck's theme.** The skill extracts fonts, colors, and layout patterns from your existing slides and replicates them on new ones. If your deck has a specific visual language (accent bars, card layouts, stat callouts), the new slides will follow it.

## Technical Notes (For Troubleshooting)

**Why not just use python-pptx to add slides?**
python-pptx silently rewrites nearly every internal XML file when it saves, even with zero changes. This causes PowerPoint to show repair dialogs, delete content, and produce duplicates. The skill uses direct ZIP/XML manipulation instead — copying every original file byte-for-byte and surgically adding only the new slides. This preserves the original deck perfectly.

**My deck has non-sequential slide file names (slide1.xml, slide5.xml, slide37.xml...)**
This is normal for decks that have been edited over time. The skill maps presentation order from the internal XML metadata, not from file names.

**The script uses a delimiter format I haven't seen before.**
The skill auto-detects delimiter patterns. If it can't detect yours, it will ask. You can also tell it explicitly: "The delimiter format is ## SLIDE N: TITLE".
