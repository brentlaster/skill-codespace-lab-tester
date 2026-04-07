---
name: deck-to-template
description: Convert a conference talk deck (.pptx) and speaker script (.md) to a business template style using tst_template.pptx. Applies theme, curved-lines background, bookend slides, section divider styling, text recoloring, dimension scaling, chart copying, and script sync. Trigger on "convert to template", "apply template", "restyle my deck", "brand my slides", "match tst_template", or converting a talk deck to a business theme.
---

# Deck-to-Template Converter

Converts a talk deck + speaker script to the business template style defined in `tst_template.pptx`.

## What This Skill Does

Given three inputs:
1. **Talk deck** (.pptx) — the presentation to convert
2. **Speaker script** (.md) — with `## SLIDE N` delimiters matching each slide
3. **Template deck** (`tst_template.pptx`) — the reference business template

The skill:
- Replaces the talk deck's theme, slide master, and slide layouts with the template's
- Ensures all content slides use the white curved-lines background (slideLayout5)
- Section divider slides get the template's divider style (centered bold Poppins title, teal accent bar, semi-transparent overlay)
- Prepends the template's first 3 slides: version slide (hidden, auto-updated version/date), title slide (with auto-extracted title), and "About me" slide (as-is from template)
- Appends the template's closing slide ("That's all - thanks!")
- Skips the talk deck's own version, title, and ending slides (template provides these)
- Recolors white/light text and dark-background accent colors for readability on the white template
- Scales all shape positions and sizes when slide dimensions differ (including charts and embedded objects)
- Copies charts, embedded Excel workbooks, and other linked objects
- Preserves ALL script content — including full opening and closing speech text from bookend slides
- Auto-increments the version number and sets today's date on the version slide
- Saves the deck as `_templated.pptx` and the updated script as `_templated.md`

## Prerequisites

Read the pptx SKILL.md first — this skill builds on its editing workflow and tools.

**Required**: The pptx skill must be installed at `.claude/skills/pptx/scripts/` — the conversion script uses its `unpack.py`, `pack.py` (with validation/auto-repair), and `clean.py` for reliable OOXML output.

```bash
pip install "markitdown[pptx]" Pillow --break-system-packages -q
```

## Step-by-Step Workflow

### Phase 1: Locate Files and Extract Info

