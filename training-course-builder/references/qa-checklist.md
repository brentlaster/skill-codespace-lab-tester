# QA Checklist for Training Course Materials

Use this checklist when reviewing or auditing existing training materials.
Report findings organized by severity: Critical (blocks students), Warning (confusing but workable),
and Info (polish/improvement suggestions).

## 1. Labs.md Integrity

### Step Numbering
- [ ] Steps are numbered sequentially within each lab (no gaps, no duplicates)
- [ ] Lab numbers are sequential across the document
- [ ] No steps reference a future step that doesn't exist

### Code Commands
- [ ] All code blocks contain valid, runnable commands
- [ ] Commands match the current working directory context (has the student cd'd there?)
- [ ] File paths in commands match actual files in the repo
- [ ] Python scripts referenced actually exist in the expected directory
- [ ] Model names in commands match what's installed/available in the environment

### Image References
- [ ] Every `![...](./images/...)` reference points to an existing file in images/
- [ ] Image filenames match exactly (case-sensitive)
- [ ] All images use `?raw=true` parameter
- [ ] Screenshots show what the text describes (if viewable)

### Internal Links
- [ ] File links like `[**dir/file.py**](./dir/file.py)` point to existing files
- [ ] External URLs (HuggingFace, documentation sites) are still valid

### Format Consistency
- [ ] Every lab has a bold title and Purpose statement
- [ ] Every lab ends with the END OF LAB marker
- [ ] Spacing (`<br><br>`) is consistent between steps
- [ ] Optional steps are clearly marked
- [ ] Copyright/attribution footer is present and current year

## 2. Code Files

### Skeleton + Complete Pairs
- [ ] Every skeleton file in topic dirs has a corresponding complete version in extra/
- [ ] Complete files contain ALL the code the skeleton is missing (no partial completions)
- [ ] Skeleton files have clear TODO markers or gaps where students merge code
- [ ] The diff between skeleton and complete is clean (no unrelated differences)

### Code Quality
- [ ] All Python files have proper docstrings explaining what they do
- [ ] Import statements reference installed packages (check requirements.txt)
- [ ] No hardcoded paths that won't work in the devcontainer
- [ ] API endpoints use correct URLs (localhost ports, service names)
- [ ] Model names are current and available

### Runability
- [ ] Each script can be run with the command shown in labs.md
- [ ] Scripts handle common errors gracefully (service not running, model not downloaded)
- [ ] Output matches what labs.md describes students should see

## 3. Environment & Setup

### devcontainer.json
- [ ] Base image is current and available
- [ ] Python version is appropriate for all dependencies
- [ ] All required features are listed
- [ ] postCreateCommand installs all dependencies successfully
- [ ] postAttachCommand correctly restarts services
- [ ] Host requirements are reasonable (not too high for typical laptops)
- [ ] Copilot is disabled in settings

### requirements.txt
- [ ] All packages imported in any .py file are listed
- [ ] Version constraints are reasonable (not pinned to exact old versions)
- [ ] No conflicting version requirements between packages
- [ ] Comments explain each group of dependencies
- [ ] Non-pip dependencies are noted in comments

### Scripts
- [ ] pysetup.sh creates venv and installs requirements correctly
- [ ] Service startup scripts work in the devcontainer environment
- [ ] Scripts have proper shebang lines (#!/usr/bin/env bash)
- [ ] Scripts are executable (have execute permissions or are called with bash)

### README.md
- [ ] Dev Container open button URL is correct for this repo
- [ ] Prerequisites list is accurate and complete
- [ ] System requirements are realistic
- [ ] Troubleshooting section covers common issues
- [ ] Setup timing estimates are accurate

## 4. Slides (if present)

### Content Alignment
- [ ] Slide topics correspond to lab topics in order
- [ ] Code snippets in slides match actual code files
- [ ] Version numbers mentioned in slides match requirements.txt
- [ ] Diagrams accurately represent the architectures students build

### Formatting
- [ ] Consistent theme/template throughout
- [ ] Text is readable (font size, contrast)
- [ ] Speaker notes are present and useful
- [ ] No orphaned slides (slides without corresponding lab content, unless intentionally conceptual)

## 5. Cross-Cutting Concerns

### Version Currency
- [ ] All library versions in requirements.txt are reasonably current
- [ ] API calls use current (non-deprecated) methods
- [ ] Model names reference currently available models
- [ ] External tool versions (Ollama, Docker, VS Code) are current
- [ ] Documentation links point to current versions

### Consistency
- [ ] File naming is consistent throughout (no mixed conventions)
- [ ] Code style is consistent across all Python files
- [ ] Terminology is consistent between slides, labs, and code comments
- [ ] The same concept isn't explained differently in different places

### Completeness
- [ ] Every concept introduced in slides has a corresponding lab exercise
- [ ] Every lab references the prerequisite knowledge/setup
- [ ] No dead-end labs (labs that set up something never used again)
- [ ] The progression from Lab 1 to Lab N tells a coherent story

## Reporting Format

When reporting QA findings, use this structure:

```
## QA Report: [Course Name] - [Date]

### Critical (Blocks Students)
1. [File]: [Description of issue]
   - **Impact**: [What goes wrong for students]
   - **Fix**: [Suggested resolution]

### Warning (Confusing but Workable)
1. [File]: [Description of issue]
   - **Impact**: [How this confuses students]
   - **Fix**: [Suggested resolution]

### Info (Polish)
1. [File]: [Description of issue]
   - **Suggestion**: [Improvement idea]

### Summary
- Critical: [N] issues
- Warning: [N] issues
- Info: [N] suggestions
- Overall assessment: [Ready/Needs fixes/Major revision needed]
```
