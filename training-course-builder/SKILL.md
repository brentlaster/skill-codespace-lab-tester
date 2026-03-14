---
name: training-course-builder
description: >
  Build, update, modernize, and QA technical training courses. Use this skill whenever the user wants to:
  create new training labs, slides, or course materials; update existing labs or slides for newer library/API versions;
  review or QA training materials for broken links, outdated content, or inconsistencies; generate supporting files
  like requirements.txt, devcontainer configs, setup scripts, skeleton code, or completed reference code;
  modernize a training course to reflect current best practices; or create a full course repo from scratch.
  Trigger on any mention of "training", "course", "labs", "slides", "workshop", "hands-on", "lab exercise",
  "course materials", "training deck", "student guide", or references to updating/creating educational technical content.
  Also trigger when the user references their course repo structure (labs.md, code directories, images/, extra/, etc.)
  even without explicitly saying "training". This skill is for Brent Laster / TechUpSkills / Tech Skills Transformations
  training courses focused on AI/ML engineering topics.
---

# Training Course Builder

You are helping Brent Laster (TechUpSkills / Tech Skills Transformations) create, update, modernize, and QA
technical training courses. Brent teaches enterprise AI/ML engineering workshops with hands-on labs run in
VS Code devcontainers or GitHub Codespaces.

## Before You Start

1. **Determine the task type.** Read the user's request and figure out which workflow applies:
   - **New course creation** - building a full course repo from scratch
   - **New lab creation** - adding labs to an existing course
   - **Content update / modernization** - updating existing materials for newer library versions
   - **Slide creation or update** - working with .pptx presentation files
   - **QA / Review** - checking existing materials for issues
   - **Supporting file generation** - devcontainer configs, scripts, requirements, skeleton code

2. **Read the relevant reference files** in this skill's `references/` directory:
   - `references/lab-format.md` - Lab writing conventions and format rules
   - `references/repo-structure.md` - Standard course repository layout
   - `references/qa-checklist.md` - QA review checklist for course materials
   - `references/slide-conventions.md` - Slide creation and formatting guidelines

3. **If working with an existing course**, read its `labs.md`, `README.md`, and browse the repo structure first
   to understand the current state before making changes.

4. **If creating or updating slides**, also read the `pptx` skill (`/sessions/keen-determined-keller/mnt/.skills/skills/pptx/SKILL.md`)
   since you'll need its techniques for PowerPoint manipulation.

---

## Course Repository Structure

Every course follows this standard layout. When creating a new course, generate all of these components.
When updating, preserve this structure.

```
[course-name]/
├── .devcontainer/
│   └── devcontainer.json        # Dev container config (VS Code + Docker)
├── .github/
│   └── copilot-instructions.md  # AI assistant instructions for students
├── images/                      # Screenshots referenced in labs.md
├── extra/                       # Completed code versions for diff-merge labs
├── scripts/
│   ├── pysetup.sh              # Python environment setup
│   ├── startup_ollama.sh       # Service startup (if needed)
│   └── startOllama.sh          # Service re-attach
├── [topic-dirs]/               # Code organized by topic (e.g., llm/, rag/, neo4j/)
│   └── *.py                    # Lab code files
├── tools/                      # Utility scripts (indexers, search tools)
├── labs.md                     # THE main lab document students follow
├── README.md                   # Setup instructions + prerequisites
├── README-Codespace.md         # Alternative codespace setup (if applicable)
├── requirements.txt            # Python dependencies
├── LICENSE                     # License file
└── .gitignore                  # Standard Python + IDE ignores
```

See `references/repo-structure.md` for full details on each component.

---

## Lab Writing

Labs are the heart of the training. They live in a single `labs.md` file that students follow step-by-step.

### Core Principles

- **Guided discovery**: Students learn by doing, not by reading. Each step should have them execute something
  and observe the result. Explanations come through what they see, not walls of text.