1. Find the three input files: the talk deck, the script, and `tst_template.pptx` (should be in the same folder or the user's workspace folder).

2. The script auto-extracts the talk title from both the script's SLIDE 2 section and the actual slide XML, combining multi-line titles at the same font size.

3. Count slides in the talk deck and SLIDE sections in the script — they must match before proceeding.

```bash
python -m markitdown <talk-deck>.pptx 2>/dev/null | grep -c "Slide number:"
grep -c '^## SLIDE' <script>.md
```

### Phase 2: Run the Conversion Script

```bash
python <skill-path>/scripts/convert_to_template.py \
  --talk-deck <path-to-talk.pptx> \
  --template-deck <path-to-tst_template.pptx> \
  --script <path-to-script.md> \
  --title "The Talk Title" \
  --subtitle "Optional subtitle line" \
  --output-dir <output-directory>
```

**Arguments:**
- `--talk-deck`: Path to the talk's .pptx file
- `--template-deck`: Path to tst_template.pptx
- `--script`: Path to the speaker script .md file
- `--title`: Talk title (auto-extracted from script/slides if not provided)
- `--subtitle`: Optional subtitle for the title slide
- `--output-dir`: Where to save outputs (defaults to same folder as talk deck)

**Outputs:**
- `<original-name>_templated.pptx` — the converted deck
- `<original-name>_templated.md` — the updated script

### Phase 3: Verify the Conversion

**This is critical — always verify after conversion.**

#### 3a. Content verification

```bash
python -m markitdown <output>.pptx 2>/dev/null
```

Check:
- First 3 slides are version (with updated version/date), title (with correct talk title), about-me
- Last slide is the closing slide
- All original talk slides are present in the correct order between front and end
- Section divider text is preserved
- No content was lost or garbled
- Charts and embedded objects are present and correctly sized

#### 3b. Slide count verification

```bash
# Count output slides
python -m markitdown <output>.pptx 2>/dev/null | grep -c "Slide number:"

# Count script sections
grep -c '^## SLIDE' <output-script>.md

# They must be equal
```

The output deck should have: talk content slides + 3 front bookends + 1 end bookend.
The output script should have the same number of SLIDE sections.

#### 3c. Script content verification

```bash
# Check that SLIDE 2 (TITLE) has the full opening speech, not just a stub
head -40 <output-script>.md
```

Verify that the original speech content from the talk script's title/opening section is preserved in SLIDE 2, and the closing remarks are preserved in the ending slide section.

#### 3d. Visual verification (if soffice available)

```bash
python <pptx-skill-path>/scripts/office/soffice.py --headless --convert-to pdf <output>.pptx
pdftoppm -jpeg -r 150 <output>.pdf slide
```

Inspect key slides:
- Slide 1: Version slide (hidden, shows updated version + today's date)
- Slide 2: Title slide with correct talk title
- Slide 3: About me slide
- Slide 4+: Content slides with white curved lines background, readable dark text
- Section dividers: Bold centered text with teal accent bar
- Slides with charts/graphics: correctly sized, not tiny or overflowing
- Last slide: "That's all - thanks!" closing

### Phase 4: Verify Script Sync

Read the output script and confirm:
- SLIDE 1 (VERSION): `[Skip]`
- SLIDE 2 (TITLE): **Full original opening speech preserved** — NOT a stub
- SLIDE 3 (ABOUT ME): Brief placeholder
- Middle sections: All original SLIDE sections in order with content intact
- Last SLIDE (ENDING): **Full original closing speech preserved** — NOT a stub
- Total SLIDE count matches total slide count in the deck

## What the Conversion Script Does Internally

The script handles complex OOXML-level work:

### Theme & Layout Replacement
- Unpacks both decks using the pptx skill's `unpack.py`
- Copies the template's theme, slide master, and ALL slide layouts into the output
- Every content slide is remapped to use slideLayout5 (white curved-lines background)
- The curved-lines background is a `blipFill` with `image1.png` on the layout, NOT a solid fill on the master

### Background Stripping
- Strips explicit `<p:bg>` elements from ALL imported talk slides
- Original slides typically have hardcoded solid color fills (F5F5F5, FFFFFF, 011936, etc.) that would override the layout background inheritance
- Without stripping, slides appear with their original solid backgrounds instead of the curved-lines

### Text Recoloring
- Slides designed for dark themes have white (FFFFFF) or light scheme-colored text (bg1, lt1, lt2, bg2) invisible on white
- The script changes these to dark (#333333) for readability
- **Also remaps accent colors that don't work on white backgrounds**: teal #00A79D (designed for dark slides) is remapped to dark blue #003366
- Handles both explicit `a:srgbClr` and scheme colors in `a:rPr` (run properties) and `a:defRPr` (default paragraph run properties)

### Dimension Scaling
- Detects slide size mismatch between talk deck and template (e.g., 10"×5.63" → 13.33"×7.5")
- Scales ALL shape positions and sizes by the ratio (typically 4/3 for this template)
- Handles BOTH `a:xfrm` (regular shapes) AND `p:xfrm` (graphicFrames like charts) — **this is critical**: charts use `p:xfrm`, and failing to scale them leaves chart graphics tiny
- Also scales group shape child offsets/extents (`a:chOff`, `a:chExt`)

### Font Size Scaling
- When slide dimensions change, font sizes must also be scaled or text appears too small on the larger canvas
- Scales ALL `sz=` attributes in `a:rPr` (run properties) and `a:defRPr` (default run properties)
- Uses the average of x and y scale factors (font sizes are isotropic — not direction-dependent)
- Rounds to nearest 25 (quarter-point) to avoid fractional font size artifacts

### Overflow Clamping (Uniform Compression)
- After scaling, some slides may have shapes extending beyond the slide boundary
- Uses a **uniform compression strategy**: finds the maximum overflow across ALL shapes, then compresses all positions and sizes proportionally
- This preserves relative spacing instead of just squishing the rightmost shapes
- Applies a 150,000 EMU (~0.16") safe margin from edges to prevent shadow/antialiasing overflow

### Chart and Embedded Object Copying
- Detects chart relationships in slide rels (both relative `../charts/chart1.xml` and absolute `/ppt/charts/chart1.xml` paths)
- Copies chart XML files, chart relationship files, and embedded Excel workbooks
- Normalizes absolute chart paths to relative paths in the output rels
- Adds Content_Type overrides for all copied chart and embedding files

### Section Divider Detection & Restyling
- Identifies section dividers by: script header containing "section divider"/"divider", or slides with 1-8 words of non-numeric text
- Replaces divider content with the template's format: centered bold Poppins title (45pt, #003366), teal accent bar (#00A79D), semi-transparent overlay

### Version Slide Update
- Auto-increments the minor version number (e.g., 2.7 → 2.8)
- Sets the date to today's date in MM/DD/YY format
- Uses regex to find "Version X.Y" and date patterns in text runs

### Script Update (Content Preservation)
- Replaces front bookend sections with template versions BUT preserves the original speech content
- The body text from the talk's SLIDE 2 (opening speech) is preserved in the output's SLIDE 2 (TITLE)
- The body text from the talk's last slide (closing remarks) is preserved in the output's ending slide
- This is critical — these sections often contain substantial memorized speech content that must not be lost
- Renumbers all sections to match the new slide order
- Removes sections for skipped duplicate slides

### Duplicate Slide Detection
- Compares text content of consecutive slides
- Slides with identical text to their predecessor are flagged and skipped during conversion

### Cleanup & Validation
- Removes orphaned media files, notes slides, and rels from the template that aren't used
- Cleans stale Content_Types defaults for extensions (like .svg, .mp4) with no matching files
- Fixes notes slide back-references to point to correct slide numbers
- Packs with validation via the pptx skill's `pack.py` (catches broken references before the user sees them)

## Known OOXML Pitfalls (Lessons Learned)

These are hard-won lessons from iterative testing. Keep them in mind if modifying the script:

1. **minidom `id` attribute bug**: Using `setAttribute('id', ...)` on programmatically-created elements causes the value to be silently dropped during `toxml()`. The script uses string manipulation for `p:sldId` elements instead.

2. **Chart paths can be absolute**: Slide rels may use `/ppt/charts/chart1.xml` (absolute) instead of `../charts/chart1.xml` (relative). Must check for both when copying charts.

3. **Content_Types completeness**: Every file in the ZIP (charts, embeddings, slides, notes) must have a matching Override or Default entry in `[Content_Types].xml`. Missing entries cause PowerPoint to prompt for "repair" and silently delete content.

4. **Background inheritance hierarchy**: A slide's background comes from: (1) explicit `<p:bg>` on the slide itself, (2) the slide layout's background, (3) the slide master's background. If the slide has an explicit `<p:bg>`, it blocks layout inheritance entirely. Must strip it for the layout background to show through.

5. **`p:xfrm` vs `a:xfrm`**: Regular shapes use `a:xfrm` for positioning, but graphicFrames (charts, tables, SmartArt) use `p:xfrm`. Scaling/clamping code must handle BOTH or charts/tables will be the wrong size.

6. **Uniform compression for overflow**: Per-shape clamping (just shrinking overflowing shapes) produces ugly results where some shapes are squished while others are normal. Uniform compression of ALL shapes preserves proportional relationships.

7. **Scheme colors resolve differently per theme**: `bg1`, `lt1`, `bg2`, `lt2` resolve to white/light in most themes but dark in dark themes. When switching themes, these must be replaced with explicit colors.

8. **Accent colors from dark themes**: Colors like teal #00A79D work as readable accents on dark backgrounds but look washed-out or oddly colored on white. They need to be remapped to colors that work on the new background.

9. **Work directory permissions**: When the output directory is on a mounted/shared filesystem, `shutil.rmtree` may fail with permission errors. Use `tempfile.gettempdir()` for intermediate work directories.

10. **Script content preservation**: Bookend slides (title/opening, closing) often contain substantial speech content. The script updater must preserve the BODY text from these sections, not replace them with stubs.

11. **Font sizes must scale with slide dimensions**: When slide dimensions change (e.g., 10"→13.33" wide), shape positions and sizes get scaled but font sizes are left untouched by default. This makes text appear too small on the larger canvas. All `sz=` attributes in `a:rPr` and `a:defRPr` must be scaled by the same factor as the slide dimensions.

## Handling Edge Cases

- **Missing tst_template.pptx**: Ask the user where their template deck is located
- **Slide/script count mismatch**: Warn the user and ask them to verify before proceeding
- **No section dividers detected**: That's fine — all slides get the standard content layout
- **Charts and embedded objects**: Automatically copied with their Excel data and relationship files
- **Media files**: All images, videos, and other media from both decks are merged (with conflict resolution for same-named files)
- **Different slide dimensions**: Automatically detected and scaled (common: 10"×5.63" talk → 13.33"×7.5" template)
- **PowerPoint repair prompt on open**: Usually caused by missing Content_Types entries — check that all files in the ZIP have matching entries

## Template Structure Reference

The `tst_template.pptx` uses these slides:
- **Slide 1**: Version slide (hidden with `show="0"`) — contains version number and date
- **Slide 2**: Title slide — uses slideLayout1 with branded imagery
- **Slide 3**: "About me" slide — uses slideLayout11 with embedded profile images
- **Slides 4-31**: Various content slides (not used by this converter)
- **Slide 32**: Closing slide — "That's all - thanks!" with contact info

Slide dimensions: 12,192,000 × 6,858,000 EMU (13.33" × 7.5" / widescreen 16:9)

The slide master's background is solid gray (bg2/E7E6E6) — this is NOT what content slides should show. Content slides must use **slideLayout5** which has the white curved-lines background image (`image1.png` via `blipFill`).
