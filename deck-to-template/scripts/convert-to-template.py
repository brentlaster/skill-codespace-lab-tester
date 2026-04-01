#!/usr/bin/env python3
"""
Deck-to-Template Converter

Converts a talk deck (.pptx) to a business template style by:
1. Replacing theme, slide master, and layouts with the template's
2. Adding bookend slides (version, title, about-me at start; closing at end)
3. Restyling section divider slides
4. Updating the speaker script with new SLIDE sections

Usage:
    python convert_to_template.py \
        --talk-deck talk.pptx \
        --template-deck tst_template.pptx \
        --script script.md \
        --title "My Talk Title" \
        --output-dir ./output
"""

import argparse
import os
import re
import shutil
import sys
import zipfile
import glob
from pathlib import Path
from copy import deepcopy

try:
    from defusedxml import minidom
except ImportError:
    from xml.dom import minidom


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def parse_xml(path):
    """Parse an XML file and return the DOM."""
    with open(path, 'r', encoding='utf-8') as f:
        return minidom.parseString(f.read())


def write_xml(doc, path):
    """Write a DOM back to an XML file with pretty formatting."""
    xml_str = doc.toxml()
    # Ensure XML declaration
    if not xml_str.startswith('<?xml'):
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_str
    with open(path, 'w', encoding='utf-8') as f:
        f.write(xml_str)


def get_text_content(xml_path):
    """Extract all text from a slide XML file."""
    doc = parse_xml(xml_path)
    texts = []
    for t_elem in doc.getElementsByTagName('a:t'):
        if t_elem.firstChild and t_elem.firstChild.nodeValue:
            texts.append(t_elem.firstChild.nodeValue.strip())
    return ' '.join(texts)


def strip_slide_background(slide_xml_path):
    """Remove explicit <p:bg> from a slide so it inherits from the layout."""
    doc = parse_xml(slide_xml_path)
    for bg in doc.getElementsByTagName('p:bg'):
        bg.parentNode.removeChild(bg)
    write_xml(doc, slide_xml_path)


def recolor_light_text(slide_xml_path, dark_color="333333", accent_remap=None):
    """Recolor white and light-colored text to a dark color.

    After stripping dark backgrounds, slides designed for dark themes have
    white (FFFFFF) or light-scheme-colored text that becomes invisible on
    the white template background. This scans all text runs and replaces
    explicit white/light colors with a readable dark color.

    accent_remap is an optional dict mapping source accent colors (uppercase hex)
    to replacement colors. For example, {'00A79D': '003366'} remaps teal accent
    text (designed for dark backgrounds) to dark blue for readability on white.
    """
    if accent_remap is None:
        accent_remap = {}

    changed = False

    # Pattern: replace FFFFFF, FEFEFE, F5F5F5 and similar near-white colors in text runs
    light_colors = {'FFFFFF', 'FEFEFE', 'FDFDFD', 'FCFCFC', 'FBFBFB', 'FAFAFA',
                    'F9F9F9', 'F8F8F8', 'F7F7F7', 'F6F6F6', 'F5F5F5'}

    # Combine: light colors map to dark_color, accent colors map to their remap target
    all_remaps = {c: dark_color for c in light_colors}
    all_remaps.update({k.upper(): v for k, v in accent_remap.items()})

    # Parse XML and fix run properties
    doc = parse_xml(slide_xml_path)

    for rPr in doc.getElementsByTagName('a:rPr'):
        for solidFill in rPr.getElementsByTagName('a:solidFill'):
            for clr in solidFill.getElementsByTagName('a:srgbClr'):
                val = clr.getAttribute('val').upper()
                if val in all_remaps:
                    clr.setAttribute('val', all_remaps[val])
                    changed = True

            # Also check scheme colors that resolve to white/light
            for schemeClr in solidFill.getElementsByTagName('a:schemeClr'):
                scheme_val = schemeClr.getAttribute('val')
                # bg1, lt1, bg2, lt2 typically resolve to white/light in most themes
                if scheme_val in ('bg1', 'lt1', 'bg2', 'lt2'):
                    # Replace scheme color with explicit dark color
                    new_clr = doc.createElement('a:srgbClr')
                    new_clr.setAttribute('val', dark_color)
                    solidFill.replaceChild(new_clr, schemeClr)
                    changed = True

    # Also handle default paragraph run properties (a:defRPr)
    for defRPr in doc.getElementsByTagName('a:defRPr'):
        for solidFill in defRPr.getElementsByTagName('a:solidFill'):
            for clr in solidFill.getElementsByTagName('a:srgbClr'):
                val = clr.getAttribute('val').upper()
                if val in all_remaps:
                    clr.setAttribute('val', all_remaps[val])
                    changed = True
            for schemeClr in solidFill.getElementsByTagName('a:schemeClr'):
                scheme_val = schemeClr.getAttribute('val')
                if scheme_val in ('bg1', 'lt1', 'bg2', 'lt2'):
                    new_clr = doc.createElement('a:srgbClr')
                    new_clr.setAttribute('val', dark_color)
                    solidFill.replaceChild(new_clr, schemeClr)
                    changed = True

    if changed:
        write_xml(doc, slide_xml_path)

    return changed


def detect_duplicate_slides(unpacked_dir, slide_order):
    """Detect content-duplicate slides in a list and return indices to skip.

    Compares text content of each slide with the previous slide.
    If two consecutive slides have identical text, the second one is marked
    as a duplicate to skip.

    Returns a set of indices (into slide_order) that are duplicates.
    """
    duplicates = set()
    prev_text = None
    for idx, slide_rel_path in enumerate(slide_order):
        slide_basename = os.path.basename(slide_rel_path)
        slide_path = os.path.join(unpacked_dir, 'ppt', 'slides', slide_basename)
        text = get_text_content(slide_path).strip()

        if prev_text is not None and text == prev_text and text:
            duplicates.add(idx)

        prev_text = text

    return duplicates


def clean_stale_content_type_defaults(content_types_path, unpacked_dir):
    """Remove Default entries from Content_Types for extensions with no matching files.

    For example, if there's a Default for .svg but no SVG files exist in the
    package, this removes that entry to prevent repair prompts.
    """
    doc = parse_xml(content_types_path)
    changed = False

    for default in list(doc.getElementsByTagName('Default')):
        ext = default.getAttribute('Extension')
        if not ext:
            continue

        # Check if any file with this extension exists in the package
        has_file = False
        for root, dirs, files in os.walk(unpacked_dir):
            for f in files:
                if f.lower().endswith(f'.{ext.lower()}'):
                    has_file = True
                    break
            if has_file:
                break

        if not has_file:
            # Keep essential defaults even without files (rels, xml)
            essential = {'rels', 'xml'}
            if ext.lower() not in essential:
                default.parentNode.removeChild(default)
                changed = True
                print(f"  Removed stale Content_Types Default for .{ext}")

    if changed:
        write_xml(doc, content_types_path)


def get_slide_size(pres_xml_path):
    """Get slide width and height in EMUs from presentation.xml."""
    doc = parse_xml(pres_xml_path)
    for sz in doc.getElementsByTagName('p:sldSz'):
        cx = int(sz.getAttribute('cx'))
        cy = int(sz.getAttribute('cy'))
        return cx, cy
    return 12192000, 6858000  # default widescreen