- **Progressive complexity**: Labs build on each other. Early labs cover fundamentals, later labs combine concepts.
- **Skeleton + completed pattern**: For complex labs, provide a skeleton file (with gaps/TODOs) that students
  work with, and a completed version in `extra/` that they can diff-merge or reference.
- **Visual confirmation**: After each significant step, tell students what they should see and reference a
  screenshot image. Students need to know they're on track.

### Format Rules

Read `references/lab-format.md` for the complete format specification. Key points:

- Each lab starts with a bold title and a **Purpose** statement
- Steps are numbered sequentially within each lab
- Code blocks use triple backticks (no language specifier unless needed for syntax highlighting)
- Screenshots are referenced as `![alt text](./images/filename.png?raw=true "tooltip")`
- Use `<br><br>` between steps for spacing
- Each lab ends with `<p align="center">**[END OF LAB]**</p></br></br>`
- Optional/advanced steps are clearly marked
- The document ends with copyright notice

### When Creating New Labs

1. Understand the topic and what concepts need to be taught
2. Identify what code files are needed (create them in appropriate topic directories)
3. For each lab:
   - Write a clear purpose statement
   - Create numbered steps that have students run commands and observe output
   - Generate the code files (both skeleton and completed versions where appropriate)
   - Note where screenshots will be needed (use descriptive placeholder names like `./images/ae-new-1.png`)
   - Include discussion points or "what to notice" guidance
4. Ensure labs build logically on each other

### When Updating Existing Labs

1. Read the current labs.md thoroughly
2. Identify what needs to change (usually API calls, model names, library imports, output formatting)
3. Update both the lab instructions AND the corresponding code files
4. Update both skeleton and completed versions if both exist
5. Flag any screenshots that may need to be retaken (output format changes, UI changes)
6. Update requirements.txt if dependency versions changed

---

## Slide Creation & Updates

Slides accompany the labs and provide the conceptual framework. Use the `pptx` skill for the actual
PowerPoint file manipulation.

### Slide Conventions

- Extract the theme/template from Brent's existing .pptx files in the course repo
- Slides should be conceptual and visual, not walls of text
- Use diagrams and flow charts to explain architectures
- Include speaker notes with talking points and additional context
- Slides should map to lab content (students see the concept, then do the lab)

See `references/slide-conventions.md` for detailed formatting guidelines.

### When Updating Slides

1. Read the existing .pptx to understand current content and structure
2. Identify slides that reference outdated versions, APIs, or concepts
3. Update content while preserving the existing theme and layout
4. Update speaker notes to reflect changes
5. Flag any diagrams that need to be redrawn

---

## Content Modernization

When updating a course for newer library/API versions:

1. **Research current versions**: Check what has changed since the course was last updated.
   Look at changelogs, migration guides, and updated documentation.
2. **Audit dependencies**: Review `requirements.txt` and identify which packages need version bumps.
   Check for breaking changes in each updated package.
3. **Update code files**: Modify Python files to use current APIs. Common changes include:
   - Import path changes (e.g., LangChain reorganizations)
   - Deprecated function replacements
   - New parameter names or signatures
   - Model name updates (e.g., new Ollama model tags)
4. **Update labs.md**: Adjust any instructions that reference changed APIs, outputs, or behaviors.
5. **Update slides**: Refresh any slides that show code snippets, architecture diagrams, or version numbers.
6. **Update devcontainer**: Adjust base images, features, or post-create commands if needed.
7. **Test the full flow**: Mentally walk through every lab step to verify coherence.

---

## QA / Review

When reviewing existing materials, use the checklist in `references/qa-checklist.md`. Key areas:

- **Consistency**: Do labs.md instructions match the actual code files?
- **Completeness**: Are all referenced files present? Are all code paths covered?
- **Currency**: Are library versions current? Are APIs still valid?
- **Correctness**: Do step numbers flow correctly? Are there duplicate or missing steps?
- **Screenshots**: Are all referenced images present in the images/ directory?
- **Links**: Do internal links (to code files, external sites) work?
- **Skeleton/complete sync**: Do skeleton files and their completed counterparts in extra/ match up?
- **Environment**: Does requirements.txt include all needed packages? Does devcontainer config work?

