---
name: talk-expander
description: >
  Expand a conference talk deck by adding slides that surface key talking points from the speaker
  script, reducing memorization burden. Takes a .pptx deck and matching .md script with SLIDE
  delimiters, finds sections hardest to deliver from memory (stats, case studies, lists), and
  inserts visually attractive new slides showing those key points. Updates the script with new
  SLIDE delimiters to stay in sync. Creates new file versions. Trigger on: "expand my slides",
  "can't memorize this talk", "add more slides from script", "break up dense slides", "too much
  to memorize", "put talking points on slides", "expand the deck", "talk expander", or any
  request to reduce memorization by adding slides with key script content. Also trigger when
  someone has too much script per slide or wants their deck to carry more content visually.
  Do NOT use for speaker notes only (use presentation-speaker-cues) or creating talks from
  scratch (use conference-talk-builder).
---

# Talk Expander Skill

Expand a conference talk deck by inserting new slides that surface key talking points from the
speaker script, so the speaker can read/deduce content from their slides rather than memorize
long script passages.

## Philosophy

The speaker has a polished deck and a detailed script synced by SLIDE delimiters. The problem:
too much script per slide means too much memorization. The solution: split dense script sections
across more slides, each displaying the key points the speaker needs to convey. The audience
sees relevant, well-designed content slides. The speaker sees their talking-point cues right
on screen.

The balance to strike: new slides should look like natural, intentional content slides that
add value for the audience — not cheat sheets or teleprompter screens. Think of it as
"unpacking" a dense slide into a short sequence where each slide focuses on one idea, with
the key phrases and data points visible.

## Before You Start

1. **Read the pptx skill's SKILL.md** — you'll need it for deck manipulation. Then read its
   `editing.md` reference for the unpack/edit/pack workflow.
2. **Collect inputs**: You need a `.pptx` deck and a `.md` script file with SLIDE delimiters.
3. **Confirm output naming**: Create new versions with a suffix like `_expanded` — never
   overwrite the originals.

## Step-by-Step Process

### Phase 1: Analyze the Deck and Script

1. Extract deck content:
   ```bash
   python -m markitdown input.pptx
   python scripts/thumbnail.py input.pptx
   ```

2. Read the full script and parse it into sections by SLIDE delimiter. Detect the delimiter
   format used (e.g., `## [SLIDE N — Title]`, `## **SLIDE N — Title**`, or other variants).

3. For each slide section, compute:
   - **Word count** of the script section
   - **Content density score** — how much unique information (stats, names, steps, examples)
     is packed into the section
   - **Memorization difficulty** — rate how hard this section is to deliver from memory:
     - HIGH: Contains specific statistics, multiple case studies, technical configurations,
       ordered lists of 4+ items, code examples, or regulatory citations
     - MEDIUM: Contains 2-3 key points with some specifics, comparisons, or scenario
       descriptions
     - LOW: Contains narrative flow, transitions, audience interactions, or content that's
       already well-represented on the existing slide

4. Build the **expansion plan** — a table showing:
   - Each original slide number and title
   - Script word count for that section
   - Memorization difficulty rating
   - Recommended number of slides (1 = keep as-is, 2+ = expand)
   - Brief description of what each new slide would show

   Expansion criteria (use judgment, not rigid rules):
   - Slides with HIGH difficulty and 150+ words of script are strong expansion candidates
   - Slides with MEDIUM difficulty and 200+ words may benefit from splitting
   - Slides with LOW difficulty or those that are already visual/interactive generally stay as-is
   - Title slides, Q&A slides, section dividers, and audience interaction slides stay as-is
   - Consider the overall talk flow — don't expand so aggressively that transitions feel choppy

5. **Present the expansion plan to the user** for approval before making changes. Show the
   table and the projected new slide count. Ask if they want to adjust anything.

### Phase 2: Design the New Slides

For each expansion point, design the new slide content following these principles:

**What goes on new slides:**
- Key statistics with their context (e.g., "97% — no proper AI access controls" with source)
- Individual case studies or examples that were bundled into one script section
- Steps in a process, shown one or two per slide instead of all at once
- Comparison columns (before/after, problem/solution, anti-pattern/fix)
- Key framework elements or decision points
- Important quotes or principles that the speaker needs to deliver verbatim
- Code snippets or configuration examples mentioned in the script

**Visual treatment for new slides (keep it attractive, not text-heavy):**
- Use the same visual layouts that exist in the deck — duplicate similar slides as templates
- Large stat callouts: big number (48-60pt) with a short explanation below
- Icon + text rows for lists of concepts or steps
- Two-column layouts for comparisons or before/after
- Diagrams or flow elements when describing processes
- Use color blocks, accent shapes, or visual hierarchy — not just plain text
- Maximum 4-5 text elements per slide; if you need more, split again
- Each new slide should have a clear single focus — one idea, one visual anchor

**What does NOT go on new slides:**
- Full paragraphs from the script (this is not a teleprompter)
- More than 30-40 words of visible text per slide
- Content that duplicates what the previous or next slide already shows
- Audience interaction instructions (keep those in the script only)
- Stage directions or timing notes

### Phase 3: Build the Expanded Deck

Use the pptx editing workflow (unpack → modify → pack):

1. **Unpack the deck**:
   ```bash
   python scripts/office/unpack.py input.pptx unpacked/
   ```

2. **Map presentation order to file names** (critical — see the pptx editing.md and the
   presentation-speaker-cues skill for details on why file numbers != display order):
   - Read `ppt/presentation.xml` for `<p:sldIdLst>` order
   - Read `ppt/_rels/presentation.xml.rels` for file mappings
   - Build a position-to-file lookup