def scale_slide_positions(slide_xml_path, x_scale, y_scale, max_cx=12192000, max_cy=6858000):
    """
    Scale all shape positions and sizes in a slide by the given factors.
    This handles the case where the source deck uses different slide dimensions
    than the target template.

    After scaling, clamps shape positions and sizes so no shape overflows
    the slide boundaries (max_cx x max_cy in EMUs).
    """
    doc = parse_xml(slide_xml_path)

    # Scale all xfrm elements (positions and sizes)
    # Note: both a:xfrm (shapes) and p:xfrm (graphicFrames like charts) need scaling
    all_xfrms = list(doc.getElementsByTagName('a:xfrm')) + list(doc.getElementsByTagName('p:xfrm'))
    for xfrm in all_xfrms:
        # Skip child offsets/extents inside group shapes for clamping
        # (they use a different coordinate space)
        is_child = False
        parent = xfrm.parentNode
        if parent and parent.nodeName == 'p:grpSpPr':
            # This is the group's own xfrm, not a child shape's
            pass

        for off in xfrm.getElementsByTagName('a:off'):
            # Skip a:chOff (child offset) — handled separately
            if off.nodeName != 'a:off' or off.parentNode != xfrm:
                continue
            x = off.getAttribute('x')
            y = off.getAttribute('y')
            if x:
                off.setAttribute('x', str(int(round(int(x) * x_scale))))
            if y:
                off.setAttribute('y', str(int(round(int(y) * y_scale))))
        for ext in xfrm.getElementsByTagName('a:ext'):
            if ext.nodeName != 'a:ext' or ext.parentNode != xfrm:
                continue
            cx = ext.getAttribute('cx')
            cy = ext.getAttribute('cy')
            if cx:
                ext.setAttribute('cx', str(int(round(int(cx) * x_scale))))
            if cy:
                ext.setAttribute('cy', str(int(round(int(cy) * y_scale))))

        # Also scale child offset/extent for grouped shapes
        for chOff in xfrm.getElementsByTagName('a:chOff'):
            x = chOff.getAttribute('x')
            y = chOff.getAttribute('y')
            if x:
                chOff.setAttribute('x', str(int(round(int(x) * x_scale))))
            if y:
                chOff.setAttribute('y', str(int(round(int(y) * y_scale))))
        for chExt in xfrm.getElementsByTagName('a:chExt'):
            cx = chExt.getAttribute('cx')
            cy = chExt.getAttribute('cy')
            if cx:
                chExt.setAttribute('cx', str(int(round(int(cx) * x_scale))))
            if cy:
                chExt.setAttribute('cy', str(int(round(int(cy) * y_scale))))

    # Clamping pass: ensure no shape overflows slide boundaries.
    # Strategy: first find the max overflow across ALL shapes, then uniformly
    # compress all x-positions so everything fits with a small margin.
    # This preserves relative spacing instead of just squishing the rightmost shapes.
    SAFE_MARGIN = 150000  # ~0.16" margin from edge to prevent shadow/antialiasing overflow
    effective_max_cx = max_cx - SAFE_MARGIN
    effective_max_cy = max_cy - SAFE_MARGIN

    # Pass 1: Find max right-edge and bottom-edge overflow
    max_right_overflow = 0
    max_bottom_overflow = 0
    shape_data = []  # (off_elem, ext_elem, x, y, cx, cy)

    all_xfrms_clamp = list(doc.getElementsByTagName('a:xfrm')) + list(doc.getElementsByTagName('p:xfrm'))
    for xfrm in all_xfrms_clamp:
        off_elem = None
        ext_elem = None
        for child in xfrm.childNodes:
            if child.nodeName == 'a:off':
                off_elem = child
            elif child.nodeName == 'a:ext':
                ext_elem = child

        if off_elem is None or ext_elem is None:
            continue

        x_str = off_elem.getAttribute('x')
        y_str = off_elem.getAttribute('y')
        cx_str = ext_elem.getAttribute('cx')
        cy_str = ext_elem.getAttribute('cy')

        if not (x_str and y_str and cx_str and cy_str):
            continue

        x = int(x_str)
        y = int(y_str)
        cx_val = int(cx_str)
        cy_val = int(cy_str)

        shape_data.append((off_elem, ext_elem, x, y, cx_val, cy_val))

        right_overflow = (x + cx_val) - effective_max_cx
        if right_overflow > 0:
            max_right_overflow = max(max_right_overflow, right_overflow)

        bottom_overflow = (y + cy_val) - effective_max_cy
        if bottom_overflow > 0:
            max_bottom_overflow = max(max_bottom_overflow, bottom_overflow)

    # Pass 2: If there's overflow, compute a uniform compression ratio
    # and apply to all shape positions (not sizes) to preserve proportions
    if max_right_overflow > 0 or max_bottom_overflow > 0:
        # Calculate how much to compress positions to fit everything
        # Find the max right edge across all shapes
        max_right_edge = max((x + cx_val) for _, _, x, _, cx_val, _ in shape_data) if shape_data else 0
        max_bottom_edge = max((y + cy_val) for _, _, _, y, _, cy_val in shape_data) if shape_data else 0

        x_compress = effective_max_cx / max_right_edge if max_right_edge > effective_max_cx else 1.0
        y_compress = effective_max_cy / max_bottom_edge if max_bottom_edge > effective_max_cy else 1.0

        for off_elem, ext_elem, x, y, cx_val, cy_val in shape_data:
            new_x = x
            new_y = y
            new_cx = cx_val
            new_cy = cy_val
            changed = False

            if x_compress < 1.0:
                new_x = int(round(x * x_compress))
                new_cx = int(round(cx_val * x_compress))
                changed = True

            if y_compress < 1.0:
                new_y = int(round(y * y_compress))
                new_cy = int(round(cy_val * y_compress))
                changed = True

            # Final safety clamp (shouldn't be needed but just in case)
            if new_x + new_cx > max_cx:
                new_cx = max_cx - new_x
                changed = True
            if new_y + new_cy > max_cy:
                new_cy = max_cy - new_y
                changed = True
            if new_x < 0:
                new_x = 0
                changed = True
            if new_y < 0:
                new_y = 0
                changed = True

            if changed:
                off_elem.setAttribute('x', str(new_x))
                off_elem.setAttribute('y', str(new_y))
                ext_elem.setAttribute('cx', str(new_cx))
                ext_elem.setAttribute('cy', str(new_cy))

    write_xml(doc, slide_xml_path)


def clean_orphaned_notes(unpacked_dir):
    """Remove notes slides that reference non-existent slides."""
    notes_dir = os.path.join(unpacked_dir, 'ppt', 'notesSlides')
    if not os.path.exists(notes_dir):
        return

    notes_rels_dir = os.path.join(notes_dir, '_rels')
    slides_dir = os.path.join(unpacked_dir, 'ppt', 'slides')

    orphaned = []
    if os.path.exists(notes_rels_dir):
        for f in os.listdir(notes_rels_dir):
            if not f.endswith('.rels'):
                continue
            doc = parse_xml(os.path.join(notes_rels_dir, f))
            for rel in doc.getElementsByTagName('Relationship'):
                target = rel.getAttribute('Target')
                if '../slides/' in target:
                    slide_name = os.path.basename(target)
                    if not os.path.exists(os.path.join(slides_dir, slide_name)):
                        notes_name = f.replace('.xml.rels', '.xml')
                        orphaned.append(notes_name)
                        break

    # Remove orphaned notes and their rels
    for notes_name in orphaned:
        notes_path = os.path.join(notes_dir, notes_name)
        rels_path = os.path.join(notes_rels_dir, f'{notes_name}.rels')
        if os.path.exists(notes_path):
            os.remove(notes_path)
        if os.path.exists(rels_path):
            os.remove(rels_path)

    # Clean Content_Types of orphaned notes
    ct_path = os.path.join(unpacked_dir, '[Content_Types].xml')
    if os.path.exists(ct_path) and orphaned:
        doc = parse_xml(ct_path)
        for override in list(doc.getElementsByTagName('Override')):
            part_name = override.getAttribute('PartName')
            for notes_name in orphaned:
                if notes_name in part_name:
                    override.parentNode.removeChild(override)
        write_xml(doc, ct_path)

    if orphaned:
        print(f"  Cleaned {len(orphaned)} orphaned notes slides")


# ---------------------------------------------------------------------------
# Unpacking / Packing (uses pptx skill's battle-tested scripts)
# ---------------------------------------------------------------------------

# Path to pptx skill scripts (resolved at import time)
_SKILL_SCRIPTS_DIR = None

def _find_skill_scripts():
    """Find the pptx skill scripts directory."""
    global _SKILL_SCRIPTS_DIR
    if _SKILL_SCRIPTS_DIR:
        return _SKILL_SCRIPTS_DIR

    # Check common locations
    candidates = [
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '.claude', 'skills', 'pptx', 'scripts'),
        '/sessions/epic-tender-maxwell/mnt/.claude/skills/pptx/scripts',
    ]
    # Also check relative to the workspace mount
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Walk up to find .claude/skills/pptx/scripts
    parts = script_dir.split(os.sep)
    for i in range(len(parts), 0, -1):
        candidate = os.path.join(os.sep.join(parts[:i]), '.claude', 'skills', 'pptx', 'scripts')
        if os.path.exists(candidate):
            candidates.insert(0, candidate)
            break

    for c in candidates:
        c = os.path.abspath(c)
        if os.path.exists(os.path.join(c, 'office', 'pack.py')):
            _SKILL_SCRIPTS_DIR = c
            return c

    raise FileNotFoundError(
        "Could not find pptx skill scripts. Ensure the pptx skill is installed "
        "at .claude/skills/pptx/scripts/ relative to the workspace."
    )


def unpack_pptx(pptx_path, dest_dir):
    """Unpack a .pptx file using the pptx skill's unpack.py."""
    import subprocess
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    scripts = _find_skill_scripts()
    unpack_script = os.path.join(scripts, 'office', 'unpack.py')

    result = subprocess.run(
        [sys.executable, unpack_script, pptx_path, dest_dir],
        cwd=os.path.join(scripts, 'office'),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  unpack.py stderr: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"unpack.py failed: {result.stderr}")
    print(f"  {result.stdout.strip()}")
    return dest_dir