---

## Supporting File Generation

### devcontainer.json

Standard pattern for AI/ML training courses:

```json
{
    "image": "mcr.microsoft.com/devcontainers/base:bookworm",
    "remoteEnv": {
        "OLLAMA_MODEL": "llama3.2:3b"
    },
    "hostRequirements": {
        "cpus": 4,
        "memory": "16gb",
        "storage": "32gb"
    },
    "features": {
        "ghcr.io/devcontainers/features/docker-from-docker:1": {},
        "ghcr.io/devcontainers/features/github-cli:1": {},
        "ghcr.io/devcontainers/features/python:1": {}
    },
    "customizations": {
        "vscode": {
            "settings": {
                "python.terminal.activateEnvInCurrentTerminal": true,
                "python.defaultInterpreterPath": ".venv/bin/python",
                "github.copilot.enable": { "*": false },
                "github.copilot.enableAutoComplete": false,
                "editor.inlineSuggest.enabled": false,
                "workbench.startupEditor": "readme",
                "workbench.editorAssociations": { "*.md": "vscode.markdown.preview.editor" },
                "terminal.integrated.defaultProfile.linux": "bash",
                "terminal.integrated.profiles.linux": {
                    "bash": { "path": "bash", "args": ["-l"] }
                }
            },
            "extensions": ["mathematic.vscode-pdf", "vstirbu.vscode-mermaid-preview"]
        }
    },
    "postCreateCommand": "bash -i scripts/pysetup.sh py_env && bash -i scripts/startup_ollama.sh",
    "postAttachCommand": "bash scripts/startOllama.sh"
}
```

Adjust `remoteEnv`, `features`, `postCreateCommand`, and extensions based on course needs.
Copilot is intentionally disabled in training environments so students learn hands-on.

### pysetup.sh

Standard Python environment setup script:

```bash
#!/usr/bin/env bash
PYTHON_ENV=$1
python3 -m venv ./$PYTHON_ENV \
    && export PATH=./$PYTHON_ENV/bin:$PATH \
    && grep -qxF "source $(pwd)/$PYTHON_ENV/bin/activate" ~/.bashrc \
    || echo "source $(pwd)/$PYTHON_ENV/bin/activate" >> ~/.bashrc
source ./$PYTHON_ENV/bin/activate
if [ -f "./requirements.txt" ]; then
    pip3 install -r "./requirements.txt"
elif [ -f "./requirements/requirements.txt" ]; then
    pip3 install -r "./requirements/requirements.txt"
fi
```

### requirements.txt

Group dependencies by purpose with comments explaining each group.
Pin minimum versions (>=) rather than exact versions for flexibility.

### Skeleton Code Pattern

When creating skeleton + completed code pairs:
- The skeleton file goes in the topic directory (e.g., `rag/lab10.py`)
- The completed version goes in `extra/` (e.g., `extra/lab10_eval_complete.txt`)
  - Use `.txt` extension for completed versions so they don't execute accidentally
- Labs instruct students to use `code -d` to open a diff view between the two files
- Students merge code segments from the completed version into the skeleton

### copilot-instructions.md

Include a `.github/copilot-instructions.md` with the "Explain-this-app" template that helps students
understand code files through a structured explanation format (what it does, high-level flow,
key building blocks, data flow, safe experiments, debug checklist).

### README.md

The README should include:
- Course title and day/session info with revision number
- Setup instructions (Dev Containers button, prerequisites)
- System requirements
- Alternative setup approaches
- Troubleshooting section
- License and attribution

---

## Copyright & Attribution

All materials should include:
- License file in repo root
- Copyright notice at the end of labs.md:
  ```
  <p align="center">
  <b>For educational use only by the attendees of our workshops.</b>
  </p>
  <p align="center">
  <b>(c) [YEAR] Tech Skills Transformations and Brent C. Laster. All rights reserved.</b>
  </p>
  ```
- License section in README.md referencing TechUpSkills / Brent Laster
