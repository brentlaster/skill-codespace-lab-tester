# Common Lab Patterns Reference

This reference covers specific patterns you'll encounter in TechUpSkills training labs and how to handle them during automated testing.

## Table of Contents
1. [Code Block Types](#code-block-types)
2. [Diff-Merge Pattern Details](#diff-merge-pattern-details)
3. [Server/Application Patterns](#serverapplication-patterns)
4. [Environment Setup Patterns](#environment-setup-patterns)
5. [GitHub-Related Steps](#github-related-steps)

## Code Block Types

### Terminal commands
Fenced code blocks (gray boxes) directly under a step number typically contain terminal commands:
```
python my_script.py
```
Execute these in the terminal and observe output.

### File content to write
Some code blocks contain content that should be written to a file. The step text will say something like "paste the following into [filename]" or "add the following code to [filename]." Use `cat > filename << 'EOF'` or similar to write the content.

### Code to observe (not execute)
Occasionally code blocks show code for reference only — the step text will say "notice" or "observe" rather than "run" or "enter." Don't execute these.

## Diff-Merge Pattern Details

The diff-merge pattern looks like this in labs:

```
N. [Context]. Use the diff command to see the differences:
code -d ../extra/complete_file.txt skeleton_file.py
```

**Decision tree:**
1. Read the surrounding text carefully
2. If text says "you don't need to make any changes" / "no changes are necessary" / "just observe" → skip the copy, move on
3. Otherwise → run: `cp ../extra/complete_file.txt skeleton_file.py`

**Common paths:**
- Complete files: `extra/labN_topic_complete.txt` or `../extra/labN_complete.txt`
- Skeleton files: `topic/labN.py` or `topic/labN_skeleton.py`
- Sometimes referenced from `labs/common/` directory

## Server/Application Patterns

### Python web servers (Flask, Gradio, Streamlit)
- Start with: `python app.py` or `gradio app.py` or `streamlit run app.py`
- They'll print a URL (usually localhost:PORT)
- The codespace may auto-forward the port
- Leave running, open a new terminal for subsequent steps
- Stop with Ctrl+C when instructed

### Ollama model operations
- `ollama pull model:tag` — downloads a model (can take minutes)
- `ollama run model:tag` — starts interactive session (Ctrl+D or /bye to exit)
- `ollama list` — check available models

### Background processes
- Some steps run things with `&` or `nohup` — these continue running
- If a step uses `&`, the terminal will show a PID and return to prompt

## Environment Setup Patterns

### Python virtual environments
Labs typically activate a venv at the start:
- `source py_env/bin/activate` or `source .venv/bin/activate`
- The prompt changes to show `(py_env)` or `(.venv)`
- If you see "ModuleNotFoundError" it often means the venv isn't activated

### pip installs within labs
Some labs install additional packages:
- `pip install package_name`
- These should succeed if the venv is active

### Environment variables
Labs may set environment variables:
- `export VAR_NAME=value`
- These persist only in the current terminal session

## GitHub-Related Steps

### Viewing GitHub features
Some steps may reference GitHub features (Issues, PRs, Actions). These may require:
- Navigating to the GitHub repo in a browser tab (separate from the Codespace tab)
- Using `gh` CLI commands in the terminal

### Git operations within the codespace
Some labs include git commands:
- `git add`, `git commit`, `git push`
- These operate on the codespace's copy of the repo
- They should work as-is in the codespace terminal
