# training-course-builder

A Claude skill for building, updating, modernizing, and QA-checking technical training courses — slides, labs, code, and devcontainer setup.

## What It Does

This skill gives Claude deep knowledge of how TechUpSkills / Brent Laster training courses are structured so it can help with the full lifecycle of course development:

- **Create new courses** from scratch with the standard repo layout (devcontainer, labs.md, code directories, scripts, README)
- **Create new labs** with properly formatted step-by-step instructions, skeleton + completed code pairs, and screenshot placeholders
- **Update/modernize existing materials** when libraries release new versions — updates code files, labs.md, requirements.txt, slides, and devcontainer configs
- **QA and review** existing courses for broken links, outdated content, step numbering issues, missing files, and inconsistencies between labs and code
- **Generate supporting files** like devcontainer.json, pysetup.sh, requirements.txt, copilot-instructions.md, and .gitignore
- **Create and update slides** (.pptx) that align with lab content, using the existing course theme/template

## When It Triggers

The skill activates when you mention training, course, labs, slides, workshop, hands-on exercises, lab exercises, course materials, training deck, student guide, labs.md, or anything about creating/updating educational technical content.

## Skill Structure

```
training-course-builder/
├── SKILL.md                          # Main instructions and workflows
└── references/
    ├── lab-format.md                 # Exact labs.md format specification
    ├── repo-structure.md             # Standard course repository layout
    ├── qa-checklist.md               # QA review checklist with reporting format
    └── slide-conventions.md          # Slide creation and formatting guidelines
```

## Key Conventions It Enforces

- Labs follow a strict format: bold titles, purpose statements, numbered steps, `<br><br>` spacing, screenshot references, END OF LAB markers
- Skeleton code files live in topic directories; completed versions go in `extra/` with `.txt` extensions
- Students use `code -d` to diff-merge completed code into skeletons
- Copilot is disabled in devcontainer settings so students learn hands-on
- All materials include Tech Skills Transformations / Brent C. Laster copyright notices

## Installation

Install the `.skill` file through Claude's Settings → Skills, or copy the `training-course-builder/` folder into your skills directory.
