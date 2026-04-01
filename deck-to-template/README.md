# Deck-to-Template Converter

A Claude skill that converts conference talk slide decks (.pptx) and their matching speaker scripts (.md) to a branded business template style.

## Overview

This skill takes a talk deck you've built for a conference and re-skins it to match your business template (`tst_template.pptx`). It handles the full pipeline: swapping themes, adding your branded bookend slides, restyling section dividers, recoloring text for the new background, scaling shapes when dimensions differ, copying charts and embedded objects, and keeping the speaker script in sync with the updated deck.

## Inputs

| File | Description |
|------|-------------|
| Talk deck (.pptx) | The conference presentation to convert |
| Speaker script (.md) | Script with `## SLIDE N: TITLE` delimiters, one section per slide |
| Template deck (tst_template.pptx) | Your branded reference template |

## Outputs

| File | Description |
|------|-------------|
| `<name>_templated.pptx` | Converted deck with template styling |
| `<name>_templated.md` | Updated script synced with the new slide order |

## What It Does

**Template application:**
- Replaces theme, slide master, and layouts with the template's
- All content slides get the white curved-lines background (slideLayout5)
- Section divider slides are restyled with Poppins 45pt title, teal accent bar, and overlay

**Bookend slides:**
- Prepends: version slide (hidden, auto-updated version + date), title slide (auto-extracted title), about-me slide
- Appends: closing slide
- Automatically skips the talk deck's own version, title, and ending slides

**Content preservation:**
- All talk content slides preserved in order
- Charts, embedded Excel workbooks, and linked objects are copied
- Full opening and closing speech text preserved in the script (not replaced with stubs)

**Visual fixes for theme switch:**
- White/light text recolored to dark (#333333) for visibility on white background
- Teal accent text (#00A79D from dark backgrounds) remapped to dark blue (#003366)
- Shapes scaled proportionally when slide dimensions differ
- Overflow handled with uniform compression (preserves relative spacing)

**Script sync:**
- Adds SLIDE sections for bookend slides
- Preserves all original speech content
- Renumbers to match the new deck
- Removes sections for detected duplicate slides

## Usage

```bash
python scripts/convert_to_template.py \
  --talk-deck my-talk.pptx \
  --template-deck tst_template.pptx \
  --script my-talk-script.md \
  --output-dir ./output
```

Optional arguments:
- `--title "Talk Title"` — override auto-extracted title
- `--subtitle "Subtitle"` — add subtitle to title slide

## Dependencies

- Python 3.8+
- The **pptx skill** must be installed at `.claude/skills/pptx/scripts/` (provides `unpack.py`, `pack.py`, `clean.py`)
- `markitdown[pptx]` and `Pillow` Python packages

```bash
pip install "markitdown[pptx]" Pillow --break-system-packages -q
```

## File Structure

```
deck-to-template/
├── SKILL.md                          # Skill definition and detailed instructions
├── README.md                         # This file
└── scripts/
    └── convert_to_template.py        # Main conversion script (~1970 lines)
```

## Template Reference

The converter expects `tst_template.pptx` with this structure:
- Slide 1: Version slide (hidden) — "Version X.Y" and "MM/DD/YY" text
- Slide 2: Title slide — branded layout with imagery
- Slide 3: About-me slide — profile images and bio
- Slide 32 (last): Closing slide — "That's all - thanks!"
- Slide dimensions: 12,192,000 × 6,858,000 EMU (13.33" × 7.5")
- slideLayout5: White background with curved-lines image (image1.png)

## Key Technical Details

The script handles several OOXML complexities:

- **Background inheritance**: Strips explicit `<p:bg>` from imported slides so the layout's curved-lines background shows through
- **Dual xfrm scaling**: Handles both `a:xfrm` (shapes) and `p:xfrm` (charts/tables) for dimension scaling
- **Chart copying**: Copies chart XML, relationship files, and embedded Excel workbooks; normalizes absolute paths to relative
- **Content_Types completeness**: Ensures every file in the ZIP has a matching entry to prevent PowerPoint repair prompts
- **minidom id bug workaround**: Uses string manipulation for `p:sldId` elements instead of `setAttribute('id', ...)`
- **Uniform overflow compression**: When shapes overflow after scaling, all positions are compressed proportionally rather than clamping individual shapes

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| PowerPoint asks to repair on open | Missing Content_Types entries for charts/embeddings | Script auto-handles; if still occurs, check for new file types |
| White/blank slides | Text is white on white background | Script auto-recolors; add new colors to `recolor_light_text()` if needed |
| Chart appears tiny | GraphicFrame uses `p:xfrm` not `a:xfrm` | Script handles both; verify with markitdown output |
| Shapes overflow right edge | Source slide already overflowed + scaling | Uniform compression handles this; adjust `SAFE_MARGIN` if needed |
| Script missing speech content | Bookend content replaced with stubs | Script preserves body text from original title/ending sections |
| Teal text hard to read on white | Dark-theme accent color (#00A79D) | Remapped to #003366; add more colors to `accent_remap` dict |
| Permission error during conversion | Work dir on mounted filesystem | Script uses temp directory for intermediate work |