3. **For each expansion point**, find the most visually similar existing slide to use as a
   template. Use `add_slide.py` to duplicate it:
   ```bash
   python scripts/add_slide.py unpacked/ slideN.xml
   ```
   This prints a `<p:sldId>` entry. Insert it into `<p:sldIdLst>` at the correct position
   (immediately after the slide it expands from, or between slides as appropriate).

4. **Edit the content** of each new slide's XML:
   - Replace placeholder/template text with the designed content
   - Adjust font sizes, colors, and layout to match the deck theme
   - Use the Edit tool for all XML changes (not sed or Python scripts)

5. **Update content on original slides if needed** — if a slide is being split, the original
   may need its content adjusted (e.g., removing items that now have their own slides, or
   changing its title to reflect it's now the first in a sequence).

6. **Clean and pack**:
   ```bash
   python scripts/clean.py unpacked/
   python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
   ```

### Phase 4: Update the Script

The script MUST be updated to match the new slide structure. For every new slide added:

1. **Detect the existing delimiter format** from the script (e.g., `## [SLIDE N — Title]`)

2. **Split the original section**: Take the script text that was under the original slide and
   redistribute it across the original + new slide sections. Each section should contain only
   the script text the speaker delivers while that specific slide is showing.

3. **Insert new SLIDE delimiters** for each added slide. Use letter suffixes to avoid
   renumbering the entire script (e.g., if you split slide 14 into three slides, they become
   SLIDE 14, SLIDE 14b, SLIDE 14c). This preserves the original numbering so the speaker's
   existing mental map isn't disrupted.

4. **Preserve all stage directions** — `*[PAUSE]*`, `*[GESTURE]*`, `*[TRANSITION]*`, audience
   polls, etc. Place them in whichever new section they naturally belong to.

5. **Preserve timing checkpoints** at the end of the script — update them to note that the
   expanded deck has more slides but the same timing targets.

6. **Add a change summary** at the top of the new script file noting:
   - Original slide count vs. expanded slide count
   - Which slides were expanded and into how many
   - That timing targets are unchanged — the same content is delivered, just across more slides

### Phase 5: Verify (CRITICAL — do not skip or abbreviate)

Script-to-deck alignment is the single most important quality gate. A mismatch means the
speaker loses their place during delivery. Every step below is mandatory.

1. **Count deck slides**:
   ```bash
   python -m markitdown output.pptx | grep -c '<!-- Slide'
   ```
   Record this number as DECK_COUNT.

2. **Count script SLIDE delimiters**:
   ```bash
   grep -c '^\## \[SLIDE' output_script.md
   ```
   (Adjust the pattern to match whatever delimiter format the script uses.)
   Record this number as SCRIPT_COUNT.

3. **Compare counts — they MUST be equal**:
   If DECK_COUNT != SCRIPT_COUNT, do NOT proceed. Diagnose and fix:
   - List all SLIDE headers from the script: `grep '^\## \[SLIDE' output_script.md`
   - List all slide titles from the deck via markitdown
   - Identify which slides are missing script sections or vice versa
   - Add missing SLIDE sections to the script, or remove orphaned ones
   - Re-count until DECK_COUNT == SCRIPT_COUNT exactly

   Common causes of mismatch:
   - Forgetting to add a SLIDE delimiter for a newly created slide
   - The original script already had non-standard delimiters for some slides (e.g., 46b)
     that the counting pattern missed — make sure your grep catches ALL delimiter variants
   - Off-by-one errors when inserting multiple new sections

4. **Content verification**:
   ```bash
   python -m markitdown output.pptx
   ```
   Confirm all new slides have content, no placeholder text remains, and slide order is correct.

5. **Visual QA** (if subagents are available):
   Convert to images and inspect:
   ```bash
   python scripts/office/soffice.py --headless --convert-to pdf output.pptx
   pdftoppm -jpeg -r 150 output.pdf slide
   ```
   Check that new slides match the deck's visual theme and don't look out of place.

6. **Spot-check script sections**: Read 3-4 expanded script sections and verify the text
   makes sense split across multiple slides — transitions should be natural, not abrupt.

### Phase 6: Produce the Change Report

Write a markdown report (`expansion-report.md`) containing:

1. **Summary**: Original slide count, new slide count, number of slides added
2. **Expansion Details**: For each expanded slide, show:
   - Original slide number and title
   - Number of new slides created
   - What each new slide displays
   - Why this section was expanded (the memorization challenge it addresses)
3. **Script Changes**: Summary of how the script was restructured
4. **Delivery Tips**: Advice on using the expanded deck — e.g., "Slides 14-14c now walk
   through the three data classification techniques one at a time. You can simply describe
   what's on screen rather than recalling the details from memory."

## Output Files

All outputs go in the same directory as the inputs, with suffixes:
- `{basename}_expanded.pptx` — the expanded deck
- `{basename}_expanded.md` — the updated script
- `{basename}_expansion-report.md` — the change report

## Important Reminders

- **Never overwrite originals** — always create new files with `_expanded` suffix
- **New slides must look intentional** — they should enhance the audience experience, not
  look like speaker notes projected on screen
- **The script must stay in sync** — every slide in the deck needs a matching SLIDE section
  in the script, and vice versa
- **Letter suffixes for numbering** — use 14, 14b, 14c rather than renumbering everything,
  so the speaker's existing familiarity with slide numbers is preserved
- **Respect the talk's timing** — adding slides doesn't add time; the same content is just
  spread across more visual anchors. Note this in the script header.
