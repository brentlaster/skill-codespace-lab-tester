# Lab Format Specification

This document defines the exact format for labs.md files in TechUpSkills training courses.
Follow these conventions precisely when creating or updating labs.

## Document Header

```markdown
# [Course Full Name]
## [Day/Session] - [Topic Description]
## Session labs
## Revision [X.Y] - [MM/DD/YY]

**Follow the startup instructions in the README.md file IF NOT ALREADY DONE!**

**NOTE: To copy and paste in the codespace, you may need to use keyboard commands - CTRL-C and CTRL-V. Chrome may work best for this.**
```

## Lab Structure

Each lab follows this pattern:

### Lab Title
```markdown
**Lab [N] - [Descriptive Title]**

**Purpose: In this lab, we'll [learn/see/explore] [what the lab teaches].**
```

The purpose statement always starts with "In this lab, we'll" and describes what students will
learn or accomplish. Keep it to one sentence.

### Step Format

Steps are numbered sequentially starting at 1 for each lab:

```markdown
[N]. [Instruction text that tells the student what to do. Can reference files by name
using *italic* formatting or by linking them as [**dir/filename.py**](./dir/filename.py).]

\```
[command to run or code to look at]
\```
![descriptive alt text](./images/imagename.png?raw=true "tooltip text")

<br><br>
```

Key conventions:
- **Step numbering**: Sequential within each lab (1, 2, 3...), resets for each new lab
- **File references**: Use italics for inline mentions (*filename.py*) and bold links for "click to open" ([**dir/filename.py**](./dir/filename.py))
- **Directory references**: Use italics (*llm*, *rag*, *extra*)
- **Commands**: Always in fenced code blocks (triple backticks)
- **Screenshots**: Format is `![alt text](./images/name.png?raw=true "tooltip")`
- **Spacing**: `<br><br>` between each step for visual separation
- **Terminal context**: When students need to change directories, explicitly tell them with a `cd` command

### Code Blocks

- Use plain fenced code blocks (no language specifier) for commands students type
- Use language-specific fencing only when showing code to read (not execute)
- Show the exact command, not abbreviated versions

### Tables

Use markdown tables when comparing data or showing mappings:

```markdown
| **Header 1** | **Header 2** | **Header 3** |
| :---------: | :--------: | :--------------------: |
| value | value | value |
```

Center-align with `:-:` syntax. Bold the headers.

### Optional/Advanced Steps

Mark optional content clearly:

```markdown
[N]. (Optional) If you get done early and want more to do, [instruction].
```

Or for multi-step optional sections:

```markdown
**Steps [N]-[M] are optional and may take longer than lab time allows.**

<br>
```

### Discussion Points

For conceptual takeaways, use a numbered list with bold keywords:

```markdown
[N]. Discussion Points:
   - **[Concept Name]**: [Brief explanation]
   - **[Concept Name]**: [Brief explanation]
```

### Lab Ending

Every lab ends with:

```markdown
<p align="center">
**[END OF LAB]**
</p>
</br></br>
```

Note: Some labs use `<b>[END OF LAB]</b>` instead of `**[END OF LAB]**`. Either is acceptable
but be consistent within a single labs.md file.

### Key Takeaways

Between lab groups or at major transitions, include:

```markdown
**Key Takeaway:**
> [One sentence summary of the key concept]
```

## Document Footer

```markdown
<p align="center">
<b>For educational use only by the attendees of our workshops.</b>
</p>

<p align="center">
<b>(c) [YEAR] Tech Skills Transformations and Brent C. Laster. All rights reserved.</b>
</p>
```

## Image Naming Conventions

- Use descriptive, short names: `ae-[topic]-[number].png` or `arag[number].png`
- The prefix typically relates to the course (ae = AI Engineering, arag = AI RAG, etc.)
- Include the `?raw=true` parameter for GitHub rendering
- Alt text should describe what the screenshot shows
- Tooltip text should match or paraphrase the alt text

## Writing Style

- Use second person ("you will see", "enter the command")
- Be direct and concise in instructions
- Explain the "why" briefly, but focus on the "do"
- After running something, tell students what output to expect
- When output is interesting, explain what it means
- Use "Notice..." to draw attention to important observations
- Reference line numbers when pointing to specific code ("Scroll down to around line 55")

## Diff-Merge Lab Pattern

For labs where students merge completed code into a skeleton:

```markdown
[N]. [Context about what we're building]. We have a completed version and a skeleton version.
Use the diff command to see the differences:

\```
code -d ../extra/[complete_file].txt [skeleton_file].py
\```

<br><br>

[N+1]. Once you have the diff view open, take a moment to look at the structure in the complete
version on the left. Notice [key things to observe].

<br><br>

[N+2]. Now, merge the code segments from the complete file (left side) into the skeleton file
(right side) by clicking the arrow pointing right in the middle bar for each difference.
[Specific order guidance if needed].

<br><br>

[N+3]. After merging all the changes, double-check that there are no remaining diffs
(red blocks on the side). Then close the diff view by clicking the "X" in the tab.
```