def clean_unpacked(unpacked_dir):
    """Run the pptx skill's clean.py to remove orphaned files."""
    import subprocess
    scripts = _find_skill_scripts()
    clean_script = os.path.join(scripts, 'clean.py')

    result = subprocess.run(
        [sys.executable, clean_script, unpacked_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  clean.py stderr: {result.stderr}", file=sys.stderr)
    else:
        print(f"  {result.stdout.strip()}")


def pack_pptx(src_dir, output_path, original_pptx=None):
    """Pack a directory into a .pptx using the pptx skill's pack.py with validation."""
    import subprocess
    if os.path.exists(output_path):
        os.remove(output_path)

    scripts = _find_skill_scripts()
    pack_script = os.path.join(scripts, 'office', 'pack.py')

    cmd = [sys.executable, pack_script, src_dir, output_path]
    if original_pptx:
        cmd.extend(['--original', original_pptx])

    result = subprocess.run(
        cmd,
        cwd=os.path.join(scripts, 'office'),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  pack.py stderr: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"pack.py failed: {result.stderr}")
    print(f"  {result.stdout.strip()}")


# ---------------------------------------------------------------------------
# Slide order helpers
# ---------------------------------------------------------------------------

def get_slide_list(pres_xml_path):
    """Get ordered list of (id, rId) from presentation.xml sldIdLst."""
    doc = parse_xml(pres_xml_path)
    slides = []
    for sld_id in doc.getElementsByTagName('p:sldId'):
        sid = sld_id.getAttribute('id')
        rid = sld_id.getAttribute('r:id')
        slides.append((sid, rid))
    return slides


def get_rid_to_slide_map(pres_rels_path):
    """Map rId -> slide filename from presentation.xml.rels."""
    doc = parse_xml(pres_rels_path)
    rid_map = {}
    for rel in doc.getElementsByTagName('Relationship'):
        rid = rel.getAttribute('Id')
        target = rel.getAttribute('Target')
        if 'slides/slide' in target:
            rid_map[rid] = target  # e.g., "slides/slide1.xml"
    return rid_map


def get_slide_to_rid_map(pres_rels_path):
    """Map slide filename -> rId from presentation.xml.rels."""
    doc = parse_xml(pres_rels_path)
    slide_map = {}
    for rel in doc.getElementsByTagName('Relationship'):
        rid = rel.getAttribute('Id')
        target = rel.getAttribute('Target')
        if 'slides/slide' in target:
            slide_map[target] = rid
    return slide_map


def get_slide_order(unpacked_dir):
    """Get ordered list of slide filenames as they appear in the presentation."""
    pres_xml = os.path.join(unpacked_dir, 'ppt', 'presentation.xml')
    pres_rels = os.path.join(unpacked_dir, 'ppt', '_rels', 'presentation.xml.rels')
    slide_list = get_slide_list(pres_xml)
    rid_map = get_rid_to_slide_map(pres_rels)
    ordered = []
    for sid, rid in slide_list:
        if rid in rid_map:
            ordered.append(rid_map[rid])  # "slides/slide1.xml"
    return ordered


# ---------------------------------------------------------------------------
# Section divider detection
# ---------------------------------------------------------------------------

def is_section_divider(slide_xml_path, slide_text, slide_header=""):
    """Detect if a slide is a section divider based on content and header."""
    # Check script header for explicit section divider markers
    header_lower = slide_header.lower()
    if 'section divider' in header_lower or 'divider' in header_lower:
        return True

    # Check for very short text content (just a title phrase)
    text = slide_text.strip()
    words = text.split()
    if len(words) <= 8 and len(words) >= 1:
        # Short text that looks like a section title
        # But exclude slides with numbers, stats, or complex content
        if not any(c.isdigit() for c in text) and '%' not in text:
            return True

    return False


# ---------------------------------------------------------------------------
# Template section divider XML
# ---------------------------------------------------------------------------

SECTION_DIVIDER_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="10" name="Accent Bar"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="5619750" y="2709862"/>
            <a:ext cx="952500" cy="47625"/>
          </a:xfrm>
          <a:prstGeom prst="rect">
            <a:avLst/>
          </a:prstGeom>
          <a:solidFill>
            <a:srgbClr val="00A79D"/>
          </a:solidFill>
          <a:ln>
            <a:noFill/>
          </a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr spcFirstLastPara="1" wrap="square" lIns="91425" tIns="45700" rIns="91425" bIns="45700" anchor="ctr" anchorCtr="0">
            <a:noAutofit/>
          </a:bodyPr>
          <a:lstStyle/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:endParaRPr sz="1800"/>
          </a:p>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="11" name="Divider Title"/>
          <p:cNvSpPr txBox="1"/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="907627" y="3125613"/>
            <a:ext cx="10376745" cy="692497"/>
          </a:xfrm>
          <a:prstGeom prst="rect">
            <a:avLst/>
          </a:prstGeom>
          <a:noFill/>
          <a:ln>
            <a:noFill/>
          </a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr spcFirstLastPara="1" wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" anchorCtr="0">
            <a:spAutoFit/>
          </a:bodyPr>
          <a:lstStyle/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:r>
              <a:rPr lang="en-US" sz="4500" b="1" dirty="0">
                <a:solidFill>
                  <a:srgbClr val="003366"/>
                </a:solidFill>
                <a:latin typeface="Poppins"/>
                <a:cs typeface="Poppins"/>
                <a:sym typeface="Poppins"/>
              </a:rPr>
              <a:t>{DIVIDER_TEXT}</a:t>
            </a:r>
            <a:endParaRPr dirty="0"/>
          </a:p>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="12" name="Overlay"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="0" y="42861"/>
            <a:ext cx="12192000" cy="6858000"/>
          </a:xfrm>
          <a:prstGeom prst="rect">
            <a:avLst/>
          </a:prstGeom>
          <a:solidFill>
            <a:srgbClr val="EBE3D0">
              <a:alpha val="16000"/>
            </a:srgbClr>
          </a:solidFill>
        </p:spPr>
        <p:style>
          <a:lnRef idx="2">
            <a:schemeClr val="accent1">
              <a:shade val="15000"/>
            </a:schemeClr>
          </a:lnRef>
          <a:fillRef idx="1">
            <a:schemeClr val="accent1"/>
          </a:fillRef>
          <a:effectRef idx="0">
            <a:schemeClr val="accent1"/>
          </a:effectRef>
          <a:fontRef idx="minor">
            <a:schemeClr val="lt1"/>
          </a:fontRef>
        </p:style>
        <p:txBody>
          <a:bodyPr rtlCol="0" anchor="ctr"/>
          <a:lstStyle/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:endParaRPr lang="en-US" dirty="0"/>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>'''


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def find_next_slide_num(slides_dir):
    """Find the next available slide number in a slides directory."""
    existing = []
    for f in os.listdir(slides_dir):
        m = re.match(r'slide(\d+)\.xml', f)
        if m:
            existing.append(int(m.group(1)))
    return max(existing) + 1 if existing else 1


def find_next_rid(rels_path):
    """Find the next available rId number in a .rels file."""
    doc = parse_xml(rels_path)
    max_id = 0
    for rel in doc.getElementsByTagName('Relationship'):
        rid = rel.getAttribute('Id')
        m = re.match(r'rId(\d+)', rid)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def find_next_sld_id(pres_xml_path):
    """Find the next available slide ID in presentation.xml."""
    doc = parse_xml(pres_xml_path)
    max_id = 256  # PowerPoint starts around here
    for sld_id in doc.getElementsByTagName('p:sldId'):
        sid_str = sld_id.getAttribute('id')
        if sid_str:
            sid = int(sid_str)
            max_id = max(max_id, sid)
    return max_id + 1


def copy_slide_file(src_slide_path, dest_slides_dir, new_slide_num):
    """Copy a slide XML file with a new number."""
    dest_path = os.path.join(dest_slides_dir, f'slide{new_slide_num}.xml')
    shutil.copy2(src_slide_path, dest_path)
    return dest_path


def create_slide_rels(dest_rels_dir, slide_num, layout_target="../slideLayouts/slideLayout5.xml",
                      extra_rels=None):
    """Create a .rels file for a slide pointing to the specified layout."""
    rels_path = os.path.join(dest_rels_dir, f'slide{slide_num}.xml.rels')

    rels_xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    rels_xml += '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
    rels_xml += f'  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="{layout_target}"/>\n'

    if extra_rels:
        for rid, rtype, target in extra_rels:
            rels_xml += f'  <Relationship Id="{rid}" Type="{rtype}" Target="{target}"/>\n'

    rels_xml += '</Relationships>'

    with open(rels_path, 'w', encoding='utf-8') as f:
        f.write(rels_xml)
    return rels_path


def fix_notes_back_references(output_unpacked):
    """Fix bidirectional references between slides and their notes slides.

    When slides are renumbered, the notes slides still point back to the old
    slide numbers. This updates the notes rels to point to the correct slide.
    """
    notes_dir = os.path.join(output_unpacked, 'ppt', 'notesSlides')
    notes_rels_dir = os.path.join(notes_dir, '_rels')
    slides_dir = os.path.join(output_unpacked, 'ppt', 'slides')
    slides_rels_dir = os.path.join(slides_dir, '_rels')

    if not os.path.exists(notes_rels_dir):
        return

    # Build a map: which slide references which notes slide?
    slide_to_notes = {}
    notes_to_slide = {}
    if os.path.exists(slides_rels_dir):
        for f in os.listdir(slides_rels_dir):
            if not f.endswith('.rels'):
                continue
            m = re.match(r'slide(\d+)\.xml\.rels', f)
            if not m:
                continue
            slide_num = int(m.group(1))
            doc = parse_xml(os.path.join(slides_rels_dir, f))
            for rel in doc.getElementsByTagName('Relationship'):
                if 'notesSlide' in rel.getAttribute('Type'):
                    notes_target = os.path.basename(rel.getAttribute('Target'))
                    slide_to_notes[slide_num] = notes_target
                    notes_to_slide[notes_target] = slide_num

    # Fix each notes slide's back-reference to its parent slide
    fixed = 0
    for notes_name, correct_slide_num in notes_to_slide.items():
        notes_rels_path = os.path.join(notes_rels_dir, f'{notes_name}.rels')
        if not os.path.exists(notes_rels_path):
            continue

        doc = parse_xml(notes_rels_path)
        changed = False
        for rel in doc.getElementsByTagName('Relationship'):
            target = rel.getAttribute('Target')
            if '../slides/' in target:
                correct_target = f'../slides/slide{correct_slide_num}.xml'
                if target != correct_target:
                    rel.setAttribute('Target', correct_target)
                    changed = True
                    fixed += 1

        if changed:
            write_xml(doc, notes_rels_path)

    if fixed:
        print(f"  Fixed {fixed} notes back-reference(s)")


def copy_slide_with_rels(src_unpacked, src_slide_rel_path, dest_unpacked, new_slide_num,
                         layout_target="../slideLayouts/slideLayout5.xml",
                         copy_media=True):
    """
    Copy a slide and its relationships, remapping the layout reference.
    Returns list of (old_media_path, new_media_path) for media files that need copying.
    """
    src_slide_name = os.path.basename(src_slide_rel_path).replace('.xml', '')
    # e.g., "slide5"
    m = re.match(r'slide(\d+)', src_slide_name)
    src_num = m.group(1) if m else src_slide_name

    src_slide_xml = os.path.join(src_unpacked, 'ppt', 'slides', f'slide{src_num}.xml')
    dest_slide_xml = os.path.join(dest_unpacked, 'ppt', 'slides', f'slide{new_slide_num}.xml')

    # Copy slide XML
    shutil.copy2(src_slide_xml, dest_slide_xml)

    # Process relationships
    src_rels_path = os.path.join(src_unpacked, 'ppt', 'slides', '_rels', f'slide{src_num}.xml.rels')
    dest_rels_dir = os.path.join(dest_unpacked, 'ppt', 'slides', '_rels')
    os.makedirs(dest_rels_dir, exist_ok=True)
    dest_rels_path = os.path.join(dest_rels_dir, f'slide{new_slide_num}.xml.rels')

    media_copies = []

    if os.path.exists(src_rels_path):
        doc = parse_xml(src_rels_path)
        for rel in doc.getElementsByTagName('Relationship'):
            rtype = rel.getAttribute('Type')
            target = rel.getAttribute('Target')

            # Remap slideLayout reference to the template's layout
            if 'slideLayout' in rtype:
                rel.setAttribute('Target', layout_target)

            # Track media files that need copying
            if 'image' in rtype or 'video' in rtype or 'audio' in rtype:
                if target.startswith('../media/'):
                    media_name = os.path.basename(target)
                    src_media = os.path.join(src_unpacked, 'ppt', 'media', media_name)
                    dest_media = os.path.join(dest_unpacked, 'ppt', 'media', media_name)
                    if os.path.exists(src_media):
                        media_copies.append((src_media, dest_media))

        write_xml(doc, dest_rels_path)
    else:
        # Create minimal rels with just the layout
        create_slide_rels(dest_rels_dir, new_slide_num, layout_target)

    # Copy notes slide if it exists
    src_notes_dir = os.path.join(src_unpacked, 'ppt', 'notesSlides')
    if os.path.exists(src_notes_dir):
        # Find the notes slide that corresponds to this slide
        src_notes_rels = os.path.join(src_unpacked, 'ppt', 'slides', '_rels', f'slide{src_num}.xml.rels')
        if os.path.exists(src_notes_rels):
            ndoc = parse_xml(src_notes_rels)
            for rel in ndoc.getElementsByTagName('Relationship'):
                if 'notesSlide' in rel.getAttribute('Type'):
                    notes_target = rel.getAttribute('Target')
                    # We don't copy notes for now - they'd need their own remapping
                    break

    return media_copies


def add_slide_to_presentation(pres_xml_path, pres_rels_path, slide_num, position=None):
    """
    Add a slide reference to presentation.xml and its rels.
    position=None means append at end.
    Returns the rId used.

    NOTE: Uses string manipulation for sldIdLst because minidom has a known bug
    where setAttribute('id', ...) on programmatically-created elements gets
    silently dropped during toxml() serialization.
    """
    # Add to presentation.xml.rels
    next_rid_num = find_next_rid(pres_rels_path)
    rid = f'rId{next_rid_num}'

    rels_doc = parse_xml(pres_rels_path)
    rels_root = rels_doc.documentElement
    new_rel = rels_doc.createElement('Relationship')
    new_rel.setAttribute('Id', rid)
    new_rel.setAttribute('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide')
    new_rel.setAttribute('Target', f'slides/slide{slide_num}.xml')
    rels_root.appendChild(new_rel)
    write_xml(rels_doc, pres_rels_path)

    # Add to presentation.xml sldIdLst using string manipulation
    # (minidom drops 'id' attributes on programmatically-created elements)
    next_sid = find_next_sld_id(pres_xml_path)

    with open(pres_xml_path, 'r', encoding='utf-8') as f:
        pres_content = f.read()

    sld_id_xml = f'<p:sldId id="{next_sid}" r:id="{rid}"/>'

    if position is not None:
        # Find the Nth existing sldId and insert before it
        sld_id_pattern = re.compile(r'<p:sldId\s[^/]*/>')
        matches = list(sld_id_pattern.finditer(pres_content))
        if position < len(matches):
            insert_pos = matches[position].start()
            pres_content = pres_content[:insert_pos] + sld_id_xml + pres_content[insert_pos:]
        else:
            # Append before </p:sldIdLst>
            pres_content = pres_content.replace('</p:sldIdLst>', sld_id_xml + '</p:sldIdLst>')
    else:
        # Append before </p:sldIdLst>
        pres_content = pres_content.replace('</p:sldIdLst>', sld_id_xml + '</p:sldIdLst>')

    with open(pres_xml_path, 'w', encoding='utf-8') as f:
        f.write(pres_content)

    return rid


def remove_all_slides_from_presentation(pres_xml_path, pres_rels_path):
    """Remove all slide references from presentation.xml and rels. Returns removed (rid, target) tuples."""
    removed = []

    # Get current slides and remove from rels
    rels_doc = parse_xml(pres_rels_path)
    slide_rels = []
    for rel in rels_doc.getElementsByTagName('Relationship'):
        if 'relationships/slide' in rel.getAttribute('Type') and 'slides/slide' in rel.getAttribute('Target'):
            slide_rels.append(rel)

    for rel in slide_rels:
        rid = rel.getAttribute('Id')
        target = rel.getAttribute('Target')
        removed.append((rid, target))
        rel.parentNode.removeChild(rel)
    write_xml(rels_doc, pres_rels_path)

    # Clear sldIdLst using string manipulation (avoids minidom 'id' attribute bug)
    with open(pres_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all <p:sldId .../> elements from within sldIdLst
    content = re.sub(r'<p:sldId\s[^/]*/>', '', content)

    with open(pres_xml_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return removed


def update_content_types(content_types_path, slide_nums, unpacked_dir=None):
    """Ensure [Content_Types].xml has entries for all slides, charts, and embeddings."""
    doc = parse_xml(content_types_path)
    types_elem = doc.documentElement

    # Find existing slide overrides
    existing_slides = set()
    existing_parts = set()
    for override in doc.getElementsByTagName('Override'):
        part_name = override.getAttribute('PartName')
        existing_parts.add(part_name)
        m = re.match(r'/ppt/slides/slide(\d+)\.xml', part_name)
        if m:
            existing_slides.add(int(m.group(1)))

    # Add missing slide entries
    for num in slide_nums:
        if num not in existing_slides:
            new_override = doc.createElement('Override')
            new_override.setAttribute('PartName', f'/ppt/slides/slide{num}.xml')
            new_override.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
            types_elem.appendChild(new_override)

    # Remove entries for slides that no longer exist
    for override in list(doc.getElementsByTagName('Override')):
        part_name = override.getAttribute('PartName')
        m = re.match(r'/ppt/slides/slide(\d+)\.xml', part_name)
        if m and int(m.group(1)) not in slide_nums:
            override.parentNode.removeChild(override)

    # Add Content_Types for charts and embeddings if they exist
    if unpacked_dir:
        # Add Content_Types for chart files
        charts_dir = os.path.join(unpacked_dir, 'ppt', 'charts')
        if os.path.exists(charts_dir):
            for f in os.listdir(charts_dir):
                if f.endswith('.xml') and not f.startswith('_'):
                    part_name = f'/ppt/charts/{f}'
                    if part_name not in existing_parts:
                        new_override = doc.createElement('Override')
                        new_override.setAttribute('PartName', part_name)
                        new_override.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml')
                        types_elem.appendChild(new_override)
                        existing_parts.add(part_name)
                        print(f"  Added Content_Type for {part_name}")

        # Add Content_Types for embedded files (Excel workbooks, etc.)
        embeddings_dir = os.path.join(unpacked_dir, 'ppt', 'embeddings')
        if os.path.exists(embeddings_dir):
            # Map file extensions to content types
            embedding_content_types = {
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.bin': 'application/vnd.openxmlformats-officedocument.oleObject',
            }
            for f in os.listdir(embeddings_dir):
                if f.startswith('_') or f.startswith('.'):
                    continue
                part_name = f'/ppt/embeddings/{f}'
                if part_name not in existing_parts:
                    _, ext = os.path.splitext(f)
                    ct = embedding_content_types.get(ext.lower(), 'application/vnd.openxmlformats-officedocument.oleObject')
                    new_override = doc.createElement('Override')
                    new_override.setAttribute('PartName', part_name)
                    new_override.setAttribute('ContentType', ct)
                    types_elem.appendChild(new_override)
                    existing_parts.add(part_name)
                    print(f"  Added Content_Type for {part_name}")

    write_xml(doc, content_types_path)


def update_version_slide(slide_xml_path, version=None, date_str=None):
    """Update the version number and date on the version slide (slide 1).

    Scans text runs for version patterns (e.g., "Version 2.7") and date
    patterns (e.g., "03/23/26"), replacing them with the provided values.
    If no version is provided, auto-increments the major version.
    If no date is provided, uses today's date.
    """
    from datetime import date as dt_date

    if date_str is None:
        today = dt_date.today()
        date_str = today.strftime('%m/%d/%y')

    doc = parse_xml(slide_xml_path)

    for t_elem in doc.getElementsByTagName('a:t'):
        if not t_elem.firstChild or not t_elem.firstChild.nodeValue:
            continue
        text = t_elem.firstChild.nodeValue

        # Update version number
        version_match = re.search(r'(Version\s+)(\d+\.\d+)', text)
        if version_match:
            if version is None:
                # Auto-increment: bump minor version
                old_ver = version_match.group(2)
                parts = old_ver.split('.')
                new_minor = int(parts[1]) + 1 if len(parts) > 1 else 1
                version = f"{parts[0]}.{new_minor}"
            t_elem.firstChild.nodeValue = text.replace(version_match.group(0), f'Version {version}')
            print(f"  Updated version: {version_match.group(2)} -> {version}")

        # Update date (MM/DD/YY format)
        date_match = re.search(r'\d{2}/\d{2}/\d{2}', text)
        if date_match:
            t_elem.firstChild.nodeValue = text.replace(date_match.group(0), date_str)
            print(f"  Updated date: {date_match.group(0)} -> {date_str}")

    write_xml(doc, slide_xml_path)


def update_title_slide(slide_xml_path, title, subtitle=None):
    """Update the title slide text content.

    Finds the body placeholder on the template title slide and replaces the
    first prominent text line with the talk title, and the second with the subtitle
    (or clears it if no subtitle provided).
    """
    doc = parse_xml(slide_xml_path)

    # Find text elements and update them
    # The title slide (slide 2 from template) has a body placeholder with the title text
    for sp in doc.getElementsByTagName('p:sp'):
        nvSpPr = sp.getElementsByTagName('p:nvSpPr')
        if nvSpPr:
            for ph in sp.getElementsByTagName('p:ph'):
                ph_type = ph.getAttribute('type')
                if ph_type == 'body' or ph_type == '':
                    # This is the body/subtitle placeholder
                    txBody = sp.getElementsByTagName('p:txBody')
                    if txBody:
                        # Collect paragraphs with their text runs
                        paragraphs = txBody[0].getElementsByTagName('a:p')
                        title_set = False
                        subtitle_set = False
                        for p_elem in paragraphs:
                            runs = p_elem.getElementsByTagName('a:r')
                            if not runs:
                                continue
                            # Get the combined text of this paragraph
                            para_text = ''
                            for r in runs:
                                for t in r.getElementsByTagName('a:t'):
                                    if t.firstChild and t.firstChild.nodeValue:
                                        para_text += t.firstChild.nodeValue
                            para_text = para_text.strip()

                            # Skip lines that are attribution/copyright
                            if not para_text or 'presented by' in para_text.lower() or \
                               '©' in para_text or 'all rights' in para_text.lower() or \
                               para_text.strip() == '':
                                continue

                            if not title_set:
                                # Replace the first significant line with the title
                                for r in runs:
                                    for t in r.getElementsByTagName('a:t'):
                                        if t.firstChild and t.firstChild.nodeValue:
                                            t.firstChild.nodeValue = title
                                            title_set = True
                                            break
                                    if title_set:
                                        # Clear any additional runs in this paragraph
                                        for r2 in runs[runs.index(r)+1:] if r in runs else []:
                                            for t2 in r2.getElementsByTagName('a:t'):
                                                if t2.firstChild:
                                                    t2.firstChild.nodeValue = ''
                                        break
                            elif not subtitle_set:
                                # Replace or clear the subtitle line
                                for r in runs:
                                    for t in r.getElementsByTagName('a:t'):
                                        if t.firstChild and t.firstChild.nodeValue:
                                            t.firstChild.nodeValue = subtitle if subtitle else ''
                                            subtitle_set = True
                                            break
                                    if subtitle_set:
                                        break

    write_xml(doc, slide_xml_path)


def create_section_divider(dest_slides_dir, slide_num, divider_text):
    """Create a section divider slide with the template style."""
    slide_xml = SECTION_DIVIDER_TEMPLATE.replace('{DIVIDER_TEXT}', divider_text)
    dest_path = os.path.join(dest_slides_dir, f'slide{slide_num}.xml')
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(slide_xml)
    return dest_path


# ---------------------------------------------------------------------------
# Script processing
# ---------------------------------------------------------------------------

def parse_script_slides(script_path):
    """Parse the script into SLIDE sections. Returns list of (header, content) tuples."""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on ## SLIDE headers
    pattern = r'^(## SLIDE .+?)(?=\n## SLIDE |\n## TIMING CHECKPOINTS|\n## WORD COUNT|\Z)'
    sections = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    result = []
    for section in sections:
        lines = section.strip().split('\n')
        header = lines[0] if lines else ''
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
        result.append((header, body))

    return result


def extract_title_from_slide(slide_xml_path):
    """Extract the title text from a slide's XML content.

    Looks for the largest/most prominent text in the slide, which is typically the title.
    Combines consecutive paragraphs at the same font size (handles multi-line titles).
    Returns None if no suitable title text is found.
    """
    if not os.path.exists(slide_xml_path):
        return None

    doc = parse_xml(slide_xml_path)

    # Collect all paragraphs with their font sizes (ordered as they appear)
    text_runs = []
    for sp in doc.getElementsByTagName('p:sp'):
        for p_elem in sp.getElementsByTagName('a:p'):
            para_text_parts = []
            max_font_size = 0
            for r_elem in p_elem.getElementsByTagName('a:r'):
                for rPr in r_elem.getElementsByTagName('a:rPr'):
                    sz = rPr.getAttribute('sz')
                    if sz:
                        max_font_size = max(max_font_size, int(sz))
                for t_elem in r_elem.getElementsByTagName('a:t'):
                    if t_elem.firstChild and t_elem.firstChild.nodeValue:
                        para_text_parts.append(t_elem.firstChild.nodeValue.strip())
            if para_text_parts:
                text_runs.append((max_font_size, ' '.join(para_text_parts)))

    if not text_runs:
        return None

    # Find the maximum font size
    max_size = max(sz for sz, _ in text_runs)

    # Combine consecutive paragraphs at the largest font size
    title_parts = []
    for font_size, text in text_runs:
        text = text.strip()
        if font_size == max_size and text:
            # Skip organizational info even at largest size
            if text.lower().startswith('presented by') or 'llc' in text.lower():
                continue
            if text.replace('.', '').replace('/', '').isdigit():
                continue
            title_parts.append(text)
        elif title_parts:
            # Stop once we hit a different font size after collecting title parts
            break

    if title_parts:
        return ' '.join(title_parts)

    return None


def extract_title_from_script(script_path, talk_unpacked_dir=None):
    """Extract the talk title from the script or the talk's title slide.

    Strategy:
    1. If a talk unpacked dir is provided, read the title from the title slide XML
       (the second slide in the deck).
    2. Otherwise, try to parse the script header for SLIDE 2.
    3. If the header just says "TITLE", look in the script body content.
    """
    # Strategy 1: Read from the talk's actual title slide (most reliable)
    if talk_unpacked_dir:
        slide_order = get_slide_order(talk_unpacked_dir)
        if len(slide_order) >= 2:
            title_slide_file = os.path.basename(slide_order[1])
            title_slide_path = os.path.join(talk_unpacked_dir, 'ppt', 'slides', title_slide_file)
            title = extract_title_from_slide(title_slide_path)
            if title:
                return title

    # Strategy 2: Parse the script
    sections = parse_script_slides(script_path)
    if len(sections) >= 2:
        header = sections[1][0]  # Second SLIDE header
        content = sections[1][1]

        # Try the header (e.g., "## SLIDE 2: MY ACTUAL TITLE")
        m = re.match(r'## SLIDE \d+[a-z]?:\s*(.+)', header)
        if m:
            header_title = m.group(1).strip()
            # Only use if it's not a generic label
            if header_title.upper() not in ('TITLE', 'TITLE SLIDE', 'OPENING'):
                return header_title

        # Try the script body content - first non-stage-direction line
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Skip stage directions [bracketed], greetings, and intro phrases
            if (line.startswith('[') or line.startswith('Good ') or
                    line.startswith("I'm ") or line.startswith('Hi ') or
                    line.startswith('Hello') or line.startswith('Welcome')):
                continue
            # This could be the title
            if len(line) > 5 and len(line) < 100:
                return line

    return "Untitled Talk"


def update_script(script_path, output_path, talk_title, skip_front=0, skip_end=0,
                   skip_duplicate_indices=None):
    """Update script to match the templated deck.

    Replaces the talk's bookend sections with template versions, adds an about-me
    section, and renumbers everything to match the new slide order.

    Args:
        script_path: Path to the original script
        output_path: Path to write the updated script
        talk_title: The talk title to use on the title slide
        skip_front: Number of front bookend slides skipped from talk deck
        skip_end: Number of end bookend slides skipped from talk deck
        skip_duplicate_indices: Set of indices (relative to post-bookend-skip order)
            that are duplicates and should be removed from the script
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse existing sections
    sections = parse_script_slides(script_path)

    # Extract the preamble (everything before the first ## SLIDE)
    first_slide_match = re.search(r'^## SLIDE ', content, re.MULTILINE)
    if not first_slide_match:
        print("ERROR: No ## SLIDE sections found in script")
        return
    preamble = content[:first_slide_match.start()]

    # Get the raw text for each section by splitting the content
    # We need the full raw text (not just header+body from parse) to preserve formatting
    slide_content = content[first_slide_match.start():]

    # Find all section boundaries
    section_starts = [(m.start(), m.group(0)) for m in re.finditer(r'^## SLIDE .+', slide_content, re.MULTILINE)]

    # Helper: extract raw text for section i
    def get_section_raw(i):
        if i >= len(section_starts):
            return ""
        start = section_starts[i][0]
        if i + 1 < len(section_starts):
            end = section_starts[i + 1][0]
        else:
            timing_match = re.search(r'^## TIMING CHECKPOINTS', slide_content, re.MULTILINE)
            word_count_match = re.search(r'^## WORD COUNT', slide_content, re.MULTILINE)
            end = len(slide_content)
            if timing_match:
                end = min(end, timing_match.start())
            if word_count_match:
                end = min(end, word_count_match.start())
        return slide_content[start:end]

    # Helper: extract just the body from a raw section (everything after the header line)
    def get_section_body(raw):
        lines = raw.split('\n', 1)
        return lines[1] if len(lines) > 1 else ''

    # Build the template front sections, PRESERVING original content from bookend slides.
    # The template adds 3 front slides: version (new), title (keep original body), about-me (new).
    # The original script's front bookend slides have speech content that must be kept.

    # Version slide: new section (template's hidden version slide has no speech)
    version_section = "## SLIDE 1: VERSION\n[Skip]\n\n---\n\n"

    # Title slide: keep the BODY from the original SLIDE 2 (the opening speech)
    if skip_front >= 2 and len(section_starts) >= 2:
        original_title_body = get_section_body(get_section_raw(1))
        title_section = f"## SLIDE 2: TITLE\n{original_title_body}"
    else:
        title_section = f"## SLIDE 2: TITLE\n\n{talk_title}\n\n[Advance to next slide]\n\n---\n\n"

    # About-me slide: new section (template's about-me slide is new)
    about_me_section = "## SLIDE 3: ABOUT ME\n\n[Brief personal introduction - use content on slide]\n\n---\n\n"

    front_sections = [version_section, title_section, about_me_section]

    # Determine which sections to keep from the talk (skip bookends)
    keep_start = skip_front
    keep_end = len(sections) - skip_end if skip_end > 0 else len(sections)

    # Extract raw text for the sections we're keeping (excluding duplicates)
    kept_raw_sections = []
    relative_idx = 0  # Index relative to post-bookend-skip order
    for i in range(keep_start, keep_end):
        raw = get_section_raw(i)
        if not raw:
            relative_idx += 1
            continue

        # Skip if this section corresponds to a duplicate slide
        if skip_duplicate_indices and relative_idx in skip_duplicate_indices:
            relative_idx += 1
            continue

        kept_raw_sections.append(raw)
        relative_idx += 1

    # Build the ending section, preserving original content if the talk had an ending slide
    if skip_end > 0 and len(section_starts) > 0:
        original_ending_body = get_section_body(get_section_raw(len(section_starts) - 1))
        ending_has_content = original_ending_body.strip() and len(original_ending_body.strip()) > 10
    else:
        ending_has_content = False

    # Renumber the kept sections sequentially starting from 4
    # (1=version, 2=title, 3=about-me, 4+ = talk content)
    slide_num = 4
    renumbered_sections = []
    for raw_section in kept_raw_sections:
        # Replace the SLIDE number in the header
        def renumber(match):
            nonlocal slide_num
            prefix = match.group(1)
            label = match.group(3)
            result = f'{prefix}{slide_num}{label}'
            slide_num += 1
            return result

        renumbered = re.sub(
            r'^(## SLIDE )(\d+[a-z]?)(:.*)$',
            renumber,
            raw_section,
            count=1,
            flags=re.MULTILINE
        )
        renumbered_sections.append(renumbered)

    # Build the ending section, preserving original ending content if available
    ending_num = slide_num  # Next number after all content slides
    if ending_has_content:
        ending_section = f"\n## SLIDE {ending_num}: CLOSING SLIDE\n{original_ending_body}"
    else:
        ending_section = f"\n## SLIDE {ending_num}: CLOSING SLIDE\n\n[Template closing slide - contact info displayed]\n\n---\n\n"

    # Preserve timing/word count appendix
    timing_match = re.search(r'^## TIMING CHECKPOINTS.*', slide_content, re.MULTILINE | re.DOTALL)
    appendix = slide_content[timing_match.start():] if timing_match else ""

    # Assemble the output
    output = preamble
    for section in front_sections:
        output += section + "\n"
    for section in renumbered_sections:
        output += section
    output = output.rstrip() + "\n\n"
    output += ending_section
    if appendix:
        output += appendix

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Updated script saved to: {output_path}")

    # Count sections for verification
    new_count = len(re.findall(r'^## SLIDE ', output, re.MULTILINE))
    print(f"Script now has {new_count} SLIDE sections")


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert(talk_deck_path, template_deck_path, script_path, title=None, subtitle=None, output_dir=None):
    """Main conversion function."""

    # Set up paths
    talk_name = Path(talk_deck_path).stem
    template_name = Path(template_deck_path).stem

    if output_dir is None:
        output_dir = os.path.dirname(talk_deck_path) or '.'
    os.makedirs(output_dir, exist_ok=True)

    output_pptx = os.path.join(output_dir, f'{talk_name}_templated.pptx')
    output_script = os.path.join(output_dir, f'{Path(script_path).stem}_templated.md')

    # Working directories — use temp space to avoid permission issues on mounted dirs
    import tempfile
    work_dir = os.path.join(tempfile.gettempdir(), '_conversion_work')
    talk_unpacked = os.path.join(work_dir, 'talk')
    template_unpacked = os.path.join(work_dir, 'template')
    output_unpacked = os.path.join(work_dir, 'output')

    print("=" * 60)
    print("Deck-to-Template Converter")
    print("=" * 60)

    # Step 1: Unpack both decks
    print("\n[1/8] Unpacking decks...")
    unpack_pptx(talk_deck_path, talk_unpacked)
    unpack_pptx(template_deck_path, template_unpacked)

    # Extract title from talk slide XML (most reliable) or script
    if not title:
        title = extract_title_from_script(script_path, talk_unpacked_dir=talk_unpacked)
        print(f"Auto-extracted title: {title}")

    # Step 2: Start from template as base
    print("[2/8] Setting up template base...")
    if os.path.exists(output_unpacked):
        shutil.rmtree(output_unpacked)
    shutil.copytree(template_unpacked, output_unpacked)

    # Step 3: Get template slide order and identify bookend slides
    print("[3/8] Identifying template bookend slides...")
    template_slide_order = get_slide_order(template_unpacked)
    print(f"  Template has {len(template_slide_order)} slides")

    # Template front slides: slides 1-3 (version, title, about-me)
    # Template ending slide: last slide
    front_slides = template_slide_order[:3]  # First 3 slides
    ending_slide = template_slide_order[-1]   # Last slide

    print(f"  Front slides: {front_slides}")
    print(f"  Ending slide: {ending_slide}")

    # Step 4: Get talk deck slide order and compute scaling
    talk_slide_order_full = get_slide_order(talk_unpacked)
    print(f"\n[4/8] Talk deck has {len(talk_slide_order_full)} slides")

    # Identify and skip the talk's own bookend slides (version, title, ending)
    # since the template already provides these.
    # Detect bookends by examining slide content.
    talk_slides_dir = os.path.join(talk_unpacked, 'ppt', 'slides')
    talk_skip_front = 0
    talk_skip_end = 0

    # Check first 2 slides for version/title patterns
    for i, slide_path in enumerate(talk_slide_order_full[:3]):
        slide_file = os.path.join(talk_slides_dir, os.path.basename(slide_path))
        text = get_text_content(slide_file).lower()
        if i == 0 and ('version' in text or re.search(r'v?\d+\.\d+', text)):
            talk_skip_front = max(talk_skip_front, 1)
            print(f"  Skipping talk slide 1 (version slide)")
        elif i == 1 and (title.lower() in text or 'presented by' in text):
            talk_skip_front = max(talk_skip_front, 2)
            print(f"  Skipping talk slide 2 (title slide)")

    # Check last slide for ending pattern
    last_slide_path = os.path.join(talk_slides_dir, os.path.basename(talk_slide_order_full[-1]))
    last_text = get_text_content(last_slide_path).lower()
    if ("that's all" in last_text or 'thanks' in last_text or
            'thank you' in last_text or 'contact' in last_text):
        talk_skip_end = 1
        print(f"  Skipping talk last slide (ending slide)")

    # Apply bookend skipping
    if talk_skip_end:
        talk_slide_order = talk_slide_order_full[talk_skip_front:-talk_skip_end]
    else:
        talk_slide_order = talk_slide_order_full[talk_skip_front:]
    print(f"  Using {len(talk_slide_order)} talk content slides (skipped {talk_skip_front} front, {talk_skip_end} end)")

    # Detect and remove duplicate slides (consecutive slides with identical text)
    duplicate_indices = detect_duplicate_slides(talk_unpacked, talk_slide_order)
    if duplicate_indices:
        print(f"  Detected {len(duplicate_indices)} duplicate slides to skip: {sorted(duplicate_indices)}")
        talk_slide_order = [s for i, s in enumerate(talk_slide_order) if i not in duplicate_indices]
        print(f"  After dedup: {len(talk_slide_order)} talk content slides")

    # Compute scaling factors for position/size adjustment
    talk_pres_xml = os.path.join(talk_unpacked, 'ppt', 'presentation.xml')
    template_pres_xml = os.path.join(template_unpacked, 'ppt', 'presentation.xml')
    talk_cx, talk_cy = get_slide_size(talk_pres_xml)
    tmpl_cx, tmpl_cy = get_slide_size(template_pres_xml)
    x_scale = tmpl_cx / talk_cx
    y_scale = tmpl_cy / talk_cy
    needs_scaling = abs(x_scale - 1.0) > 0.01 or abs(y_scale - 1.0) > 0.01
    if needs_scaling:
        print(f"  Slide size mismatch: talk={talk_cx}x{talk_cy} template={tmpl_cx}x{tmpl_cy}")
        print(f"  Will scale positions by {x_scale:.4f}x, {y_scale:.4f}y")
    else:
        print(f"  Slide sizes match - no scaling needed")

    # Parse script to identify section dividers
    script_sections = parse_script_slides(script_path)
    print(f"  Script has {len(script_sections)} SLIDE sections")

    # Build a set of divider indices relative to the post-bookend-skip, post-dedup
    # talk_slide_order list. The script sections include all slides (including
    # bookends), so we offset by talk_skip_front. Then we also need to account
    # for any duplicate slides that were removed.

    # First: collect divider indices relative to post-bookend-skip order
    # (before dedup)
    script_offset = talk_skip_front

    # Step 5: Remove all template content slides from output (keep infrastructure)
    print("\n[5/8] Rebuilding slide list...")
    pres_xml = os.path.join(output_unpacked, 'ppt', 'presentation.xml')
    pres_rels = os.path.join(output_unpacked, 'ppt', '_rels', 'presentation.xml.rels')

    # Remove all existing slides from the output presentation
    remove_all_slides_from_presentation(pres_xml, pres_rels)

    # Also remove all slide XML files from the output (we'll copy fresh ones)
    output_slides_dir = os.path.join(output_unpacked, 'ppt', 'slides')
    output_rels_dir = os.path.join(output_slides_dir, '_rels')
    for f in glob.glob(os.path.join(output_slides_dir, 'slide*.xml')):
        os.remove(f)
    for f in glob.glob(os.path.join(output_rels_dir, 'slide*.xml.rels')):
        os.remove(f)

    # Ensure media directory exists
    output_media_dir = os.path.join(output_unpacked, 'ppt', 'media')
    os.makedirs(output_media_dir, exist_ok=True)

    # Step 6: Copy bookend slides from template + talk slides
    print("[6/8] Copying and remapping slides...")
    all_slide_nums = []
    slide_counter = 1
    all_media_copies = []

    # --- Copy template front slides (1-3) ---
    for i, slide_rel_path in enumerate(front_slides):
        slide_basename = os.path.basename(slide_rel_path)
        m = re.match(r'slide(\d+)\.xml', slide_basename)
        src_num = int(m.group(1))

        new_num = slide_counter

        # Copy the slide file
        src_slide = os.path.join(template_unpacked, 'ppt', 'slides', slide_basename)
        dest_slide = os.path.join(output_slides_dir, f'slide{new_num}.xml')
        shutil.copy2(src_slide, dest_slide)

        # Copy the rels file (keep original layout references since we're using the template)
        src_rels = os.path.join(template_unpacked, 'ppt', 'slides', '_rels', f'{slide_basename}.rels')
        dest_rels = os.path.join(output_rels_dir, f'slide{new_num}.xml.rels')
        if os.path.exists(src_rels):
            shutil.copy2(src_rels, dest_rels)
            # Copy any media referenced by this slide
            rels_doc = parse_xml(src_rels)
            for rel in rels_doc.getElementsByTagName('Relationship'):
                target = rel.getAttribute('Target')
                if '../media/' in target:
                    media_name = os.path.basename(target)
                    src_media = os.path.join(template_unpacked, 'ppt', 'media', media_name)
                    dest_media = os.path.join(output_media_dir, media_name)
                    if os.path.exists(src_media) and not os.path.exists(dest_media):
                        shutil.copy2(src_media, dest_media)

        # Add to presentation
        add_slide_to_presentation(pres_xml, pres_rels, new_num)
        all_slide_nums.append(new_num)

        # Handle special attributes (version slide is hidden)
        if i == 0:
            # Ensure version slide has show="0"
            doc = parse_xml(dest_slide)
            sld_elem = doc.getElementsByTagName('p:sld')[0]
            sld_elem.setAttribute('show', '0')
            write_xml(doc, dest_slide)
            # Update version number and date
            update_version_slide(dest_slide)

        print(f"  Template slide {src_num} -> slide{new_num} (front {'version' if i==0 else 'title' if i==1 else 'about-me'})")
        slide_counter += 1

    # Update title on slide 2
    title_slide_path = os.path.join(output_slides_dir, 'slide2.xml')
    if os.path.exists(title_slide_path):
        update_title_slide(title_slide_path, title, subtitle)
        print(f"  Updated title slide with: {title}")

    # --- Copy talk slides ---
    # Build a map of script slide index -> section info for divider detection.
    # script_offset accounts for skipped front bookend slides so script indices
    # align with the pre-dedup talk slide order. We then remap through dedup
    # to get the final index in the current talk_slide_order.

    # Step 1: Find divider indices in the pre-dedup order
    pre_dedup_divider_indices = set()
    for idx, (header, body) in enumerate(script_sections):
        header_lower = header.lower()
        if 'section divider' in header_lower or 'divider' in header_lower:
            adjusted_idx = idx - script_offset
            if adjusted_idx >= 0:
                pre_dedup_divider_indices.add(adjusted_idx)

    # Step 2: Remap through dedup — build old_idx -> new_idx mapping
    # duplicate_indices contains indices that were removed from the pre-dedup order
    divider_indices = set()
    new_idx = 0
    pre_dedup_len = len(talk_slide_order) + len(duplicate_indices) if duplicate_indices else len(talk_slide_order)
    for old_idx in range(pre_dedup_len):
        if duplicate_indices and old_idx in duplicate_indices:
            continue  # This slide was removed
        if old_idx in pre_dedup_divider_indices:
            divider_indices.add(new_idx)
        new_idx += 1

    talk_media_prefix = "talk_"  # Prefix for talk media to avoid conflicts

    for idx, slide_rel_path in enumerate(talk_slide_order):
        slide_basename = os.path.basename(slide_rel_path)
        m_num = re.match(r'slide(\d+)\.xml', slide_basename)
        src_num = int(m_num.group(1))
        new_num = slide_counter

        # Check if this is a section divider (by script header match)
        is_divider = idx in divider_indices

        if is_divider:
            # Get the divider text from the slide
            src_slide = os.path.join(talk_unpacked, 'ppt', 'slides', slide_basename)
            divider_text = get_text_content(src_slide).strip()
            # Clean up: remove slide numbers and extra whitespace
            divider_text = re.sub(r'\s*\d+\s*$', '', divider_text).strip()
            if not divider_text:
                divider_text = "Section"

            # Create styled section divider
            create_section_divider(output_slides_dir, new_num, divider_text)
            create_slide_rels(output_rels_dir, new_num, "../slideLayouts/slideLayout5.xml")
            print(f"  Talk slide {src_num} -> slide{new_num} (section divider: {divider_text[:40]})")
        else:
            # Regular slide: copy and remap layout to slideLayout5
            src_slide = os.path.join(talk_unpacked, 'ppt', 'slides', slide_basename)
            dest_slide = os.path.join(output_slides_dir, f'slide{new_num}.xml')
            shutil.copy2(src_slide, dest_slide)

            # Handle relationships
            src_rels = os.path.join(talk_unpacked, 'ppt', 'slides', '_rels', f'{slide_basename}.rels')
            if os.path.exists(src_rels):
                rels_doc = parse_xml(src_rels)

                for rel in rels_doc.getElementsByTagName('Relationship'):
                    rtype = rel.getAttribute('Type')
                    target = rel.getAttribute('Target')

                    # Remap layout to template's slideLayout5 (white curved lines)
                    if 'slideLayout' in rtype:
                        rel.setAttribute('Target', '../slideLayouts/slideLayout5.xml')

                    # Handle media: copy with potential rename to avoid conflicts
                    if '../media/' in target:
                        media_name = os.path.basename(target)
                        src_media = os.path.join(talk_unpacked, 'ppt', 'media', media_name)

                        # Check for conflict with template media
                        dest_media = os.path.join(output_media_dir, media_name)
                        if os.path.exists(dest_media) and os.path.exists(src_media):
                            # Check if they're the same file
                            if os.path.getsize(src_media) != os.path.getsize(dest_media):
                                # Different file, need to rename
                                name_base, name_ext = os.path.splitext(media_name)
                                new_media_name = f'{talk_media_prefix}{name_base}{name_ext}'
                                dest_media = os.path.join(output_media_dir, new_media_name)
                                rel.setAttribute('Target', f'../media/{new_media_name}')

                        if os.path.exists(src_media):
                            shutil.copy2(src_media, dest_media)

                    # Handle charts: copy chart XML, chart rels, and embedded data
                    # Target can be relative (../charts/chart1.xml) or absolute (/ppt/charts/chart1.xml)
                    if 'chart' in rtype.lower() and ('charts/' in target):
                        chart_name = os.path.basename(target)
                        src_chart = os.path.join(talk_unpacked, 'ppt', 'charts', chart_name)
                        # Normalize target to relative path for the output rels
                        if target.startswith('/'):
                            rel.setAttribute('Target', f'../charts/{chart_name}')
                        dest_charts_dir = os.path.join(output_unpacked, 'ppt', 'charts')
                        os.makedirs(dest_charts_dir, exist_ok=True)
                        dest_chart = os.path.join(dest_charts_dir, chart_name)
                        if os.path.exists(src_chart):
                            shutil.copy2(src_chart, dest_chart)
                            # Copy chart rels
                            src_chart_rels_dir = os.path.join(talk_unpacked, 'ppt', 'charts', '_rels')
                            dest_chart_rels_dir = os.path.join(dest_charts_dir, '_rels')
                            os.makedirs(dest_chart_rels_dir, exist_ok=True)
                            src_chart_rels = os.path.join(src_chart_rels_dir, f'{chart_name}.rels')
                            if os.path.exists(src_chart_rels):
                                shutil.copy2(src_chart_rels, os.path.join(dest_chart_rels_dir, f'{chart_name}.rels'))
                                # Copy embedded files referenced by chart rels
                                chart_rels_doc = parse_xml(src_chart_rels)
                                for chart_rel in chart_rels_doc.getElementsByTagName('Relationship'):
                                    chart_target = chart_rel.getAttribute('Target')
                                    if '../embeddings/' in chart_target:
                                        emb_name = os.path.basename(chart_target)
                                        src_emb = os.path.join(talk_unpacked, 'ppt', 'embeddings', emb_name)
                                        dest_emb_dir = os.path.join(output_unpacked, 'ppt', 'embeddings')
                                        os.makedirs(dest_emb_dir, exist_ok=True)
                                        if os.path.exists(src_emb):
                                            shutil.copy2(src_emb, os.path.join(dest_emb_dir, emb_name))
                            print(f"    Copied chart: {chart_name}")

                    # Handle diagrams: copy diagram files
                    if 'diagram' in rtype.lower() and 'diagrams/' in target:
                        diag_name = os.path.basename(target)
                        src_diag = os.path.join(talk_unpacked, 'ppt', 'diagrams', diag_name)
                        dest_diag_dir = os.path.join(output_unpacked, 'ppt', 'diagrams')
                        os.makedirs(dest_diag_dir, exist_ok=True)
                        if os.path.exists(src_diag):
                            shutil.copy2(src_diag, os.path.join(dest_diag_dir, diag_name))

                    # Remove notes slide references (they'd need separate handling)
                    if 'notesSlide' in rtype:
                        rel.parentNode.removeChild(rel)

                dest_rels = os.path.join(output_rels_dir, f'slide{new_num}.xml.rels')
                write_xml(rels_doc, dest_rels)
            else:
                create_slide_rels(output_rels_dir, new_num)

            # Strip explicit background so slide inherits curved-lines from layout
            strip_slide_background(dest_slide)

            # Recolor white/light text to dark (invisible on white background)
            # Also remap accent colors that don't work on white backgrounds:
            # - 00A79D (teal) was accent text on dark slides -> 003366 (dark blue)
            recolor_light_text(dest_slide, accent_remap={'00A79D': '003366'})

            # Scale positions/sizes if slide dimensions differ
            if needs_scaling:
                scale_slide_positions(dest_slide, x_scale, y_scale, max_cx=tmpl_cx, max_cy=tmpl_cy)

            print(f"  Talk slide {src_num} -> slide{new_num}")

        # Add to presentation
        add_slide_to_presentation(pres_xml, pres_rels, new_num)
        all_slide_nums.append(new_num)
        slide_counter += 1

    # --- Copy template ending slide ---
    ending_basename = os.path.basename(ending_slide)
    m_end = re.match(r'slide(\d+)\.xml', ending_basename)
    src_end_num = int(m_end.group(1))
    new_num = slide_counter

    src_end = os.path.join(template_unpacked, 'ppt', 'slides', ending_basename)
    dest_end = os.path.join(output_slides_dir, f'slide{new_num}.xml')
    shutil.copy2(src_end, dest_end)

    # Copy ending slide rels
    src_end_rels = os.path.join(template_unpacked, 'ppt', 'slides', '_rels', f'{ending_basename}.rels')
    dest_end_rels = os.path.join(output_rels_dir, f'slide{new_num}.xml.rels')
    if os.path.exists(src_end_rels):
        shutil.copy2(src_end_rels, dest_end_rels)
    else:
        create_slide_rels(output_rels_dir, new_num, "../slideLayouts/slideLayout1.xml")

    add_slide_to_presentation(pres_xml, pres_rels, new_num)
    all_slide_nums.append(new_num)
    print(f"  Template slide {src_end_num} -> slide{new_num} (ending)")
    slide_counter += 1

    # Step 7: Update Content_Types.xml and clean orphans
    print("\n[7/9] Updating Content_Types.xml...")
    content_types = os.path.join(output_unpacked, '[Content_Types].xml')
    update_content_types(content_types, set(all_slide_nums), unpacked_dir=output_unpacked)

    # Step 8: Fix notes back-references and clean orphaned files
    print("[8/11] Fixing notes back-references...")
    fix_notes_back_references(output_unpacked)

    print("[9/11] Cleaning orphaned references...")
    clean_orphaned_notes(output_unpacked)

    # Step 10: Run pptx skill's comprehensive clean
    print("[10/12] Running comprehensive cleanup...")
    clean_unpacked(output_unpacked)

    # Step 11: Remove stale Content_Types defaults (e.g., .svg with no SVG files)
    print("[11/12] Cleaning stale Content_Types entries...")
    clean_stale_content_type_defaults(content_types, output_unpacked)

    # Step 12: Pack the output (with validation against template)
    print("[12/12] Packing output deck...")
    # Don't pass --original since our output merges content from multiple sources
    # (template + talk deck), so baseline validation comparison would flag pre-existing
    # issues in the talk deck (e.g., chart XML quirks) as "new" errors.
    pack_pptx(output_unpacked, output_pptx)

    # Update the script
    print("\nUpdating script...")
    update_script(script_path, output_script, title,
                  skip_front=talk_skip_front, skip_end=talk_skip_end,
                  skip_duplicate_indices=duplicate_indices if duplicate_indices else None)

    # Clean up work directory
    shutil.rmtree(work_dir)

    # Summary
    total_slides = len(all_slide_nums)
    print("\n" + "=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"Output deck: {output_pptx}")
    print(f"Output script: {output_script}")
    print(f"Total slides: {total_slides}")
    print(f"  - Front bookend slides: 3 (version, title, about-me)")
    print(f"  - Talk slides: {len(talk_slide_order)} (skipped {talk_skip_front} front + {talk_skip_end} end bookends)")
    print(f"  - Ending slide: 1")
    print(f"  - Section dividers restyled: {len(divider_indices)}")
    print("=" * 60)

    return output_pptx, output_script


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Convert a talk deck to business template style')
    parser.add_argument('--talk-deck', required=True, help='Path to the talk .pptx file')
    parser.add_argument('--template-deck', required=True, help='Path to tst_template.pptx')
    parser.add_argument('--script', required=True, help='Path to the speaker script .md file')
    parser.add_argument('--title', help='Talk title (auto-extracted from script if not provided)')
    parser.add_argument('--subtitle', help='Optional subtitle for the title slide')
    parser.add_argument('--output-dir', help='Output directory (defaults to same as talk deck)')

    args = parser.parse_args()

    # Validate inputs
    for path, name in [(args.talk_deck, 'talk deck'), (args.template_deck, 'template deck'), (args.script, 'script')]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found: {path}")
            sys.exit(1)

    convert(
        talk_deck_path=args.talk_deck,
        template_deck_path=args.template_deck,
        script_path=args.script,
        title=args.title,
        subtitle=args.subtitle,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
